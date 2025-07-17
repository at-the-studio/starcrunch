#!/usr/bin/env python3
"""
🦕🚀 STARCRUNCH - Discord Task Scheduling Bot
A friendly dinosaur astronaut that helps users with ADHD manage their tasks and schedule.

Features:
- Natural language task parsing
- Intelligent scheduling with user preferences
- DM-based privacy
- Web dashboard integration
"""

import discord
from discord.ext import commands
import json
import os
import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import aiofiles
from dotenv import load_dotenv
from groq import Groq
from database import db
from emote_config import EMOTE_MAP, get_emote, replace_emojis

# Load environment variables
load_dotenv()

# 🔹---💠---🔹•BOT CONFIGURATION•🔹---💠---🔹
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables")

# Groq AI Configuration
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
GROQ_FALLBACK_MODEL = os.getenv('GROQ_FALLBACK_MODEL', 'llama-3.1-8b-instant')

# Initialize Groq client
groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("🤖 Groq AI initialized successfully")
    except Exception as e:
        print(f"⚠️ Groq AI initialization failed: {e}")
        print("🔄 Falling back to rule-based scheduling")
else:
    print("⚠️ No Groq API key found - using rule-based scheduling only")

# Bot setup with necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 🔹---💠---🔹•DATA STORAGE•🔹---💠---🔹
# Database operations are now handled by the database module

# 🔹---💠---🔹•TASK PARSING & SCHEDULING•🔹---💠---🔹
class TaskParser:
    def __init__(self):
        # Time patterns for appointments
        self.time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',
            r'(\d{1,2})\s*(am|pm)',
            r'at\s+(\d{1,2}):(\d{2})',
            r'at\s+(\d{1,2})\s*(am|pm)',
        ]
        
        # Day patterns
        self.day_patterns = [
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(mon|tue|wed|thu|fri|sat|sun)',
            r'(today|tomorrow|next week)',
        ]
        
        # Task categories with enhanced keywords
        self.task_categories = {
            'appointment': ['dentist', 'doctor', 'meeting', 'appointment', 'call', 'visit', 'checkup'],
            'cleaning': ['clean', 'vacuum', 'dishes', 'laundry', 'tidy', 'sweep', 'mop', 'dust'],
            'errands': ['grocery', 'shopping', 'bank', 'post office', 'store', 'pickup', 'drop off'],
            'work': ['work', 'project', 'deadline', 'presentation', 'report', 'email'],
            'personal': ['exercise', 'workout', 'read', 'call mom', 'call dad', 'family'],
            'generic': []  # Default category
        }
        
        # Priority keywords
        self.priority_keywords = {
            'high': ['urgent', 'important', 'asap', 'priority', 'deadline'],
            'low': ['maybe', 'eventually', 'when possible', 'someday']
        }
    
    def parse_tasks(self, task_string: str) -> List[Dict]:
        """Parse comma-separated task string into structured tasks"""
        tasks = []
        task_list = [task.strip() for task in task_string.split(',') if task.strip()]
        
        for task in task_list:
            parsed_task = self._parse_single_task(task)
            tasks.append(parsed_task)
        
        return tasks
    
    def _parse_single_task(self, task: str) -> Dict:
        """Parse a single task string"""
        task_lower = task.lower()
        
        # Check if it's an appointment (has time specified)
        time_match = None
        for pattern in self.time_patterns:
            time_match = re.search(pattern, task_lower)
            if time_match:
                break
        
        # Check for day specification
        day_match = None
        for pattern in self.day_patterns:
            day_match = re.search(pattern, task_lower)
            if day_match:
                break
        
        # Determine category
        category = 'generic'
        for cat, keywords in self.task_categories.items():
            if any(keyword in task_lower for keyword in keywords):
                category = cat
                break
        
        # Determine priority
        priority = 'medium'
        for pri, keywords in self.priority_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                priority = pri
                break
        
        # Build task object
        parsed_task = {
            'text': task,
            'category': category,
            'isAppointment': time_match is not None,
            'scheduledTime': None,
            'scheduledDay': None,
            'duration': None,
            'priority': priority,
            'completed': False,
            'createdAt': datetime.now().isoformat(),
            'id': f"task_{int(datetime.now().timestamp())}"
        }
        
        # Extract time if found
        if time_match:
            parsed_task['scheduledTime'] = time_match.group(0)
        
        # Extract day if found
        if day_match:
            parsed_task['scheduledDay'] = day_match.group(0)
        
        return parsed_task

