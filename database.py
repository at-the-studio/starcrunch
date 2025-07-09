#!/usr/bin/env python3
"""
🦕🚀 STARCRUNCH DATABASE MODULE
MySQL database connection and operations for fps.ms hosting
"""

import aiomysql
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

# 🔹---💠---🔹•DATABASE CONFIGURATION•🔹---💠---🔹
DB_CONFIG = {
    'host': 'db0.fps.ms',
    'port': 3306,
    'user': 'u48754_mRctAZqVYA',
    'password': '^r^On@Mz@h9ixqVsmvD3nyDy',
    'db': 's48754_Starcrunch',
    'charset': 'utf8mb4',
    'autocommit': True
}

class StarcrunchDatabase:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        """Create database connection pool"""
        try:
            self.pool = await aiomysql.create_pool(
                **DB_CONFIG,
                minsize=5,
                maxsize=20
            )
            print("🦕 Database connected successfully!")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            print("🦕 Database connection closed")
    
    async def execute_query(self, query: str, params: tuple = None):
        """Execute a query and return results"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                return await cursor.fetchall()
    
    async def execute_update(self, query: str, params: tuple = None):
        """Execute an update/insert/delete query"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                return cursor.rowcount
    
    # 🔹---💠---🔹•USER OPERATIONS•🔹---💠---🔹
    async def get_user(self, discord_id: str) -> Dict:
        """Get user data or create new user"""
        query = "SELECT * FROM users WHERE discord_id = %s"
        result = await self.execute_query(query, (discord_id,))
        
        if result:
            user = result[0]
            # Parse JSON preferences
            if user['preferences']:
                user['preferences'] = json.loads(user['preferences'])
            return user
        else:
            # Create new user with default preferences
            default_preferences = {
                'excludedTimes': [],
                'taskDurations': {
                    'appointment': 60,
                    'cleaning': 45,
                    'errands': 90,
                    'work': 120,
                    'personal': 60,
                    'generic': 60
                },
                'preferredTaskTimes': {
                    'cleaning': 'morning',
                    'errands': 'weekend',
                    'work': 'morning',
                    'personal': 'evening',
                    'appointment': 'any'
                }
            }
            
            await self.create_user(discord_id, default_preferences)
            return {
                'discord_id': discord_id,
                'preferences': default_preferences,
                'created_at': datetime.now()
            }
    
    async def create_user(self, discord_id: str, preferences: Dict):
        """Create a new user"""
        query = """
            INSERT INTO users (discord_id, preferences) 
            VALUES (%s, %s)
        """
        preferences_json = json.dumps(preferences)
        await self.execute_update(query, (discord_id, preferences_json))
    
    async def update_user_preferences(self, discord_id: str, preferences: Dict):
        """Update user preferences"""
        query = """
            UPDATE users 
            SET preferences = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE discord_id = %s
        """
        preferences_json = json.dumps(preferences)
        await self.execute_update(query, (preferences_json, discord_id))
    
    # 🔹---💠---🔹•TASK OPERATIONS•🔹---💠---🔹
    async def create_task(self, user_id: str, task_data: Dict):
        """Create a new task"""
        query = """
            INSERT INTO tasks (
                id, user_id, text, category, priority, completed, duration,
                scheduled_time, scheduled_day, is_appointment, ai_enhanced,
                adhd_tips, scheduling_suggestions
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        params = (
            task_data['id'],
            user_id,
            task_data['text'],
            task_data.get('category', 'generic'),
            task_data.get('priority', 'medium'),
            task_data.get('completed', False),
            task_data.get('duration', 60),
            task_data.get('scheduledTime'),
            task_data.get('scheduledDay'),
            task_data.get('isAppointment', False),
            task_data.get('ai_enhanced', False),
            json.dumps(task_data.get('adhd_tips', [])),
            json.dumps(task_data.get('schedulingSuggestions', []))
        )
        
        await self.execute_update(query, params)
    
    async def get_user_tasks(self, user_id: str, completed: Optional[bool] = None) -> List[Dict]:
        """Get all tasks for a user"""
        if completed is None:
            query = """
                SELECT * FROM tasks 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """
            params = (user_id,)
        else:
            query = """
                SELECT * FROM tasks 
                WHERE user_id = %s AND completed = %s 
                ORDER BY created_at DESC
            """
            params = (user_id, completed)
        
        results = await self.execute_query(query, params)
        
        # Parse JSON fields
        for task in results:
            if task['adhd_tips']:
                task['adhd_tips'] = json.loads(task['adhd_tips'])
            if task['scheduling_suggestions']:
                task['scheduling_suggestions'] = json.loads(task['scheduling_suggestions'])
        
        return results
    
    async def update_task(self, task_id: str, updates: Dict):
        """Update a task"""
        set_clauses = []
        params = []
        
        for key, value in updates.items():
            if key in ['adhd_tips', 'scheduling_suggestions']:
                set_clauses.append(f"{key} = %s")
                params.append(json.dumps(value))
            else:
                set_clauses.append(f"{key} = %s")
                params.append(value)
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(task_id)
        
        query = f"""
            UPDATE tasks 
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """
        
        await self.execute_update(query, params)
    
    async def complete_task(self, task_id: str):
        """Mark a task as completed"""
        query = """
            UPDATE tasks 
            SET completed = TRUE, completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        await self.execute_update(query, (task_id,))
    
    async def delete_task(self, task_id: str):
        """Delete a task"""
        query = "DELETE FROM tasks WHERE id = %s"
        await self.execute_update(query, (task_id,))
    
    # 🔹---💠---🔹•DAILY NOTES OPERATIONS•🔹---💠---🔹
    async def get_daily_note(self, user_id: str, date_string: str) -> Optional[Dict]:
        """Get daily note for a specific date"""
        query = """
            SELECT * FROM daily_notes 
            WHERE user_id = %s AND date_string = %s
        """
        result = await self.execute_query(query, (user_id, date_string))
        return result[0] if result else None
    
    async def save_daily_note(self, user_id: str, date_string: str, notes: str):
        """Save or update daily note"""
        query = """
            INSERT INTO daily_notes (id, user_id, date_string, notes) 
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            notes = VALUES(notes), updated_at = CURRENT_TIMESTAMP
        """
        
        note_id = f"note_{user_id}_{date_string.replace(' ', '_')}"
        await self.execute_update(query, (note_id, user_id, date_string, notes))
    
    async def get_user_notes(self, user_id: str) -> List[Dict]:
        """Get all daily notes for a user"""
        query = """
            SELECT * FROM daily_notes 
            WHERE user_id = %s 
            ORDER BY date_string DESC
        """
        return await self.execute_query(query, (user_id,))
    
    # 🔹---💠---🔹•FOCUS SESSION OPERATIONS•🔹---💠---🔹
    async def create_focus_session(self, user_id: str, session_type: str, duration: int):
        """Create a new focus session"""
        query = """
            INSERT INTO focus_sessions (id, user_id, session_type, duration) 
            VALUES (%s, %s, %s, %s)
        """
        
        session_id = f"session_{user_id}_{int(datetime.now().timestamp())}"
        await self.execute_update(query, (session_id, user_id, session_type, duration))
        return session_id
    
    async def complete_focus_session(self, session_id: str):
        """Mark a focus session as completed"""
        query = """
            UPDATE focus_sessions 
            SET completed = TRUE, ended_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """
        await self.execute_update(query, (session_id,))
    
    async def get_user_focus_sessions(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent focus sessions for a user"""
        query = """
            SELECT * FROM focus_sessions 
            WHERE user_id = %s 
            ORDER BY started_at DESC 
            LIMIT %s
        """
        return await self.execute_query(query, (user_id, limit))
    
    # 🔹---💠---🔹•ANALYTICS OPERATIONS•🔹---💠---🔹
    async def get_user_stats(self, user_id: str) -> Dict:
        """Get user statistics"""
        # Get task stats
        task_stats = await self.execute_query("""
            SELECT 
                COUNT(*) as total_tasks,
                SUM(completed) as completed_tasks,
                SUM(CASE WHEN priority = 'high' AND completed = 0 THEN 1 ELSE 0 END) as high_priority_pending,
                AVG(duration) as avg_duration
            FROM tasks 
            WHERE user_id = %s
        """, (user_id,))
        
        # Get focus session stats
        focus_stats = await self.execute_query("""
            SELECT 
                COUNT(*) as total_sessions,
                SUM(completed) as completed_sessions,
                SUM(CASE WHEN completed = 1 THEN duration ELSE 0 END) as total_focus_time
            FROM focus_sessions 
            WHERE user_id = %s AND DATE(started_at) = CURDATE()
        """, (user_id,))
        
        return {
            'tasks': task_stats[0] if task_stats else {},
            'focus': focus_stats[0] if focus_stats else {}
        }

# Global database instance
db = StarcrunchDatabase()