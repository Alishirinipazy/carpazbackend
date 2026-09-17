from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import Brand, CarModel, CarTrim, User
from app.schemas.car_catalog import CarModelIn, CarTrimIn
from app.services.slug import slugify
from app.utils.response import success_response, error_response

router = APIRouter(tags=["car-catalog"])
admin_router = APIRouter(prefix="/admin-panel", tags=["admin-car-catalog"])


def _build_tree(db: Session) -> list[dict]:
    """
    درخت کامل برند → مدل → تیریم - برای مگامنو/سلکتور استفاده می‌شه.
    تعداد ردیف‌ها معمولاً کوچیکه (چند صد تا)، پس یک‌جا لود کردن مشکلی نداره.
    """
    brands = (
        db.query(Brand)
        .options(joinedload(Brand.models).joinedload(CarModel.trims))
        .order_by(Brand.name)
        .all()
    )
    return [
        {
            "id": b.id,
            "name": b.name,
            "slug": b.slug,
            "logo": f"/storage/images/brands/{b.logo}" if b.logo else None,
            "models": [
                {
                    "id": m.id,
                    "name": m.name,
                    "slug": m.slug,
                    "trims": [{"id": t.id, "name": t.name} for t in m.trims],
                }
                for m in sorted(b.models, key=lambda m: m.name)
            ],
        }
        for b in brands
    ]


@router.get("/car-catalog")
def public_tree(db: Session = Depends(get_db)):
    return success_response(_build_tree(db))


@router.get("/car-catalog/search")
def public_search(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """
    جستجوی مسطح روی برند/مدل/تیریم - برای اتوکامپلیت. هر نتیجه شامل
    مسیر کامل (برند > مدل > تیریم) هست تا در فهرست جستجو خوانا باشه.
    """
    like = f"%{q}%"
    results = []

    models = (
        db.query(CarModel)
        .join(Brand)
        .options(joinedload(CarModel.brand), joinedload(CarModel.trims))
        .filter((CarModel.name.ilike(like)) | (Brand.name.ilike(like)))
        .order_by(Brand.name, CarModel.name)
        .limit(30)
        .all()
    )
    for m in models:
        results.append({
            "type": "model",
            "brand_id": m.brand.id,
            "brand_name": m.brand.name,
            "model_id": m.id,
            "model_name": m.name,
            "trim_id": None,
            "trim_name": None,
            "label": f"{m.brand.name} > {m.name}",
        })
        for t in m.trims:
            # چون مدل match شده، تیریم‌هاش هم به‌عنوان نتیجه‌ی جدا نشون داده می‌شن
            results.append({
                "type": "trim",
                "brand_id": m.brand.id,
                "brand_name": m.brand.name,
                "model_id": m.id,
                "model_name": m.name,
                "trim_id": t.id,
                "trim_name": t.name,
                "label": f"{m.brand.name} > {m.name} > {t.name}",
            })

    return success_response(results[:40])


# ---------------------------------------------------------------------------
# Admin panel
# ---------------------------------------------------------------------------

@admin_router.get("/car-catalog")
def admin_tree(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return success_response(_build_tree(db))


@admin_router.post("/car-models")
def admin_create_model(payload: CarModelIn, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    brand = db.query(Brand).filter(Brand.id == payload.brand_id).first()
    if brand is None:
        return error_response("برند پیدا نشد", 404)

    item = CarModel(brand_id=payload.brand_id, name=payload.name, slug=slugify(f"{brand.name}-{payload.name}"))
    db.add(item)
    db.commit()
    db.refresh(item)
    return success_response({"id": item.id, "name": item.name, "brand_id": item.brand_id}, 201)


@admin_router.patch("/car-models/{model_id}")
def admin_update_model(model_id: int, payload: CarModelIn, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = db.query(CarModel).filter(CarModel.id == model_id).first()
    if item is None:
        return error_response("مدل پیدا نشد", 404)
    item.name = payload.name
    item.brand_id = payload.brand_id
    db.commit()
    return success_response({"id": item.id, "name": item.name, "brand_id": item.brand_id})


@admin_router.delete("/car-models/{model_id}")
def admin_delete_model(model_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = db.query(CarModel).filter(CarModel.id == model_id).first()
    if item is None:
        return error_response("مدل پیدا نشد", 404)
    db.delete(item)
    db.commit()
    return success_response({"message": "مدل حذف شد"})


@admin_router.post("/car-trims")
def admin_create_trim(payload: CarTrimIn, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    model = db.query(CarModel).filter(CarModel.id == payload.model_id).first()
    if model is None:
        return error_response("مدل پیدا نشد", 404)

    item = CarTrim(model_id=payload.model_id, name=payload.name)
    db.add(item)
    db.commit()
    db.refresh(item)
    return success_response({"id": item.id, "name": item.name, "model_id": item.model_id}, 201)


@admin_router.patch("/car-trims/{trim_id}")
def admin_update_trim(trim_id: int, payload: CarTrimIn, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = db.query(CarTrim).filter(CarTrim.id == trim_id).first()
    if item is None:
        return error_response("تیریم پیدا نشد", 404)
    item.name = payload.name
    item.model_id = payload.model_id
    db.commit()
    return success_response({"id": item.id, "name": item.name, "model_id": item.model_id})


@admin_router.delete("/car-trims/{trim_id}")
def admin_delete_trim(trim_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = db.query(CarTrim).filter(CarTrim.id == trim_id).first()
    if item is None:
        return error_response("تیریم پیدا نشد", 404)
    db.delete(item)
    db.commit()
    return success_response({"message": "تیریم حذف شد"})