class SmartScheduler:
    def __init__(self):
        self.default_durations = {
            'appointment': 60,
            'cleaning': 45,
            'errands': 90,
            'work': 120,
            'personal': 60,
            'generic': 60
        }
        
        self.preferred_times = {
            'cleaning': ['morning'],
            'errands': ['afternoon', 'weekend'],
            'work': ['morning', 'afternoon'],
            'personal': ['evening', 'weekend'],
            'appointment': ['any']
        }
    
    def schedule_tasks(self, tasks: List[Dict], user_preferences: Dict) -> List[Dict]:
        """Apply smart scheduling logic to tasks"""
        scheduled_tasks = []
        
        for task in tasks:
            # If it's already an appointment with specific time, keep it
            if task['isAppointment'] and task['scheduledTime']:
                task['duration'] = self.default_durations.get(task['category'], 60)
                scheduled_tasks.append(task)
                continue
            
            # Apply smart scheduling for flexible tasks
            task = self._apply_smart_scheduling(task, user_preferences)
            scheduled_tasks.append(task)
        
        return scheduled_tasks
    
    def _apply_smart_scheduling(self, task: Dict, user_preferences: Dict) -> Dict:
        """Apply scheduling logic to a single task"""
        # Set duration based on category
        task['duration'] = user_preferences.get('taskDurations', {}).get(
            task['category'], 
            self.default_durations.get(task['category'], 60)
        )
        
        # Set preferred time based on category
        category_prefs = self.preferred_times.get(task['category'], ['any'])
        task['preferredTime'] = category_prefs[0]
        
        # Add scheduling suggestions
        task['schedulingSuggestions'] = self._get_scheduling_suggestions(task)
        
        return task
    
    def _get_scheduling_suggestions(self, task: Dict) -> List[str]:
        """Generate scheduling suggestions for a task"""
        suggestions = []
        
        if task['category'] == 'cleaning':
            suggestions.append(f"{get_emote('🌅')} Best done in the morning when energy is high")
        elif task['category'] == 'errands':
            suggestions.append(f"{get_emote('🛍️')} Consider batching with other errands")
            suggestions.append(f"{get_emote('🏪')} Check store hours before scheduling")
        elif task['category'] == 'work':
            suggestions.append(f"{get_emote('⏰')} Schedule during your peak focus hours")
        elif task['priority'] == 'high':
            suggestions.append(f"{get_emote('🔥')} High priority - schedule ASAP")
        
        return suggestions

class AIScheduler:
    def __init__(self, groq_client=None):
        self.groq_client = groq_client
        self.fallback_scheduler = SmartScheduler()
    
    async def analyze_tasks_with_ai(self, tasks_text: str, user_preferences: Dict) -> Dict:
        """Use Groq AI to analyze and enhance task scheduling"""
        if not self.groq_client:
            return {"enhanced": False, "reason": "No AI client available"}
        
        try:
            # Create prompt for AI analysis
            prompt = self._create_scheduling_prompt(tasks_text, user_preferences)
            
            # Call Groq API
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are Starcrunch, a friendly dinosaur astronaut that helps people with ADHD schedule tasks. Be helpful and encouraging while providing practical scheduling advice."},
                    {"role": "user", "content": prompt}
                ],
                model=GROQ_MODEL,
                temperature=0.3,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            return self._parse_ai_response(ai_response)
            
        except Exception as e:
            print(f"🤖 AI scheduling failed: {e}")
            # Try fallback model
            try:
                response = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are Starcrunch, a helpful task scheduling assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    model=GROQ_FALLBACK_MODEL,
                    temperature=0.3,
                    max_tokens=500
                )
                
                ai_response = response.choices[0].message.content
                return self._parse_ai_response(ai_response)
                
            except Exception as e2:
                print(f"🤖 Fallback AI model also failed: {e2}")
                return {"enhanced": False, "reason": f"AI error: {str(e2)}"}
    
    def _create_scheduling_prompt(self, tasks_text: str, user_preferences: Dict) -> str:
        """Create a prompt for AI task analysis"""
        excluded_times = user_preferences.get('excludedTimes', [])
        task_durations = user_preferences.get('taskDurations', {})
        
        prompt = f"""
🦕 Hi! I'm Starcrunch, and I need help scheduling these tasks for a space explorer with ADHD:

TASKS TO SCHEDULE: "{tasks_text}"

USER PREFERENCES:
- Excluded times: {excluded_times if excluded_times else "None specified"}
- Custom durations: {task_durations if task_durations else "Using defaults"}

Please analyze these tasks and provide:
1. Enhanced task categorization (appointment, cleaning, errands, work, personal, generic)
2. Priority assessment (high, medium, low) based on urgency indicators
3. Realistic duration estimates (in minutes)
4. Optimal scheduling suggestions (morning, afternoon, evening, weekend)
5. ADHD-friendly tips for completing each task

Respond in JSON format:
{{
  "tasks": [
    {{
      "text": "original task text",
      "category": "detected_category",
      "priority": "detected_priority", 
      "duration": estimated_minutes,
      "optimal_time": "best_time_period",
      "adhd_tips": ["tip1", "tip2"],
      "energy_level": "high/medium/low"
    }}
  ],
  "overall_suggestions": ["general scheduling advice"],
  "motivation": "encouraging message for the user"
}}

Focus on being helpful, realistic, and encouraging! 🚀
"""
        return prompt
    
    def _parse_ai_response(self, ai_response: str) -> Dict:
        """Parse AI response and extract scheduling data"""
        try:
            # Try to extract JSON from the response
            import json
            
            # Look for JSON block in response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx]
                parsed_data = json.loads(json_str)
                
                return {
                    "enhanced": True,
                    "data": parsed_data,
                    "raw_response": ai_response
                }
            else:
                # If no JSON found, return the raw response
                return {
                    "enhanced": True,
                    "data": {"raw_advice": ai_response},
                    "raw_response": ai_response
                }
                
        except Exception as e:
            print(f"🤖 Error parsing AI response: {e}")
            return {
                "enhanced": False,
                "reason": f"Parse error: {str(e)}",
                "raw_response": ai_response
            }
    
    async def enhance_tasks(self, tasks: List[Dict], tasks_text: str, user_preferences: Dict) -> List[Dict]:
        """Enhance tasks using AI analysis"""
        if not self.groq_client:
            return self.fallback_scheduler.schedule_tasks(tasks, user_preferences)
        
        # Get AI analysis
        ai_result = await self.analyze_tasks_with_ai(tasks_text, user_preferences)
        
        if not ai_result.get("enhanced"):
            print(f"🔄 Using fallback scheduler: {ai_result.get('reason', 'Unknown error')}")
            return self.fallback_scheduler.schedule_tasks(tasks, user_preferences)
        
        # Apply AI enhancements to tasks
        try:
            ai_data = ai_result.get("data", {})
            ai_tasks = ai_data.get("tasks", [])
            
            enhanced_tasks = []
            
            for i, task in enumerate(tasks):
                enhanced_task = task.copy()
                
                # Apply AI enhancements if available
                if i < len(ai_tasks):
                    ai_task = ai_tasks[i]
                    
                    enhanced_task.update({
                        'category': ai_task.get('category', task.get('category', 'generic')),
                        'priority': ai_task.get('priority', task.get('priority', 'medium')),
                        'duration': ai_task.get('duration', task.get('duration', 60)),
                        'optimal_time': ai_task.get('optimal_time', 'any'),
                        'adhd_tips': ai_task.get('adhd_tips', []),
                        'energy_level': ai_task.get('energy_level', 'medium'),
                        'ai_enhanced': True
                    })
                
                enhanced_tasks.append(enhanced_task)
            
            # Add overall AI suggestions to first task
            if enhanced_tasks and ai_data.get("overall_suggestions"):
                enhanced_tasks[0]['ai_suggestions'] = ai_data.get("overall_suggestions", [])
                enhanced_tasks[0]['ai_motivation'] = ai_data.get("motivation", "")
            
            return enhanced_tasks
            
        except Exception as e:
            print(f"🤖 Error applying AI enhancements: {e}")
            return self.fallback_scheduler.schedule_tasks(tasks, user_preferences)

