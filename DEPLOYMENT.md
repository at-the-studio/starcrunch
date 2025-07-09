# 🦕🚀 Starcrunch Vercel Deployment Guide

## 📋 Prerequisites

1. **Vercel Account** - Already have one ✅
2. **GitHub Repository** - Push your code to GitHub
3. **fps.ms Database** - Already configured ✅

## 🔧 Environment Variables

### Required Variables for Vercel:
Add these to your Vercel project settings:

```bash
# Database Configuration
DB_HOST=db0.fps.ms
DB_PORT=3306
DB_USER=u48754_mRctAZqVYA
DB_PASSWORD=^r^On@Mz@h9ixqVsmvD3nyDy
DB_NAME=s48754_Starcrunch

# Groq AI Configuration (for Discord bot integration)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_FALLBACK_MODEL=llama-3.1-8b-instant
```

## 🚀 Deployment Steps

### 1. Prepare Your Repository

```bash
# Make sure you're in the starcrunch directory
cd /mnt/c/fuckUmicrosoft/starcrunch

# Install dependencies locally (optional, for testing)
npm install

# Create .gitignore if it doesn't exist
echo "node_modules/
.env
.vercel
*.log" > .gitignore
```

### 2. Push to GitHub

```bash
# Initialize git if not already done
git init

# Add files
git add .

# Commit
git commit -m "🦕 Initial Starcrunch dashboard deployment"

# Push to your GitHub repository
git remote add origin https://github.com/yourusername/starcrunch-dashboard.git
git branch -M main
git push -u origin main
```

### 3. Deploy to Vercel

#### Option A: Vercel CLI (Recommended)
```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel --prod
```

#### Option B: Vercel Web Dashboard
1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Vercel will auto-detect the configuration from `vercel.json`

### 4. Configure Environment Variables

In your Vercel project dashboard:
1. Go to **Settings** → **Environment Variables**
2. Add all the variables listed above
3. Redeploy if needed

## 🔗 API Endpoints

After deployment, your API endpoints will be:

```
https://your-project.vercel.app/api/tasks?userId=DISCORD_USER_ID
https://your-project.vercel.app/api/notes?userId=DISCORD_USER_ID
https://your-project.vercel.app/api/complete?userId=DISCORD_USER_ID&taskId=TASK_ID
https://your-project.vercel.app/api/stats?userId=DISCORD_USER_ID
https://your-project.vercel.app/api/preferences?userId=DISCORD_USER_ID
```

## 📱 Dashboard Access

- **General**: `https://your-project.vercel.app/`
- **User-specific**: `https://your-project.vercel.app/dashboard/DISCORD_USER_ID`

## 🔄 Discord Bot Integration

The Discord bot (running on fps.ms) will connect to the same database, enabling real-time sync between:
- Discord commands (`/schedule`, `/show_week`, etc.)
- Web dashboard tasks and notes

## 🐛 Troubleshooting

### Common Issues:

1. **Database Connection Failed**
   - Check environment variables are set correctly
   - Verify database credentials

2. **API Functions Not Working**
   - Check function logs in Vercel dashboard
   - Ensure all dependencies are in package.json

3. **CORS Issues**
   - Functions should already include CORS headers
   - Check browser console for errors

### Testing Locally:
```bash
# Install dependencies
npm install

# Run Vercel development server
vercel dev

# Access at: http://localhost:3000
```

## 📈 Performance Notes

- **Cold Starts**: First request may be slower (~1-2 seconds)
- **Database Pooling**: Connection pooling enabled for better performance
- **Caching**: Vercel automatically caches static assets

## 🔒 Security

- All API endpoints include CORS protection
- Database credentials stored securely in environment variables
- No sensitive data exposed in client-side code

## 🎯 Next Steps

1. **Custom Domain**: Add your own domain in Vercel settings
2. **Analytics**: Enable Vercel Analytics for usage tracking
3. **Monitoring**: Set up alerts for API errors

Your Starcrunch dashboard is now ready to deploy! 🚀