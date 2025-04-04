import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import threading

# إعدادات تليجرام
TELEGRAM_TOKEN = "8129013837:AAHZ36_0XqVyb7gIWQQzKtNh9Tf8p5LS-uw"
CHAT_ID = "-1002547689611"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# قائمة المنتجات للمراقبة
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

last_status = {product["url"]: None for product in products}
last_available_time = {product["url"]: None for product in products}
daily_status = {product["name"]: None for product in products}


def check_product_info(product_url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(product_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ خطأ أثناء تحميل الصفحة: {response.status_code}")
            return None, None

        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text().lower()
        status = "غير متوفر" if "نفذ من المخزون" in page_text else "متوفر"

        # 🔹 رابط صورة مباشر لمنتج Riyadh Season Edition
        if "riyadh-season-edition" in product_url:
            image_url = "https://www.dzrt.com/_next/image?url=https%3A%2F%2Fstatic-be.dzrt.com%2Fdffacf0a-54bb-4df4-94f8-fafd8d4c77fd%252FDZRT_0084.jpg&w=1920&q=75"
            return status, image_url

        # استخراج صورة باقي المنتجات
        image_url = None

        og_tag = soup.find("meta", property="og:image")
        if og_tag and og_tag.get("content"):
            image_url = og_tag["content"]

        if not image_url:
            img_tags = soup.find_all("img")
            for img in img_tags:
                src = img.get("src") or img.get("data-src")
                if src and ("cdn.shopify.com" in src or "files" in src) and (".jpg" in src or ".png" in src):
                    if src.startswith("//"):
                        src = "https:" + src
                    elif src.startswith("/"):
                        src = "https://www.dzrt.com" + src
                    image_url = src
                    break

        return status, image_url

    except Exception as e:
        print(f"❌ حدث خطأ أثناء التحقق: {e}")
        return None, None


def send_product_alert_with_image(product_name, status, image_url, product_url, last_available=None):
    now = datetime.now()
    now_str = now.strftime("%H:%M:%S")
    emoji = "🔔" if status == "متوفر" else "❌"

    if status == "غير متوفر" and last_available:
        duration = now - last_available
        message = f"""
{emoji} <b>المنتج: {product_name}</b>

🚫 <b>الحالة الحالية:</b> <code>{status}</code>
📅 <b>آخر مرة كان متوفر:</b> {last_available.strftime("%H:%M:%S")}
🕒 <b>وقت التحول إلى غير متوفر:</b> {now_str}
⏳ <b>المدة التي كان متوفرًا:</b> {str(duration).split('.')[0]}
"""
    else:
        message = f"""
{emoji} <b>المنتج: {product_name}</b>

🔄 <b>الحالة الجديدة:</b> <code>{status}</code>
🕒 <b>وقت التحديث:</b> {now_str}
"""

    keyboard = {
        "inline_keyboard": [[
            {
                "text": "🛒 اضغط هنا للشراء" if status == "متوفر" else "❌ نفذت الكمية - تصفح المتجر",
                "url": product_url if status == "متوفر" else "https://www.dzrt.com/ar-sa"
            }
        ]]
    }

    if image_url and image_url.startswith("http") and (".jpg" in image_url or ".png" in image_url or "image?" in image_url):
        payload = {
            "chat_id": CHAT_ID,
            "photo": image_url,
            "caption": message.strip(),
            "parse_mode": "HTML",
            "reply_markup": keyboard
        }
        try:
            r = requests.post(f"{TELEGRAM_API_URL}/sendPhoto", json=payload)
            if r.status_code != 200:
                print("⚠️ فشل إرسال الصورة:", r.text)
        except Exception as e:
            print(f"❌ فشل في إرسال رسالة تليجرام مع صورة: {e}")
    else:
        print(f"ℹ️ لم يتم العثور على صورة مناسبة، إرسال كنص فقط: {image_url}")
        payload = {
            "chat_id": CHAT_ID,
            "text": message.strip(),
            "parse_mode": "HTML",
            "reply_markup": keyboard
        }
        try:
            r = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
            if r.status_code != 200:
                print("⚠️ فشل إرسال الرسالة النصية:", r.text)
        except Exception as e:
            print(f"❌ فشل في إرسال الرسالة بدون صورة: {e}")


def send_daily_summary():
    now = datetime.now().strftime("%Y-%m-%d")
    message = f"📊 <b>ملخص المنتجات - {now}</b>\n\n"

    for product in products:
        name = product["name"]
        status = daily_status.get(name, "غير معروف")
        symbol = "✅" if status == "متوفر" else "❌"
        message += f"{symbol} <b>{name}</b>: <code>{status}</code>\n"

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        r = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)
        if r.status_code != 200:
            print("⚠️ فشل إرسال الملخص اليومي:", r.text)
    except Exception as e:
        print(f"❌ فشل في إرسال الملخص اليومي: {e}")


def schedule_daily_summary():
    while True:
        now = datetime.now()
        target_time = now.replace(hour=23, minute=59, second=0, microsecond=0)
        if now >= target_time:
            target_time += timedelta(days=1)
        wait_seconds = (target_time - now).total_seconds()
        time.sleep(wait_seconds)
        send_daily_summary()


# تشغيل الملخص اليومي في Thread منفصل
threading.Thread(target=schedule_daily_summary, daemon=True).start()

# حلقة المراقبة
while True:
    for product in products:
        name = product["name"]
        url = product["url"]

        status, image_url = check_product_info(url)
        print(f"[{name}] الحالة الحالية: {status}")

        if status:
            previous_status = last_status[url]
            daily_status[name] = status

            if status != previous_status:
                if status == "غير متوفر" and last_available_time[url]:
                    send_product_alert_with_image(name, status, image_url, url, last_available_time[url])
                else:
                    send_product_alert_with_image(name, status, image_url, url)

                last_status[url] = status

            if status == "متوفر":
                last_available_time[url] = datetime.now()

    time.sleep(20)
