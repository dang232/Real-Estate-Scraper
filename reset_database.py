"""
Database Reset Script

This script resets the database to start fresh with the new schema.
"""

import os
import sys
import logging

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Reset the database to start fresh"""
    try:
        # Remove existing database file
        db_file = "realestate.db"
        if os.path.exists(db_file):
            os.remove(db_file)
            logger.info(f"✅ Removed existing database: {db_file}")
        
        # Import and run migrations
        from database.migrations import run_migrations
        
        if run_migrations():
            logger.info("✅ Database reset successful")
            return True
        else:
            logger.error("❌ Database reset failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error resetting database: {e}")
        return False

def main():
    """Main function"""
    logger.info("🔄 Resetting database...")
    
    if reset_database():
        logger.info("🎉 Database reset completed successfully!")
        logger.info("📝 You can now run: python test_setup.py")
    else:
        logger.error("💥 Database reset failed!")
        sys.exit(1)

if __name__ == '__main__':
    main() 