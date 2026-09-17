from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from io import BytesIO

from app.api.deps import get_current_admin
from app.core.car_constants import TRANSMISSION_TYPES, FUEL_TYPES
from app.db.session import get_db
from app.models import Contract, Car, User
from app.schemas.contract import ContractIn
from app.services.contract_pdf import generate_contract_pdf
from app.utils.jalali import format_jalali
from app.utils.pagination import paginate
from app.utils.response import success_response, error_response

admin_router = APIRouter(prefix="/admin-panel", tags=["admin-contracts"])


def _serialize(item: Contract) -> dict:
    car_title = None
    if item.car_id and item.car is not None:
        car_title = item.car.title
    elif (item.details or {}).get("vehicle_brand_model"):
        car_title = item.details["vehicle_brand_model"]

    return {
        "id": item.id,
        "car_id": item.car_id,
        "car_title": car_title,
        "car_exists": item.car_id is not None and item.car is not None,
        "contract_date": item.contract_date.isoformat() if item.contract_date else None,
        "price": item.price,
        "price_text": item.price_text,
        "status": item.status,
        "status_label": "نهایی‌شده" if item.status == 1 else "پیش‌نویس",
        "details": item.details or {},
        "seller_name": (item.details or {}).get("seller_name"),
        "buyer_name": (item.details or {}).get("buyer_name"),
        "created_at": format_jalali(item.created_at),
        "updated_at": format_jalali(item.updated_at),
    }


def _snapshot_from_car(car: Car) -> dict:
    """پرکردن خودکار فیلدهایی از قرارداد که از روی رکورد خودرو قابل استخراجه."""
    fuel_label = FUEL_TYPES.get(car.fuel_type, car.fuel_type)
    transmission_label = TRANSMISSION_TYPES.get(car.transmission, car.transmission)
    return {
        "vehicle_type": car.category.name if car.category else None,
        "vehicle_brand_model": f"{car.brand.name if car.brand else ''} {car.model_name or ''}".strip(),
        "vehicle_model_year": str(car.model_year) if car.model_year else None,
        "vehicle_system": f"{fuel_label or ''} - {transmission_label or ''}".strip(" -"),
        "vehicle_color": car.color,
        "chassis_number": car.vin,
        "vin_code": car.vin,
        "mileage_km": car.mileage_km,
        "has_paint_damage": (not car.body_healthy) if car.body_healthy is not None else None,
    }


@admin_router.get("/contracts")
def admin_index(request: Request, page: int = 1, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    query = (
        db.query(Contract)
        .options(joinedload(Contract.car))
        .order_by(Contract.created_at.desc())
    )
    items, links, meta = paginate(query, request, page, per_page=15)
    return success_response({"contracts": [_serialize(i) for i in items], "links": links, "meta": meta})


@admin_router.get("/contracts/new-from-car/{car_id}")
def admin_new_from_car(car_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    """قبل از باز کردن فرم «ثبت قرارداد جدید»، فیلدهای قابل استخراج از خودرو رو پیش‌پر می‌کنه."""
    car = db.query(Car).options(joinedload(Car.brand), joinedload(Car.category)).filter(Car.id == car_id).first()
    if car is None:
        return error_response("خودرو پیدا نشد", 404)
    return success_response({
        "car_id": car.id,
        "car_title": car.title,
        "price": car.price,
        "details": _snapshot_from_car(car),
    })


@admin_router.get("/contracts/{contract_id}")
def admin_show(contract_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = db.query(Contract).options(joinedload(Contract.car)).filter(Contract.id == contract_id).first()
    if item is None:
        return error_response("قرارداد پیدا نشد", 404)
    return success_response(_serialize(item))


@admin_router.post("/contracts")
def admin_create(payload: ContractIn, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    details = payload.details.model_dump(exclude_none=True)

    # اگه به یک خودروی موجود لینک شده، هر فیلدی که کاربر خالی گذاشته رو از
    # روی خودرو پر کن (فیلدهایی که کاربر صریحا مقدار داده دست‌نخورده می‌مونه)
    if payload.car_id:
        car = db.query(Car).options(joinedload(Car.brand), joinedload(Car.category)).filter(Car.id == payload.car_id).first()
        if car is not None:
            for k, v in _snapshot_from_car(car).items():
                details.setdefault(k, v)

    item = Contract(
        car_id=payload.car_id,
        contract_date=payload.contract_date,
        price=payload.price,
        price_text=payload.price_text,
        status=payload.status,
        details=details,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return success_response(_serialize(item), 201)


@admin_router.patch("/contracts/{contract_id}")
def admin_update(contract_id: int, payload: ContractIn, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = db.query(Contract).filter(Contract.id == contract_id).first()
    if item is None:
        return error_response("قرارداد پیدا نشد", 404)

    item.car_id = payload.car_id
    item.contract_date = payload.contract_date
    item.price = payload.price
    item.price_text = payload.price_text
    item.status = payload.status
    item.details = payload.details.model_dump(exclude_none=True)

    db.commit()
    db.refresh(item)
    return success_response(_serialize(item))


@admin_router.delete("/contracts/{contract_id}")
def admin_destroy(contract_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = db.query(Contract).filter(Contract.id == contract_id).first()
    if item is None:
        return error_response("قرارداد پیدا نشد", 404)
    db.delete(item)
    db.commit()
    return success_response({"message": "قرارداد حذف شد"})


@admin_router.get("/contracts/{contract_id}/pdf")
def admin_download_pdf(contract_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = db.query(Contract).filter(Contract.id == contract_id).first()
    if item is None:
        return error_response("قرارداد پیدا نشد", 404)

    pdf_bytes = generate_contract_pdf(item)
    filename = f"carpaz-contract-{item.id:06d}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )
