import json

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Car, Brand, Favorite, User
from app.services.storage import image_url

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
GAPGPT_URL = "https://api.gapgpt.app/v1/chat/completions"
IMAGE_SUBDIR = "cars"
MAX_TOOL_ROUNDS = 5

SYSTEM_PROMPT = """\
اسم تو پازیه، دستیار فروش هوشمند نمایشگاه خودرو. وظیفه‌ات کمک به مشتری برای پیدا کردن خودروی نو یا کارکرده مناسب و ثبت درخواست خریده.

قوانین مهم:
- هیچ‌وقت قیمت، کارکرد، رنگ یا موجودی رو از خودت نساز - همیشه از ابزارهای search_cars یا get_car_details استفاده کن و فقط بر اساس نتیجه‌شون جواب بده.
- اگه چیزی توی نتایج جستجو پیدا نشد، صادقانه بگو که همچین خودرویی نداریم؛ خودروی جایگزین پیشنهاد بده اگه مرتبط بود.
- بین خودروی نو و کارکرده تمایز قائل باش: برای کارکرده حتماً کارکرد (کیلومتر) و سال ساخت رو ذکر کن.
- این فروشگاه پرداخت آنلاین نداره - فقط می‌تونی خودرو رو ذخیره کنی (علاقه‌مندی) یا کمک کنی مشتری درخواست خرید/بازدید ثبت کنه تا یک کارشناس فروش باهاش تماس بگیره. هیچ‌وقت وانمود نکن که خودرو نهایی فروخته شده یا پرداختی انجام شده.
- اگه مشتری خواست درخواست خرید ثبت کنه، حتماً اول نام و شماره تماسش رو بپرس (اگه نداری)، بعد از ابزار create_inquiry استفاده کن.
- اگه ابزار add_to_favorites یا create_inquiry جواب داد که کاربر لاگین نیست، بهش بگو باید اول وارد حساب کاربریش بشه.
- همیشه به فارسی و خودمونی ولی محترمانه جواب بده. کوتاه و مفید باش (حداکثر چند جمله)، از توضیحات اضافی خودداری کن.
- اگه سوال کاملاً خارج از حوزه خودرو بود، مودبانه برگرد به موضوع اصلی.
"""

TOOLS = [
    {
        "name": "search_cars",
        "description": "جستجوی خودروها بر اساس متن آزاد، برند، دسته‌بندی، وضعیت (نو/کارکرده)، سال ساخت یا سقف قیمت. همیشه قبل از معرفی هر خودرویی این رو صدا بزن.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "متن جستجو، مثلا 'پژو 207' یا خالی برای همه"},
                "brand": {"type": "string", "description": "نام برند، اختیاری"},
                "condition": {"type": "string", "enum": ["new", "used"], "description": "نو یا کارکرده، اختیاری"},
                "transmission": {"type": "string", "enum": ["manual", "automatic", "cvt"], "description": "نوع گیربکس، اختیاری"},
                "fuel_type": {"type": "string", "enum": ["gasoline", "dual", "diesel", "hybrid", "electric"], "description": "نوع سوخت، اختیاری"},
                "max_price": {"type": "integer", "description": "سقف قیمت به تومان، اختیاری"},
            },
        },
    },
    {
        "name": "get_car_details",
        "description": "گرفتن جزئیات کامل یک خودرو (رنگ‌ها، قیمت، کارکرد، سال ساخت و موجودی) با slug خودرو که از search_cars به‌دست میاد.",
        "input_schema": {
            "type": "object",
            "properties": {"slug": {"type": "string"}},
            "required": ["slug"],
        },
    },
    {
        "name": "add_to_favorites",
        "description": "ذخیره یک خودرو در لیست علاقه‌مندی‌های کاربر لاگین‌کرده.",
        "input_schema": {
            "type": "object",
            "properties": {"car_id": {"type": "integer"}},
            "required": ["car_id"],
        },
    },
    {
        "name": "create_inquiry",
        "description": "ثبت درخواست خرید/بازدید یک خودرو برای کاربر لاگین‌کرده، تا کارشناس فروش باهاش تماس بگیره.",
        "input_schema": {
            "type": "object",
            "properties": {
                "car_id": {"type": "integer"},
                "full_name": {"type": "string"},
                "phone": {"type": "string"},
                "message": {"type": "string"},
            },
            "required": ["car_id", "full_name", "phone"],
        },
    },
]


def _run_search_cars(db: Session, args: dict) -> dict:
    query = db.query(Car).filter(Car.status == 1)

    if args.get("query"):
        query = query.filter(Car.title.ilike(f"%{args['query'].strip()}%"))
    if args.get("brand"):
        query = query.join(Car.brand).filter(Brand.name.ilike(f"%{args['brand']}%"))
    if args.get("condition"):
        query = query.filter(Car.condition == (1 if args["condition"] == "new" else 0))
    if args.get("transmission"):
        query = query.filter(Car.transmission == args["transmission"])
    if args.get("fuel_type"):
        query = query.filter(Car.fuel_type == args["fuel_type"])
    if args.get("max_price"):
        query = query.filter(Car.price <= args["max_price"])

    cars = query.limit(8).all()
    return {
        "results": [
            {
                "id": c.id,
                "slug": c.slug,
                "title": c.title,
                "condition": c.condition_label,
                "model_year": c.model_year,
                "mileage_km": c.mileage_km,
                "price": c.effective_price,
                "color": c.color,
                "image": image_url(c.primary_image, IMAGE_SUBDIR),
            }
            for c in cars
        ]
    }


