from datetime import date

from pydantic import BaseModel, field_validator

from app.core.inspection_constants import validate_item_status


class InspectionItemIn(BaseModel):
    category: str
    label: str
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        try:
            validate_item_status(v)
        except ValueError as e:
            raise ValueError(str(e))
        return v


class CarInspectionIn(BaseModel):
    expert_name: str = ""
    vehicle_type: str = ""
    color: str = ""
    model: str = ""
    client_name: str = ""
    chassis_number: str = ""
    plate_number: str = ""
    inspection_date: date | None = None
    mileage_km: int | None = None
    visit_time: str = ""
    visit_location: str = ""
    suggested_price: int | None = None
    description: str = ""
    items: list[InspectionItemIn] = []
