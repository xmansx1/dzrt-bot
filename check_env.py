import os
from dotenv import load_dotenv

# تحميل من .env عند التشغيل المحلي فقط (اختياري)
load_dotenv()

# قراءة المتغيرات البيئية
token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("CHAT_ID")

# عرض النتائج
print("✅ TELEGRAM_TOKEN:", "موجود ✅" if token else "❌ مفقود")
print("✅ CHAT_ID:", "موجود ✅" if chat_id else "❌ مفقود")
