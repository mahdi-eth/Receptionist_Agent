#!/usr/bin/env python3
"""
Database seeding script for Hotel Receptionist API
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.seeders.simple_seeder import SimpleDatabaseSeeder
    
    async def main():
        """Main function to run the database seeder"""
        seeder = SimpleDatabaseSeeder()
        await seeder.seed_database()
    
    if __name__ == "__main__":
        asyncio.run(main())
        
except ImportError as e:
    sys.exit(1)
except Exception as e:
    sys.exit(1) 