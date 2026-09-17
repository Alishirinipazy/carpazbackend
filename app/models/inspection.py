from datetime import date, datetime

from sqlalchemy import String, Text, ForeignKey, Integer, Date, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin


class CarInspection(Base, TimestampMixin):
    """
    برگ کارشناسی خودرو - one expert inspection report per car (one-to-one).
    Header fields mirror the paper form's info box (expert name, chassis
    number, plate, ...); `items` is the checklist itself, stored as JSON
    since it's an admin-editable list of {category, label, status} rather
    than a fixed set of columns - keeps it flexible without needing a
    separate items table + extra joins for what's always read/written as
    a single unit alongside its report.
    """

    __tablename__ = "car_inspections"

    id: Mapped[int] = mapped_column(primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id", ondelete="CASCADE"), unique=True)

    expert_name: Mapped[str] = mapped_column(String(255), default="")  # نام کارشناس
    vehicle_type: Mapped[str] = mapped_column(String(255), default="")  # نوع خودرو
    color: Mapped[str] = mapped_column(String(64), default="")  # رنگ خودرو
    model: Mapped[str] = mapped_column(String(255), default="")  # مدل
    client_name: Mapped[str] = mapped_column(String(255), default="")  # نام سفارش‌دهنده
    chassis_number: Mapped[str] = mapped_column(String(64), default="")  # شماره شاسی
    plate_number: Mapped[str] = mapped_column(String(32), default="")  # پلاک
    inspection_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # تاریخ کارشناسی
    mileage_km: Mapped[int | None] = mapped_column(Integer, nullable=True)  # کیلومتر
    visit_time: Mapped[str] = mapped_column(String(32), default="")  # ساعت بازدید
    visit_location: Mapped[str] = mapped_column(String(255), default="")  # محل بازدید
    suggested_price: Mapped[int | None] = mapped_column(Integer, nullable=True)  # قیمت پیشنهادی
    description: Mapped[str] = mapped_column(Text, default="")  # توضیحات

    # [{"category": "بدنه", "label": "شاسی جلو", "status": "healthy"}, ...]
    items: Mapped[list] = mapped_column(JSON, default=list)

    # عکس‌های اسکن/عکاسی‌شده از برگه‌ی فیزیکی کارشناسی (مکمل چک‌لیست بالا) -
    # [{"filename": "123456.jpg"}, ...] - آدرس قابل‌نمایش موقع serialize با
    # image_url() از روی filename ساخته میشه، نه اینکه خودش ذخیره بشه
    sheet_images: Mapped[list] = mapped_column(JSON, default=list)

    car: Mapped["Car"] = relationship(back_populates="inspection")
