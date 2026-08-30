"""
Seeds the `brands` table.

Two sources, in order:

1. STATIC_BRANDS below - a curated list of car brands actually sold/common
   in the Iranian market (domestic + the most common imports). Always
   available, no network needed.

2. --from-divar - best-effort fetch from Divar's internal car-brand
   hierarchy endpoint. IMPORTANT: this sandbox has no outbound network
   access and Divar's robots.txt blocks automated fetches, so this path
   has NOT been run or verified against a real response. It's written
   defensively (tries a few response shapes) and prints what it finds
   before touching the DB, but you should run it yourself and sanity
   check the printed brand names before confirming the DB write. If the
   endpoint's shape doesn't match, use --dump-only to inspect the raw
   JSON and adjust `_extract_brand_names()` accordingly.

Idempotent: looks up by name before inserting.

Usage:
    cd fastapi-project
    python -m scripts.seed_brands                  # static list only
    python -m scripts.seed_brands --from-divar      # static list + Divar (best-effort)
    python -m scripts.seed_brands --from-divar --dump-only   # just print Divar's raw JSON, no DB writes
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models import Brand
from app.services.slug import make_unique_brand_slug

DIVAR_URL = "https://api.divar.ir/v8/w/lazy-multi-select-hierarchy-options"

# Curated for the Iranian market: domestic manufacturers + the imported
# brands that actually show up on Divar/Bama car listings regularly.
STATIC_BRANDS: list[str] = [
    # domestic
    "ایران خودرو", "سایپا", "پارس خودرو", "بهمن موتور", "کرمان موتور",
    "مدیران خودرو", "رامک خودرو",
    # French (locally assembled historically + imported)
    "پژو", "رنو", "سیتروئن",
    # Korean
    "کیا", "هیوندای", "دوو",
    # Japanese
    "تویوتا", "هوندا", "نیسان", "مزدا", "میتسوبیشی", "سوزوکی",
    # Chinese (very common in the current Iranian market)
    "چری", "جک", "MVM", "بریلیانس", "گریت وال", "چانگان", "لیفان",
    "جیلی", "فوتون", "هاوال", "بایک",
    # German / other European (mostly used-import segment)
    "بی‌ام‌و", "مرسدس‌بنز", "فولکس‌واگن", "آئودی", "اپل",
    # American
    "فورد", "شورولت", "جیپ",
]


def seed_static(db) -> int:
    added = 0
    for name in STATIC_BRANDS:
        if db.query(Brand).filter(Brand.name == name).first():
            continue
        db.add(Brand(name=name, slug=make_unique_brand_slug(db, name)))
        added += 1
    db.commit()
    return added


def _extract_brand_names(payload) -> list[str]:
    """
    Best-effort extraction of brand/manufacturer names out of whatever
    Divar's hierarchy endpoint returns. UNVERIFIED - written to handle a
    few plausible shapes (a flat list of {"title"/"name": ...} options, or
    a nested {"children"/"options": [...]} tree) since the exact schema
    couldn't be confirmed from here. Adjust this if it doesn't match what
    --dump-only shows you.
    """
    names: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            title = node.get("title") or node.get("name") or node.get("label")
            if isinstance(title, str) and title.strip():
                names.append(title.strip())
            for key in ("children", "options", "items", "data"):
                if key in node:
                    walk(node[key])
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    # de-duplicate, keep order
    seen = set()
    unique = []
    for n in names:
        if n not in seen:
            seen.add(n)
            unique.append(n)
    return unique


def fetch_divar_brands(dump_only: bool) -> list[str]:
    import httpx

    # The exact request body is unconfirmed (undocumented internal API) -
    # try a plain GET first, then a couple of common POST shapes used by
    # Divar's category/field endpoints if GET is rejected.
    attempts = [
        ("GET", {}),
        ("POST", {"json": {"category_slug": "light"}}),
        ("POST", {"json": {}}),
    ]

    last_error = None
    for method, kwargs in attempts:
        try:
            response = httpx.request(method, DIVAR_URL, timeout=15.0, **kwargs)
            response.raise_for_status()
            payload = response.json()
            if dump_only:
                print(json.dumps(payload, ensure_ascii=False, indent=2)[:5000])
                return []
            names = _extract_brand_names(payload)
            if names:
                return names
        except Exception as e:  # noqa: BLE001 - best-effort, report and move on
            last_error = e
            continue

    print(f"Could not get a usable response from Divar: {last_error}")
    print("Run with --dump-only to inspect whatever came back, or add the brands manually.")
    return []


def main():
    dump_only = "--dump-only" in sys.argv
    from_divar = "--from-divar" in sys.argv or dump_only

    db = SessionLocal()
    try:
        if from_divar:
            names = fetch_divar_brands(dump_only)
            if dump_only:
                return
            print(f"Divar returned {len(names)} candidate brand name(s).")
            added = 0
            for name in names:
                if db.query(Brand).filter(Brand.name == name).first():
                    continue
                db.add(Brand(name=name, slug=make_unique_brand_slug(db, name)))
                added += 1
            db.commit()
            print(f"Added {added} brand(s) from Divar.")

        added = seed_static(db)
        print(f"Added {added} brand(s) from the static list.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
