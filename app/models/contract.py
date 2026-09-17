from datetime import date

from sqlalchemy import String, Text, BigInteger, Date, ForeignKey, JSON, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin

STATUS_DRAFT = 0
STATUS_FINALIZED = 1


class Contract(Base, TimestampMixin, SoftDeleteMixin):
    """
    مبایعه‌نامه (قرارداد خرید و فروش) یک خودرو.

    چون یک خودرو وقتی فروخته می‌شه از جدول Car حذف می‌شه (نه اینکه فقط
    وضعیتش عوض بشه - به توضیح docstring کلاس Car نگاه کنید)، این مدل یک
    "عکس‌فوری" کامل از مشخصات خودرو رو در لحظه‌ی ثبت قرارداد در ستون
    `details` نگه می‌داره؛ یعنی حتی بعد از حذف شدن ردیف Car، قرارداد و
    PDF ش هنوز کامل و درست قابل بازسازیه. car_id فقط یک ارجاع کمکی/اختیاریه
    (برای لینک به صفحه‌ی خودرو تا وقتی هنوز حذف نشده)، نه منبع اصلی داده.

    `details` یک دیکشنری با کلیدهای زیره (همه اختیاری، رشته یا عدد):
      seller_name, seller_father_name, seller_national_id,
      seller_id_issued_from, seller_birth_date, seller_address, seller_phone
      buyer_name, buyer_father_name, buyer_national_id,
      buyer_id_issued_from, buyer_birth_date, buyer_address, buyer_phone
      vehicle_type, vehicle_brand_model, vehicle_model_year, vehicle_system,
      vehicle_color, plate_number, engine_number, chassis_number,
      vin_code, fuel_card_number, third_party_insurance_expiry,
      technical_inspection_expiry, accessories, documents
      mileage_km, has_paint_damage, paint_damage_location,
      technical_completeness
      deposit_amount, deposit_date, deposit_method, deposit_tracking_number
      remaining_amount, remaining_method, remaining_account_number,
      remaining_check_due_date, remaining_bank_name
      plate_transfer_date, plate_transfer_time, plate_transfer_location
      delivery_date, delivery_time, daily_penalty_amount
      seller_bank_account, buyer_bank_account, notes
    """

    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    car_id: Mapped[int | None] = mapped_column(ForeignKey("cars.id", ondelete="SET NULL"), nullable=True)

    contract_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # ثمن معامله - ریال
    price_text: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[int] = mapped_column(SmallInteger, default=STATUS_DRAFT)
    details: Mapped[dict] = mapped_column(JSON, default=dict)

    car: Mapped["Car"] = relationship()