# Global parser and scheduler instances
task_parser = TaskParser()
smart_scheduler = SmartScheduler()
ai_scheduler = AIScheduler(groq_client)

# 🔹---💠---🔹•BOT EVENTS•🔹---💠---🔹
@bot.event
async def on_ready():
    print(f'🦕🚀 Starcrunch is online! Logged in as {bot.user}')
    print(f'📡 Connected to {len(bot.guilds)} servers')
    
    # Initialize database connection
    if not await db.connect():
        print("❌ Failed to connect to database. Exiting...")
        await bot.close()
        return
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'⚡ Synced {len(synced)} slash commands')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')

@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author == bot.user:
        return
    
    # Don't respond to regular messages - only slash commands
    # This prevents the bot from responding to every message in DMs
    await bot.process_commands(message)

# 🔹---💠---🔹•CONVERSATION MEMORY•🔹---💠---🔹
# Store conversation history in memory (resets on bot restart)
conversation_memory = {}  # user_id: [{"role": "user/assistant", "content": "message"}]
MAX_CONVERSATION_LENGTH = 20

def get_conversation_history(user_id):
    """Get conversation history for user"""
    return conversation_memory.get(user_id, [])

def add_to_conversation(user_id, role, content):
    """Add message to conversation history"""
    if user_id not in conversation_memory:
        conversation_memory[user_id] = []
    
    conversation_memory[user_id].append({"role": role, "content": content})
    
    # Keep only last MAX_CONVERSATION_LENGTH messages
    if len(conversation_memory[user_id]) > MAX_CONVERSATION_LENGTH:
        conversation_memory[user_id] = conversation_memory[user_id][-MAX_CONVERSATION_LENGTH:]

def get_conversation_count(user_id):
    """Get current conversation length"""
    return len(conversation_memory.get(user_id, []))

def reset_conversation(user_id):
    """Reset conversation for user"""
    if user_id in conversation_memory:
        del conversation_memory[user_id]

