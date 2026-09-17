from datetime import date, datetime

from fastapi import APIRouter, Depends, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models import PriceGuideEntry, User
from app.models.price_guide import SOURCE_MANUAL, SOURCE_EXCEL, SOURCE_SCRAPER
from app.schemas.price_guide import PriceGuideEntryIn
from app.services.price_guide_import import parse_price_guide_excel, build_price_guide_excel_template
from app.services.price_scraper import fetch_zero_km_prices, PriceScraperError
from app.utils.jalali import format_jalali
from app.utils.pagination import paginate
from app.utils.response import success_response, error_response

router = APIRouter(tags=["price-guide"])
admin_router = APIRouter(prefix="/admin-panel", tags=["admin-price-guide"])


def _serialize(item: PriceGuideEntry) -> dict:
    price_date_dt = datetime.combine(item.price_date, datetime.min.time()) if item.price_date else None
    return {
        "id": item.id,
        "brand": item.brand,
        "model": item.model,
        "trim": item.trim,
        "year": item.year,
        "condition": item.condition,
        "condition_label": "صفر کیلومتر" if item.condition == 0 else "کارکرده",
        "market_price": item.market_price,
        "agency_price": item.agency_price,
        "price_date": item.price_date.isoformat() if item.price_date else None,
        "price_date_jalali": format_jalali(price_date_dt) if price_date_dt else None,
        "source": item.source,
        "updated_at": format_jalali(item.updated_at),
    }


def _upsert(db: Session, data: dict, source: str) -> PriceGuideEntry:
    """اگر ردیفی با همین برند/مدل/تیریم/سال/وضعیت از قبل باشد، قیمتش را به‌روز می‌کند؛ وگرنه ردیف تازه می‌سازد."""
    query = (
        db.query(PriceGuideEntry)
        .filter(
            PriceGuideEntry.brand == data["brand"],
            PriceGuideEntry.model == data["model"],
            PriceGuideEntry.trim == data.get("trim"),
            PriceGuideEntry.year == data.get("year"),
            PriceGuideEntry.condition == data["condition"],
        )
    )
    item = query.first()
    if item is None:
        item = PriceGuideEntry(**data, source=source)
        db.add(item)
    else:
        item.market_price = data.get("market_price", item.market_price)
        item.agency_price = data.get("agency_price", item.agency_price)
        item.price_date = data.get("price_date") or date.today()
        item.source = source
    return item


# ---------------------------------------------------------------------------
# Public - "قیمت روز خودرو" page
# ---------------------------------------------------------------------------

