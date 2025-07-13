"""
Payment Service

This module handles payment processing and subscription management
using Stripe for the real estate scraper application.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import stripe
from utils.auth_service import AuthService

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Handles payment processing and subscription management
    """
    
    def __init__(self, stripe_secret_key: Optional[str] = None):
        """
        Initialize the payment service
        
        Args:
            stripe_secret_key: Stripe secret key (defaults to environment variable)
        """
        self.stripe_secret_key = stripe_secret_key or os.getenv('STRIPE_SECRET_KEY')
        if self.stripe_secret_key:
            stripe.api_key = self.stripe_secret_key
        else:
            logger.warning("Stripe secret key not found. Payment features will be disabled.")
        
        self.auth_service = AuthService()
        
        # Subscription plans (in cents)
        self.plans = {
            'pro': {
                'price_id': os.getenv('STRIPE_PRO_PRICE_ID', 'price_pro_monthly'),
                'amount': 500,  # $5.00
                'currency': 'usd',
                'interval': 'month',
                'name': 'Pro Plan',
                'description': 'Access to advanced features including trends, maps, and unlimited alerts'
            },
            'enterprise': {
                'price_id': os.getenv('STRIPE_ENTERPRISE_PRICE_ID', 'price_enterprise_monthly'),
                'amount': 2000,  # $20.00
                'currency': 'usd',
                'interval': 'month',
                'name': 'Enterprise Plan',
                'description': 'Full access with priority support and custom features'
            }
        }
    
    def create_checkout_session(self, user_id: int, plan: str, success_url: str, cancel_url: str) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for subscription
        
        Args:
            user_id: User ID
            plan: Subscription plan (pro, enterprise)
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment
            
        Returns:
            Dict: Checkout session details
        """
        try:
            if not self.stripe_secret_key:
                return {
                    'success': False,
                    'error': 'Payment processing not configured'
                }
            
            if plan not in self.plans:
                return {
                    'success': False,
                    'error': 'Invalid subscription plan'
                }
            
            # Get user details
            user = self.auth_service.get_current_user()
            if not user or int(user.id) != user_id:  # type: ignore
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            plan_details = self.plans[plan]
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer_email=str(user.email),
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': plan_details['currency'],
                        'product_data': {
                            'name': plan_details['name'],
                            'description': plan_details['description'],
                        },
                        'unit_amount': plan_details['amount'],
                        'recurring': {
                            'interval': plan_details['interval'],
                        },
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user_id),
                    'plan': plan
                },
                allow_promotion_codes=True,
            )
            
            return {
                'success': True,
                'session_id': session.id,
                'checkout_url': session.url
            }
            
        except Exception as e:  # type: ignore
            logger.error(f"Error creating checkout session: {e}")
            return {
                'success': False,
                'error': 'Failed to create checkout session'
            }
    
    def handle_webhook(self, payload: bytes, sig_header: str, webhook_secret: str) -> Dict[str, Any]:
        """
        Handle Stripe webhook events
        
        Args:
            payload: Raw webhook payload
            sig_header: Stripe signature header
            webhook_secret: Webhook secret for verification
            
        Returns:
            Dict: Webhook processing result
        """
        try:
            if not self.stripe_secret_key:
                return {
                    'success': False,
                    'error': 'Payment processing not configured'
                }
            
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            # Handle different event types
            if event['type'] == 'checkout.session.completed':
                return self._handle_checkout_completed(event['data']['object'])
            elif event['type'] == 'customer.subscription.updated':
                return self._handle_subscription_updated(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                return self._handle_subscription_cancelled(event['data']['object'])
            elif event['type'] == 'invoice.payment_failed':
                return self._handle_payment_failed(event['data']['object'])
            else:
                logger.info(f"Unhandled webhook event: {event['type']}")
                return {
                    'success': True,
                    'message': 'Event ignored'
                }
                
        except Exception as e:  # type: ignore
            logger.error(f"Error handling webhook: {e}")
            return {
                'success': False,
                'error': 'Webhook processing failed'
            }
    
    def _handle_checkout_completed(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful checkout completion"""
        try:
            user_id = int(session['metadata']['user_id'])
            plan = session['metadata']['plan']
            
            # Calculate subscription expiration
            expires_at = datetime.utcnow() + timedelta(days=30)  # Monthly subscription
            
            # Update user subscription
            success = self.auth_service.update_user_subscription(
                user_id=user_id,
                tier=plan,
                expires_at=expires_at
            )
            
            if success:
                logger.info(f"Updated subscription for user {user_id} to {plan}")
                return {
                    'success': True,
                    'message': f'Subscription activated for user {user_id}'
                }
            else:
                logger.error(f"Failed to update subscription for user {user_id}")
                return {
                    'success': False,
                    'error': 'Failed to update user subscription'
                }
                
        except Exception as e:
            logger.error(f"Error handling checkout completion: {e}")
            return {
                'success': False,
                'error': 'Failed to process checkout completion'
            }
    
    def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updates"""
        try:
            # Extract user ID from subscription metadata
            customer_id = subscription['customer']
            
            # Find user by customer ID (you might need to store this mapping)
            # For now, we'll log the event
            logger.info(f"Subscription updated for customer {customer_id}")
            
            return {
                'success': True,
                'message': 'Subscription update processed'
            }
            
        except Exception as e:
            logger.error(f"Error handling subscription update: {e}")
            return {
                'success': False,
                'error': 'Failed to process subscription update'
            }
    
    def _handle_subscription_cancelled(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation"""
        try:
            customer_id = subscription['customer']
            
            # Find and update user subscription
            # For now, we'll log the event
            logger.info(f"Subscription cancelled for customer {customer_id}")
            
            return {
                'success': True,
                'message': 'Subscription cancellation processed'
            }
            
        except Exception as e:
            logger.error(f"Error handling subscription cancellation: {e}")
            return {
                'success': False,
                'error': 'Failed to process subscription cancellation'
            }
    
    def _handle_payment_failed(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payments"""
        try:
            customer_id = invoice['customer']
            
            logger.warning(f"Payment failed for customer {customer_id}")
            
            return {
                'success': True,
                'message': 'Payment failure processed'
            }
            
        except Exception as e:
            logger.error(f"Error handling payment failure: {e}")
            return {
                'success': False,
                'error': 'Failed to process payment failure'
            }
    
    def cancel_subscription(self, user_id: int) -> Dict[str, Any]:
        """
        Cancel user subscription
        
        Args:
            user_id: User ID
            
        Returns:
            Dict: Cancellation result
        """
        try:
            if not self.stripe_secret_key:
                return {
                    'success': False,
                    'error': 'Payment processing not configured'
                }
            
            # Get user
            user = self.auth_service.get_current_user()
            if not user or int(user.id) != user_id:  # type: ignore
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # For now, just update the user to free tier
            # In a full implementation, you'd cancel the Stripe subscription
            success = self.auth_service.update_user_subscription(
                user_id=user_id,
                tier='free',
                expires_at=None
            )
            
            if success:
                return {
                    'success': True,
                    'message': 'Subscription cancelled successfully'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to cancel subscription'
                }
                
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            return {
                'success': False,
                'error': 'Failed to cancel subscription'
            }
    
    def get_subscription_plans(self) -> Dict[str, Any]:
        """
        Get available subscription plans
        
        Returns:
            Dict: Available plans
        """
        return {
            'success': True,
            'plans': {
                'free': {
                    'name': 'Free Plan',
                    'price': 0,
                    'currency': 'usd',
                    'features': [
                        '10 listings per day',
                        '1 alert',
                        'Basic search'
                    ]
                },
                'pro': {
                    'name': 'Pro Plan',
                    'price': 5.00,
                    'currency': 'usd',
                    'interval': 'month',
                    'features': [
                        '100 listings per day',
                        '5 alerts',
                        'Export to CSV/Excel',
                        'Price trend analysis',
                        'Map view',
                        'Email notifications'
                    ]
                },
                'enterprise': {
                    'name': 'Enterprise Plan',
                    'price': 20.00,
                    'currency': 'usd',
                    'interval': 'month',
                    'features': [
                        'Unlimited listings',
                        'Unlimited alerts',
                        'All Pro features',
                        'Priority support',
                        'Custom integrations',
                        'API access'
                    ]
                }
            }
        }
    
    def create_payment_intent(self, amount: int, currency: str = 'usd') -> Dict[str, Any]:
        """
        Create a payment intent for one-time payments
        
        Args:
            amount: Amount in cents
            currency: Currency code
            
        Returns:
            Dict: Payment intent details
        """
        try:
            if not self.stripe_secret_key:
                return {
                    'success': False,
                    'error': 'Payment processing not configured'
                }
            
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                automatic_payment_methods={
                    'enabled': True,
                },
            )
            
            return {
                'success': True,
                'client_secret': intent.client_secret
            }
            
        except Exception as e:  # type: ignore
            logger.error(f"Error creating payment intent: {e}")
            return {
                'success': False,
                'error': 'Failed to create payment intent'
            } 