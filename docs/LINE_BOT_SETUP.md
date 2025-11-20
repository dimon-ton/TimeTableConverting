# LINE Bot Setup Guide

Complete guide to setting up a LINE Messaging API bot for the automated leave request system.

## Overview

This system uses LINE for two purposes:
1. **Receiving leave requests** from teachers via LINE group messages
2. **Sending daily substitute reports** back to the LINE group

---

## Prerequisites

- LINE account (personal LINE account)
- LINE Developers account (free, created from personal account)
- Access to add bots to LINE groups

---

## Step 1: Create LINE Developers Account

1. **Go to LINE Developers Console**
   - Visit: https://developers.line.biz/console/

2. **Log in with LINE**
   - Click "Log in with LINE"
   - Use your personal LINE account credentials

3. **Create a Provider** (if you don't have one)
   - Click "Create a new provider"
   - Enter provider name: "School Leave Management" (or any name)
   - Click "Create"

---

## Step 2: Create Messaging API Channel

1. **Create Channel**
   - In your provider page, click "Create a new channel"
   - Select "Messaging API"

2. **Fill in Channel Information**
   - **Channel name**: "Leave Request Bot"
   - **Channel description**: "Automated teacher leave request and substitute assignment system"
   - **Category**: Education
   - **Subcategory**: Educational platform
   - **Email address**: Your email

3. **Review and Create**
   - Accept the terms
   - Click "Create"

---

## Step 3: Get Channel Credentials

### 3.1 Get Channel Secret

1. Go to the "Basic settings" tab
2. Find "Channel secret"
3. Click "Show" or "Copy"
4. Save this value - you'll need it for `.env` file

### 3.2 Get Channel Access Token

1. Go to the "Messaging API" tab
2. Scroll down to "Channel access token (long-lived)"
3. Click "Issue"
4. Click "Copy"
5. Save this value - you'll need it for `.env` file

**Important**: Never share these credentials or commit them to git!

---

## Step 4: Configure Bot Settings

### 4.1 Enable Webhook

1. In "Messaging API" tab, find "Webhook settings"
2. Set "Webhook URL": `https://your-domain-or-ngrok-url.com/callback`
   - For local testing: Use ngrok (explained later)
   - For production: Use your Raspberry Pi's public URL
3. Toggle "Use webhook" to **Enabled**
4. Click "Verify" to test (will fail until your server is running)

### 4.2 Disable Auto-Reply

1. In "Messaging API" tab, find "Auto-reply messages"
2. Click "Edit" (opens LINE Official Account Manager)
3. Toggle "Auto-reply" to **Disabled**
4. Toggle "Greeting message" to **Disabled** (optional)

This prevents the bot from sending automatic replies while your custom webhook handles messages.

### 4.3 Allow Bot to Join Groups

1. In "Messaging API" tab, find "Bot settings"
2. Toggle "Allow bot to join group chats" to **Enabled**

---

## Step 5: Create Your .env File

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```env
   # Google Sheets Configuration
   SPREADSHEET_ID=1KpQZlrJk03ZS_Q0bTWvxHjG9UFiD1xPZGyIsQfRkRWo

   # LINE Bot Credentials (from Step 3)
   LINE_CHANNEL_SECRET=your_actual_channel_secret_here
   LINE_CHANNEL_ACCESS_TOKEN=your_actual_channel_access_token_here

   # LINE Group ID (will get this in Step 7)
   LINE_GROUP_ID=

   # OpenRouter API (from Step 6)
   OPENROUTER_API_KEY=your_openrouter_api_key_here

   # Flask Settings
   WEBHOOK_HOST=0.0.0.0
   WEBHOOK_PORT=5000
   DEBUG_MODE=False
   ```

3. **Never commit .env to git!** (It's already in .gitignore)

---

## Step 6: Get OpenRouter API Key (for AI Message Parsing)

The system uses Gemini (free tier) via OpenRouter to parse teacher leave requests.

1. **Sign up for OpenRouter**
   - Visit: https://openrouter.ai/
   - Click "Sign In" (can use Google account)

2. **Get API Key**
   - Go to "Keys" section: https://openrouter.ai/keys
   - Click "Create Key"
   - Name it: "Leave Request Parser"
   - Copy the key

3. **Add to .env**
   ```env
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   ```

4. **Free Tier**
   - We use `google/gemini-2.0-flash-exp:free` model
   - Free with rate limits (sufficient for school use)
   - Monitor usage at: https://openrouter.ai/activity

---

## Step 7: Add Bot to LINE Group

### 7.1 Create or Use Existing Group

1. Open LINE app on your phone
2. Create a new group or use existing: "พรุ่งนี้ขอลานะครับ" (Teachers' group)
3. Add members (teachers who will send leave requests)

### 7.2 Add Bot to Group

1. In the LINE group, tap the menu (≡) → "Add friends"
2. Search for your bot name: "Leave Request Bot"
   - Or use QR code from Messaging API tab
3. Add the bot to the group

### 7.3 Get Group ID

**Option A: From Webhook Events (Recommended)**

1. Start your webhook server:
   ```bash
   python webhook.py
   ```

2. In the LINE group, send a test message: "Hello bot"

3. Check your webhook logs - you'll see the `groupId` in the event data

4. Copy the group ID and add to `.env`:
   ```env
   LINE_GROUP_ID=C1234567890abcdef1234567890abcdef
   ```

**Option B: Using LINE Official Account Manager**

- This is more complex and may not show group IDs directly
- Option A (webhook logs) is easier

---

## Step 8: Local Testing with ngrok

For local development on Windows, use ngrok to expose your Flask server:

### 8.1 Install ngrok

1. Download from: https://ngrok.com/download
2. Extract to a folder
3. Sign up for free account
4. Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken
5. Run: `ngrok authtoken YOUR_AUTH_TOKEN`

### 8.2 Start ngrok Tunnel

```bash
# Start ngrok on port 5000 (same as Flask)
ngrok http 5000
```

You'll see output like:
```
Forwarding    https://abc123.ngrok.io -> http://localhost:5000
```

### 8.3 Update LINE Webhook URL

1. Go to LINE Developers Console → Messaging API tab
2. Update Webhook URL to: `https://abc123.ngrok.io/callback`
3. Click "Verify"

### 8.4 Start Your Flask Server

```bash
python webhook.py
```

### 8.5 Test

1. Send a message in your LINE group
2. Check your Flask server logs
3. You should see incoming webhook events

**Note**: ngrok URLs change each restart (free tier). For production, use a fixed domain.

---

## Step 9: Production Deployment (Raspberry Pi)

### 9.1 Prerequisites

- Raspberry Pi with internet connection
- Static IP or domain name
- Port forwarding configured on router

### 9.2 Install Dependencies

```bash
# SSH into Raspberry Pi
ssh pi@your-pi-address

# Navigate to project
cd /home/pi/TimeTableConverting

# Install Python packages
pip install -r requirements.txt
```

### 9.3 Set Up Systemd Service

Create `/etc/systemd/system/line-webhook.service`:

```ini
[Unit]
Description=LINE Bot Webhook Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/TimeTableConverting
ExecStart=/usr/bin/python3 /home/pi/TimeTableConverting/webhook.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable line-webhook
sudo systemctl start line-webhook
sudo systemctl status line-webhook
```

### 9.4 Set Up Cron Job for Daily Processing

Edit crontab:
```bash
crontab -e
```

Add this line (runs at 8:55 AM Mon-Fri):
```cron
55 8 * * 1-5 cd /home/pi/TimeTableConverting && /usr/bin/python3 process_daily_leaves.py --send-line >> /home/pi/logs/daily_process.log 2>&1
```

### 9.5 Configure Firewall

```bash
# Allow Flask port (if needed)
sudo ufw allow 5000/tcp
```

### 9.6 Update LINE Webhook URL

1. Set up port forwarding on your router: External port 5000 → Pi's port 5000
2. Get your public IP or domain
3. Update LINE webhook URL to: `http://your-public-ip:5000/callback`
   - For security, consider using nginx with SSL

---

## Step 10: Verify Setup

### 10.1 Test Configuration

```bash
python config.py
```

Should show all credentials as "Set" with no errors.

### 10.2 Test Webhook

1. Start webhook server: `python webhook.py`
2. Send message in LINE group
3. Check server logs for incoming events

### 10.3 Test AI Parsing

```bash
python -c "from ai_parser import parse_leave_request; print(parse_leave_request('ครูสุกฤษฎิ์ ขอลาพรุ่งนี้คาบ 1-3'))"
```

Should return structured data with teacher, date, periods.

### 10.4 Test Daily Processing

```bash
# Test mode (no Sheets update)
python process_daily_leaves.py --test

# Real run
python process_daily_leaves.py
```

### 10.5 Test LINE Messaging

```bash
python -c "from line_messaging import send_test_message; send_test_message()"
```

Should send a test message to your configured LINE group.

---

## Troubleshooting

### Webhook not receiving messages

- Check webhook URL is correct in LINE Console
- Verify webhook is enabled
- Check Flask server is running and accessible
- For ngrok: ensure tunnel is active
- Check LINE bot is added to group

### "Invalid signature" errors

- Check `LINE_CHANNEL_SECRET` in `.env` matches LINE Console
- Ensure no extra spaces or quotes in `.env` values

### AI parsing not working

- Verify `OPENROUTER_API_KEY` is correct
- Check OpenRouter rate limits: https://openrouter.ai/activity
- Try different model if free tier has issues

### Messages sent but not showing in LINE

- Check `LINE_CHANNEL_ACCESS_TOKEN` is correct
- Verify bot is not blocked in the group
- Check `LINE_GROUP_ID` is correct

### Cron job not running

- Check cron logs: `grep CRON /var/log/syslog`
- Verify paths are absolute in crontab
- Test command manually first
- Ensure Python environment is activated in cron

---

## Security Best Practices

1. **Never commit credentials**
   - Always use `.env` for secrets
   - Keep `.env` in `.gitignore`

2. **Use HTTPS in production**
   - LINE requires HTTPS for webhooks (or use ngrok)
   - Consider nginx reverse proxy with Let's Encrypt SSL

3. **Validate webhook signatures**
   - Already implemented in `webhook.py`
   - Never skip signature verification

4. **Restrict API access**
   - Use firewall rules on Raspberry Pi
   - Only allow necessary ports

5. **Monitor API usage**
   - Check OpenRouter usage regularly
   - Set up alerts for unusual activity

6. **Regular backups**
   - Backup Google Sheets data
   - Backup `.env` file securely (not in git!)

---

## Next Steps

Once setup is complete:

1. **Add test absence** to Google Sheets manually
2. **Run** `python process_daily_leaves.py --test`
3. **Verify** substitute assignments appear
4. **Test LINE integration** with real messages
5. **Monitor** for a few days before going fully automated
6. **Set up cron** for production daily processing

For issues, check:
- Server logs: `journalctl -u line-webhook -f`
- Cron logs: `/var/log/syslog`
- Application logs in your script output

---

## References

- LINE Messaging API Docs: https://developers.line.biz/en/docs/messaging-api/
- OpenRouter Docs: https://openrouter.ai/docs
- ngrok Docs: https://ngrok.com/docs
- Flask Docs: https://flask.palletsprojects.com/
