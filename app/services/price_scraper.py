"""
اسکرپر کمکی (best-effort) برای «قیمت روز خودرو صفر کیلومتر».

⚠️ نکات مهم قبل از استفاده:
  1) هیچ سایت مرجع (باما، دیوار و..) API رسمی برای این داده منتشر نکرده؛
     این ماژول فقط HTML صفحه عمومی را می‌خواند و متن آن را پارس می‌کند.
     یعنی: (الف) ممکن است با قوانین استفاده (ToS) آن سایت در تضاد باشد -
     مسئولیتش با کسی است که این قابلیت را فعال/اجرا می‌کند، و (ب) هر تغییر
     در قالب صفحه‌ی مبدا می‌تواند این پارسر را از کار بیندازد.
  2) این اسکرپر فقط برای خودروهای «صفر کیلومتر» طراحی شده، چون فقط برای
     صفرها یک «قیمت روز» ثابت و مرجع (بازار/نمایندگی) روی این سایت‌ها منتشر
     می‌شود. برای خودروی «کارکرده» چنین عدد ثابتی اساساً وجود ندارد (قیمت
     کارکرده به کارکرد/شرایط/شهر بستگی دارد) - آن قیمت‌ها را باید دستی یا
     از طریق اکسل وارد کرد.
  3) این تابع به‌صورت خودکار/زمان‌بندی‌شده اجرا نمی‌شود؛ فقط وقتی ادمین از
     پنل روی دکمه‌ی «دریافت خودکار (آزمایشی)» بزند فراخوانی می‌شود، تا هیچ
     ترافیک مکرر ناخواسته‌ای به سمت سایت مبدا نره.
  4) الگوی regex زیر بر پایه‌ی نمونه متن‌های عمومی این صفحه نوشته شده و
     احتمالاً بعد از هر تغییر در قالب سایت مبدا نیاز به بازبینی selectors/regex
     دارد - آدرس واقعی صفحه و ساختار دقیقش را قبل از فعال‌سازی در محیط
     Production حتماً بررسی کنید.
"""
import re
from datetime import date

import httpx
from bs4 import BeautifulSoup

from app.models.price_guide import CONDITION_ZERO

DEFAULT_SOURCE_URL = "https://bama.ir/price"

# نمونه متنی که این regex قرار است پارس کند:
#   "آریسان ,2 1405 ایران خودرو 22 ساعت پیش قیمت بازار-3.12%1,550,000,000 تومان"
# یعنی: {برند} ,{مدل} {تیریم اختیاری} {سال} ... قیمت (بازار|نمایندگی|کارخانه) {درصد}% {عدد} تومان
ROW_PATTERN = re.compile(
    r"(?P<brand>[\u0600-\u06FF\w\s()]+?)\s*,\s*"
    r"(?P<rest>[\u0600-\u06FF\w\s()\-]+?)\s+(?P<year>1[34]\d{2})\b"
    r"[^\n]*?قیمت\s+(?P<price_type>بازار|نمایندگی|کارخانه)\s*"
    r"[-+]?\d+(?:\.\d+)?%\s*(?P<price>[\d,]+)\s*تومان"
)


class PriceScraperError(Exception):
    pass


def fetch_zero_km_prices(source_url: str = DEFAULT_SOURCE_URL, timeout: float = 15.0) -> tuple[list[dict], list[str]]:
    """
    تلاش می‌کند قیمت روز خودروهای صفر را از یک صفحه‌ی عمومی بخواند و پارس کند.
    خروجی: (لیست ردیف‌های قابل درج در PriceGuideEntry، لیست هشدار/خطا).

    این تابع هرگز استثنای شبکه را بالا نمی‌فرستد مگر در دسترس نبودن کامل
    سایت مبدا - خطاهای پارس تک‌تک ردیف‌ها را نادیده می‌گیرد و در لیست دوم
    خروجی گزارش می‌کند تا کل عملیات به خاطر چند ردیف عجیب متوقف نشود.
    """
    warnings: list[str] = []

    try:
        resp = httpx.get(
            source_url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; CarpazPriceBot/1.0)"},
            follow_redirects=True,
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise PriceScraperError(f"عدم دسترسی به سایت مبدا: {e}") from e

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator=" ")
    # فاصله‌های تکراری/خط جدید را یکدست کن تا regex راحت‌تر match کند
    text = re.sub(r"\s+", " ", text)

    rows: list[dict] = []
    seen = set()

    for m in ROW_PATTERN.finditer(text):
        try:
            brand = m.group("brand").strip(" ,")
            rest = m.group("rest").strip(" ,")
            year = m.group("year")
            price_type = m.group("price_type")
            price = int(m.group("price").replace(",", ""))

            # "rest" ممکن است شامل مدل + تیریم باشد؛ اولین بخش را مدل و باقی را تیریم می‌گیریم
            parts = rest.split(" ", 1)
            model = parts[0].strip()
            trim = parts[1].strip() if len(parts) > 1 else None

            if not brand or not model or price <= 0:
                continue

            key = (brand, model, trim, year, price_type)
            if key in seen:
                continue
            seen.add(key)

            entry = {
                "brand": brand,
                "model": model,
                "trim": trim,
                "year": year,
                "condition": CONDITION_ZERO,
                "price_date": date.today(),
            }
            if price_type in ("نمایندگی", "کارخانه"):
                entry["agency_price"] = price
            else:
                entry["market_price"] = price

            rows.append(entry)
        except Exception as e:  # noqa: BLE001 - یک ردیف بد نباید کل عملیات را متوقف کند
            warnings.append(f"یک ردیف قابل پارس نبود: {e}")

    if not rows:
        warnings.append(
            "هیچ ردیفی استخراج نشد - احتمالاً قالب صفحه‌ی مبدا تغییر کرده و "
            "الگوی ROW_PATTERN در app/services/price_scraper.py نیاز به بازبینی دارد."
        )

    return rows, warnings