@router.get("/price-guide")
def public_index(
    request: Request,
    page: int = 1,
    brand: str | None = None,
    condition: int | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(PriceGuideEntry).order_by(PriceGuideEntry.brand, PriceGuideEntry.model)
    if brand:
        query = query.filter(PriceGuideEntry.brand == brand)
    if condition is not None:
        query = query.filter(PriceGuideEntry.condition == condition)
    if q:
        like = f"%{q}%"
        query = query.filter((PriceGuideEntry.brand.ilike(like)) | (PriceGuideEntry.model.ilike(like)))

    items, links, meta = paginate(query, request, page, per_page=30)

    brands = [r[0] for r in db.query(PriceGuideEntry.brand).distinct().order_by(PriceGuideEntry.brand).all()]
    last_update = db.query(PriceGuideEntry.updated_at).order_by(PriceGuideEntry.updated_at.desc()).first()

    return success_response({
        "entries": [_serialize(i) for i in items],
        "links": links,
        "meta": meta,
        "brands": brands,
        "last_update": format_jalali(last_update[0]) if last_update else None,
    })


# ---------------------------------------------------------------------------
# Admin panel
# ---------------------------------------------------------------------------

@admin_router.get("/price-guide")
def admin_index(
    request: Request,
    page: int = 1,
    brand: str | None = None,
    condition: int | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    query = db.query(PriceGuideEntry).order_by(PriceGuideEntry.updated_at.desc())
    if brand:
        query = query.filter(PriceGuideEntry.brand == brand)
    if condition is not None:
        query = query.filter(PriceGuideEntry.condition == condition)
    if q:
        like = f"%{q}%"
        query = query.filter((PriceGuideEntry.brand.ilike(like)) | (PriceGuideEntry.model.ilike(like)))

    items, links, meta = paginate(query, request, page, per_page=25)
    return success_response({"entries": [_serialize(i) for i in items], "links": links, "meta": meta})


@admin_router.post("/price-guide")
def admin_create(payload: PriceGuideEntryIn, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    data = payload.model_dump()
    data["price_date"] = data.get("price_date") or date.today()
    item = _upsert(db, data, source=SOURCE_MANUAL)
    db.commit()
    db.refresh(item)
    return success_response(_serialize(item), 201)


@admin_router.patch("/price-guide/{entry_id}")
def admin_update(
    entry_id: int, payload: PriceGuideEntryIn, db: Session = Depends(get_db), _: User = Depends(get_current_admin)
):
    item = db.query(PriceGuideEntry).filter(PriceGuideEntry.id == entry_id).first()
    if item is None:
        return error_response("ردیف پیدا نشد", 404)

    data = payload.model_dump()
    item.brand = data["brand"]
    item.model = data["model"]
    item.trim = data.get("trim")
    item.year = data.get("year")
    item.condition = data["condition"]
    item.market_price = data.get("market_price")
    item.agency_price = data.get("agency_price")
    item.price_date = data.get("price_date") or date.today()
    item.source = SOURCE_MANUAL

    db.commit()
    db.refresh(item)
    return success_response(_serialize(item))


@admin_router.delete("/price-guide/{entry_id}")
def admin_destroy(entry_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = db.query(PriceGuideEntry).filter(PriceGuideEntry.id == entry_id).first()
    if item is None:
        return error_response("ردیف پیدا نشد", 404)
    db.delete(item)
    db.commit()
    return success_response({"message": "ردیف حذف شد"})


@admin_router.get("/price-guide/template")
def admin_download_template(_: User = Depends(get_current_admin)):
    """دانلود یک فایل اکسل نمونه با ستون‌های درست برای آپلود دسته‌جمعی."""
    content = build_price_guide_excel_template()
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=price-guide-template.xlsx"},
    )


@admin_router.post("/price-guide/import")
async def admin_import_excel(
    file: UploadFile = File(...), db: Session = Depends(get_db), _: User = Depends(get_current_admin)
):
    content = await file.read()
    try:
        rows, errors = parse_price_guide_excel(content)
    except Exception as e:  # noqa: BLE001 - فایل بی‌فرمت/خراب
        return error_response({"error": [f"فایل اکسل قابل خواندن نبود: {e}"]}, 422)

    today = date.today()
    for row in rows:
        row["price_date"] = today
        _upsert(db, row, source=SOURCE_EXCEL)
    db.commit()

    return success_response({
        "imported": len(rows),
        "failed": len(errors),
        "errors": errors[:50],  # از سرریز شدن پاسخ با هزاران خطا جلوگیری می‌کند
    })


@admin_router.post("/price-guide/scrape")
def admin_trigger_scrape(source_url: str | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    """
    دریافت خودکار (آزمایشی/best-effort) قیمت روز خودروهای صفر از یک سایت مرجع.
    فقط با کلیک دستی ادمین اجرا می‌شود - هیچ زمان‌بندی خودکاری برایش تنظیم نشده.
    """
    try:
        rows, warnings = fetch_zero_km_prices(source_url) if source_url else fetch_zero_km_prices()
    except PriceScraperError as e:
        return error_response({"error": [str(e)]}, 502)

    today = date.today()
    for row in rows:
        row["price_date"] = today
        _upsert(db, row, source=SOURCE_SCRAPER)
    db.commit()

    return success_response({
        "imported": len(rows),
        "warnings": warnings,
    })
