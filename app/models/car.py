from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, Integer, SmallInteger, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin


class Car(Base, TimestampMixin, SoftDeleteMixin):
    """
    Each row is one physical car - there's no quantity/stock concept, new or
    used. Once it's sold (an Inquiry is closed as a deal), the row is
    deleted rather than decremented, so `color`/`price` live directly here
    instead of on a separate variant table.
    """

    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True)

    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"))
    # body-type category, e.g. Sedan, SUV, Crossover, Pickup, Hatchback -
    # this already covers "نوع خودرو" (coupe/sedan/...), so it isn't
    # duplicated as a separate field; add more Category rows for it.
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))

    model_name: Mapped[str] = mapped_column(String(255))  # e.g. "207", "Cerato", "Tara"
    model_year: Mapped[int] = mapped_column(Integer)  # سال ساخت/تولید

    # 0 = کارکرده (used), 1 = نو (new)
    condition: Mapped[int] = mapped_column(SmallInteger, default=1)
    mileage_km: Mapped[int] = mapped_column(Integer, default=0)  # کارکرد به کیلومتر، صفر برای خودروی نو
    vin: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)

    # رنگ - یک مقدار از app.core.car_constants.STANDARD_COLORS، چون هر خودرو
    # دقیقاً یک رنگ دارد (نه چند گزینه‌ی رنگ مثل یک محصول با موجودی چندتایی)
    color: Mapped[str] = mapped_column(String(32))
    color_code: Mapped[str] = mapped_column(String(32))

    # نوع گیربکس / نوع سوخت - values from app.core.car_constants
    transmission: Mapped[str] = mapped_column(String(16), default="manual")
    fuel_type: Mapped[str] = mapped_column(String(16), default="gasoline")

    # وضعیت شاسی و بدنه - true = سالم (healthy/undamaged), false = دارای
    # آسیب/تعویض/رنگ‌شدگی. Kept as two plain booleans rather than a
    # per-panel breakdown (front-left door, rear bumper, ...) since that
    # level of detail isn't needed for filtering/search - just "would this
    # car pass a basic chassis/body check". New cars default to True/True.
    chassis_healthy: Mapped[bool] = mapped_column(Boolean, default=True)
    body_healthy: Mapped[bool] = mapped_column(Boolean, default=True)

    primary_image: Mapped[str] = mapped_column(String(255))
    primary_image_blur_data_url: Mapped[str] = mapped_column(
        "primary_image_blurDataURL", Text
    )
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)

    sale_price: Mapped[int] = mapped_column(Integer, default=0)
    date_on_sale_from: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    date_on_sale_to: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    brand: Mapped["Brand"] = relationship(back_populates="cars")
    category: Mapped["Category"] = relationship(back_populates="cars")
    images: Mapped[list["CarImage"]] = relationship(back_populates="car")
    inquiries: Mapped[list["Inquiry"]] = relationship(back_populates="car")

    _STATUS_LABELS = {0: "غیر فعال", 1: "فعال"}
    _CONDITION_LABELS = {0: "کارکرده", 1: "نو"}

    @property
    def status_label(self) -> str:
        return self._STATUS_LABELS.get(self.status, str(self.status))

    @property
    def condition_label(self) -> str:
        return self._CONDITION_LABELS.get(self.condition, str(self.condition))

    @property
    def effective_price(self) -> int:
        return self.sale_price or self.price


class CarImage(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "car_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id", ondelete="CASCADE"))
    image: Mapped[str] = mapped_column(String(255))

    car: Mapped["Car"] = relationship(back_populates="images")
