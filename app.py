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
            suggestions.append("🌅 Best done in the morning when energy is high")
        elif task['category'] == 'errands':
            suggestions.append("🛍️ Consider batching with other errands")
            suggestions.append("🏪 Check store hours before scheduling")
        elif task['category'] == 'work':
            suggestions.append("⏰ Schedule during your peak focus hours")
        elif task['priority'] == 'high':
            suggestions.append("🔥 High priority - schedule ASAP")
        
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
    
    # Only respond to DMs or mentions
    if isinstance(message.channel, discord.DMChannel):
        # Check if it's a command
        if not message.content.startswith('/'):
            await message.channel.send(
                "🦕 Hey there, space explorer! I'm Starcrunch, your friendly task scheduling assistant.\n"
                "Use `/schedule` to add tasks, or `/help` to see all my commands! 🚀"
            )
    
    await bot.process_commands(message)

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
                'appointment': '📅',
                'cleaning': '🧹',
                'errands': '🛍️',
                'work': '💼',
                'personal': '👤',
                'generic': '📋'
            }
            
            priority_emoji = {
                'high': '🔥',
                'medium': '⚡',
                'low': '💤'
            }
            
            # Build task info
            task_info = f"**{task['text']}**\n"
            task_info += f"Category: {task['category'].title()}\n"
            task_info += f"Priority: {priority_emoji.get(task['priority'], '⚡')} {task['priority'].title()}\n"
            task_info += f"Duration: {task['duration']} minutes\n"
            
            if task['isAppointment']:
                task_info += f"⏰ Fixed appointment"
                if task['scheduledTime']:
                    task_info += f" at {task['scheduledTime']}"
                if task['scheduledDay']:
                    task_info += f" on {task['scheduledDay']}"
            else:
                task_info += f"📋 Flexible task"
                if task.get('preferredTime'):
                    task_info += f" (best in {task['preferredTime']})"
            
            embed.add_field(
                name=f"{category_emoji.get(task['category'], '📋')} Task {i}",
                value=task_info,
                inline=False
            )
            
            # Add AI tips if available
            if task.get('adhd_tips'):
                ai_tips = "\n".join([f"🤖 {tip}" for tip in task['adhd_tips'][:2]])
                embed.add_field(
                    name="🧠 ADHD Tips",
                    value=ai_tips,
                    inline=False
                )
            elif task.get('schedulingSuggestions'):
                suggestions = "\n".join(task['schedulingSuggestions'][:2])
                embed.add_field(
                    name="💡 Scheduling Tips",
                    value=suggestions,
                    inline=False
                )
        
        # Add AI motivation message if available
        first_task = scheduled_tasks[0] if scheduled_tasks else None
        if first_task and first_task.get('ai_motivation'):
            embed.add_field(
                name="🦕 Starcrunch says:",
                value=first_task['ai_motivation'],
                inline=False
            )
        
        # Add AI overall suggestions if available  
        if first_task and first_task.get('ai_suggestions'):
            ai_suggestions = "\n".join([f"• {tip}" for tip in first_task['ai_suggestions'][:3]])
            embed.add_field(
                name="🚀 Mission Strategy:",
                value=ai_suggestions,
                inline=False
            )
        
        # Show if AI was used
        ai_enhanced = any(task.get('ai_enhanced', False) for task in scheduled_tasks)
        if ai_enhanced:
            embed.set_footer(text="🤖 Enhanced with AI • Use /show_week to see your full schedule!")
        else:
            embed.set_footer(text="🚀 Use /show_week to see your full schedule!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Oops! Something went wrong: {str(e)}", 
            ephemeral=True
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
                ephemeral=True
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
                status_emoji = "📅" if task['isAppointment'] else "📋"
                pending_text += f"{status_emoji} {task['text']}\n"
            
            embed.add_field(
                name="🎯 Pending Tasks",
                value=pending_text,
                inline=False
            )
        
        if completed_tasks:
            completed_text = ""
            for task in completed_tasks[-5:]:  # Show last 5 completed
                completed_text += f"✅ {task['text']}\n"
            
            embed.add_field(
                name="🏆 Recently Completed",
                value=completed_text,
                inline=False
            )
        
        embed.set_footer(text="🚀 Great job on your space mission progress!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Houston, we have a problem: {str(e)}", 
            ephemeral=True
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
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Oops! Something went wrong: {str(e)}", 
            ephemeral=True
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
                ephemeral=True
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
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Houston, we have a problem: {str(e)}", 
            ephemeral=True
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
                ephemeral=True
            )
            return
        
        if minutes < 5 or minutes > 480:  # 5 minutes to 8 hours
            await interaction.response.send_message(
                "🦕 Duration must be between 5 and 480 minutes (8 hours)!",
                ephemeral=True
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
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Oops! Something went wrong: {str(e)}", 
            ephemeral=True
        )

@bot.tree.command(name="help", description="Show all available commands")
async def help_command(interaction: discord.Interaction):
    """Display help information"""
    embed = discord.Embed(
        title="🦕🚀 Starcrunch Command Center",
        description="Hey there, space explorer! I'm Starcrunch, your friendly dinosaur astronaut assistant. Here's how I can help you manage your mission:",
        color=0xDAA520
    )
    
    embed.add_field(
        name="📋 `/schedule [tasks]`",
        value="Add tasks to your mission log\n*Example: `/schedule Clean kitchen, Dentist 2pm Tuesday, Buy groceries`*",
        inline=False
    )
    
    embed.add_field(
        name="📅 `/show_week`",
        value="Display your weekly schedule and mission progress",
        inline=False
    )
    
    embed.add_field(
        name="✅ `/complete [task_id]`",
        value="Mark a task as completed\n*Example: `/complete Clean kitchen`*",
        inline=False
    )
    
    embed.add_field(
        name="🚫 `/exclude [day] [time_range]`",
        value="Set times when you're unavailable\n*Example: `/exclude Monday 9am-5pm`*",
        inline=False
    )
    
    embed.add_field(
        name="⏰ `/set_duration [task_type] [minutes]`",
        value="Set custom duration for task types\n*Example: `/set_duration cleaning 30`*",
        inline=False
    )
    
    embed.add_field(
        name="🎯 Smart Features",
        value="• 🤖 AI-powered task analysis and ADHD-friendly tips\n"
              "• 📅 Automatic appointment detection with times\n"
              "• 🏷️ Smart categorization (cleaning, errands, work, etc.)\n"
              "• ⚡ Priority detection from your language\n"
              "• 🚫 Respects your excluded times\n"
              "• 🔒 Works best in DMs for privacy!",
        inline=False
    )
    
    embed.add_field(
        name="🧠 AI Enhancement",
        value="Powered by Groq AI for intelligent scheduling and personalized ADHD support!",
        inline=False
    )
    
    embed.set_footer(text="🚀 Ready to launch your productivity into orbit!")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

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