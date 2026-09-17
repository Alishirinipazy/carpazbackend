from datetime import date

from pydantic import BaseModel, field_validator


class PriceGuideEntryIn(BaseModel):
    brand: str
    model: str
    trim: str | None = None
    year: str | None = None
    condition: int  # 0 = صفر, 1 = کارکرده
    market_price: int | None = None
    agency_price: int | None = None
    price_date: date | None = None  # اگر نده، امروز در نظر گرفته می‌شود

    @field_validator("brand", "model")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("این فیلد نمی‌تواند خالی باشد")
        return v.strip()

    @field_validator("condition")
    @classmethod
    def valid_condition(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError("وضعیت باید صفر (0) یا کارکرده (1) باشد")
        return v
