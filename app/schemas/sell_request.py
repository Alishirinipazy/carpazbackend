import re

from pydantic import BaseModel, field_validator

CELLPHONE_RE = re.compile(r"^(\+98|0)?9\d{9}$")


class SellRequestIn(BaseModel):
    full_name: str
    car_type: str
    car_model: str
    phone: str

    @field_validator("full_name", "car_type", "car_model")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("این فیلد نمی‌تواند خالی باشد")
        return v.strip()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not CELLPHONE_RE.match(v):
            raise ValueError("شماره تماس باید یک شماره موبایل معتبر باشد")
        return v


class SellRequestStatusIn(BaseModel):
    status: int
    admin_notes: str | None = None
