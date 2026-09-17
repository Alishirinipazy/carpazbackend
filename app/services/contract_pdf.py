"""
تولید PDF «مبایعه‌نامه خرید و فروش خودرو» با فونت فارسی (Vazirmatn)، راست‌به‌چپ،
لوگوی کارپاز در هر صفحه، و مقادیر پرشده (جاهای خالی تکمیل‌شده) با رنگ قرمز
هویت بصری کارپاز - طبق فرم مرجعی که کاربر آپلود کرده.

نکات فنی مهم درباره‌ی راست‌به‌چپ نویسی با fpdf2:
- fpdf2 خودش از BIDI/شکل‌دهی حروف فارسی-عربی پشتیبانی نمی‌کنه، پس هر رشته
  باید قبل از چاپ با arabic_reshaper (اتصال درست حروف) و python-bidi
  (ترتیب بصری راست‌به‌چپ) پردازش بشه - تابع rtl() این کار رو می‌کنه.
- برای متن تک‌خطی (لیبل‌ها، مقادیر کوتاه) کل رشته یک‌جا rtl() می‌شه.
- برای پاراگراف‌های چندخطی، خط‌شکنی باید روی متن *اصلی* (قبل از bidi) انجام
  بشه و بعد هر خط جدا rtl() بشه - وگرنه ترتیب کلمات بین خطوط به‌هم می‌ریزه.
"""
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from fpdf import FPDF

from app.models.contract import Contract
from app.services.num2persian import rial_to_toman_words

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
FONT_REGULAR = str(ASSETS_DIR / "fonts" / "Vazirmatn-Regular.ttf")
FONT_BOLD = str(ASSETS_DIR / "fonts" / "Vazirmatn-Bold.ttf")
LOGO_PATH = str(ASSETS_DIR / "images" / "carpaz-logo.png")

CARPAZ_RED = (225, 15, 31)      # #E10F1F
CARPAZ_DARK = (27, 36, 48)      # #1B2430
BLACK = (20, 20, 20)
GRAY = (110, 110, 110)

PAGE_MARGIN = 15


def rtl(text) -> str:
    """آماده‌سازی یک رشته‌ی تک‌خطی فارسی برای چاپ صحیح راست‌به‌چپ."""
    if text is None:
        return ""
    text = str(text)
    if not text:
        return ""
    return get_display(arabic_reshaper.reshape(text))


class ContractPDF(FPDF):
    def header(self):
        # لوگو سمت چپ، اسم برند سمت راست - هردو روی یک خط، وسط‌چین عمودی
        logo_h = 14
        logo_w = logo_h * (1023 / 1535)  # نسبت واقعی تصویر لوگو، برای جلوگیری از کش‌شدگی
        logo_y = 8
        self.image(LOGO_PATH, x=PAGE_MARGIN, y=logo_y, h=logo_h)

        text_x = PAGE_MARGIN + logo_w + 6
        self.set_font("Vazirmatn", "B", 15)
        self.set_text_color(*CARPAZ_DARK)
        self.set_xy(text_x, logo_y - 1)
        self.cell(self.w - PAGE_MARGIN - text_x, 7, rtl("کارپاز"), align="R")

        self.set_font("Vazirmatn", "", 8.5)
        self.set_text_color(*GRAY)
        self.set_xy(text_x, logo_y + 6.5)
        self.cell(self.w - PAGE_MARGIN - text_x, 5, rtl("خرید و فروش خودرو"), align="R")

        # خط دوتُنه‌ی جداکننده‌ی هدر
        y = logo_y + logo_h + 4
        self.set_draw_color(*CARPAZ_RED)
        self.set_line_width(0.7)
        self.line(PAGE_MARGIN, y, self.w - PAGE_MARGIN, y)
        self.set_draw_color(*CARPAZ_DARK)
        self.set_line_width(0.25)
        self.line(PAGE_MARGIN, y + 1.3, self.w - PAGE_MARGIN, y + 1.3)

        self.set_y(y + 6)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(*CARPAZ_RED)
        self.set_line_width(0.2)
        self.line(PAGE_MARGIN, self.get_y(), self.w - PAGE_MARGIN, self.get_y())
        self.set_font("Vazirmatn", "", 8)
        self.set_text_color(*GRAY)
        self.set_y(-12)
        self.cell(0, 8, rtl(f"صفحه {self.page_no()}"), align="C")