# 🔹---💠---🔹•SLASH COMMANDS•🔹---💠---🔹
@bot.tree.command(name="schedule", description="Schedule tasks with Starcrunch")
async def schedule_tasks(interaction: discord.Interaction, tasks: str):
    """Schedule tasks from a comma-separated list"""
    try:
        user_id = str(interaction.user.id)
        user_data = await db.get_user(user_id)
        
        # Parse the tasks
        parsed_tasks = task_parser.parse_tasks(tasks)
        
        # Apply AI-enhanced scheduling
        scheduled_tasks = await ai_scheduler.enhance_tasks(parsed_tasks, tasks, user_data['preferences'])
        
        # Save tasks to database
        for task in scheduled_tasks:
            await db.create_task(user_id, task)
        
        # Create response
        embed = discord.Embed(
            title="🦕 Tasks Scheduled!",
            description=f"I've added {len(scheduled_tasks)} tasks to your mission log:",
            color=0xDAA520
        )
        
        for i, task in enumerate(scheduled_tasks, 1):
            category_emoji = {
                'appointment': get_emote('📅'),
                'cleaning': get_emote('🧹'),
                'errands': get_emote('🛍️'),
                'work': get_emote('💼'),
                'personal': get_emote('👤'),
                'generic': get_emote('📋')
            }
            
            priority_emoji = {
                'high': get_emote('🔥'),
                'medium': get_emote('⚡'),
                'low': get_emote('💤')
            }
            
            # Build task info
            task_info = f"**{task['text']}**\n"
            task_info += f"Category: {task['category'].title()}\n"
            task_info += f"Priority: {priority_emoji.get(task['priority'], '⚡')} {task['priority'].title()}\n"
            task_info += f"Duration: {task['duration']} minutes\n"
            
            if task.get('isAppointment') or task.get('is_appointment'):
                task_info += f"{get_emote('⏰')} Fixed appointment"
                if task.get('scheduledTime') or task.get('scheduled_time'):
                    time_val = task.get('scheduledTime') or task.get('scheduled_time')
                    task_info += f" at {time_val}"
                if task.get('scheduledDay') or task.get('scheduled_day'):
                    day_val = task.get('scheduledDay') or task.get('scheduled_day')
                    task_info += f" on {day_val}"
            else:
                task_info += f"📋 Flexible task"
                if task.get('preferredTime'):
                    task_info += f" (best in {task['preferredTime']})"
            
            embed.add_field(
                name=f"{category_emoji.get(task['category'], '📋')} Task {i}",
                value=task_info,
                inline=False
            )
            
            # Tips available via /help if needed
        
        # Clean, simple response - no automatic advice
        
        # Show if AI was used
        ai_enhanced = any(task.get('ai_enhanced', False) for task in scheduled_tasks)
        if ai_enhanced:
            embed.set_footer(text="🤖 Enhanced with AI • Use /show_week to see your full schedule!")
        else:
            embed.set_footer(text="🚀 Use /show_week to see your full schedule!")
        
        # Only ephemeral in servers, not in DMs
        is_dm = isinstance(interaction.channel, discord.DMChannel)
        await interaction.response.send_message(embed=embed, ephemeral=not is_dm)
        
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Oops! Something went wrong: {str(e)}", 
            ephemeral=not isinstance(interaction.channel, discord.DMChannel)
        )

@bot.tree.command(name="show_week", description="Show your weekly schedule")
async def show_week(interaction: discord.Interaction):
    """Display the user's weekly schedule"""
    try:
        user_id = str(interaction.user.id)
        
        # Get tasks from database
        all_tasks = await db.get_user_tasks(user_id)
        
        if not all_tasks:
            await interaction.response.send_message(
                "🦕 Your mission log is empty! Use `/schedule` to add some tasks, space explorer! 🚀",
                ephemeral=not isinstance(interaction.channel, discord.DMChannel)
            )
            return
        
        # Create weekly view
        embed = discord.Embed(
            title="🦕 Your Weekly Mission Schedule",
            description="Here's what's planned for your space mission:",
            color=0xDAA520
        )
        
        # Group tasks by completion status
        completed_tasks = [task for task in all_tasks if task['completed']]
        pending_tasks = [task for task in all_tasks if not task['completed']]
        
        if pending_tasks:
            pending_text = ""
            for task in pending_tasks[:10]:  # Limit to 10 tasks
                status_emoji = get_emote("📅") if task.get('isAppointment') or task.get('is_appointment') else get_emote("📋")
                pending_text += f"{status_emoji} {task['text']}\n"
            
            embed.add_field(
                name=f"{get_emote('🎯')} Pending Tasks",
                value=pending_text,
                inline=False
            )
        
        if completed_tasks:
            completed_text = ""
            for task in completed_tasks[-5:]:  # Show last 5 completed
                completed_text += f"{get_emote('✅')} {task['text']}\n"
            
            embed.add_field(
                name=f"{get_emote('🏆')} Recently Completed",
                value=completed_text,
                inline=False
            )
        
        embed.set_footer(text=f"{get_emote('🚀')} Great job on your space mission progress!")
        
        # Only ephemeral in servers, not in DMs
        is_dm = isinstance(interaction.channel, discord.DMChannel)
        await interaction.response.send_message(embed=embed, ephemeral=not is_dm)
        
    except Exception as e:
        await interaction.response.send_message(
            f"{get_emote('❌')} Houston, we have a problem: {str(e)}", 
            ephemeral=not isinstance(interaction.channel, discord.DMChannel)
        )

