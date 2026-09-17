from datetime import datetime

from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_admin
from app.core.car_constants import STANDARD_COLORS, TRANSMISSION_TYPES, FUEL_TYPES, validate_color
from app.db.session import get_db
from app.models import Car, CarImage, Category, Brand, User, Inquiry
from app.services.slug import make_unique_car_slug
from app.services.storage import save_upload, image_url
from app.utils.pagination import paginate
from app.utils.response import success_response, error_response

router = APIRouter(tags=["cars"])
admin_router = APIRouter(prefix="/admin-panel", tags=["admin-cars"])

IMAGE_SUBDIR = "cars"

STATUS_LABELS = {0: "غیر فعال", 1: "فعال"}
CONDITION_LABELS = {0: "کارکرده", 1: "نو"}


def _with_relations(query):
    return query.options(
        joinedload(Car.images),
        joinedload(Car.brand),
    )


def _serialize_car(car: Car) -> dict:
    return {
        "id": car.id,
        "title": car.title,
        "slug": car.slug,
        "brand": car.brand.name if car.brand else None,
        "brand_id": car.brand_id,
        "category": car.category.name if car.category else None,
        "category_id": car.category_id,
        "model_name": car.model_name,
        "model_year": car.model_year,
        "car_model_id": car.car_model_id,
        "car_trim_id": car.car_trim_id,
        "condition_value": car.condition,
        "condition": CONDITION_LABELS.get(car.condition, car.condition),
        "mileage_km": car.mileage_km,
        "vin": car.vin,
        "color": car.color,
        "color_code": car.color_code,
        "transmission": car.transmission,
        "transmission_label": TRANSMISSION_TYPES.get(car.transmission, car.transmission),
        "fuel_type": car.fuel_type,
        "fuel_type_label": FUEL_TYPES.get(car.fuel_type, car.fuel_type),
        "chassis_healthy": car.chassis_healthy,
        "body_healthy": car.body_healthy,
        "primary_image": image_url(car.primary_image, IMAGE_SUBDIR),
        "status_value": car.status,
        "status": STATUS_LABELS.get(car.status, car.status),
        "description": car.description,
        "price": car.price,
        "sale_price": car.sale_price or 0,
        "effective_price": car.effective_price,
        "date_on_sale_from": car.date_on_sale_from,
        "date_on_sale_to": car.date_on_sale_to,
        "images": [
            {"id": img.id, "car_id": img.car_id, "primary_image": image_url(img.image, IMAGE_SUBDIR)}
            for img in car.images
        ],
    }


# ---------------------------------------------------------------------------
# Public
# ---------------------------------------------------------------------------

@router.get("/cars")
def list_cars(request: Request, page: int = 1, db: Session = Depends(get_db)):
    query = _with_relations(db.query(Car)).order_by(Car.created_at.desc())
    items, links, meta = paginate(query, request, page, per_page=6)
    return success_response({"cars": [_serialize_car(c) for c in items], "links": links, "meta": meta})


@router.get("/cars/sitemap")
def cars_sitemap(db: Session = Depends(get_db)):
    """
    فهرست سبک همه‌ی آگهی‌ها (فقط slug و تاریخ آخرین ویرایش) بدون صفحه‌بندی -
    برای ساخت sitemap.xml در فرانت، نه برای نمایش به کاربر.
    """
    rows = db.query(Car.slug, Car.updated_at).order_by(Car.updated_at.desc()).all()
    return success_response([{"slug": r.slug, "updated_at": r.updated_at.isoformat()} for r in rows])


@router.get("/random-cars")
def random_cars(count: int, db: Session = Depends(get_db)):
    cars = _with_relations(db.query(Car)).order_by(func.rand()).limit(count).all()
    return success_response([_serialize_car(c) for c in cars])