def _right_x(pdf: ContractPDF) -> float:
    return pdf.w - pdf.r_margin


def _left_x(pdf: ContractPDF) -> float:
    return pdf.l_margin


def _ensure_space(pdf: ContractPDF, needed_height: float):
    """
    چون این ماژول خودش دستی مختصات x/y رو مدیریت می‌کنه (نه با جریان
    خودکار fpdf2)، auto_page_break باید خاموش باشه و به‌جاش قبل از هر
    بلوک (ردیف فیلد، پاراگراف و...) خودمون چک کنیم که جا هست یا نه - وگرنه
    اگه fpdf2 وسط یک field_row/paragraph خودش صفحه عوض کنه، محتوا با
    مختصات قدیمی (متعلق به صفحه‌ی قبل) رسم می‌شه و روی صفحه‌ی خالی گم میشه.
    """
    if pdf.get_y() + needed_height > pdf.h - pdf.b_margin:
        pdf.add_page()


def section_title(pdf: ContractPDF, text: str):
    _ensure_space(pdf, 16)
    pdf.ln(2)
    pdf.set_font("Vazirmatn", "B", 12)
    pdf.set_text_color(*CARPAZ_RED)
    pdf.set_x(_left_x(pdf))
    pdf.cell(pdf.epw, 8, rtl(text), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*CARPAZ_RED)
    pdf.set_line_width(0.3)
    pdf.line(_left_x(pdf), pdf.get_y(), _right_x(pdf), pdf.get_y())
    pdf.ln(3)


