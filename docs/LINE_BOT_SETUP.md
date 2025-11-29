# LINE Bot Setup Guide

Complete guide to setting up a LINE Messaging API bot for the automated leave request system.

## Overview

This system uses LINE with a **two-group architecture**:

1. **Teacher Group** - Teachers submit leave requests here
   - Leave requests are processed automatically
   - Admins manually forward approved reports to this group

2. **Admin Group** - Admins receive all notifications here
   - Leave request confirmations (when teachers submit)
   - Full substitute teacher reports (daily processing)
   - Processing summaries and statistics
   - Error notifications and system alerts

**Workflow:**
- Teachers → (submit leave) → Teacher Group
- System → (send confirmation) → Admin Group
- System → (send report) → Admin Group
- Admins → (review & copy) → Teacher Group

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

   # LINE Group IDs (will get these in Step 7)
   # Teacher Group - Teachers submit leave requests here
   LINE_TEACHER_GROUP_ID=

   # Admin Group - Receives all notifications
   LINE_ADMIN_GROUP_ID=

   # Legacy: Keep for backward compatibility (optional)
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

## Step 7: Set Up Two LINE Groups

### 7.1 Create Both Groups

1. Open LINE app on your phone
2. Create two groups:
   - **Teacher Group**: "พรุ่งนี้ขอลานะครับ" (Teachers submit leaves here)
   - **Admin Group**: "ระบบจัดการครูแทน - แอดมิน" (Admins receive notifications)
3. Add appropriate members:
   - Teacher Group: All teachers who will send leave requests
   - Admin Group: School administrators who will review and forward reports

### 7.2 Add Bot to Both Groups

1. In **Teacher Group**, tap menu (≡) → "Add friends"
2. Search for your bot: "Leave Request Bot" (or use QR code)
3. Add the bot to teacher group
4. Repeat for **Admin Group**

### 7.3 Get Both Group IDs

**Using Webhook Events (Recommended):**

1. Start your webhook server:
   ```bash
   python -m src.web.webhook
   ```

2. Send a test message in **Teacher Group**: "ทดสอบกลุ่มครู"

3. Check webhook logs - you'll see:
   ```
   Group ID: C1234567890abcdef...
   NOTE: Add teacher group to your .env file:
   LINE_TEACHER_GROUP_ID=C1234567890abcdef...
   ```

4. Copy the group ID and add to `.env`:
   ```env
   LINE_TEACHER_GROUP_ID=C1234567890abcdef...
   ```

5. Send a test message in **Admin Group**: "ทดสอบกลุ่มแอดมิน"

6. Check webhook logs again for admin group ID

7. Add to `.env`:
   ```env
   LINE_ADMIN_GROUP_ID=C9876543210fedcba...
   ```

**Important Notes:**
- The webhook will only process leave requests from the teacher group
- All confirmations and reports go to the admin group
- Admins manually review and forward reports to teacher group

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
python -c "from src.web.line_messaging import send_test_message; send_test_message()"
```

Should send a test message to your configured admin group.

### 10.6 Test Two-Group Workflow

**Complete end-to-end test:**

1. **Teacher sends leave request:**
   - In teacher group, send: "ครูสุกฤษฎิ์ ขอลาพรุ่งนี้ คาบ 1-3"
   - Check admin group receives confirmation with parsed details

2. **Run daily processing:**
   ```bash
   python -m src.utils.daily_leave_processor --send-line
   ```
   - Check admin group receives full substitute report
   - Admin reviews report for accuracy

3. **Admin forwards to teachers:**
   - Admin manually copies report from admin group
   - Admin pastes report into teacher group
   - Teachers see final substitute assignments

**Expected behavior:**
- Teacher group: Only receives messages from admins (manual)
- Admin group: Receives all automated notifications
- No automatic messages sent to teacher group

---

## Step 11: Understanding the Two-Group Workflow

### Daily Operations

**Morning (Teachers submit leaves):**
1. Teacher sends leave message in teacher group: "ครูสมชาย ขอลาวันพรุ่งนี้ คาบ 2-4 ป่วย"
2. LINE webhook receives message
3. AI parser extracts: teacher_name, date, periods, reason
4. System logs to Google Sheets "Leave_Requests" tab
5. **Admin group receives confirmation:**
   ```
   📝 ได้รับเรื่องขอลาใหม่

   ครู: สมชาย
   วันที่: 2025-11-25
   คาบ: 2, 3, 4

   ✓ บันทึกเรียบร้อยแล้ว (ใช้ AI Success (AI))
   ```
6. Teacher group receives nothing (admins will notify later)

**8:55 AM (Automated processing):**
1. Cron job runs daily_leave_processor.py
2. Loads leave requests from Google Sheets
3. Finds substitute teachers using algorithm
4. Updates Leave_Logs sheet with assignments
5. **Admin group receives full report:**
   ```
   📋 รายงานครูแทน

   วันที่: 25 พฤศจิกายน 2568

   สรุป:
   - ครูที่ลา: 3 คน
   - จำนวนคาบ: 8 คาบ
   - หาครูแทนได้: 6/8 (75%)

   รายละเอียด:
   จันทร์ คาบ 2 | ป.4 - คณิตศาสตร์
   ครูสมชาย → ครูสมศรี ✅
   ...
   ```

**Admin reviews and forwards:**
1. Admin reviews report in admin group
2. If approved, admin **manually copies** report text
3. Admin **manually pastes** into teacher group
4. Teachers see final substitute assignments

### Why This Design?

**Benefits:**
- **Admin oversight:** Reports reviewed before teachers see them
- **Quality control:** Admins can verify accuracy before distribution
- **Flexibility:** Admins can edit/annotate reports before forwarding
- **Error prevention:** Incorrect assignments caught before teachers act on them
- **Simplicity:** No complex approval commands needed

**Trade-offs:**
- Requires manual admin action (copy & paste)
- Not fully automated end-to-end
- Admins must be available to forward reports

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
- Check group IDs are correct (`LINE_TEACHER_GROUP_ID`, `LINE_ADMIN_GROUP_ID`)

### Two-group specific issues

**Admin not receiving leave confirmations:**
- Check `LINE_ADMIN_GROUP_ID` is set correctly in `.env`
- Verify bot is added to admin group
- Check webhook logs show messages being processed
- Run `python -m src.config` to verify config

**Teacher group receiving automated messages:**
- This should NOT happen - only admins receive automated messages
- If happening, check webhook.py modifications are correct
- Verify line_messaging.py sends to admin group

**Webhook ignoring teacher messages:**
- Check `LINE_TEACHER_GROUP_ID` matches actual teacher group
- Send test message and check webhook logs
- Verify leave request keywords present: ลา, ขอลา, หยุด, ไม่มา

**Getting wrong group IDs:**
- Send message "test" in each group separately
- Check webhook logs for each message's group_id
- Update `.env` with correct IDs

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