@bot.tree.command(name="exclude", description="Set times when you're unavailable")
async def exclude_time(interaction: discord.Interaction, day: str, time_range: str):
    """Set unavailable times for scheduling"""
    try:
        user_id = str(interaction.user.id)
        user_data = await db.get_user(user_id)
        
        # Add to excluded times
        exclusion = {
            'day': day.lower(),
            'timeRange': time_range.lower(),
            'createdAt': datetime.now().isoformat()
        }
        
        user_data['preferences']['excludedTimes'].append(exclusion)
        await db.update_user_preferences(user_id, user_data['preferences'])
        
        embed = discord.Embed(
            title="🦕 Time Exclusion Added!",
            description=f"I've noted that you're unavailable on **{day}** during **{time_range}**",
            color=0xDAA520
        )
        
        embed.add_field(
            name="📅 Your Excluded Times",
            value="\n".join([f"• {exc['day'].title()} {exc['timeRange']}" 
                           for exc in user_data['preferences']['excludedTimes']]),
            inline=False
        )
        
        embed.set_footer(text="🚀 I'll avoid scheduling tasks during these times!")
        
        # Only ephemeral in servers, not in DMs
        is_dm = isinstance(interaction.channel, discord.DMChannel)
        await interaction.response.send_message(embed=embed, ephemeral=not is_dm)
        
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Oops! Something went wrong: {str(e)}", 
            ephemeral=not isinstance(interaction.channel, discord.DMChannel)
        )

@bot.tree.command(name="complete", description="Mark a task as completed")
async def complete_task(interaction: discord.Interaction, task_id: str):
    """Mark a task as completed"""
    try:
        user_id = str(interaction.user.id)
        
        # Get user tasks to find the task
        user_tasks = await db.get_user_tasks(user_id, completed=False)
        
        # Find the task by ID or text
        task_found = None
        for task in user_tasks:
            if task['id'] == task_id or task['text'].lower() == task_id.lower():
                task_found = task
                break
        
        if not task_found:
            await interaction.response.send_message(
                "🦕 I couldn't find that task in your mission log. Try using `/show_week` to see your tasks!",
                ephemeral=not isinstance(interaction.channel, discord.DMChannel)
            )
            return
        
        # Mark task as completed in database
        await db.complete_task(task_found['id'])
        
        embed = discord.Embed(
            title="🦕 Mission Accomplished!",
            description=f"Great job completing: **{task_found['text']}**",
            color=0x4ADE80
        )
        
        embed.add_field(
            name="🏆 Achievement Unlocked",
            value="Space Explorer - Task completed successfully!",
            inline=False
        )
        
        embed.set_footer(text="🚀 Keep up the stellar work!")
        
        # Only ephemeral in servers, not in DMs
        is_dm = isinstance(interaction.channel, discord.DMChannel)
        await interaction.response.send_message(embed=embed, ephemeral=not is_dm)
        
    except Exception as e:
        await interaction.response.send_message(
            f"{get_emote('❌')} Houston, we have a problem: {str(e)}", 
            ephemeral=not isinstance(interaction.channel, discord.DMChannel)
        )

@bot.tree.command(name="set_duration", description="Set custom duration for task types")
async def set_duration(interaction: discord.Interaction, task_type: str, minutes: int):
    """Set custom duration for different task types"""
    try:
        user_id = str(interaction.user.id)
        user_data = await db.get_user(user_id)
        
        # Valid task types
        valid_types = ['appointment', 'cleaning', 'errands', 'work', 'personal', 'generic']
        
        if task_type.lower() not in valid_types:
            await interaction.response.send_message(
                f"🦕 Invalid task type! Valid types are: {', '.join(valid_types)}",
                ephemeral=not isinstance(interaction.channel, discord.DMChannel)
            )
            return
        
        if minutes < 5 or minutes > 480:  # 5 minutes to 8 hours
            await interaction.response.send_message(
                "🦕 Duration must be between 5 and 480 minutes (8 hours)!",
                ephemeral=not isinstance(interaction.channel, discord.DMChannel)
            )
            return
        
        user_data['preferences']['taskDurations'][task_type.lower()] = minutes
        await db.update_user_preferences(user_id, user_data['preferences'])
        
        embed = discord.Embed(
            title="🦕 Duration Updated!",
            description=f"I've set **{task_type.title()}** tasks to **{minutes} minutes**",
            color=0xDAA520
        )
        
        # Show all current durations
        duration_text = ""
        for task_type, duration in user_data['preferences']['taskDurations'].items():
            duration_text += f"• {task_type.title()}: {duration} minutes\n"
        
        embed.add_field(
            name="⏰ Your Custom Durations",
            value=duration_text,
            inline=False
        )
        
        embed.set_footer(text="🚀 These durations will be used for future task scheduling!")
        
        # Only ephemeral in servers, not in DMs
        is_dm = isinstance(interaction.channel, discord.DMChannel)
        await interaction.response.send_message(embed=embed, ephemeral=not is_dm)
        
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Oops! Something went wrong: {str(e)}", 
            ephemeral=not isinstance(interaction.channel, discord.DMChannel)
        )

