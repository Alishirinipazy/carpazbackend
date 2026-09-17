from datetime import date

from sqlalchemy import String, SmallInteger, BigInteger, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin

# منبع قیمت: از کجا وارد شده
SOURCE_MANUAL = "manual"
SOURCE_EXCEL = "excel"
SOURCE_SCRAPER = "scraper"

# وضعیت خودرو
CONDITION_ZERO = 0   # صفر کیلومتر
CONDITION_USED = 1   # کارکرده


class PriceGuideEntry(Base, TimestampMixin, SoftDeleteMixin):
    """
    "قیمت روز خودرو" - جدول مرجع قیمت بازار/نمایندگی خودروها (صفر و کارکرده)،
    مستقل از آگهی‌های واقعی نمایشگاه (جدول Car). این یک "لیست قیمت روز" است
    که هرروز به‌روزرسانی می‌شود - یا دستی از پنل ادمین، یا با آپلود اکسل،
    یا (به‌صورت کمکی و best-effort) با اسکرپر داخلی از یک سایت مرجع.

    برند/مدل عمداً متن آزاد هستند (نه FK به جدول Brand) چون این لیست قیمت،
    بازار کل خودرو کشور را پوشش می‌دهد نه فقط برندهایی که در انبار خودمان هست.
    """

    __tablename__ = "price_guide_entries"

    id: Mapped[int] = mapped_column(primary_key=True)

    brand: Mapped[str] = mapped_column(String(255), index=True)
    model: Mapped[str] = mapped_column(String(255), index=True)
    trim: Mapped[str | None] = mapped_column(String(255), nullable=True)   # تیریم/نوع موتور
    year: Mapped[str | None] = mapped_column(String(32), nullable=True)   # سال ساخت/مدل

    # 0 = صفر کیلومتر , 1 = کارکرده
    condition: Mapped[int] = mapped_column(SmallInteger, index=True)

    market_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)   # قیمت بازار (تومان)
    agency_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)   # قیمت نمایندگی/کارخانه (تومان)

    price_date: Mapped[date] = mapped_column(Date)   # این قیمت مربوط به چه روزی است
    source: Mapped[str] = mapped_column(String(20), default=SOURCE_MANUAL)
