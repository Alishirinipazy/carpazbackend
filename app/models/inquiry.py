from sqlalchemy import String, Text, ForeignKey, SmallInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin


class Inquiry(Base, TimestampMixin, SoftDeleteMixin):
    """
    A customer's request to buy/reserve a specific car. There's no online
    payment in this business - a sales agent follows up by phone to
    negotiate, arrange a test drive/visit, and close the deal offline.
    This replaces the shop's Order/OrderItems/Coupon/ShippingMethod/
    Transaction/payment-gateway chain, which doesn't apply here.

    Each Car is a single physical unit (no quantity/stock) - once a deal
    closes, the Car row is deleted rather than decremented. `car_id` is
    therefore nullable/ON DELETE SET NULL, and car_title/car_price/car_image
    are snapshotted at the time the inquiry is created, so the inquiry's
    history stays readable in the admin panel even after the car is gone.
    """

    __tablename__ = "inquiries"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    car_id: Mapped[int | None] = mapped_column(
        ForeignKey("cars.id", ondelete="SET NULL"), nullable=True
    )
    car_title: Mapped[str] = mapped_column(String(255))
    car_price: Mapped[int] = mapped_column(Integer)
    car_image: Mapped[str] = mapped_column(String(255))

    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(32))
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_contact_time: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # 0 pending, 1 contacted, 2 negotiating, 3 test-drive scheduled,
    # 4 deal closed / sold, 5 cancelled, 6 rejected
    status: Mapped[int] = mapped_column(SmallInteger, default=0)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="inquiries")
    car: Mapped["Car | None"] = relationship(back_populates="inquiries")