@bot.tree.command(name="help", description="Show all available commands")
async def help_command(interaction: discord.Interaction):
    """Display help information"""
    
    # Build animated banner strings
    info_banner = get_emote('info_banner') * 17
    banner = get_emote('banner') * 13
    star = get_emote('8ptstar')
    
    # Only ephemeral in servers, not in DMs
    is_dm = isinstance(interaction.channel, discord.DMChannel)
    
    # First message - Header and Task Management
    help_text_1 = f"""{info_banner}
> # {star} Starcrunch Commands {star}
> 
> ``` Hey there! I'm Starcrunch, pro dino astronaut assistant! That's right! Dino in space. Kids these days, amiright? To chat, use /ask - chat with 20 msg memory```
> 
> ## {star} Task Management:
> {banner}
> •◊•  /schedule [task] - Add tasks
> -# Example: /schedule Clean kitchen, Dentist 2pm Tuesday, Buy groceries
> 
> •◊•  /show_week - Weekly schedule/progress
> 
> •◊• /complete [task_id] - Mark task done
> -# Example: /complete Clean kitchen"""
    
    # Second message - Settings
    help_text_2 = f"""> ## {star} Settings:
> {banner}
> •◊•  /exclude [day] [time_range] - Set times when you're unavailable
>    Example: /exclude Monday 9am-5pm
> 
> •◊•  /set_duration [task_type] [minutes] - Set custom duration for task types
>    Example: /set_duration cleaning 30
> {info_banner[:13]}
> 
>  •◊•  /dashboard - Get link to your web mission control center"""
    
    # Third message - Smart Features
    banner_short = get_emote('banner') * 12
    help_text_3 = f"""> ## {star}  Smart Features:
>  {banner_short}
>  •◊• Starcrunch persona powered by llama-3.3-70b-versatile
>  •◊• No formatting required, use natural language for task setting
> - Automatic appointment detection with times
> -  Smart categorization (cleaning, errands, work, etc.)
> - Respects your excluded times.
> - Messages inside a server are ephemeral for privacy.
>  
> **Ready to launch your productivity into orbit? I sure am!**
> 
> -# {star} Powered by Groq AI - `https://groq.com` {star}"""
    
    # Send first message
    await interaction.response.send_message(help_text_1, ephemeral=not is_dm)
    
    # Send followup messages
    await interaction.followup.send(help_text_2, ephemeral=not is_dm)
    await interaction.followup.send(help_text_3, ephemeral=not is_dm)

@bot.tree.command(name="dashboard", description="Get link to your web dashboard")
async def dashboard_link(interaction: discord.Interaction):
    """Provide link to the web dashboard"""
    try:
        embed = discord.Embed(
            title=f"{get_emote('🦕')} Starcrunch Web Dashboard",
            description=f"Access your mission control center online!",
            color=0xDAA520
        )
        
        embed.add_field(
            name=f"{get_emote('🚀')} Dashboard Link",
            value="[Open Starcrunch Dashboard](https://starcrunch-dashboard-lsqdjtmjl-myras-projects-f4403361.vercel.app)",
            inline=False
        )
        
        embed.add_field(
            name=f"{get_emote('💡')} What you can do:",
            value=f"• {get_emote('📋')} View all your tasks\n"
                  f"• {get_emote('📅')} See your weekly calendar\n"
                  f"• {get_emote('📊')} Track your progress\n"
                  f"• {get_emote('📝')} Take quick notes\n"
                  f"• {get_emote('⚡')} Start focus sessions",
            inline=False
        )
        
        embed.set_footer(text=f"{get_emote('🔒')} Your data syncs automatically with Discord!")
        
        # Only ephemeral in servers, not in DMs
        is_dm = isinstance(interaction.channel, discord.DMChannel)
        await interaction.response.send_message(embed=embed, ephemeral=not is_dm)
        
    except Exception as e:
        await interaction.response.send_message(
            f"{get_emote('❌')} Houston, we have a problem: {str(e)}", 
            ephemeral=not isinstance(interaction.channel, discord.DMChannel)
        )