@router.get("/menu")
def menu(
    request: Request,
    page: int = 1,
    category: int | None = None,
    brand: int | None = None,
    condition: str | None = None,  # "new" or "used"
    year_min: int | None = None,
    year_max: int | None = None,
    transmission: str | None = None,
    fuel_type: str | None = None,
    chassis_healthy: bool | None = None,
    body_healthy: bool | None = None,
    color: str | None = None,
    sort_by: str | None = None,
    search: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    db: Session = Depends(get_db),
):
    query = _with_relations(db.query(Car))

    if category is not None:
        query = query.filter(Car.category_id == category)

    if brand is not None:
        query = query.filter(Car.brand_id == brand)

    if condition in ("new", "used"):
        query = query.filter(Car.condition == (1 if condition == "new" else 0))

    if year_min is not None:
        query = query.filter(Car.model_year >= year_min)
    if year_max is not None:
        query = query.filter(Car.model_year <= year_max)

    if transmission in TRANSMISSION_TYPES:
        query = query.filter(Car.transmission == transmission)

    if fuel_type in FUEL_TYPES:
        query = query.filter(Car.fuel_type == fuel_type)

    if chassis_healthy is not None:
        query = query.filter(Car.chassis_healthy == chassis_healthy)

    if body_healthy is not None:
        query = query.filter(Car.body_healthy == body_healthy)

    if color:
        query = query.filter(Car.color == color)

    if search and search.strip():
        query = query.filter(Car.title.ilike(f"%{search.strip()}%"))

    if price_min is not None:
        query = query.filter(Car.price >= price_min)
    if price_max is not None:
        query = query.filter(Car.price <= price_max)

    if sort_by == "max":
        query = query.order_by(Car.price.desc())
    elif sort_by == "min":
        query = query.order_by(Car.price.asc())
    elif sort_by == "newest":
        query = query.order_by(Car.created_at.desc())
    elif sort_by == "year_new":
        query = query.order_by(Car.model_year.desc())
    elif sort_by == "year_old":
        query = query.order_by(Car.model_year.asc())
    elif sort_by == "mileage":
        query = query.order_by(Car.mileage_km.asc())
    elif sort_by == "bestseller":
        # rank by closed deals - ties fall back to newest first. Sold cars
        # are deleted, so this only reflects deals closed while the car
        # still existed as a row (i.e. it's really "most inquired-about
        # among currently listed cars" more than a historical sales count).
        sold = (
            db.query(Inquiry.car_id, func.count(Inquiry.id).label("sold"))
            .filter(Inquiry.status == 4)  # deal closed / sold
            .group_by(Inquiry.car_id)
            .subquery()
        )
        query = query.outerjoin(sold, sold.c.car_id == Car.id).order_by(
            func.coalesce(sold.c.sold, 0).desc(), Car.created_at.desc()
        )
    else:
        query = query.order_by(Car.created_at.desc())

    items, links, meta = paginate(query, request, page, per_page=6)
    return success_response({"cars": [_serialize_car(c) for c in items], "links": links, "meta": meta})


@router.get("/filter-options")
def filter_options(db: Session = Depends(get_db)):
    """
    Metadata to populate a car-listing filter sidebar: categories/brands
    (with how many cars each has), the overall price/year range, and the
    standard colors that actually appear on a listed car - so the UI only
    ever offers filters that can return results.
    """
    categories = (
        db.query(Category.id, Category.name, Category.parent_id, Category.image, func.count(Car.id).label("count"))
        .outerjoin(Car, Car.category_id == Category.id)
        .group_by(Category.id, Category.name, Category.parent_id, Category.image)
        .order_by(Category.name)
        .all()
    )

    brands = (
        db.query(Brand.id, Brand.name, Brand.logo, func.count(Car.id).label("count"))
        .outerjoin(Car, Car.brand_id == Brand.id)
        .group_by(Brand.id, Brand.name, Brand.logo)
        .order_by(Brand.name)
        .all()
    )

    price_row = db.query(func.min(Car.price), func.max(Car.price)).first()
    price_min, price_max = price_row if price_row else (0, 0)

    year_row = db.query(func.min(Car.model_year), func.max(Car.model_year)).first()
    year_min, year_max = year_row if year_row else (0, 0)

    colors_in_use = {name for (name,) in db.query(Car.color).distinct().all()}

    return success_response({
        "categories": [
            {
                "id": c.id,
                "name": c.name,
                "parent_id": c.parent_id,
                "image": image_url(c.image, "categories"),
                "car_count": c.count,
            }
            for c in categories
        ],
        "brands": [
            {"id": b.id, "name": b.name, "logo": image_url(b.logo, "brands"), "car_count": b.count}
            for b in brands
        ],
        "price_range": {"min": price_min or 0, "max": price_max or 0},
        "year_range": {"min": year_min or 0, "max": year_max or 0},
        "colors": [
            {"name": name, "color_code": STANDARD_COLORS[name]}
            for name in STANDARD_COLORS
            if name in colors_in_use
        ],
        "conditions": [{"value": 1, "label": "نو"}, {"value": 0, "label": "کارکرده"}],
        "transmissions": [{"value": k, "label": v} for k, v in TRANSMISSION_TYPES.items()],
        "fuel_types": [{"value": k, "label": v} for k, v in FUEL_TYPES.items()],
        "chassis_body_options": [
            {"value": True, "label": "سالم"},
            {"value": False, "label": "دارای آسیب/تعویض/رنگ‌شدگی"},
        ],
    })


