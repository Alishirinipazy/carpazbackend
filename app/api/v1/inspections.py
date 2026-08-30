from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.inspection_constants import DEFAULT_INSPECTION_CHECKLIST, INSPECTION_ITEM_STATUSES
from app.db.session import get_db
from app.models import Car, CarInspection, User
from app.schemas.inspection import CarInspectionIn
from app.utils.response import success_response, error_response

router = APIRouter(tags=["inspections"])
admin_router = APIRouter(prefix="/admin-panel", tags=["admin-inspections"])


def _serialize_inspection(inspection: CarInspection) -> dict:
    return {
        "id": inspection.id,
        "car_id": inspection.car_id,
        "expert_name": inspection.expert_name,
        "vehicle_type": inspection.vehicle_type,
        "color": inspection.color,
        "model": inspection.model,
        "client_name": inspection.client_name,
        "chassis_number": inspection.chassis_number,
        "plate_number": inspection.plate_number,
        "inspection_date": inspection.inspection_date,
        "mileage_km": inspection.mileage_km,
        "visit_time": inspection.visit_time,
        "visit_location": inspection.visit_location,
        "suggested_price": inspection.suggested_price,
        "description": inspection.description,
        "items": inspection.items or [],
        "updated_at": inspection.updated_at,
    }


# ---------------------------------------------------------------------------
# Public - shown on the car's product page
# ---------------------------------------------------------------------------

@router.get("/cars/{car_id}/inspection")
def show_inspection(car_id: int, db: Session = Depends(get_db)):
    inspection = db.query(CarInspection).filter(CarInspection.car_id == car_id).first()
    if inspection is None:
        return error_response("برای این خودرو کارشناسی ثبت نشده است", 404)
    return success_response(_serialize_inspection(inspection))


# ---------------------------------------------------------------------------
# Admin panel
# ---------------------------------------------------------------------------

@admin_router.get("/inspection-options")
def admin_inspection_options(_: User = Depends(get_current_admin)):
    """Status vocabulary + a default checklist to seed the form for a car with no report yet."""
    return success_response({
        "statuses": [{"value": k, "label": v} for k, v in INSPECTION_ITEM_STATUSES.items()],
        "default_checklist": DEFAULT_INSPECTION_CHECKLIST,
    })


@admin_router.get("/cars/{car_id}/inspection")
def admin_show_inspection(
    car_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)
):
    inspection = db.query(CarInspection).filter(CarInspection.car_id == car_id).first()
    if inspection is None:
        return error_response("برای این خودرو کارشناسی ثبت نشده است", 404)
    return success_response(_serialize_inspection(inspection))


@admin_router.put("/cars/{car_id}/inspection")
def admin_upsert_inspection(
    car_id: int,
    payload: CarInspectionIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    car = db.query(Car).filter(Car.id == car_id).first()
    if car is None:
        return error_response("خودرو پیدا نشد", 404)

    inspection = db.query(CarInspection).filter(CarInspection.car_id == car_id).first()
    if inspection is None:
        inspection = CarInspection(car_id=car_id)
        db.add(inspection)

    inspection.expert_name = payload.expert_name
    inspection.vehicle_type = payload.vehicle_type
    inspection.color = payload.color
    inspection.model = payload.model
    inspection.client_name = payload.client_name
    inspection.chassis_number = payload.chassis_number
    inspection.plate_number = payload.plate_number
    inspection.inspection_date = payload.inspection_date
    inspection.mileage_km = payload.mileage_km
    inspection.visit_time = payload.visit_time
    inspection.visit_location = payload.visit_location
    inspection.suggested_price = payload.suggested_price
    inspection.description = payload.description
    inspection.items = [item.model_dump() for item in payload.items]

    db.commit()
    db.refresh(inspection)
    return success_response(_serialize_inspection(inspection))


@admin_router.delete("/cars/{car_id}/inspection")
def admin_delete_inspection(
    car_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)
):
    inspection = db.query(CarInspection).filter(CarInspection.car_id == car_id).first()
    if inspection is None:
        return error_response("برای این خودرو کارشناسی ثبت نشده است", 404)
    db.delete(inspection)
    db.commit()
    return success_response({"data": ["deleted"]})