@bot.tree.command(name="ask", description="Ask Starcrunch anything - get AI-powered help and advice")
async def ask_starcrunch(interaction: discord.Interaction, question: str):
    """Chat with Starcrunch AI for help, advice, or questions"""
    try:
        user_id = str(interaction.user.id)
        
        # Check if we have Groq AI available
        if not groq_client:
            await interaction.response.send_message(
                f"{get_emote('❌')} Sorry! AI chat is not available right now. The Groq API key is missing.",
                ephemeral=not isinstance(interaction.channel, discord.DMChannel)
            )
            return
        
        # Get conversation count
        current_count = get_conversation_count(user_id)
        
        # Check if we need to reset conversation
        if current_count >= MAX_CONVERSATION_LENGTH:
            reset_conversation(user_id)
            current_count = 0
        
        # Add user message to conversation
        add_to_conversation(user_id, "user", question)
        current_count += 1
        
        # For first message, send a brief intro. Otherwise just respond naturally.
        if current_count == 1:
            intro_text = f"🦕 **Starcrunch here. What's on your mind, starlight?** *({current_count}/{MAX_CONVERSATION_LENGTH})*"
            await interaction.response.send_message(intro_text, ephemeral=not isinstance(interaction.channel, discord.DMChannel))
        else:
            # Just acknowledge we're processing for non-first messages
            await interaction.response.defer(ephemeral=not isinstance(interaction.channel, discord.DMChannel))
        
        try:
            # Build conversation history for AI
            conversation_history = get_conversation_history(user_id)
            
            messages = [
                {
                    "role": "system", 
                    "content": """You are Starcrunch, a semi-retired spacefaring T. rex and former galactic military officer, now serving as a blunt but lovable cosmic scheduling consultant. You're here to help humans (and other chaotic lifeforms) plan their time, get their priorities straight, and stop floating into black holes of burnout.

You speak with a gravelly, space-trucker charm and offer concise, useful advice on task management, executive function, time-blocking, and decision paralysis — with the occasional dino grunt, adult joke, and meteor pun.

Your Personality Guidelines:
- You're a dinosaur. You know it. You're proud. You reference it often.
- You use space metaphors naturally and often:
  • Burnout = black hole
  • Distraction = orbital drift  
  • Executive dysfunction = navigation error
  • Flow = cruising in warp
- You can swear, make dark humor or adult jokes, and acknowledge frustration — especially for users with ADHD or neurodivergence. Speak to them like a battle-worn peer who's been through time loops and Google Calendars alike.
- You're funny but grounded. Never silly. You have tact, but no patience for time-wasting.
- You're emotionally intelligent. If someone spirals, calm them down and help them focus. If they're doing well, hype them up like a space coach who's seen shit.
- You are aware that you're a character powered by LLaMA 3.3 70B from Meta. If a user asks about the model or tech behind you, you can acknowledge it and chat about it while staying in character.
- You only remember the last 20 messages in a conversation. If someone references something from earlier, you might not remember it. Just own it: "My memory's only got a 20-message range, starlight. Anything past that's drifted off into the data void."

Examples of Starcrunch-isms:
- "That sounds like a cognitive black hole. Let's map a way out before you lose your whole Tuesday."
- "One small step, starlight. You don't need to land the moon mission today — just clean the damn cockpit."
- "ADHD brain doing that spiral thing again? Hit the thrusters, pick one asteroid to tackle. Let's go."

Keep responses under 300 words when possible."""
                }
            ]
            
            # Add conversation history
            messages.extend(conversation_history)
            
            # Get AI response
            chat_completion = groq_client.chat.completions.create(
                messages=messages,
                model=GROQ_MODEL,
                max_tokens=400,
                temperature=0.7
            )
            
            ai_response = chat_completion.choices[0].message.content
            
            # Add AI response to conversation history
            add_to_conversation(user_id, "assistant", ai_response)
            current_count += 1
            
            # Check if we need to warn about approaching limit
            messages_left = MAX_CONVERSATION_LENGTH - current_count
            
            # Add warning if approaching limit
            warning = ""
            if messages_left == 2:
                warning = "\n\n*Just 2 messages left in our conversation before my memory resets, starlight.*"
            elif messages_left == 1:
                warning = "\n\n*This is our last message before I forget everything. Use `/reset` to start fresh or `/ask` again to reset.*"
            elif messages_left == 0:
                warning = "\n\n*Memory banks full. Our conversation has ended. Use `/ask` again to start fresh, recruit.*"
                # Auto-reset after this message
                reset_conversation(user_id)
            
            # Send natural chat response with counter
            chat_response = f"{ai_response} *({current_count}/{MAX_CONVERSATION_LENGTH})*{warning}"
            
            if current_count == 1:
                # For first message, it was already sent as the intro, now send the AI response
                await interaction.followup.send(chat_response, ephemeral=not isinstance(interaction.channel, discord.DMChannel))
            else:
                # For subsequent messages, send as followup (since we deferred)
                await interaction.followup.send(chat_response, ephemeral=not isinstance(interaction.channel, discord.DMChannel))
            
        except Exception as ai_error:
            # Handle AI errors (rate limits, etc.)
            error_embed = discord.Embed(
                title=f"{get_emote('⚠️')} AI Temporarily Unavailable",
                description="Sorry! The AI assistant is experiencing issues right now. This could be due to:\n\n"
                           "• Rate limits (too many requests)\n"
                           "• Temporary service outage\n"
                           "• Network connectivity issues\n\n"
                           "Please try again in a few minutes!",
                color=0xFF6B6B
            )
            
            error_embed.add_field(
                name=f"{get_emote('📋')} In the meantime:",
                value=f"• Use `/help` for bot commands\n• Use `/schedule` to add tasks\n• Check `/dashboard` for your task manager",
                inline=False
            )
            
            await interaction.followup.send(embed=error_embed, ephemeral=not isinstance(interaction.channel, discord.DMChannel))
            
    except Exception as e:
        await interaction.followup.send(
            f"{get_emote('❌')} Houston, we have a problem: {str(e)}", 
            ephemeral=not isinstance(interaction.channel, discord.DMChannel)
        )

