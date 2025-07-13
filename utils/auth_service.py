"""
Authentication Service

This module handles user authentication, registration, and JWT token management
for the real estate scraper application.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy.orm import Session
from database.models import User, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class AuthService:
    """
    Handles user authentication and authorization
    """
    
    def __init__(self, database_url: str = "sqlite:///realestate.db"):
        """
        Initialize the authentication service
        
        Args:
            database_url: Database connection URL
        """
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        
    def register_user(self, username: str, email: str, password: str, name: str) -> Dict[str, Any]:
        """
        Register a new user
        
        Args:
            username: Unique username
            email: User email
            password: User password
            name: User's full name
            
        Returns:
            Dict: Registration result
        """
        try:
            session = self.Session()
            
            # Check if user already exists
            existing_user = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                session.close()
                return {
                    'success': False,
                    'error': 'Username or email already exists'
                }
            
            # Create new user
            password_hash = generate_password_hash(password)
            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                name=name,
                subscription_tier='free',
                created_at=datetime.utcnow()
            )
            
            session.add(new_user)
            session.commit()
            
            # Get user ID for token creation
            user_id = new_user.id
            
            session.close()
            
            # Create access token
            access_token = create_access_token(identity=user_id)
            
            return {
                'success': True,
                'message': 'User registered successfully',
                'user': {
                    'id': user_id,
                    'username': username,
                    'email': email,
                    'name': name,
                    'subscription_tier': 'free'
                },
                'access_token': access_token
            }
            
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return {
                'success': False,
                'error': 'Registration failed'
            }
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user login
        
        Args:
            username: Username or email
            password: User password
            
        Returns:
            Dict: Login result
        """
        try:
            session = self.Session()
            
            # Find user by username or email
            user = session.query(User).filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if not user:
                session.close()
                return {
                    'success': False,
                    'error': 'Invalid credentials'
                }
            
            # Check password
            if not check_password_hash(user.password_hash, password):
                session.close()
                return {
                    'success': False,
                    'error': 'Invalid credentials'
                }
            
            # Check if user is active
            if not user.is_active:
                session.close()
                return {
                    'success': False,
                    'error': 'Account is deactivated'
                }
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            session.close()
            
            return {
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'name': user.name,
                    'subscription_tier': user.subscription_tier,
                    'subscription_expires': user.subscription_expires.isoformat() if user.subscription_expires else None
                },
                'access_token': access_token
            }
            
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return {
                'success': False,
                'error': 'Login failed'
            }
    
    def get_current_user(self) -> Optional[User]:
        """
        Get current authenticated user
        
        Returns:
            Optional[User]: Current user or None
        """
        try:
            user_id = get_jwt_identity()
            if not user_id:
                return None
            
            session = self.Session()
            user = session.query(User).filter(User.id == user_id).first()
            session.close()
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None
    
    def update_user_subscription(self, user_id: int, tier: str, expires_at: Optional[datetime] = None) -> bool:
        """
        Update user subscription tier
        
        Args:
            user_id: User ID
            tier: Subscription tier (free, pro, enterprise)
            expires_at: Subscription expiration date
            
        Returns:
            bool: Success status
        """
        try:
            session = self.Session()
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                session.close()
                return False
            
            user.subscription_tier = tier
            user.subscription_expires = expires_at
            
            session.commit()
            session.close()
            
            logger.info(f"Updated subscription for user {user_id} to {tier}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user subscription: {e}")
            return False
    
    def check_subscription_access(self, user: User, feature: str) -> bool:
        """
        Check if user has access to a specific feature based on subscription
        
        Args:
            user: User object
            feature: Feature to check access for
            
        Returns:
            bool: Access granted
        """
        # Check if subscription has expired
        if user.subscription_expires and user.subscription_expires < datetime.utcnow():
            return False
        
        # Feature access rules
        access_rules = {
            'listings': {
                'free': 10,      # 10 listings per day
                'pro': 100,      # 100 listings per day
                'enterprise': -1  # Unlimited
            },
            'alerts': {
                'free': 1,       # 1 alert
                'pro': 5,        # 5 alerts
                'enterprise': -1  # Unlimited
            },
            'exports': {
                'free': False,
                'pro': True,
                'enterprise': True
            },
            'trends': {
                'free': False,
                'pro': True,
                'enterprise': True
            },
            'maps': {
                'free': False,
                'pro': True,
                'enterprise': True
            }
        }
        
        if feature not in access_rules:
            return False
        
        tier_access = access_rules[feature].get(user.subscription_tier, False)
        
        if tier_access == -1:  # Unlimited
            return True
        elif isinstance(tier_access, bool):
            return tier_access
        else:
            # For numeric limits, we'd need to track usage
            # For now, return True for pro+ tiers
            return user.subscription_tier in ['pro', 'enterprise']
    
    def get_user_usage_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get user usage statistics
        
        Args:
            user_id: User ID
            
        Returns:
            Dict: Usage statistics
        """
        try:
            session = self.Session()
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                session.close()
                return {}
            
            # Get user's alerts
            alerts = session.query(User).filter(User.id == user_id).first().alerts
            
            stats = {
                'user_id': user_id,
                'subscription_tier': user.subscription_tier,
                'subscription_expires': user.subscription_expires.isoformat() if user.subscription_expires else None,
                'active_alerts': len([a for a in alerts if a.is_active]),
                'total_alerts': len(alerts),
                'created_at': user.created_at.isoformat(),
                'is_active': user.is_active
            }
            
            session.close()
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user usage stats: {e}")
            return {}
    
    def deactivate_user(self, user_id: int) -> bool:
        """
        Deactivate a user account
        
        Args:
            user_id: User ID
            
        Returns:
            bool: Success status
        """
        try:
            session = self.Session()
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                session.close()
                return False
            
            user.is_active = False
            session.commit()
            session.close()
            
            logger.info(f"Deactivated user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            return False
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change user password
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
            
        Returns:
            Dict: Result
        """
        try:
            session = self.Session()
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                session.close()
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # Verify current password
            if not check_password_hash(user.password_hash, current_password):
                session.close()
                return {
                    'success': False,
                    'error': 'Current password is incorrect'
                }
            
            # Update password
            user.password_hash = generate_password_hash(new_password)
            session.commit()
            session.close()
            
            return {
                'success': True,
                'message': 'Password changed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return {
                'success': False,
                'error': 'Password change failed'
            } 