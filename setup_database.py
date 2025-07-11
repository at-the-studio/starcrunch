#!/usr/bin/env python3
"""
🦕🚀 STARCRUNCH DATABASE SETUP
Run this script to initialize the database tables on fps.ms
"""

import asyncio
import aiomysql
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': 'HOST_SECRET',
    'port': 'PORT_NUMBER',
    'user': 'USERNAME',
    'password': 'PASSWORD',
    'db': 'DATABASE',
    'charset': 'CHARSET'
}

async def setup_database():
    """Initialize database tables"""
    print("🦕 Setting up Starcrunch database...")
    
    try:
        # Connect to database
        connection = await aiomysql.connect(**DB_CONFIG)
        cursor = await connection.cursor()
        
        # Read SQL file
        with open('database_setup.sql', 'r') as f:
            sql_commands = f.read()
        
        # Split commands and execute each one
        commands = sql_commands.split(';')
        
        for command in commands:
            command = command.strip()
            if command:
                print(f"📋 Executing: {command[:50]}...")
                await cursor.execute(command)
        
        await connection.commit()
        print("✅ Database setup completed successfully!")
        
        # Test connection
        await cursor.execute("SHOW TABLES")
        tables = await cursor.fetchall()
        print(f"📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        await cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(setup_database())
    if success:
        print("\n🦕🚀 Starcrunch database is ready!")
        print("You can now run:")
        print("  - python app.py    (Discord bot)")
        print("  - python api.py    (API server)")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