def paragraph(pdf: ContractPDF, text: str, size: float = 10, line_height: float = 6.2):
    """پاراگراف چندخطی، خط‌شکنی صحیح راست‌به‌چپ (بدون درهم‌ریختن ترتیب کلمات)."""
    pdf.set_font("Vazirmatn", "", size)
    pdf.set_text_color(*BLACK)
    max_width = pdf.epw

    words = text.split(" ")
    lines, current = [], []
    for word in words:
        trial = current + [word]
        shaped_w = pdf.get_string_width(arabic_reshaper.reshape(" ".join(trial)))
        if shaped_w <= max_width or not current:
            current = trial
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    for line in lines:
        _ensure_space(pdf, line_height)
        pdf.set_x(_left_x(pdf))
        pdf.cell(pdf.epw, line_height, rtl(line), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def field_row(pdf: ContractPDF, fields: list[tuple[str, object]], size: float = 10, line_height: float = 7, gap: float = 5):
    """
    یک یا چند فیلد «برچسب: مقدار» در یک ردیف، از راست به چپ.
    مقدار همیشه با رنگ قرمز چاپ می‌شه (چه پر شده باشه چه خالی).
    fields: [(label, value), ...]
    """
    # حداکثر ممکنه این ردیف (اگه هیچ‌کدوم جا نشه) به تعداد فیلدها خط بشه -
    # برای سادگی و اطمینان، جای کافی برای کل ردیف رو از قبل رزرو می‌کنیم
    _ensure_space(pdf, line_height * len(fields))

    pdf.set_font("Vazirmatn", "", size)
    cur_x = _right_x(pdf)
    y = pdf.get_y()
    min_x = _left_x(pdf)

    for label, value in fields:
        label_txt = rtl(f"{label}: ") if label else ""
        pdf.set_text_color(*BLACK)
        w = pdf.get_string_width(label_txt)
        cur_x -= w
        if cur_x < min_x:  # سر ریز به خط بعد (همون صفحه)
            cur_x = _right_x(pdf) - w
            y += line_height
        pdf.set_xy(cur_x, y)
        pdf.cell(w, line_height, label_txt, align="L")

        value_str = str(value) if value not in (None, "") else "..................."
        value_txt = rtl(value_str)
        pdf.set_text_color(*CARPAZ_RED)
        w = pdf.get_string_width(value_txt)
        cur_x -= w
        pdf.set_xy(cur_x, y)
        pdf.cell(w, line_height, value_txt, align="L")

        cur_x -= gap

    pdf.set_xy(_left_x(pdf), y + line_height)


def draw_party_box(pdf: ContractPDF, x: float, y: float, w: float, title: str, fields: list[tuple[str, object]]) -> float:
    """
    یک باکس مستطیلی با نوار عنوان قرمز برای اطلاعات فروشنده/خریدار - هر
    فیلد یک خط جدا (برچسب سیاه، مقدار قرمز). خروجی: y پایین باکس، برای
    هم‌تراز کردن دو باکس کنار هم وقتی تعداد فیلدهاشون یکی نیست.
    """
    padding = 4
    title_h = 9
    line_h = 6.5
    box_h = title_h + len(fields) * line_h + padding * 1.5

    # بدنه‌ی باکس
    pdf.set_draw_color(210, 210, 210)
    pdf.set_line_width(0.3)
    pdf.rect(x, y, w, box_h, style="D")

    # نوار عنوان
    pdf.set_fill_color(*CARPAZ_RED)
    pdf.rect(x, y, w, title_h, style="F")
    pdf.set_font("Vazirmatn", "B", 11)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(x, y + 1.8)
    pdf.cell(w, 6, rtl(title), align="C")

    # فیلدها
    cy = y + title_h + padding * 0.7
    inner_right = x + w - padding
    for label, value in fields:
        pdf.set_font("Vazirmatn", "", 9.5)
        label_txt = rtl(f"{label}: ")
        pdf.set_text_color(*BLACK)
        lw = pdf.get_string_width(label_txt)
        pdf.set_xy(inner_right - lw, cy)
        pdf.cell(lw, line_h, label_txt, align="L")

        value_str = str(value) if value not in (None, "") else "----------"
        value_txt = rtl(value_str)
        pdf.set_text_color(*CARPAZ_RED)
        vw = pdf.get_string_width(value_txt)
        max_vw = inner_right - lw - (x + padding)
        if vw > max_vw:  # مقدار خیلی بلند - کوچیک‌ترش کن که از باکس بیرون نزنه
            pdf.set_font("Vazirmatn", "", 8)
            value_txt = rtl(value_str)
            vw = pdf.get_string_width(value_txt)
        pdf.set_xy(inner_right - lw - vw, cy)
        pdf.cell(vw, line_h, value_txt, align="L")
        cy += line_h

    return y + box_h


def _fmt_money(n) -> str | None:
    if not n:
        return None
    return f"{int(n):,}"


def generate_contract_pdf(contract: Contract) -> bytes:
    d = contract.details or {}

    pdf = ContractPDF(format="A4")
    pdf.set_margins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
    pdf.set_auto_page_break(auto=False, margin=20)
    pdf.add_font("Vazirmatn", "", FONT_REGULAR)
    pdf.add_font("Vazirmatn", "B", FONT_BOLD)
    pdf.add_page()

    pdf.set_font("Vazirmatn", "", 11)
    pdf.set_text_color(*GRAY)
    pdf.cell(pdf.epw, 6, rtl("به نام خدا"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Vazirmatn", "B", 16)
    pdf.set_text_color(*CARPAZ_DARK)
    pdf.cell(pdf.epw, 10, rtl("مبایعه‌نامه خرید و فروش خودرو"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    contract_date_str = contract.contract_date.isoformat() if contract.contract_date else None
    field_row(pdf, [("تاریخ تنظیم قرارداد", contract_date_str), ("شماره قرارداد", f"{contract.id:06d}" if contract.id else None)])
    pdf.ln(3)

    section_title(pdf, "ماده ۱ - طرفین قرارداد")

    seller_fields = [
        ("نام و نام خانوادگی", d.get("seller_name")),
        ("نام پدر", d.get("seller_father_name")),
        ("شماره شناسنامه/کدملی", d.get("seller_national_id")),
        ("صادره از", d.get("seller_id_issued_from")),
        ("متولد", d.get("seller_birth_date")),
        ("نشانی", d.get("seller_address")),
        ("تلفن همراه و ثابت", d.get("seller_phone")),
    ]
    buyer_fields = [
        ("نام و نام خانوادگی", d.get("buyer_name")),
        ("نام پدر", d.get("buyer_father_name")),
        ("شماره شناسنامه/کدملی", d.get("buyer_national_id")),
        ("صادره از", d.get("buyer_id_issued_from")),
        ("متولد", d.get("buyer_birth_date")),
        ("نشانی", d.get("buyer_address")),
        ("تلفن همراه و ثابت", d.get("buyer_phone")),
    ]

    box_gap = 6
    box_w = (pdf.epw - box_gap) / 2
    _ensure_space(pdf, 9 + len(seller_fields) * 6.5 + 6)
    top_y = pdf.get_y()
    seller_box_x = _right_x(pdf) - box_w
    buyer_box_x = _left_x(pdf)
    bottom1 = draw_party_box(pdf, seller_box_x, top_y, box_w, "فروشنده", seller_fields)
    bottom2 = draw_party_box(pdf, buyer_box_x, top_y, box_w, "خریدار", buyer_fields)
    pdf.set_xy(_left_x(pdf), max(bottom1, bottom2) + 4)

    section_title(pdf, "ماده ۲ - موضوع و مشخصات مورد معامله")
    paragraph(pdf, "موضوع این قرارداد عبارت است از انتقال قطعی و قانونی مالکیت تمام و کمال (شش دانگ) یک دستگاه خودروی مشخص‌شده در زیر، از فروشنده به خریدار، با تمام متعلقات، منصوبات، تجهیزات و اسناد و مدارک مربوطه:")
    field_row(pdf, [("نوع خودرو", d.get("vehicle_type")), ("برند و مدل", d.get("vehicle_brand_model")), ("سال ساخت", d.get("vehicle_model_year"))])
    field_row(pdf, [("سیستم", d.get("vehicle_system")), ("رنگ", d.get("vehicle_color")), ("شماره انتظامی", d.get("plate_number"))])
    field_row(pdf, [("شماره موتور", d.get("engine_number")), ("شماره شاسی", d.get("chassis_number"))])
    field_row(pdf, [("شناسه VIN", d.get("vin_code")), ("شماره کارت سوخت", d.get("fuel_card_number"))])
    field_row(pdf, [("تاریخ انقضای بیمه شخص ثالث", d.get("third_party_insurance_expiry")), ("تاریخ انقضای معاینه فنی", d.get("technical_inspection_expiry"))])
    if d.get("accessories"):
        field_row(pdf, [("متعلقات و تجهیزات", d.get("accessories"))])
    if d.get("documents"):
        field_row(pdf, [("اسناد و مدارک همراه", d.get("documents"))])

    section_title(pdf, "ماده ۳ - اظهارات فروشنده در خصوص وضعیت خودرو")
    field_row(pdf, [("کارکرد خودرو در زمان تنظیم قرارداد (کیلومتر)", d.get("mileage_km"))])
    paint_status = "دارد" if d.get("has_paint_damage") else ("ندارد" if d.get("has_paint_damage") is False else None)
    field_row(pdf, [("رنگ‌شدگی بدنه", paint_status)])
    if d.get("paint_damage_location"):
        field_row(pdf, [("محل و نقاط رنگ‌شدگی", d.get("paint_damage_location"))])
    if d.get("technical_completeness"):
        paragraph(pdf, "توضیحات فنی و تکمیلی وضعیت خودرو:")
        field_row(pdf, [("", d.get("technical_completeness"))])

    section_title(pdf, "ماده ۴ - ثمن معامله")
    price_text = contract.price_text or (rial_to_toman_words(contract.price) + " تومان" if contract.price else None)
    field_row(pdf, [("مبلغ کل معامله (ریال)", _fmt_money(contract.price))])
    if price_text:
        field_row(pdf, [("مبلغ به حروف", price_text)])

    paragraph(pdf, "همزمان با انعقاد این قرارداد، مبلغ زیر به‌عنوان بخشی از ثمن معامله از سوی خریدار به فروشنده پرداخت گردید:")
    field_row(pdf, [("مبلغ پیش‌پرداخت (ریال)", _fmt_money(d.get("deposit_amount"))), ("تاریخ پرداخت", d.get("deposit_date"))])
    field_row(pdf, [("روش پرداخت", d.get("deposit_method")), ("شماره پیگیری", d.get("deposit_tracking_number"))])

    paragraph(pdf, "باقی‌مانده ثمن معامله به شرح زیر در وجه فروشنده پرداخت می‌گردد:")
    field_row(pdf, [("مانده ثمن معامله (ریال)", _fmt_money(d.get("remaining_amount"))), ("روش پرداخت", d.get("remaining_method"))])
    field_row(pdf, [("شماره چک/شماره حساب", d.get("remaining_account_number")), ("تاریخ سررسید", d.get("remaining_check_due_date")), ("بانک", d.get("remaining_bank_name"))])

    section_title(pdf, "ماده ۵ - شرایط معامله و تعهدات طرفین")
    paragraph(pdf, "۵-۱- طرفین متعهد شدند جهت تعویض پلاک و/یا اعطای وکالت رسمی طبق شرایط این قرارداد، در تاریخ و ساعت زیر در دفترخانه‌ی اسناد رسمی یا مرکز تعویض پلاک مشخص‌شده حاضر شوند. فروشنده متعهد است سند را صرفاً به نام خریدار انتقال دهد و تا آن زمان، حق فروش، اجاره یا واگذاری خودرو تحت هر عنوان به شخص دیگری را ندارد.")
    field_row(pdf, [("تاریخ تعویض پلاک", d.get("plate_transfer_date")), ("ساعت", d.get("plate_transfer_time"))])
    field_row(pdf, [("محل حضور (دفترخانه/مرکز تعویض پلاک)", d.get("plate_transfer_location"))])

    paragraph(pdf, "۵-۲- مورد معامله به همراه کلیه‌ی اسناد، مدارک، متعلقات و لوازم ملحقه، در تاریخ و ساعت زیر به خریدار تحویل داده شد/خواهد شد:")
    field_row(pdf, [("تاریخ تحویل خودرو", d.get("delivery_date")), ("ساعت", d.get("delivery_time"))])

    paragraph(pdf, "۵-۳- کلیه‌ی هزینه‌های شماره‌گذاری، نصب پلاک، مالیات، عوارض و تنظیم سند رسمی یا وکالت بر عهده‌ی فروشنده است.")
    paragraph(pdf, "۵-۴- در صورتی‌که مورد معامله به هر دلیلی غیر از موارد قهریه (فورس ماژور) از قبیل مصادره، رهن یا مانع قانونی دیگر، قابل انتقال یا اجرای سند رسمی نباشد، خریدار ظرف مدت سی روز حق فسخ قرارداد را دارد و فروشنده مکلف است ده درصد ثمن معامله را به‌عنوان خسارت عدم انجام تعهد به خریدار پرداخت کند.")
    paragraph(pdf, "۵-۵- خریدار می‌تواند پیش از تنظیم این قرارداد، تصویری از خودرو و مدارک آن را از فروشنده دریافت کند.")
    paragraph(pdf, "۵-۶- هرگونه تقلب یا تدلیس از سوی فروشنده در خصوص مورد معامله که به مغبون شدن خریدار منجر شود، موجب ایجاد حق فسخ قرارداد برای طرف مغبون است.")
    paragraph(pdf, "۵-۷- در صورت عدم حضور هریک از طرفین در زمان و مکان توافق‌شده برای تنظیم سند رسمی یا تعویض پلاک، طرف ممتنع موظف است به ازای هر روز تاخیر، مبلغ زیر را به‌عنوان خسارت عدم انجام تعهد به طرف مقابل پرداخت کند - این خسارت مستقل از تعهد اصلی بوده و با آن قابل جمع است:")
    field_row(pdf, [("مبلغ خسارت روزانه تاخیر (ریال)", _fmt_money(d.get("daily_penalty_amount")))])

    paragraph(pdf, "۵-۸- فروشنده و خریدار شماره حساب شخصی خود را به شرح زیر اعلام کرده‌اند تا در صورت نیاز به بازپرداخت، دریافت یا تسویه‌ی هرگونه وجه اضافه‌پرداختی مرتبط با این قرارداد مورد استناد قرار گیرد:")
    field_row(pdf, [("شماره حساب فروشنده", d.get("seller_bank_account"))])
    field_row(pdf, [("شماره حساب خریدار", d.get("buyer_bank_account"))])

    if d.get("notes"):
        pdf.ln(2)
        paragraph(pdf, f"توضیحات: {d.get('notes')}")

    pdf.ln(8)
    if pdf.get_y() > pdf.h - 45:
        pdf.add_page()
    y = pdf.get_y()
    col_w = pdf.epw / 3
    pdf.set_font("Vazirmatn", "B", 10)
    pdf.set_text_color(*BLACK)
    for i, label in enumerate(["امضاء فروشنده", "امضاء خریدار", "امضاء شاهد"]):
        x = _right_x(pdf) - col_w * (i + 1)
        pdf.set_xy(x, y)
        pdf.cell(col_w, 6, rtl(label), align="C")
    pdf.set_draw_color(*CARPAZ_RED)
    pdf.set_line_width(0.2)
    for i in range(3):
        x = _right_x(pdf) - col_w * (i + 1) + 10
        pdf.line(x, y + 20, x + col_w - 20, y + 20)

    out = pdf.output()
    return bytes(out)
