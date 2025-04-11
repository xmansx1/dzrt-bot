import os
import time
import asyncio
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# إعدادات المسارات والمجلدات
os.makedirs("screenshots", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# إعداد التسجيل (Logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/product_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# تحميل متغيرات البيئة
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "60"))  # الفاصل الزمني بالثواني

# قائمة المنتجات للمراقبة
products = [
    {
        "name": "Seaside Frost",
        "url": "https://www.dzrt.com/ar-sa/products/seaside-frost",
        "retry_count": 0
    },
    {
        "name": "Icy Rush",
        "url": "https://www.dzrt.com/ar-sa/products/icy-rush",
        "retry_count": 0
    },
    {
        "name": "Riyadh Season Edition",
        "url": "https://www.dzrt.com/ar-sa/products/riyadh-season-edition",
        "retry_count": 0
    }
]

# حالة المنتجات السابقة
previous_status = {}
MAX_RETRIES = 3  # الحد الأقصى لمحاولات إعادة المحاولة

class ProductMonitor:
    def __init__(self):
        self.browser = None
        self.page = None

    async def initialize_browser(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # يمكن تغييرها إلى True بعد التأكد من عمل الكود
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )
        self.page = await self.browser.new_page()
        await self.page.set_viewport_size({"width": 1280, "height": 720})

    async def close_browser(self):
        if self.browser:
            await self.browser.close()

    async def fetch_product_status(self, product):
        try:
            product_name = product["name"]
            product_url = product["url"]
            
            logger.info(f"جلب بيانات المنتج: {product_name}")
            
            await self.page.goto(product_url, timeout=120000)
            await self.page.wait_for_load_state("networkidle")
            
            # انتظار ظهور عنصر المخزون
            try:
                await self.page.wait_for_selector("span.product__inventory", timeout=30000)
                inventory_element = await self.page.query_selector("span.product__inventory")
                inventory_text = await inventory_element.inner_text() if inventory_element else ""
            except Exception:
                inventory_text = ""
                logger.warning(f"لم يتم العثور على عنصر المخزون لـ {product_name}")

            # الحصول على صورة المنتج
            try:
                image_element = await self.page.query_selector("meta[property='og:image']")
                image_url = await image_element.get_attribute("content") if image_element else ""
            except Exception:
                image_url = ""
                logger.warning(f"لم يتم العثور على صورة المنتج لـ {product_name}")

            return self.analyze_status(product_name, inventory_text, image_url)

        except Exception as e:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"screenshots/error_{product_name}_{timestamp}.png"
            await self.page.screenshot(path=screenshot_path)
            logger.error(f"حدث خطأ أثناء جلب بيانات المنتج {product_name}: {str(e)}")
            return None, None

    def analyze_status(self, name, text, img_url):
        if not text or "نفد من المخزون" in text or "غير متوفر" in text or "out of stock" in text.lower():
            return "غير متوفر", img_url
        elif text and ("متوفر" in text or "in stock" in text.lower()):
            return "متوفر", img_url
        else:
            logger.warning(f"حالة غير معروفة للمنتج {name}: {text}")
            return "غير معروف", img_url

    async def send_telegram_alert(self, product_name, status, image_url, product_url):
        try:
            now = datetime.now().strftime("%H:%M:%S")
            date = datetime.now().strftime("%Y-%m-%d")
            
            message = (
                f"<b>🚀 تغيير في حالة المنتج!</b>\n\n"
                f"📅 <b>التاريخ:</b> <code>{date}</code>\n"
                f"⏰ <b>الوقت:</b> <code>{now}</code>\n"
                f"🧃 <b>المنتج:</b> <code>{product_name}</code>\n"
                f"📦 <b>الحالة:</b> <b>{status}</b>\n"
            )

            payload = {
                "chat_id": CHAT_ID,
                "photo": image_url,
                "caption": message,
                "parse_mode": "HTML",
                "reply_markup": {
                    "inline_keyboard": [[
                        {
                            "text": "🛒 اضغط للشراء المباشر",
                            "url": product_url
                        }
                    ]]
                }
            }

            response = requests.post(f"{TELEGRAM_API_URL}/sendPhoto", json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"تم إرسال التنبيه بنجاح للمنتج: {product_name}")
            else:
                logger.error(f"فشل إرسال التنبيه: {response.text}")

        except Exception as e:
            logger.error(f"حدث خطأ أثناء إرسال التنبيه عبر التليجرام: {str(e)}")

    async def monitor_product(self, product):
        product_name = product["name"]
        
        status, image_url = await self.fetch_product_status(product)
        if status is None or image_url is None:
            product["retry_count"] += 1
            if product["retry_count"] >= MAX_RETRIES:
                logger.error(f"تجاوز الحد الأقصى لمحاولات إعادة المحاولة للمنتج: {product_name}")
                product["retry_count"] = 0
            return

        # إعادة تعيين عداد المحاولات عند النجاح
        product["retry_count"] = 0

        if product_name not in previous_status:
            previous_status[product_name] = status
            logger.info(f"الحالة الأولية للمنتج {product_name}: {status}")
            return

        if status != previous_status[product_name]:
            logger.info(f"تغيير في حالة المنتج {product_name}: من {previous_status[product_name]} إلى {status}")
            await self.send_telegram_alert(product_name, status, image_url, product["url"])

        previous_status[product_name] = status

    async def monitor(self):
        logger.info("بدء تشغيل مراقب المنتجات...")
        await self.initialize_browser()

        try:
            while True:
                start_time = time.time()
                
                for product in products:
                    try:
                        await self.monitor_product(product)
                    except Exception as e:
                        logger.error(f"حدث خطأ أثناء مراقبة المنتج {product['name']}: {str(e)}")
                
                elapsed_time = time.time() - start_time
                sleep_time = max(MONITOR_INTERVAL - elapsed_time, 0)
                logger.info(f"اكتملت دورة المراقبة. الانتظار لـ {sleep_time:.1f} ثانية...")
                await asyncio.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("تلقي إشارة إيقاف. إيقاف المراقبة...")
        except Exception as e:
            logger.error(f"حدث خطأ غير متوقع: {str(e)}")
        finally:
            await self.close_browser()
            logger.info("تم إيقاف مراقب المنتجات.")

async def main():
    monitor = ProductMonitor()
    await monitor.monitor()

if __name__ == "__main__":
    asyncio.run(main())