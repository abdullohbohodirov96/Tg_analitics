#!/usr/bin/env python3
"""
Telegram Webhook O'rnatish Skripti.
Bu skript botga webhook URL ni o'rnatadi.

Ishlatish:
    python3 scripts/setup_webhook.py https://YOUR_DOMAIN

Misol:
    python3 scripts/setup_webhook.py https://mybot.example.com
"""

import sys
import os
import json

# .env faylni o'qish
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    env = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env[key.strip()] = value.strip()
    return env


def main():
    if len(sys.argv) < 2:
        print("❌ Ishlatish: python3 setup_webhook.py https://YOUR_DOMAIN")
        print("   Misol:    python3 setup_webhook.py https://mybot.example.com")
        sys.exit(1)

    domain = sys.argv[1].rstrip('/')
    env = load_env()

    bot_token = env.get('BOT_TOKEN', '')
    webhook_secret = env.get('WEBHOOK_SECRET', '')

    if not bot_token:
        print("❌ BOT_TOKEN .env faylda topilmadi!")
        sys.exit(1)

    webhook_url = f"{domain}/webhook/telegram"

    print(f"🔧 Webhook o'rnatilmoqda...")
    print(f"   URL: {webhook_url}")
    print(f"   Secret: {webhook_secret[:10]}...")

    try:
        import urllib.request

        data = json.dumps({
            "url": webhook_url,
            "secret_token": webhook_secret,
            "allowed_updates": ["message"],
        }).encode()

        req = urllib.request.Request(
            f"https://api.telegram.org/bot{bot_token}/setWebhook",
            data=data,
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())

        if result.get("ok"):
            print(f"✅ Webhook muvaffaqiyatli o'rnatildi!")
            print(f"   {result.get('description', '')}")
        else:
            print(f"❌ Xatolik: {result.get('description', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Xatolik: {e}")

    # Webhook holatini tekshirish
    print("\n📋 Webhook holati:")
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        )
        with urllib.request.urlopen(req) as response:
            info = json.loads(response.read())
            result = info.get("result", {})
            print(f"   URL: {result.get('url', 'o`rnatilmagan')}")
            print(f"   Pending updates: {result.get('pending_update_count', 0)}")
            if result.get('last_error_message'):
                print(f"   ⚠️ Oxirgi xato: {result['last_error_message']}")
    except Exception as e:
        print(f"   Tekshirib bo'lmadi: {e}")


if __name__ == "__main__":
    main()
