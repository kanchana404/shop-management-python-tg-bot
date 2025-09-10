# 🚀 Hosting Deployment Guide

This guide helps you deploy the Telegram Shop Bot to various hosting platforms.

## 🔧 Common Hosting Issues & Solutions

### ❌ **"unable to open database file" Error**

**Cause**: The bot can't create session files due to permission issues or missing directories.

**Solutions**:

#### **1. Set Custom Session Directory**
Add to your `.env` file:
```bash
# For hosting with /tmp write access
SESSION_DIR=/tmp/sessions

# For hosting with limited permissions
SESSION_DIR=/app/sessions

# For Docker containers
SESSION_DIR=/data/sessions
```

#### **2. Create Directory with Permissions**
```bash
# On your hosting platform
mkdir -p /tmp/sessions
chmod 755 /tmp/sessions

# Or wherever your SESSION_DIR points to
mkdir -p $SESSION_DIR
chmod 755 $SESSION_DIR
```

#### **3. Use System Temp Directory**
If all else fails, the bot will automatically fallback to system temp directory.

## 🌐 Platform-Specific Guides

### **Heroku**
```bash
# In your .env or Heroku config vars
SESSION_DIR=/tmp/sessions
```

### **Railway**
```bash
# In your environment variables
SESSION_DIR=/app/sessions
```

### **DigitalOcean App Platform**
```bash
# In your app spec or environment variables
SESSION_DIR=/tmp/sessions
```

### **AWS EC2/VPS**
```bash
# Create directory with proper permissions
sudo mkdir -p /opt/telegram_bot/sessions
sudo chown $USER:$USER /opt/telegram_bot/sessions
sudo chmod 755 /opt/telegram_bot/sessions

# In your .env
SESSION_DIR=/opt/telegram_bot/sessions
```

### **Docker Deployment**
```dockerfile
# In your Dockerfile
RUN mkdir -p /app/sessions && chmod 755 /app/sessions

# Or mount a volume
VOLUME ["/app/sessions"]
```

```yaml
# In docker-compose.yml
services:
  bot:
    volumes:
      - ./sessions:/app/sessions
    environment:
      - SESSION_DIR=/app/sessions
```

## 🔍 **Debugging Steps**

### **1. Test Write Permissions**
```bash
# Test if you can create files in your session directory
echo "test" > $SESSION_DIR/test.txt
rm $SESSION_DIR/test.txt
```

### **2. Check Available Directories**
```bash
# Check what directories are writable
ls -la /tmp/
ls -la /app/
ls -la ./
```

### **3. Monitor Bot Logs**
Look for these log messages:
```
✅ Session directory ready: /path/to/sessions
⚠️ Cannot write to sessions: [error]
✅ Using temp session directory: /tmp/telegram_bot_sessions
✅ Using current directory for sessions: ./.sessions
```

## 📋 **Environment Variables for Hosting**

```bash
# Required
BOT_TOKENS=your_bot_token_here
MONGO_URI=mongodb://...
OWNER_ID=your_telegram_id

# Session handling (important for hosting)
SESSION_DIR=/tmp/sessions

# Optional but recommended
API_ID=6
API_HASH=eb06d4abfb49dc3eeb1aeb98ae0f581e
LOG_LEVEL=INFO
ENVIRONMENT=production
```

## 🛠️ **Automated Fallback System**

The bot automatically tries these locations in order:

1. **Configured Directory**: `SESSION_DIR` from environment
2. **System Temp**: `/tmp/telegram_bot_sessions`
3. **Current Directory**: `./.sessions`

## ⚡ **Quick Fix Commands**

```bash
# For most hosting platforms
export SESSION_DIR=/tmp/sessions
mkdir -p $SESSION_DIR
python main.py

# For containers
export SESSION_DIR=/app/sessions
mkdir -p $SESSION_DIR
python main.py

# Let the bot auto-detect
unset SESSION_DIR
python main.py
```

## 🔐 **Security Notes**

- Session files contain authentication tokens
- Use secure directories with proper permissions
- Consider using environment-specific session directories
- Backup session files for bot persistence

## 📞 **Still Having Issues?**

1. Check your hosting platform's documentation for writable directories
2. Contact your hosting provider about file write permissions
3. Try the automatic fallback by not setting `SESSION_DIR`
4. Use Docker with proper volume mounts

The bot is designed to work on any hosting platform with these fallback mechanisms!