@router.get("/cars/{slug}")
def show_car(slug: str, db: Session = Depends(get_db)):
    car = _with_relations(db.query(Car)).filter(Car.slug == slug).first()
    if car is None:
        return error_response("خودرو پیدا نشد", 404)
    return success_response(_serialize_car(car))


# ---------------------------------------------------------------------------
# Admin panel
# ---------------------------------------------------------------------------

@admin_router.get("/cars")
def admin_index(request: Request, page: int = 1, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    query = _with_relations(db.query(Car)).order_by(Car.created_at.desc())
    items, links, meta = paginate(query, request, page, per_page=6)
    return success_response({"cars": [_serialize_car(c) for c in items], "links": links, "meta": meta})


@admin_router.post("/cars")
def admin_store(
    title: str = Form(...),
    brand_id: int = Form(...),
    category_id: int = Form(...),
    model_name: str = Form(...),
    model_year: int = Form(...),
    car_model_id: int | None = Form(None),
    car_trim_id: int | None = Form(None),
    condition: int = Form(1),
    mileage_km: int = Form(0),
    vin: str | None = Form(None),
    color: str = Form(...),
    price: int = Form(...),
    transmission: str = Form("manual"),
    fuel_type: str = Form("gasoline"),
    chassis_healthy: bool = Form(True),
    body_healthy: bool = Form(True),
    description: str = Form(...),
    status: int = Form(1),
    primary_image: UploadFile = File(...),
    images: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    if transmission not in TRANSMISSION_TYPES:
        return error_response({"transmission": [f"باید یکی از این‌ها باشد: {', '.join(TRANSMISSION_TYPES)}"]}, 422)
    if fuel_type not in FUEL_TYPES:
        return error_response({"fuel_type": [f"باید یکی از این‌ها باشد: {', '.join(FUEL_TYPES)}"]}, 422)
    try:
        color_code = validate_color(color)
    except ValueError as e:
        return error_response({"color": [str(e)]}, 422)

    primary_image_name = save_upload(primary_image, IMAGE_SUBDIR)

    car = Car(
        title=title,
        slug=make_unique_car_slug(db, title),
        brand_id=brand_id,
        category_id=category_id,
        model_name=model_name,
        model_year=model_year,
        car_model_id=car_model_id,
        car_trim_id=car_trim_id,
        condition=condition,
        mileage_km=mileage_km,
        vin=vin or None,
        color=color,
        color_code=color_code,
        price=price,
        transmission=transmission,
        fuel_type=fuel_type,
        chassis_healthy=chassis_healthy,
        body_healthy=body_healthy,
        primary_image=primary_image_name,
        primary_image_blur_data_url="",
        description=description,
        status=status,
    )
    db.add(car)
    db.flush()  # get car.id before adding children

    for image in images or []:
        db.add(CarImage(car_id=car.id, image=save_upload(image, IMAGE_SUBDIR)))

    db.commit()
    db.refresh(car)
    car = _with_relations(db.query(Car)).filter(Car.id == car.id).first()
    return success_response(_serialize_car(car), 201)


@admin_router.get("/cars/{car_id}")
def admin_show(car_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    car = _with_relations(db.query(Car)).filter(Car.id == car_id).first()
    if car is None:
        return error_response("خودرو پیدا نشد", 404)
    return success_response(_serialize_car(car))


@admin_router.put("/cars/{car_id}")
@admin_router.post("/cars/{car_id}")
def admin_update(
    car_id: int,
    title: str = Form(...),
    brand_id: int = Form(...),
    category_id: int = Form(...),
    model_name: str = Form(...),
    model_year: int = Form(...),
    car_model_id: int | None = Form(None),
    car_trim_id: int | None = Form(None),
    condition: int = Form(1),
    mileage_km: int = Form(0),
    vin: str | None = Form(None),
    color: str | None = Form(None),
    price: int | None = Form(None),
    transmission: str | None = Form(None),
    fuel_type: str | None = Form(None),
    chassis_healthy: bool | None = Form(None),
    body_healthy: bool | None = Form(None),
    description: str = Form(...),
    status: int = Form(1),
    sale_price: int | None = Form(None),
    date_on_sale_from: str | None = Form(None),
    date_on_sale_to: str | None = Form(None),
    primary_image: UploadFile | None = File(None),
    images: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Accepts both PUT and POST (some clients spoof PUT via a _method form field)."""
    car = db.query(Car).filter(Car.id == car_id).first()
    if car is None:
        return error_response("خودرو پیدا نشد", 404)

    if transmission is not None and transmission not in TRANSMISSION_TYPES:
        return error_response({"transmission": [f"باید یکی از این‌ها باشد: {', '.join(TRANSMISSION_TYPES)}"]}, 422)
    if fuel_type is not None and fuel_type not in FUEL_TYPES:
        return error_response({"fuel_type": [f"باید یکی از این‌ها باشد: {', '.join(FUEL_TYPES)}"]}, 422)
    if color is not None:
        try:
            car.color_code = validate_color(color)
        except ValueError as e:
            return error_response({"color": [str(e)]}, 422)
        car.color = color

    if primary_image is not None:
        car.primary_image = save_upload(primary_image, IMAGE_SUBDIR)

    if title != car.title:
        car.slug = make_unique_car_slug(db, title)
    car.title = title
    car.brand_id = brand_id
    car.category_id = category_id
    car.model_name = model_name
    car.model_year = model_year
    car.car_model_id = car_model_id
    car.car_trim_id = car_trim_id
    car.condition = condition
    car.mileage_km = mileage_km
    car.vin = vin or None
    if transmission is not None:
        car.transmission = transmission
    if fuel_type is not None:
        car.fuel_type = fuel_type
    if chassis_healthy is not None:
        car.chassis_healthy = chassis_healthy
    if body_healthy is not None:
        car.body_healthy = body_healthy
    car.description = description
    car.status = status
    if price is not None:
        car.price = price
    if sale_price is not None:
        car.sale_price = sale_price
    if date_on_sale_from:
        car.date_on_sale_from = datetime.fromisoformat(date_on_sale_from)
    if date_on_sale_to:
        car.date_on_sale_to = datetime.fromisoformat(date_on_sale_to)

    if images:
        for old_image in list(car.images):
            db.delete(old_image)
        db.flush()
        for image in images:
            db.add(CarImage(car_id=car.id, image=save_upload(image, IMAGE_SUBDIR)))

    db.commit()
    car = _with_relations(db.query(Car)).filter(Car.id == car_id).first()
    return success_response(_serialize_car(car))


@admin_router.delete("/cars/{car_id}")
def admin_destroy(car_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    """
    Manual removal (e.g. a listing pulled for reasons other than a sale -
    duplicate, seller changed their mind, etc). Selling a car through the
    normal flow happens via PATCH .../inquiries/{id}/status instead, which
    deletes the car itself once the deal is marked closed.
    """
    car = db.query(Car).filter(Car.id == car_id).first()
    if car is None:
        return error_response("خودرو پیدا نشد", 404)
    db.delete(car)
    db.commit()
    return success_response({"data": ["deleted"]})
