#!/usr/bin/env python3
"""
Database Seeding Script for Hotel Receptionist System

This script populates the database with sample data including:
- Sample rooms with different types and amenities
- Sample guests with realistic information
- Sample reservations for testing

Run this script after setting up your database and running migrations.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def main():
    """Main function to run the database seeder"""
    try:
        print("🌱 Starting database seeding...")
        print("=" * 50)
        
        from app.seeders.database_seeder import DatabaseSeeder
        
        seeder = DatabaseSeeder()
        await seeder.seed_database()
        
        print("=" * 50)
        print("✅ Database seeding completed successfully!")
        print("\n🎯 Next steps:")
        print("1. Set your GEMINI_API_KEY in the .env file")
        print("2. Start the application with: python start.py")
        print("3. Test the chat agent at: http://localhost:8000/docs")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you have installed all dependencies: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Database seeding failed: {e}")
        print("Make sure your database is running and accessible")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 