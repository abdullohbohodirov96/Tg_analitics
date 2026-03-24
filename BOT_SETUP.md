# Bot Setup & Troubleshooting Guide

## Prerequisites
- BotFather token (you have: 8329214616:AAFvZIEuCK9RFDHpUEP77A7Mx6Wc4KKOifo)
- Server with HTTPS (required by Telegram)
- Domain or public IP address

## Step 1: Disable Bot Privacy Mode (CRITICAL)

Go to Telegram and chat with @BotFather:

```
/setprivacy
```
Then:
1. Select your bot (or send `/start` then select from menu)
2. Choose "Disable" when asked about privacy mode

**Why**: By default, bots can't see group messages. Privacy mode disabled allows reading all messages.

---

## Step 2: Set Webhook

Replace `YOUR_DOMAIN` and `YOUR_BOT_TOKEN` below:

```bash
BOT_TOKEN="8329214616:AAFvZIEuCK9RFDHpUEP77A7Mx6Wc4KKOifo"
DOMAIN="your-domain.com"  # or IP address
WEBHOOK_SECRET="tg_analytics_webhook_secret_2024"

# Set webhook
curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"https://$DOMAIN/webhook/telegram\",
    \"secret_token\": \"$WEBHOOK_SECRET\",
    \"allowed_updates\": [\"message\", \"my_chat_member\"]
  }"
```

Expected response:
```json
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

---

## Step 3: Verify Webhook

```bash
BOT_TOKEN="8329214616:AAFvZIEuCK9RFDHpUEP77A7Mx6Wc4KKOifo"

curl "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo" | jq .
```

Check output:
```json
{
  "ok": true,
  "result": {
    "url": "https://your-domain.com/webhook/telegram",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "ip_address": "...",
    "last_error_date": null,  // Should be null
    "allowed_updates": ["message", "my_chat_member"]
  }
}
```

If `last_error_date` is not null, check:
1. Domain/IP is correct
2. SSL certificate is valid
3. Firewall allows HTTPS (443)
4. App is running

---

## Step 4: Add Bot to Group

1. Create or open a test group
2. Add the bot to it
3. Give it permissions:
   - Delete messages (optional)
   - Edit messages (optional)
   - Read message history (MUST have)

---

## Step 5: Test

1. Send a message in the group
2. Check app logs for webhook calls:
   ```bash
   docker logs app 2>&1 | grep "Webhook\|Update\|Error"
   ```

3. Check database for saved messages:
   ```bash
   # Inside container
   docker exec -it app-db psql -U postgres -d telegram_analytics -c "SELECT COUNT(*) FROM messages;"
   ```

4. Try bot commands:
   ```
   /stats
   /today
   /operators
   ```

---

## Troubleshooting

### Bot not receiving messages
- [ ] Privacy mode disabled in BotFather? (`/setprivacy` → Disable)
- [ ] Webhook is set correctly? (Check with `getWebhookInfo`)
- [ ] Server is HTTPS accessible? (Can you curl /webhook/telegram?)
- [ ] Firewall allows port 443?
- [ ] Bot is admin in group with message history access?

### Webhook errors in logs
```
# Check logs
docker logs app

# If you see "Webhook processing error", check:
- Database connection
- Admin user exists in database
```

### SSL Certificate Issues  
```bash
# If using self-signed cert:
curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"https://$DOMAIN/webhook/telegram\",
    \"secret_token\": \"$WEBHOOK_SECRET\",
    \"certificate\": \"@/path/to/cert.pem\"
  }"
```

### Clear Webhook (if needed)
```bash
BOT_TOKEN="8329214616:AAFvZIEuCK9RFDHpUEP77A7Mx6Wc4KKOifo"

curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/deleteWebhook"
```

---

## Admin User Setup

Bot needs admin user for API authentication.

Default credentials (set in .env):
- Username: `admin`
- Password: `admin123`
- Both must exist in database

If login doesn't work:
```bash
# Reset admin in database
docker exec -it app-db psql -U postgres -d telegram_analytics

# Inside psql:
DELETE FROM admin_users WHERE username = 'admin';
```

Then app will recreate on startup.

---

## API Endpoints (for testing)

Once bot is working:

```bash
# Get token
TOKEN="your_jwt_token"

# Test group data
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/stats/groups"

# Test messages
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/stats/conversations"

# Test tasks
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/stats/tasks"
```

---

## Quick Checklist

- [ ] Bot privacy mode disabled
- [ ] Webhook set with correct URL
- [ ] Server has valid HTTPS
- [ ] Bot added to test group
- [ ] Bot has message history permission
- [ ] Test message sent and appears in database
- [ ] Frontend shows collected data
- [ ] Bot commands work (/stats, etc)

---

For more help, check logs and DIAGNOSTIC.md file.