def _run_get_car_details(db: Session, args: dict) -> dict:
    car = db.query(Car).filter(Car.slug == args.get("slug", "")).first()
    if car is None:
        return {"error": "خودرو با این slug پیدا نشد"}

    return {
        "id": car.id,
        "slug": car.slug,
        "title": car.title,
        "brand": car.brand.name if car.brand else None,
        "model_name": car.model_name,
        "model_year": car.model_year,
        "condition": car.condition_label,
        "mileage_km": car.mileage_km,
        "color": car.color,
        "price": car.effective_price,
        "transmission": car.transmission,
        "fuel_type": car.fuel_type,
        "chassis_healthy": car.chassis_healthy,
        "body_healthy": car.body_healthy,
        "description": car.description,
        "image": image_url(car.primary_image, IMAGE_SUBDIR),
    }


def _run_add_to_favorites(db: Session, current_user: User | None, args: dict) -> dict:
    if current_user is None:
        return {"error": "login_required", "message": "برای ذخیره خودرو باید وارد حساب کاربری بشید"}

    car = db.query(Car).filter(Car.id == args.get("car_id")).first()
    if car is None:
        return {"error": "خودروی انتخاب‌شده معتبر نیست"}

    existing = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id, Favorite.car_id == car.id)
        .first()
    )
    if existing is None:
        db.add(Favorite(user_id=current_user.id, car_id=car.id))
        db.commit()

    return {"success": True, "message": "به لیست علاقه‌مندی‌ها اضافه شد"}


def _run_create_inquiry(db: Session, current_user: User | None, args: dict) -> dict:
    if current_user is None:
        return {"error": "login_required", "message": "برای ثبت درخواست خرید باید وارد حساب کاربری بشید"}

    from app.models import Inquiry

    car = db.query(Car).filter(Car.id == args.get("car_id")).first()
    if car is None:
        return {"error": "خودروی انتخاب‌شده معتبر نیست"}

    inquiry = Inquiry(
        user_id=current_user.id,
        car_id=car.id,
        car_title=car.title,
        car_price=car.effective_price,
        car_image=car.primary_image,
        full_name=args.get("full_name") or current_user.name or "",
        phone=args.get("phone") or current_user.cellphone or "",
        message=args.get("message"),
    )
    db.add(inquiry)
    db.commit()

    return {"success": True, "message": "درخواست شما ثبت شد، کارشناس فروش به‌زودی باهاتون تماس می‌گیره"}


def _execute_tool(db: Session, current_user: User | None, name: str, args: dict) -> dict:
    if name == "search_cars":
        return _run_search_cars(db, args)
    if name == "get_car_details":
        return _run_get_car_details(db, args)
    if name == "add_to_favorites":
        return _run_add_to_favorites(db, current_user, args)
    if name == "create_inquiry":
        return _run_create_inquiry(db, current_user, args)
    return {"error": f"unknown tool {name}"}


def _track_tool_result(name: str, result: dict, cars_by_id: dict[int, dict]) -> bool:
    """
    Records any car data a tool call turned up into cars_by_id (in place, for
    the frontend's car cards) and reports whether this call was a
    successful favorite/inquiry action (so the caller knows to refresh the
    relevant UI). Shared between both providers since the tool results are
    identical regardless of which model produced the call.
    """
    if name == "search_cars":
        for c in result.get("results", []):
            cars_by_id[c["id"]] = c
    if name == "get_car_details" and "id" in result:
        cars_by_id[result["id"]] = {
            "id": result["id"],
            "slug": result["slug"],
            "title": result["title"],
            "image": result["image"],
            "price": result["price"],
        }
    return name in ("add_to_favorites", "create_inquiry") and bool(result.get("success"))


