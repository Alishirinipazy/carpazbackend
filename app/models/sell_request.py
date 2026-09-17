from datetime import datetime

from sqlalchemy import String, Text, SmallInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin


class SellRequest(Base, TimestampMixin, SoftDeleteMixin):
    """
    "فروش ماشین شما" (Sell your car) lead - a visitor tells us they have a
    car they want to sell to the dealership; a sales agent then calls them
    to inspect/appraise/negotiate offline. Unlike Inquiry (which is a
    request to *buy* a car already listed on the site), this is a request
    for us to *buy from* the customer, so there's no car_id/listing at all -
    just the free-text description of the car they're offering.

    Requires login to submit (same as Inquiry) - the frontend gathers the
    submitter's name/phone from their account instead of asking again.
    """

    __tablename__ = "sell_requests"

    id: Mapped[int] = mapped_column(primary_key=True)

    full_name: Mapped[str] = mapped_column(String(255))
    car_type: Mapped[str] = mapped_column(String(255))  # نوع ماشین
    car_model: Mapped[str] = mapped_column(String(255))  # مدل ماشین
    phone: Mapped[str] = mapped_column(String(32))

    # 0 pending, 1 contacted, 2 accepted, 3 rejected
    status: Mapped[int] = mapped_column(SmallInteger, default=0)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # set the first time an admin opens the request, so the admin inbox can
    # show a "new"/unseen badge independently of the status pipeline above
    seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
