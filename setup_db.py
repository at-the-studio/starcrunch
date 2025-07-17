#!/usr/bin/env python3
"""
🦕🚀 Database Setup Script for Starcrunch
Creates the required tables on fps.ms MySQL database
"""

import mysql.connector
from mysql.connector import Error

# Database configuration (same as in _db.js)
DB_CONFIG = {
    'host': 'db0.fps.ms',
    'port': 3306,
    'user': 'u48754_mRctAZqVYA',
    'password': '^r^On@Mz@h9ixqVsmvD3nyDy',
    'database': 's48754_Starcrunch',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_general_ci'
}

# SQL commands to create tables
CREATE_TABLES = [
    """
    CREATE TABLE IF NOT EXISTS users (
        discord_id VARCHAR(20) PRIMARY KEY,
        preferences TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id VARCHAR(50) PRIMARY KEY,
        user_id VARCHAR(20) NOT NULL,
        text TEXT NOT NULL,
        category VARCHAR(20) DEFAULT 'generic',
        priority VARCHAR(10) DEFAULT 'medium',
        completed BOOLEAN DEFAULT FALSE,
        duration INTEGER DEFAULT 60,
        scheduled_time VARCHAR(20),
        scheduled_day VARCHAR(50),
        is_appointment BOOLEAN DEFAULT FALSE,
        ai_enhanced BOOLEAN DEFAULT FALSE,
        adhd_tips TEXT,
        scheduling_suggestions TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE,
        INDEX idx_user_id (user_id),
        INDEX idx_completed (completed),
        INDEX idx_scheduled_day (scheduled_day)
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_notes (
        id VARCHAR(50) PRIMARY KEY,
        user_id VARCHAR(20) NOT NULL,
        date_string VARCHAR(30) NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE,
        UNIQUE KEY unique_user_date (user_id, date_string),
        INDEX idx_user_date (user_id, date_string)
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
    """,
    """
    CREATE TABLE IF NOT EXISTS learning_rules (
        id VARCHAR(50) PRIMARY KEY,
        user_id VARCHAR(20) NOT NULL,
        rule_type VARCHAR(20) NOT NULL,
        pattern TEXT NOT NULL,
        action TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE,
        INDEX idx_user_id (user_id)
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
    """,
    """
    CREATE TABLE IF NOT EXISTS focus_sessions (
        id VARCHAR(50) PRIMARY KEY,
        user_id VARCHAR(20) NOT NULL,
        session_type VARCHAR(20) NOT NULL,
        duration INTEGER NOT NULL,
        completed BOOLEAN DEFAULT FALSE,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ended_at TIMESTAMP NULL,
        FOREIGN KEY (user_id) REFERENCES users(discord_id) ON DELETE CASCADE,
        INDEX idx_user_id (user_id),
        INDEX idx_started_at (started_at)
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_tasks_user_created ON tasks(user_id, created_at);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_tasks_user_completed ON tasks(user_id, completed, created_at);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_notes_user_date ON daily_notes(user_id, date_string);
    """
]

def setup_database():
    """Create all required tables and indexes"""
    connection = None
    try:
        print("🦕 Connecting to Starcrunch database...")
        connection = mysql.connector.connect(**DB_CONFIG)
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            print("✅ Connected to database!")
            print("🔨 Creating tables...")
            
            for i, sql in enumerate(CREATE_TABLES, 1):
                try:
                    cursor.execute(sql)
                    print(f"✅ Created table/index {i}/{len(CREATE_TABLES)}")
                except Error as e:
                    print(f"⚠️  Table/index {i} already exists or error: {e}")
            
            connection.commit()
            print("🚀 Database setup complete!")
            print("🎯 Your Starcrunch bot is ready to use!")
            
    except Error as e:
        print(f"❌ Database error: {e}")
        return False
        
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("📡 Database connection closed.")
    
    return True

if __name__ == "__main__":
    print("🦕🚀 Starcrunch Database Setup")
    print("=" * 40)
    setup_database()