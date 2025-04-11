import os
import time
import requests
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# إعدادات التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('product_monitor.log'),
        logging.StreamHandler()
    ]
)

# تحميل متغيرات البيئة
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# قائمة المنتجات مع إعدادات مخصصة
products = [
    {
        "name": "Seaside Frost",
        "url": "https://www.dzrt.com/ar-sa/products/seaside-frost",
        "emoji": "🧊",
        "color": "#3498db"
    },
    {
        "name": "Icy-rush",
        "url": "https://www.dzrt.com/ar-sa/products/icy-rush",
        "emoji": "❄️",
        "color": "#1abc9c"
    },
    {
        "name": "Riyadh Season Edition",
        "url": "https://www.dzrt.com/ar-sa/products/riyadh-season-edition",
        "emoji": "🏆",
        "color": "#e74c3c",
        "fallback_image": "https://www.dzrt.com/_next/image?url=https%3A%2F%2Fstatic-be.dzrt.com%2F12035bd6-c928-4be4-8abd-0a684b8642e3%252FDZRT_0105.jpg&w=1920&q=75"
    }
]

class ProductMonitor:
    def __init__(self):
        self.previous_statuses = {}
        self.availability_times = {}
        self.session = requests.Session()

    async def check_product(self, product):
        """فحص حالة المنتج باستخدام Playwright"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # إعدادات المتصفح
                await page.set_viewport_size({"width": 1920, "height": 1080})
                await page.goto(product["url"], timeout=60000)
                
                # انتظار تحميل الصفحة
                await page.wait_for_load_state("networkidle")
                
                # التحقق من حالة التوفر
                inventory_text = ""
                try:
                    inventory_element = await page.query_selector("span.product__inventory")
                    if inventory_element:
                        inventory_text = await inventory_element.inner_text()
                except:
                    pass
                
                # استخراج صورة المنتج
                image_url = await self._extract_product_image(page, product)
                
                await browser.close()

                # تحديد الحالة
                if "نفد من المخزون" in inventory_text or "غير متوفر" in inventory_text:
                    status = "غير متوفر"
                elif inventory_text:
                    status = "متوفر"
                else:
                    status = "غير معروف"

                return status, image_url

        except Exception as e:
            logging.error(f"خطأ في فحص المنتج {product['name']}: {e}")
            return None, None

    async def _extract_product_image(self, page, product):
        """استخراج صورة المنتج بطرق متعددة"""
        try:
            # المحاولة الأولى: صورة Open Graph
            og_image = await page.get_attribute("meta[property='og:image']", "content")
            if og_image and "placeholder" not in og_image.lower():
                return og_image

            # المحاولة الثانية: الصورة الرئيسية للمنتج
            main_image = await page.query_selector("div.product-single__photo-wrapper img")
            if main_image:
                image_url = await main_image.get_attribute("src") or await main_image.get_attribute("data-src")
                if image_url and "placeholder" not in image_url.lower():
                    return image_url

            # المحاولة الثالثة: أي صورة منتج أخرى
            product_images = await page.query_selector_all("img[src*='product'], img[data-src*='product']")
            for img in product_images:
                image_url = await img.get_attribute("src") or await img.get_attribute("data-src")
                if image_url and "placeholder" not in image_url.lower():
                    return image_url

            # إذا فشلت جميع المحاولات
            return product.get("fallback_image", "https://via.placeholder.com/600x600.png?text=NO+IMAGE")

        except Exception as e:
            logging.warning(f"فشل استخراج صورة المنتج {product['name']}: {e}")
            return product.get("fallback_image", "https://via.placeholder.com/600x600.png?text=NO+IMAGE")

    def send_alert(self, product, status, image_url):
        """إرسال تنبيه بتصميم احترافي"""
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%Y-%m-%d")
        
        # تصميم البطاقة
        caption = (
            f"{product['emoji']} <b>إشعار حالة المنتج</b> {product['emoji']}\n\n"
            "━━━━━━━━━━━━━━\n"
            f"🎁 <b>المنتج:</b> <code>{product['name']}</code>\n"
            f"📌 <b>الحالة:</b> {'✅ متوفر' if status == 'متوفر' else '❌ غير متوفر'}\n"
            f"📅 <b>التاريخ:</b> <code>{date_str}</code>\n"
            f"⏰ <b>الوقت:</b> <code>{time_str}</code>\n"
            "━━━━━━━━━━━━━━\n\n"
            f"🛍️ <a href='{product['url']}'>اضغط هنا للذهاب إلى الصفحة</a>\n\n"
            f"#{product['name'].replace(' ', '_')} #{'متوفر' if status == 'متوفر' else 'نفذ'}"
        )

        # زر الشراء المباشر
        keyboard = {
            "inline_keyboard": [[
                {
                    "text": "🛒 شراء مباشر" if status == "متوفر" else "🔗 زيارة الصفحة",
                    "url": product["url"]
                }
            ]]
        }

        payload = {
            "chat_id": CHAT_ID,
            "photo": image_url,
            "caption": caption,
            "parse_mode": "HTML",
            "reply_markup": keyboard
        }

        try:
            response = requests.post(f"{TELEGRAM_API_URL}/sendPhoto", json=payload, timeout=15)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"فشل إرسال التنبيه: {e}")
            # إرسال نسخة نصية إذا فشل إرسال الصورة
            text_message = caption.replace("━━━━━━━━━━━━━━\n", "").replace("\n\n", "\n")
            self.send_message(text_message)
            return False

    def send_message(self, text):
        """إرسال رسالة نصية"""
        payload = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            response = requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"فشل إرسال الرسالة: {e}")
            return False

    async def send_daily_summary(self):
        """إرسال ملخص يومي"""
        logging.info("إعداد الملخص اليومي")
        today = datetime.now().strftime('%Y-%m-%d')
        summary = f"📊 <b>ملخص المنتجات - {today}</b>\n\n"
        
        for product in products:
            status, _ = await self.check_product(product)
            symbol = "✅" if status == "متوفر" else "❌"
            summary += f"{symbol} <b>{product['name']}:</b> <code>{status if status else 'غير معروف'}</code>\n"
        
        summary += "\n🔄 جاري متابعة المخزون تلقائيًا"
        self.send_message(summary)

async def monitor_products():
    """حلقة المراقبة الرئيسية"""
    monitor = ProductMonitor()
    monitor.send_message("🚀 بدأ تشغيل بوت مراقبة المنتجات")
    
    while True:
        try:
            for product in products:
                current_status, image_url = await monitor.check_product(product)
                if current_status is None:
                    continue
                
                previous_status = monitor.previous_statuses.get(product["name"])
                monitor.previous_statuses[product["name"]] = current_status
                
                # عند تغير الحالة
                if current_status != previous_status:
                    current_time = datetime.now()
                    
                    if current_status == "متوفر":
                        monitor.availability_times[product["name"]] = current_time
                        monitor.send_alert(product, current_status, image_url)
                    
                    elif current_status == "غير متوفر" and previous_status == "متوفر":
                        available_since = monitor.availability_times.get(product["name"])
                        if available_since:
                            duration = current_time - available_since
                            hours = int(duration.total_seconds() // 3600)
                            minutes = int((duration.total_seconds() % 3600) // 60)
                            duration_str = f"{hours} ساعة {minutes} دقيقة"
                            
                            monitor.send_message(
                                f"⏳ <b>نفاد المخزون</b>\n\n"
                                f"📛 المنتج: <code>{product['name']}</code>\n"
                                f"⏱ مدة التوفر: <code>{duration_str}</code>\n\n"
                                f"#{product['name'].replace(' ', '_')} #نفذ_المخزون"
                            )
            
            await asyncio.sleep(60)  # انتظار دقيقة بين الفحوصات
            
        except Exception as e:
            logging.error(f"خطأ غير متوقع في حلقة المراقبة: {e}")
            await asyncio.sleep(120)  # انتظار أطول عند الأخطاء

async def run_daily_summary():
    """تشغيل الملخص اليومي في وقت محدد"""
    monitor = ProductMonitor()
    while True:
        now = datetime.now()
        # وقت إرسال الملخص (11:59 مساءً)
        target = now.replace(hour=23, minute=59, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        
        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        
        try:
            await monitor.send_daily_summary()
        except Exception as e:
            logging.error(f"خطأ في إرسال الملخص اليومي: {e}")

if __name__ == "__main__":
    # اختبار الاتصال بالتلجرام
    try:
        test_msg = "🔍 جاري اختبار اتصال البوت..."
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={"chat_id": CHAT_ID, "text": test_msg})
    except Exception as e:
        logging.error(f"فشل اختبار الاتصال بالتلجرام: {e}")
    
    # بدء الخدمات في خيوط منفصلة
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # تشغيل مراقبة المنتجات
    monitor_task = loop.create_task(monitor_products())
    
    # تشغيل الملخص اليومي
    summary_task = loop.create_task(run_daily_summary())
    
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info("إيقاف البوت...")
    finally:
        monitor_task.cancel()
        summary_task.cancel()
        loop.close()