from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin


class CarModel(Base, TimestampMixin, SoftDeleteMixin):
    """
    یک مدل خودرو زیرمجموعه‌ی یک برند - مثلاً «کرولا» زیر «تویوتا»، یا
    «دنا» زیر «ایران خودرو». این جدول همراه با CarTrim، ساختار درختی
    برند → مدل → تیریم رو می‌سازه که به‌جای تایپ آزاد «model_name» توی
    فرم ثبت خودرو، از یک فهرست قابل‌جستجو انتخاب می‌شه.
    """

    __tablename__ = "car_models"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255))

    brand: Mapped["Brand"] = relationship(back_populates="models")
    trims: Mapped[list["CarTrim"]] = relationship(back_populates="model", cascade="all, delete-orphan")


class CarTrim(Base, TimestampMixin, SoftDeleteMixin):
    """یک تیریم/نسخه‌ی زیرمجموعه‌ی یک مدل - مثلاً «دنا پلاس توربو» زیر «دنا»، یا «۱.۸» زیر «کرولا»."""

    __tablename__ = "car_trims"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("car_models.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))

    model: Mapped["CarModel"] = relationship(back_populates="trims")
