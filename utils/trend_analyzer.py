"""
Price Trend Analyzer

This module provides price trend analysis and deal detection functionality
using statistical models to identify market trends and undervalued properties.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from database.models import PropertyListing, Base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """
    Analyzes price trends and identifies deals in the real estate market
    """
    
    def __init__(self, database_url: str = "sqlite:///realestate.db"):
        """
        Initialize the trend analyzer
        
        Args:
            database_url: Database connection URL
        """
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        
    def calculate_price_trends(self, location: Optional[str] = None, days_back: int = 30) -> Dict:
        """
        Calculate price trends for all locations or a specific location
        
        Args:
            location: Specific location to analyze (None for all)
            days_back: Number of days to look back for analysis
            
        Returns:
            Dict: Trend analysis results
        """
        try:
            # Get data from database
            query = """
                SELECT timestamp, location, price_per_m2, price, area
                FROM property_listings 
                WHERE timestamp >= :start_date
            """
            
            if location:
                query += " AND location = :location"
            
            start_date = datetime.now() - timedelta(days=days_back)
            
            with self.engine.connect() as conn:
                if location:
                    df = pd.read_sql(text(query), conn, params={
                        'start_date': start_date,
                        'location': location
                    })
                else:
                    df = pd.read_sql(text(query), conn, params={'start_date': start_date})
            
            if df.empty:
                logger.warning(f"No data found for trend analysis")
                return {}
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            trends = {}
            
            # Analyze trends by location
            for loc, group in df.groupby('location'):
                if len(group) < 3:  # Need at least 3 data points
                    continue
                
                # Calculate days since first listing
                group = group.sort_values('timestamp')
                group['days'] = (group['timestamp'] - group['timestamp'].min()).dt.days
                
                # Simple linear regression
                X = np.array(group['days'].values).reshape(-1, 1)
                y = np.array(group['price_per_m2'].values)
                
                # Add constant for intercept
                X_with_const = np.column_stack([np.ones(len(X)), X])
                
                # Calculate regression coefficients
                try:
                    beta = np.linalg.inv(X_with_const.T @ X_with_const) @ X_with_const.T @ y
                    slope = beta[1]
                    intercept = beta[0]
                    
                    # Calculate R-squared
                    y_pred = X_with_const @ beta
                    ss_res = np.sum((y - y_pred) ** 2)
                    ss_tot = np.sum((y - np.mean(y)) ** 2)  # type: ignore
                    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                    
                    # Calculate average price for deal detection
                    avg_price = group['price_per_m2'].mean()
                    
                    trends[loc] = {
                        'slope': slope,
                        'intercept': intercept,
                        'r_squared': r_squared,
                        'avg_price_per_m2': avg_price,
                        'data_points': len(group),
                        'trend_direction': 'up' if slope > 0 else 'down' if slope < 0 else 'stable',
                        'trend_strength': 'strong' if abs(slope) > 5 else 'moderate' if abs(slope) > 2 else 'weak'
                    }
                    
                except np.linalg.LinAlgError:
                    logger.warning(f"Could not calculate trend for {loc} - insufficient data")
                    continue
            
            logger.info(f"Calculated trends for {len(trends)} locations")
            return trends
            
        except Exception as e:
            logger.error(f"Error calculating price trends: {e}")
            return {}
    
    def identify_deals(self, deal_threshold: float = 0.8) -> List[Dict]:
        """
        Identify properties that are priced below market average
        
        Args:
            deal_threshold: Threshold for deal detection (0.8 = 20% below average)
            
        Returns:
            List[Dict]: List of deals with details
        """
        try:
            session = self.Session()
            
            # Get all listings with location and price data
            listings = session.query(PropertyListing).filter(
                PropertyListing.location.isnot(None),
                PropertyListing.price_per_m2.isnot(None)
            ).all()
            
            if not listings:
                return []
            
            # Calculate average prices by location
            location_prices = {}
            for listing in listings:
                if listing.location not in location_prices:
                    location_prices[listing.location] = []
                location_prices[listing.location].append(listing.price_per_m2)
            
            # Calculate averages
            location_averages = {}
            for location, prices in location_prices.items():
                if len(prices) >= 3:  # Need at least 3 listings for meaningful average
                    location_averages[location] = np.mean(prices)
            
            deals = []
            
            # Identify deals
            for listing in listings:
                if listing.location in location_averages:
                    avg_price = location_averages[listing.location]
                    price_ratio = listing.price_per_m2 / avg_price
                    
                    if price_ratio <= deal_threshold:
                        # Update listing with deal flag and market average
                        listing.is_deal = True  # type: ignore
                        listing.market_average_price = avg_price  # type: ignore
                        
                        deals.append({
                            'id': listing.id,
                            'title': listing.title,
                            'location': listing.location,
                            'price': listing.price,
                            'price_per_m2': listing.price_per_m2,
                            'market_average': avg_price,
                            'discount_percentage': round((1 - price_ratio) * 100, 1),
                            'source': listing.source,
                            'link': listing.link
                        })
            
            # Commit changes to database
            session.commit()
            session.close()
            
            logger.info(f"Identified {len(deals)} deals")
            return deals
            
        except Exception as e:
            logger.error(f"Error identifying deals: {e}")
            return []
    
    def get_market_insights(self) -> Dict:
        """
        Get comprehensive market insights
        
        Returns:
            Dict: Market insights including trends, deals, and statistics
        """
        try:
            # Calculate trends
            trends = self.calculate_price_trends()
            
            # Identify deals
            deals = self.identify_deals()
            
            # Get basic statistics
            session = self.Session()
            total_listings = session.query(PropertyListing).count()
            active_deals = session.query(PropertyListing).filter(PropertyListing.is_deal == True).count()
            
            # Get recent listings (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_listings = session.query(PropertyListing).filter(
                PropertyListing.timestamp >= week_ago
            ).count()
            
            session.close()
            
            insights = {
                'total_listings': total_listings,
                'active_deals': active_deals,
                'recent_listings': recent_listings,
                'deal_percentage': round((active_deals / total_listings * 100), 1) if total_listings > 0 else 0,
                'trends': trends,
                'top_deals': sorted(deals, key=lambda x: x['discount_percentage'], reverse=True)[:5],
                'analysis_date': datetime.now().isoformat()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting market insights: {e}")
            return {}
    
    def update_listing_coordinates(self, location_coords: Dict[str, Tuple[float, float]]):
        """
        Update listing coordinates for map integration
        
        Args:
            location_coords: Dictionary mapping location names to (lat, lng) tuples
        """
        try:
            session = self.Session()
            
            for location, (lat, lng) in location_coords.items():
                listings = session.query(PropertyListing).filter(
                    PropertyListing.location == location
                ).all()
                
                for listing in listings:
                    listing.latitude = lat  # type: ignore
                    listing.longitude = lng  # type: ignore
            
            session.commit()
            session.close()
            
            logger.info(f"Updated coordinates for {len(location_coords)} locations")
            
        except Exception as e:
            logger.error(f"Error updating coordinates: {e}")


# Vietnamese location coordinates for map integration
VIETNAM_LOCATIONS = {
    'Ho Chi Minh City': (10.8231, 106.6297),
    'Hanoi': (21.0285, 105.8542),
    'Da Nang': (16.0544, 108.2022),
    'Hai Phong': (20.8449, 106.6881),
    'Can Tho': (10.0452, 105.7469),
    'Bien Hoa': (10.9574, 106.8426),
    'Hue': (16.4637, 107.5909),
    'Nha Trang': (12.2388, 109.1967),
    'Vung Tau': (10.3459, 107.0843),
    'Buon Ma Thuot': (12.6667, 108.0500),
    'Qui Nhon': (13.7667, 109.2333),
    'Rach Gia': (10.0167, 105.0833),
    'Long Xuyen': (10.3833, 105.4167),
    'Thu Dau Mot': (10.9667, 106.6500),
    'My Tho': (10.3500, 106.3500),
    'Vinh': (18.6733, 105.6922),
    'Thai Nguyen': (21.5944, 105.8483),
    'Quang Ninh': (21.0167, 107.3000),
    'Bac Ninh': (21.1861, 106.0763),
    'Hai Duong': (20.9373, 106.3344),
    'Hung Yen': (20.8525, 106.0169),
    'Nam Dinh': (20.4333, 106.1667),
    'Phu Ly': (20.5411, 105.9139),
    'Thanh Hoa': (19.8065, 105.7852),
    'Vinh': (18.6733, 105.6922),
    'Dong Hoi': (17.4689, 106.6222),
    'Dong Ha': (16.8167, 107.1000),
    'Tam Ky': (15.5667, 108.4833),
    'Quang Ngai': (15.1167, 108.8000),
    'Pleiku': (14.0000, 108.0000),
    'Kon Tum': (14.3500, 108.0000),
    'Buon Ma Thuot': (12.6667, 108.0500),
    'Phan Thiet': (10.9333, 108.1000),
    'Tay Ninh': (11.3000, 106.1000),
    'Thu Dau Mot': (10.9667, 106.6500),
    'Bien Hoa': (10.9574, 106.8426),
    'Vung Tau': (10.3459, 107.0843),
    'Ba Ria': (10.5000, 107.1667),
    'Long Khanh': (10.9333, 107.2333),
    'Tan An': (10.5333, 106.4167),
    'My Tho': (10.3500, 106.3500),
    'Ben Tre': (10.2333, 106.3833),
    'Tra Vinh': (9.9333, 106.3333),
    'Vinh Long': (10.2500, 105.9667),
    'Cao Lanh': (10.4667, 105.6333),
    'Long Xuyen': (10.3833, 105.4167),
    'Chau Doc': (10.7000, 105.1167),
    'Rach Gia': (10.0167, 105.0833),
    'Ca Mau': (9.1769, 105.1522),
    'Bac Lieu': (9.2833, 105.7167),
    'Soc Trang': (9.6000, 105.9667),
    'Can Tho': (10.0452, 105.7469),
} 