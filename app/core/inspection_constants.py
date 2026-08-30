"""
Reference values for the car inspection report (برگ کارشناسی خودرو) -
the checklist an expert fills out per car, in the same spirit as
car_constants.py (small fixed vocabularies for validation + building the
admin form).
"""

# Status of a single checklist item. Mirrors the legend on the paper
# inspection form ("راهنمای گزارش"): healthy / has a problem / painted /
# replaced / not inspected or not applicable to this car.
INSPECTION_ITEM_STATUSES: dict[str, str] = {
    "healthy": "سالم",
    "issue": "مشکل دارد",
    "painted": "رنگ‌شدگی",
    "replaced": "تعویض‌شدگی",
    "not_inspected": "کارشناسی نشده / موجود نیست",
}

# Seeds the checklist when an admin starts a new inspection for a car -
# they can add/remove/rename items freely afterwards, this is just a
# sensible starting point matching the standard paper form layout.
DEFAULT_INSPECTION_CHECKLIST: list[dict[str, str]] = [
    {"category": "بدنه", "label": "شاسی جلو", "status": "healthy"},
    {"category": "بدنه", "label": "سینی جلو", "status": "healthy"},
    {"category": "بدنه", "label": "شاسی عقب", "status": "healthy"},
    {"category": "بدنه", "label": "سینی عقب", "status": "healthy"},
    {"category": "فنی، موتور و گیربکس", "label": "فرمان هیدرولیک", "status": "healthy"},
    {"category": "فنی، موتور و گیربکس", "label": "ترمز", "status": "healthy"},
    {"category": "فنی، موتور و گیربکس", "label": "ایربگ", "status": "healthy"},
    {"category": "فنی، موتور و گیربکس", "label": "صفحه کلاچ", "status": "healthy"},
    {"category": "فنی، موتور و گیربکس", "label": "گیربکس اتومات", "status": "healthy"},
    {"category": "فنی، موتور و گیربکس", "label": "گیربکس دنده‌ای", "status": "healthy"},
    {"category": "فنی، موتور و گیربکس", "label": "جلوبندی", "status": "healthy"},
    {"category": "فنی، موتور و گیربکس", "label": "موتور", "status": "healthy"},
    {"category": "فنی، موتور و گیربکس", "label": "نشتی روغن", "status": "healthy"},
    {"category": "فنی، موتور و گیربکس", "label": "تعویض روغن موتور", "status": "healthy"},
    {"category": "فنی، موتور و گیربکس", "label": "دیاق", "status": "healthy"},
    {"category": "فنی، موتور و گیربکس", "label": "روغن سوزی", "status": "healthy"},
    {"category": "فنی، موتور و گیربکس", "label": "تطبیق کارکرد با ظاهر خودرو", "status": "healthy"},
    {"category": "فنی، موتور و گیربکس", "label": "رانندگی، تمیز بودن خودرو و تور گلگیر", "status": "healthy"},
]


def validate_item_status(status: str) -> None:
    if status not in INSPECTION_ITEM_STATUSES:
        allowed = "، ".join(INSPECTION_ITEM_STATUSES.keys())
        raise ValueError(f"وضعیت آیتم باید یکی از این‌ها باشد: {allowed}")
