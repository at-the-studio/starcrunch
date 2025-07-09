#!/usr/bin/env python3
"""
🦕🚀 STARCRUNCH API SERVER
Flask API to serve data to the web dashboard
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import asyncio
import json
from datetime import datetime
from database import db

app = Flask(__name__)
CORS(app)  # Enable CORS for dashboard access

# 🔹---💠---🔹•DATABASE INITIALIZATION•🔹---💠---🔹
@app.before_first_request
async def init_database():
    """Initialize database connection"""
    await db.connect()

# 🔹---💠---🔹•API ENDPOINTS•🔹---💠---🔹

@app.route('/api/user/<user_id>/tasks', methods=['GET'])
async def get_user_tasks(user_id):
    """Get all tasks for a user"""
    try:
        completed = request.args.get('completed')
        if completed is not None:
            completed = completed.lower() == 'true'
        
        tasks = await db.get_user_tasks(user_id, completed)
        
        # Convert datetime objects to ISO strings
        for task in tasks:
            if task.get('created_at'):
                task['created_at'] = task['created_at'].isoformat()
            if task.get('completed_at'):
                task['completed_at'] = task['completed_at'].isoformat()
            if task.get('updated_at'):
                task['updated_at'] = task['updated_at'].isoformat()
        
        return jsonify({
            'success': True,
            'tasks': tasks,
            'count': len(tasks)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user/<user_id>/tasks', methods=['POST'])
async def create_task(user_id):
    """Create a new task"""
    try:
        task_data = request.get_json()
        
        # Generate task ID if not provided
        if 'id' not in task_data:
            task_data['id'] = f"task_{user_id}_{int(datetime.now().timestamp())}"
        
        await db.create_task(user_id, task_data)
        
        return jsonify({
            'success': True,
            'task_id': task_data['id'],
            'message': 'Task created successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user/<user_id>/tasks/<task_id>', methods=['PUT'])
async def update_task(user_id, task_id):
    """Update a task"""
    try:
        updates = request.get_json()
        await db.update_task(task_id, updates)
        
        return jsonify({
            'success': True,
            'message': 'Task updated successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user/<user_id>/tasks/<task_id>/complete', methods=['POST'])
async def complete_task(user_id, task_id):
    """Mark a task as completed"""
    try:
        await db.complete_task(task_id)
        
        return jsonify({
            'success': True,
            'message': 'Task marked as completed'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user/<user_id>/notes', methods=['GET'])
async def get_user_notes(user_id):
    """Get all daily notes for a user"""
    try:
        notes = await db.get_user_notes(user_id)
        
        # Convert datetime objects to ISO strings
        for note in notes:
            if note.get('created_at'):
                note['created_at'] = note['created_at'].isoformat()
            if note.get('updated_at'):
                note['updated_at'] = note['updated_at'].isoformat()
        
        return jsonify({
            'success': True,
            'notes': notes,
            'count': len(notes)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user/<user_id>/notes', methods=['POST'])
async def save_daily_note(user_id):
    """Save a daily note"""
    try:
        data = request.get_json()
        date_string = data.get('date_string')
        notes = data.get('notes', '')
        
        await db.save_daily_note(user_id, date_string, notes)
        
        return jsonify({
            'success': True,
            'message': 'Daily note saved successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user/<user_id>/notes/<date_string>', methods=['GET'])
async def get_daily_note(user_id, date_string):
    """Get a specific daily note"""
    try:
        note = await db.get_daily_note(user_id, date_string)
        
        if note:
            # Convert datetime objects to ISO strings
            if note.get('created_at'):
                note['created_at'] = note['created_at'].isoformat()
            if note.get('updated_at'):
                note['updated_at'] = note['updated_at'].isoformat()
        
        return jsonify({
            'success': True,
            'note': note
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user/<user_id>/stats', methods=['GET'])
async def get_user_stats(user_id):
    """Get user statistics"""
    try:
        stats = await db.get_user_stats(user_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user/<user_id>/preferences', methods=['GET'])
async def get_user_preferences(user_id):
    """Get user preferences"""
    try:
        user_data = await db.get_user(user_id)
        
        return jsonify({
            'success': True,
            'preferences': user_data.get('preferences', {})
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user/<user_id>/preferences', methods=['POST'])
async def update_user_preferences(user_id):
    """Update user preferences"""
    try:
        preferences = request.get_json()
        await db.update_user_preferences(user_id, preferences)
        
        return jsonify({
            'success': True,
            'message': 'Preferences updated successfully'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 🔹---💠---🔹•DASHBOARD SERVING•🔹---💠---🔹
@app.route('/')
def serve_dashboard():
    """Serve the dashboard HTML"""
    return send_from_directory('.', 'dashboard.html')

@app.route('/dashboard/<user_id>')
def serve_user_dashboard(user_id):
    """Serve the dashboard for a specific user"""
    return send_from_directory('.', 'dashboard.html')

# 🔹---💠---🔹•HEALTH CHECK•🔹---💠---🔹
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'Starcrunch API is online! 🦕🚀',
        'timestamp': datetime.now().isoformat()
    })

# 🔹---💠---🔹•ERROR HANDLERS•🔹---💠---🔹
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

# 🔹---💠---🔹•MAIN EXECUTION•🔹---💠---🔹
if __name__ == '__main__':
    print("🦕🚀 Starting Starcrunch API Server...")
    app.run(host='0.0.0.0', port=5000, debug=True)