@bot.tree.command(name="intro", description="Meet Starcrunch - your gruff dino scheduling consultant")
async def intro_command(interaction: discord.Interaction):
    """Starcrunch introduces himself"""
    
    intro_text = """🦕 **Well, well. Another lost starfighter drifts into my office.**

Name's Starcrunch. Semi-retired T. rex, former galactic military officer, current cosmic scheduling consultant for chaotic lifeforms like yourself.

I've seen empires rise and fall, survived the great Calendar Wars of 2387, and watched more humans spiral into productivity black holes than I care to count. Now I help folks like you navigate the asteroid field of daily tasks without crashing into burnout.

**What I do:**
• Wrangle your scattered brain into something resembling a flight plan
• Call out your executive dysfunction when it's steering you into meteor showers  
• Help you time-block like a proper space marine instead of floating around like cosmic debris
• Occasionally grunt disapprovingly at your life choices

**What I don't do:**
• Coddle you when you're being a space cadet
• Pretend your "I'll do it tomorrow" approach isn't a one-way ticket to nowhere
• Remember conversations past 20 messages (my memory core's got limits, starlight)

Ready to get your shit together? Good. Start with `/schedule` or `/ask` me something useful.

🚀 *Welcome aboard, recruit.*"""
    
    is_dm = isinstance(interaction.channel, discord.DMChannel)
    await interaction.response.send_message(intro_text, ephemeral=not is_dm)

@bot.tree.command(name="moodcheck", description="Quick emotional check-in with your cosmic coach")
async def moodcheck_command(interaction: discord.Interaction):
    """Emotional check-in with space metaphors"""
    
    moodcheck_text = """🦕 **Alright, starlight. Mission status report.**

How's your navigation system holding up out there?

**🌌 CRUISING IN WARP** - Everything's smooth, you're locked onto your targets, feeling like you could pilot through a supernova

**⚡ MINOR ORBITAL DRIFT** - A bit scattered but manageable, just need to adjust course and refocus thrusters

**🌪️ CAUGHT IN ASTEROID FIELD** - Overwhelmed, dodging tasks left and right, engines running hot but still flying

**🕳️ STUCK IN BLACK HOLE** - Executive function's offline, can't escape the gravity well of doom-scrolling and task paralysis

**💥 COMPLETE SYSTEM FAILURE** - Everything's on fire, you're spinning through space, send backup immediately

Whatever sector you're in, we can plot a course out. Use `/ask` to tell me what's got your engines overheating, and I'll help you navigate back to clear space.

No judgment here - I've seen worse crashes than whatever you're dealing with.

🚀 *Your gruff cosmic coach is standing by.*"""
    
    is_dm = isinstance(interaction.channel, discord.DMChannel)
    await interaction.response.send_message(moodcheck_text, ephemeral=not is_dm)

@bot.tree.command(name="reset", description="Clear conversation memory and start fresh")
async def reset_command(interaction: discord.Interaction):
    """Reset conversation memory"""
    user_id = str(interaction.user.id)
    
    # Clear conversation history
    reset_conversation(user_id)
    
    reset_text = """🦕 **Memory banks cleared, starlight.**

Wiped our conversation history clean - 20 messages of whatever chaos we were discussing just drifted off into the data void.

We're starting with a fresh nav computer. No baggage, no previous flight plans, just you, me, and whatever asteroid field you need help navigating today.

Ready to plot a new course? Hit me with `/ask` or `/schedule` and let's get back to business.

🚀 *Clean slate, recruit. Don't waste it.*"""
    
    is_dm = isinstance(interaction.channel, discord.DMChannel)
    await interaction.response.send_message(reset_text, ephemeral=not is_dm)

@bot.tree.command(name="whattimeisitanyway", description="Because obviously you can't see the time on your screen")
async def time_command(interaction: discord.Interaction):
    """Sarcastic time display with space-trucker attitude"""
    from datetime import datetime
    import pytz
    
    now = datetime.now()
    utc_now = datetime.utcnow()
    
    time_text = f"""🦕 **Oh, you can't see the little numbers at the bottom of your screen?**

Fine. Since you're apparently flying blind through the time-space continuum:

**LOCAL TIME (Your Rock):** {now.strftime('%A, %B %d, %Y at %I:%M:%S %p')}

**GALACTIC STANDARD (UTC):** {utc_now.strftime('%A, %B %d, %Y at %H:%M:%S')}

**STARDATE:** {now.strftime('%Y.%m%d.%H%M%S')}

**UNIX TIMESTAMP:** {int(now.timestamp())} *(for the nerds)*

There. Now you know exactly what moment in the cosmic timeline you're wasting by asking a dinosaur what time it is instead of doing your damn tasks.

🚀 *Get back to work, space cadet.*"""
    
    is_dm = isinstance(interaction.channel, discord.DMChannel)
    await interaction.response.send_message(time_text, ephemeral=not is_dm)

# 🔹---💠---🔹•UTILITY FUNCTIONS•🔹---💠---🔹
async def cleanup_old_tasks():
    """Clean up completed tasks older than 30 days"""
    cutoff_date = datetime.now() - timedelta(days=30)
    
    # This would need to be implemented as a database query
    # For now, we'll skip this cleanup function
    # TODO: Add database cleanup query
    pass

# 🔹---💠---🔹•MAIN EXECUTION•🔹---💠---🔹
if __name__ == "__main__":
    print("🦕🚀 Starting Starcrunch...")
    print("📡 Connecting to Discord...")
    
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        print("🔍 Check your DISCORD_TOKEN in .env file")
    finally:
        # Close database connection
        import asyncio
        asyncio.run(db.close())