import os
import time
import asyncio
import threading
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

products = [
    {
        "name": "Seaside Frost",
        "url": "https://www.dzrt.com/ar-sa/products/seaside-frost"
    },
    {
        "name": "icy-rush",
        "url": "https://www.dzrt.com/ar-sa/products/icy-rush"
    },
    {
        "name": "Riyadh Season Edition",
        "url": "https://www.dzrt.com/ar-sa/products/riyadh-season-edition"
    }
]

def test_telegram_message():
    try:
        payload = {
            "chat_id": CHAT_ID,
            "text": "تم تشغيل البوت بنجاح! 🚀",
        }
        res = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
        print("✅ رسالة الاختبار:", res.status_code)
    except Exception as e:
        print("❌ فشل إرسال رسالة الاختبار:", e)

async def check_product_info(url):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            await browser.close()

            inventory_tag = soup.find("span", class_="product__inventory")
            inventory_text = inventory_tag.get_text(strip=True) if inventory_tag else ""

            if "نفد من المخزون" in inventory_text or "غير متوفر" in inventory_text:
                status = "غير متوفر"
            else:
                status = "متوفر"

            # الصورة من og:image
            img = soup.find("meta", property="og:image")
            image_url = img["content"] if img else "https://via.placeholder.com/600x600.png?text=DZRT+Product"

            return status, image_url
    except Exception as e:
        print("⚠️ خطأ في check_product_info:", e)
        return "None", None

def send_alert(name, status, img, url):
    now = datetime.now().strftime("%H:%M:%S")
    emoji = "✅" if status == "متوفر" else "❌"
    msg = f"""{emoji} <b>المنتج: {name}</b>

<b>الحالة الجديدة:</b> <code>{status}</code>
<b>وقت التحديث:</b> {now}"""

    keyboard = {
        "inline_keyboard": [[
            {
                "text": "شراء" if status == "متوفر" else "زيارة الموقع",
                "url": url
            }
        ]]
    }

    payload = {
        "chat_id": CHAT_ID,
        "photo": img,
        "caption": msg,
        "parse_mode": "HTML",
        "reply_markup": keyboard
    }

    try:
        res = requests.post(f"{TELEGRAM_API_URL}/sendPhoto", json=payload)
        print(f"📦 إرسال تنبيه {name}: {res.status_code}")
    except Exception as e:
        print("❌ خطأ في إرسال التنبيه:", e)

async def send_summary():
    print("📦 إرسال ملخص المنتجات...")
    today = datetime.now().strftime('%Y-%m-%d')
    summary = f"📊 <b>ملخص المنتجات - {today}</b>\n"

    for p in products:
        name, url = p["name"], p["url"]
        status, _ = await check_product_info(url)
        symbol = "✅" if status == "متوفر" else "❌"
        summary += f"{symbol} <b>{name}:</b> <code>{status}</code>\n"

    payload = {
        "chat_id": CHAT_ID,
        "text": summary,
        "parse_mode": "HTML"
    }

    try:
        res = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
        print("📤 تم إرسال الملخص:", res.status_code)
    except Exception as e:
        print("❌ فشل إرسال الملخص:", e)

async def monitor_loop():
    while True:
        for p in products:
            name, url = p["name"], p["url"]
            status, image = await check_product_info(url)
            if status:
                send_alert(name, status, image, url)
        await asyncio.sleep(120)

def run_async_loop():
    asyncio.run(monitor_loop())

def schedule_summary():
    while True:
        now = datetime.now()
        target = now.replace(hour=23, minute=59, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        time.sleep((target - now).total_seconds())
        asyncio.run(send_summary())

# ===== بداية التشغيل =====
test_telegram_message()
asyncio.run(send_summary())
threading.Thread(target=schedule_summary, daemon=True).start()
threading.Thread(target=run_async_loop, daemon=True).start()

while True:
    time.sleep(60)