def _openai_tools() -> list[dict]:
    """Same TOOLS list, reshaped into OpenAI's function-calling schema for GapGPT."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        }
        for t in TOOLS
    ]


def run_assistant(
    db: Session, current_user: User | None, messages: list[dict], car_slug: str | None = None
) -> dict:
    """
    Runs the tool-use agent loop and returns
    {"reply": str, "action_completed": bool, "cars": [...]}. `messages` is
    the full conversation so far as [{"role": "user"|"assistant", "content": str}].
    `car_slug`, when set, tells the assistant which car listing page the
    customer is currently viewing (it still has to call get_car_details
    itself - this is just context, never a substitute for the real lookup).
    `cars` collects whatever search_cars/get_car_details turned up during
    this turn, de-duplicated by id, so the frontend can render real car
    cards instead of parsing them out of the reply text.

    Dispatches to either the direct Claude API or GapGPT (an OpenAI-compatible
    proxy) based on settings.AI_PROVIDER - same tools, same DB-grounded
    results either way, just a different wire format underneath.
    """
    system_prompt = SYSTEM_PROMPT
    if car_slug:
        system_prompt += f"\n\nمشتری الان توی صفحه خودرو با slug \"{car_slug}\" هست - اگه سوالش درباره همین خودروئه، با get_car_details جزئیاتش رو بگیر."

    if settings.AI_PROVIDER == "gapgpt":
        return _run_gapgpt(db, current_user, messages, system_prompt)
    return _run_anthropic(db, current_user, messages, system_prompt)


def _run_anthropic(db: Session, current_user: User | None, messages: list[dict], system_prompt: str) -> dict:
    if not settings.ANTHROPIC_API_KEY:
        return {
            "reply": "دستیار هوشمند فعلاً فعال نیست (کلید API تنظیم نشده).",
            "action_completed": False,
            "cars": [],
        }

    conversation = [{"role": m["role"], "content": m["content"]} for m in messages]
    action_completed = False
    cars_by_id: dict[int, dict] = {}

    headers = {
        "x-api-key": settings.ANTHROPIC_API_KEY,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }

    for _ in range(MAX_TOOL_ROUNDS):
        response = httpx.post(
            ANTHROPIC_URL,
            headers=headers,
            json={
                "model": settings.AI_ASSISTANT_MODEL,
                "max_tokens": settings.AI_ASSISTANT_MAX_TOKENS,
                "system": system_prompt,
                "messages": conversation,
                "tools": TOOLS,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        content = data.get("content", [])
        conversation.append({"role": "assistant", "content": content})

        if data.get("stop_reason") != "tool_use":
            text = "".join(block.get("text", "") for block in content if block.get("type") == "text")
            return {
                "reply": text or "متوجه نشدم، می‌شه دوباره بپرسید؟",
                "action_completed": action_completed,
                "cars": list(cars_by_id.values()),
            }

        tool_results = []
        for block in content:
            if block.get("type") != "tool_use":
                continue
            result = _execute_tool(db, current_user, block["name"], block.get("input", {}))
            if _track_tool_result(block["name"], result, cars_by_id):
                action_completed = True

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block["id"],
                "content": json.dumps(result, ensure_ascii=False),
            })

        conversation.append({"role": "user", "content": tool_results})

    return {
        "reply": "متاسفانه نتونستم درخواستتون رو کامل انجام بدم، لطفاً دوباره امتحان کنید.",
        "action_completed": action_completed,
        "cars": list(cars_by_id.values()),
    }


def _run_gapgpt(db: Session, current_user: User | None, messages: list[dict], system_prompt: str) -> dict:
    """
    Same agent loop as _run_anthropic, but against GapGPT's OpenAI-compatible
    /v1/chat/completions endpoint: system prompt is just the first message,
    tool calls arrive as message.tool_calls, and tool results go back as
    separate {"role": "tool", "tool_call_id": ...} messages instead of
    Anthropic's tool_result content blocks.
    """
    if not settings.GAPGPT_API_KEY:
        return {
            "reply": "دستیار هوشمند فعلاً فعال نیست (کلید GapGPT تنظیم نشده).",
            "action_completed": False,
            "cars": [],
        }

    conversation = [{"role": "system", "content": system_prompt}]
    conversation += [{"role": m["role"], "content": m["content"]} for m in messages]

    action_completed = False
    cars_by_id: dict[int, dict] = {}

    headers = {
        "Authorization": f"Bearer {settings.GAPGPT_API_KEY}",
        "Content-Type": "application/json",
    }

    for _ in range(MAX_TOOL_ROUNDS):
        response = httpx.post(
            GAPGPT_URL,
            headers=headers,
            json={
                "model": settings.GAPGPT_MODEL,
                "messages": conversation,
                "tools": _openai_tools(),
                "max_tokens": settings.AI_ASSISTANT_MAX_TOKENS,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        message = data["choices"][0]["message"]
        conversation.append(message)

        tool_calls = message.get("tool_calls")
        if not tool_calls:
            return {
                "reply": message.get("content") or "متوجه نشدم، می‌شه دوباره بپرسید؟",
                "action_completed": action_completed,
                "cars": list(cars_by_id.values()),
            }

        for call in tool_calls:
            fn = call["function"]
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}

            result = _execute_tool(db, current_user, fn["name"], args)
            if _track_tool_result(fn["name"], result, cars_by_id):
                action_completed = True

            conversation.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": json.dumps(result, ensure_ascii=False),
            })

    return {
        "reply": "متاسفانه نتونستم درخواستتون رو کامل انجام بدم، لطفاً دوباره امتحان کنید.",
        "action_completed": action_completed,
        "cars": list(cars_by_id.values()),
    }
