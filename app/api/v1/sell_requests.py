from datetime import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user
from app.db.session import get_db
from app.models import SellRequest, User
from app.schemas.sell_request import SellRequestIn, SellRequestStatusIn
from app.utils.jalali import format_jalali
from app.utils.pagination import paginate
from app.utils.response import success_response, error_response

router = APIRouter(tags=["sell-requests"])
admin_router = APIRouter(prefix="/admin-panel", tags=["admin-sell-requests"])

# status values
STATUS_LIST = {
    0: {"label": "در انتظار بررسی", "color": "secondary", "icon": "clock"},
    1: {"label": "تماس گرفته شد", "color": "info", "icon": "phone"},
    2: {"label": "پذیرفته شد", "color": "success", "icon": "check-circle"},
    3: {"label": "رد شد", "color": "danger", "icon": "x-circle"},
}

ALLOWED_TRANSITIONS = {
    0: [1, 3],
    1: [2, 3],
    2: [],
    3: [],
}


def _serialize(item: SellRequest) -> dict:
    status_info = STATUS_LIST.get(item.status, {"label": "نامشخص", "color": "secondary", "icon": "question"})
    return {
        "id": item.id,
        "full_name": item.full_name,
        "car_type": item.car_type,
        "car_model": item.car_model,
        "phone": item.phone,
        "status": item.status,
        "status_label": status_info["label"],
        "status_color": status_info["color"],
        "status_icon": status_info["icon"],
        "allowed_transitions": [
            {"value": s, "label": STATUS_LIST[s]["label"], "color": STATUS_LIST[s]["color"], "icon": STATUS_LIST[s]["icon"]}
            for s in ALLOWED_TRANSITIONS.get(item.status, [])
        ],
        "admin_notes": item.admin_notes,
        "is_seen": item.seen_at is not None,
        "seen_at": format_jalali(item.seen_at) if item.seen_at else None,
        "created_at": format_jalali(item.created_at),
    }


# ---------------------------------------------------------------------------
# Public - anyone can submit, no login required (same as contact-us)
# ---------------------------------------------------------------------------

@router.post("/sell-requests")
def create_sell_request(
    payload: SellRequestIn, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    item = SellRequest(
        full_name=payload.full_name,
        car_type=payload.car_type,
        car_model=payload.car_model,
        phone=payload.phone,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return success_response(_serialize(item), 201)


# ---------------------------------------------------------------------------
# Admin panel
# ---------------------------------------------------------------------------

@admin_router.get("/sell-requests")
def admin_index(
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    query = db.query(SellRequest).order_by(SellRequest.created_at.desc())
    items, links, meta = paginate(query, request, page, per_page=15)
    unseen_count = db.query(SellRequest).filter(SellRequest.seen_at.is_(None)).count()
    return success_response(
        {
            "sell_requests": [_serialize(i) for i in items],
            "links": links,
            "meta": meta,
            "status_list": STATUS_LIST,
            "unseen_count": unseen_count,
        }
    )


@admin_router.get("/sell-requests/{request_id}")
def admin_show(request_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = db.query(SellRequest).filter(SellRequest.id == request_id).first()
    if item is None:
        return error_response("درخواست پیدا نشد", 404)

    # first time it's opened by an admin, mark it as seen
    if item.seen_at is None:
        item.seen_at = datetime.utcnow()
        db.commit()
        db.refresh(item)

    return success_response(_serialize(item))


@admin_router.patch("/sell-requests/{request_id}/status")
def admin_update_status(
    request_id: int,
    payload: SellRequestStatusIn,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    item = db.query(SellRequest).filter(SellRequest.id == request_id).first()
    if item is None:
        return error_response("درخواست پیدا نشد", 404)

    if payload.status != item.status and payload.status not in ALLOWED_TRANSITIONS.get(item.status, []):
        allowed_labels = "، ".join(STATUS_LIST[s]["label"] for s in ALLOWED_TRANSITIONS.get(item.status, []))
        return error_response(
            {"error": [f"این درخواست فقط می‌تواند به این وضعیت‌ها منتقل شود: {allowed_labels}"]}, 422
        )

    item.status = payload.status
    if payload.admin_notes is not None:
        item.admin_notes = payload.admin_notes
    if item.seen_at is None:
        item.seen_at = datetime.utcnow()

    db.commit()
    db.refresh(item)
    return success_response(_serialize(item))


@admin_router.delete("/sell-requests/{request_id}")
def admin_destroy(request_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = db.query(SellRequest).filter(SellRequest.id == request_id).first()
    if item is None:
        return error_response("درخواست پیدا نشد", 404)
    db.delete(item)
    db.commit()
    return success_response({"message": "درخواست حذف شد"})
