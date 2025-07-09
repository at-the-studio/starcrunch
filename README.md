# Starcrunch - ADHD-Friendly Task Scheduler

**Starcrunch** is a friendly dinosaur astronaut that helps users with ADHD manage their tasks and schedule through a Discord bot and web dashboard combination.

## Features

### Discord Bot
- **AI-Powered Analysis**: Uses Groq AI (Llama 3.3 70B) for intelligent task understanding
- **Smart Task Parsing**: Parse natural language like "Dentist 2pm Tuesday, Clean kitchen urgent, Buy groceries"
- **Automatic Categorization**: AI-enhanced detection of appointments, cleaning, errands, work, and personal tasks
- **Priority Detection**: AI understands urgency from context and keywords
- **ADHD-Specific Tips**: Personalized strategies for task completion
- **Scheduling Suggestions**: AI-driven optimal timing based on task type and energy levels
- **Privacy-First**: Works in DMs for personal task management
- **Slash Commands**: Modern Discord interface with `/schedule`, `/show_week`, `/complete`, etc.

### Web Dashboard
- **Real-time Task Management**: Add, complete, and organize tasks visually
- **Interactive Calendar**: Month/week views with task indicators
- **Progress Tracking**: Visual progress rings for tasks, energy, and focus
- **Brain Dump**: Free-form note-taking with auto-save
- **Quick Actions**: Pomodoro timer, focus mode, export functionality
- **Space Theme**: Animated Starfield asthetics

### ADHD-Friendly Design
- **Minimal Friction**: Quick task entry and completion
- **Visual Progress**: Clear indicators of achievement
- **Scheduling Help**: Smart suggestions for when to do tasks
- **Categorization**: Automatic organization to reduce cognitive load
- **Gamification**: Achievement messages and space explorer theme

## Quick Start

### Discord Bot Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create Discord Bot**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create new application and bot
   - Copy the bot token

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add:
   # - DISCORD_TOKEN (required)
   # - GROQ_API_KEY (optional, for AI features)
   # - GROQ_MODEL (defaults to llama-3.3-70b-versatile)
   # - GROQ_FALLBACK_MODEL (defaults to llama-3.1-8b-instant)
   ```

4. **Run the Bot**
   ```bash
   python app.py
   ```

5. **Invite Bot to Server**
   - Generate invite link with applications.commands scope
   - Invite to your server or use in DMs

### Web Dashboard Setup (Vercel Deployment)

1. **Deploy to Vercel**
   ```bash
   vercel --prod
   ```

2. **Set Environment Variables** in Vercel dashboard:
   - Database credentials (same as Discord bot)
   - Groq API key for AI features

3. **Access Dashboard**
   - General: `https://your-project.vercel.app/`
   - User-specific: `https://your-project.vercel.app/dashboard/YOUR_DISCORD_USER_ID`

4. **Real-time Sync**
   - Dashboard now syncs with Discord bot through shared database
   - Changes appear instantly in both interfaces

## Discord Bot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/schedule [tasks]` | Add comma-separated tasks | `/schedule Clean kitchen, Dentist 2pm Tuesday, Buy groceries` |
| `/show_week` | Display weekly schedule | `/show_week` |
| `/complete [task]` | Mark task as completed | `/complete Clean kitchen` |
| `/exclude [day] [time]` | Set unavailable times | `/exclude Monday 9am-5pm` |
| `/set_duration [type] [min]` | Set task durations | `/set_duration cleaning 30` |
| `/help` | Show all commands | `/help` |

## Task Categories

The bot automatically categorizes tasks based on keywords:

- **📅 Appointments**: dentist, doctor, meeting, call, visit
- **🧹 Cleaning**: clean, vacuum, dishes, laundry, tidy
- **🛍️ Errands**: grocery, shopping, bank, store, pickup
- **💼 Work**: work, project, deadline, presentation, report
- **👤 Personal**: exercise, workout, read, family
- **📋 Generic**: Everything else

## Advanced Features

### AI-Powered Scheduling (Groq Integration)
- **Natural Language Understanding**: AI analyzes complex task descriptions
- **ADHD-Specific Recommendations**: Personalized tips for task completion
- **Context-Aware Priority**: Understands urgency beyond keywords
- **Energy Level Matching**: Suggests tasks based on optimal energy periods
- **Motivational Support**: Encouraging messages tailored to ADHD users
- **Fallback Safety**: Gracefully reverts to rule-based if AI unavailable

### Smart Scheduling Logic
- **Appointment Detection**: Recognizes specific times and dates
- **Duration Estimation**: AI-enhanced time predictions per task
- **Preference Learning**: Respects excluded times and preferences
- **Energy Optimization**: AI suggests tasks based on energy patterns

### Data Persistence
- **Discord Bot**: Uses MySQL database on fps.ms
- **Web Dashboard**: Uses same MySQL database for real-time sync
- **Real-time Sync**: Changes appear instantly in both interfaces

### Customization
- **Task Durations**: Customize default time blocks per category
- **Excluded Times**: Set unavailable periods for scheduling
- **Priority Keywords**: Automatic priority detection from language

## Project Structure

```
starcrunch/
├── app.py                 # Discord bot with AI integration
├── dashboard.html         # Web dashboard (standalone)
├── requirements.txt       # Python dependencies (includes groq)
├── .env                  # Environment variables (don't commit!)
├── .env.example          # Environment template
├── README.md             # This file
├── claude.md             # Development guidelines
└── starcrunch_data.json  # Bot data storage (auto-created)
```

## AI Configuration

The bot uses **Groq AI** for enhanced task understanding:

- **Primary Model**: `llama-3.3-70b-versatile` - Fast, powerful analysis
- **Fallback Model**: `llama-3.1-8b-instant` - Quick responses if main fails
- **ADHD Focus**: Specialized prompts for neurodivergent-friendly responses
- **Graceful Degradation**: Falls back to rule-based if AI unavailable

