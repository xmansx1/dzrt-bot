import os
import time
<<<<<<< HEAD
import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from urllib.parse import urljoin

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('product_monitor.log'),
        logging.StreamHandler()
    ]
)

class ProductMonitorBot:
    def __init__(self):
        load_dotenv()
        self._validate_env_vars()
        self.telegram_token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("CHAT_ID")
        self.telegram_api_url = f"https://api.telegram.org/bot{self.telegram_token}"
        self.previous_statuses = {}
        self.availability_times = {}
        self.session = requests.Session()

        self.products = [
            {
                "name": "Seaside Frost",
                "url": "https://www.dzrt.com/ar-sa/products/seaside-frost",
                "image_selector": "div.product-single__photo-wrapper img",
                "stock_text": "نفذ من المخزون"
            },
            {
                "name": "Icy-rush",
                "url": "https://www.dzrt.com/ar-sa/products/icy-rush",
                "image_selector": "div.product-single__photo-wrapper img",
                "stock_text": "نفذ من المخزون"
            },
            {
                "name": "Riyadh Season Edition",
                "url": "https://www.dzrt.com/ar-sa/products/riyadh-season-edition",
                "image_selector": "div.product-single__photo-wrapper img",
                "stock_text": "نفذ من المخزون",
                "fallback_image": "https://www.dzrt.com/_next/image?url=https%3A%2F%2Fstatic-be.dzrt.com%2F12035bd6-c928-4be4-8abd-0a684b8642e3%252FDZRT_0105.jpg&w=1920&q=75"
            }
        ]

        self.driver = self._create_driver()
        self._running = True

    def _validate_env_vars(self):
        required_vars = ["TELEGRAM_TOKEN", "CHAT_ID"]
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise EnvironmentError(f"متغيرات البيئة التالية مفقودة: {', '.join(missing)}")

    def _create_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        return driver

    def send_telegram_message(self, text):
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            response = requests.post(f"{self.telegram_api_url}/sendMessage", json=payload, timeout=15)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"فشل إرسال الرسالة: {e}")
            return False

    def _send_telegram_photo(self, photo_url, caption, button_url):
        payload = {
            "chat_id": self.chat_id,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": [[
                    {
                        "text": "🛒 اضغط للشراء المباشر",
                        "url": button_url
                    }
                ]]
            }
        }
        try:
            response = requests.post(f"{self.telegram_api_url}/sendPhoto", json=payload, timeout=15)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"فشل إرسال الصورة: {e}")
            return False

    def send_photo_alert(self, name, status, image_url, product_url):
        now = datetime.now().strftime("%H:%M:%S")
        caption = (
            f"<b>🎉 منتج جديد متوفر الآن!</b>\n\n"
            f"🧃 <b>المنتج:</b> <code>{name}</code>\n"
            f"📦 <b>الحالة:</b> ✅ <b>{status}</b>\n"
            f"🕒 <b>الوقت:</b> <code>{now}</code>"
        )

        if not self._send_telegram_photo(image_url, caption, product_url):
            self.send_telegram_message(caption + f"\n🛒 {product_url}")

    def _get_image_from_meta(self):
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            og_img = soup.find("meta", property="og:image")
            if og_img and og_img.get("content"):
                return og_img["content"]
        except Exception as e:
            logging.warning(f"⚠️ فشل استخراج og:image: {e}")
        return None

    def _get_product_image(self, product):
        try:
            time.sleep(2)
            meta_img = self._get_image_from_meta()
            if meta_img and "placeholder.com" not in meta_img:
                return meta_img

            img_element = self.driver.find_element(By.CSS_SELECTOR, product["image_selector"])
            image_url = img_element.get_attribute("src") or img_element.get_attribute("data-src")

            if not image_url:
                raise ValueError("رابط الصورة غير موجود")

            if not image_url.startswith(('http://', 'https://')):
                image_url = urljoin(product["url"], image_url)

            headers = {"User-Agent": "Mozilla/5.0"}
            res = self.session.get(image_url, timeout=10, headers=headers)

            if res.status_code == 200 and "placeholder.com" not in image_url:
                return image_url
            else:
                raise ValueError("رابط الصورة غير صالح")

        except Exception as e:
            logging.warning(f"❌ فشل في استخراج صورة المنتج {product['name']}: {e}")
            return product.get("fallback_image", "https://via.placeholder.com/600x600.png?text=NO+IMAGE")

    def check_product(self, product):
        try:
            self.driver.get(product["url"])
            page_source = self.driver.page_source
            status = "متوفر" if product["stock_text"] not in page_source else "غير متوفر"
            image_url = self._get_product_image(product)
            return status, image_url
        except Exception as e:
            logging.error(f"⚠️ خطأ أثناء فحص المنتج {product['name']}: {e}")
            return None, None

    def monitor_loop(self):
        while self._running:
            try:
                for product in self.products:
                    status, image_url = self.check_product(product)
                    if status is None:
                        continue

                    current_time = datetime.now()
                    previous_status = self.previous_statuses.get(product["name"])
                    self.previous_statuses[product["name"]] = status

                    if status == "متوفر" and previous_status != "متوفر":
                        self.availability_times[product["name"]] = current_time
                        self.send_photo_alert(
                            product["name"],
                            status,
                            image_url,
                            product["url"]
                        )

                    elif status == "غير متوفر" and previous_status == "متوفر":
                        available_since = self.availability_times.get(product["name"])
                        if available_since:
                            duration = current_time - available_since
                            self.send_telegram_message(
                                f"❌ <b>نفد المنتج:</b> <code>{product['name']}</code>\n"
                                f"⏱️ <b>مدة التوفر:</b> <code>{str(duration).split('.')[0]}</code>"
                            )
                            del self.availability_times[product["name"]]

                time.sleep(60)

            except KeyboardInterrupt:
                self._running = False
                logging.info("📴 تم إيقاف البوت يدويًا")
                break

    def run(self):
        try:
            self.send_telegram_message("🚀 بدأ البوت في مراقبة المنتجات")
            self.monitor_loop()
        finally:
            self.driver.quit()

if __name__ == "__main__":
    bot = ProductMonitorBot()
    bot.run()
=======
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
            "text": "🚀 تم تشغيل البوت بنجاح!",
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

            # ننتظر ظهور الصفحة كاملة
            await page.wait_for_load_state("networkidle")

            # نحاول قراءة العنصر
            inventory_element = await page.query_selector("span.product__inventory")
            if inventory_element:
                inventory_text = await inventory_element.inner_text()
            else:
                inventory_text = ""

            # og:image
            image_url = await page.get_attribute("meta[property='og:image']", "content")
            await browser.close()

            if "نفد من المخزون" in inventory_text or "غير متوفر" in inventory_text:
                status = "غير متوفر"
            elif inventory_text:
                status = "متوفر"
            else:
                status = "غير معروف"

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

# ============= تشغيل البرنامج =============
if __name__ == "__main__":
    test_telegram_message()
    asyncio.run(send_summary())
    threading.Thread(target=schedule_summary, daemon=True).start()
    threading.Thread(target=run_async_loop, daemon=True).start()
    while True:
        time.sleep(60)
>>>>>>> 340b779381be77cd1608413bb0956f5dab0761d5
