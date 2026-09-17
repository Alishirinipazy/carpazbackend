from pydantic import BaseModel, field_validator


class CarModelIn(BaseModel):
    brand_id: int
    name: str

    @field_validator("name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("نام مدل نمی‌تواند خالی باشد")
        return v.strip()


class CarTrimIn(BaseModel):
    model_id: int
    name: str

    @field_validator("name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("نام تیریم نمی‌تواند خالی باشد")
        return v.strip()
