# Car Sales API (FastAPI)

A FastAPI backend for a new+used car marketplace: browse/search cars by
brand, body type, condition (new/used), year and price, save favorites, and
submit a purchase/visit inquiry that a sales agent follows up on by phone.
There is **no online checkout or payment gateway** — deals are negotiated
and closed offline once an inquiry comes in.

This project started as a shoe/slipper e-commerce API and was restructured
into this car-marketplace domain; the architecture (auth, admin panel,
pagination, file uploads, AI assistant) carried over largely unchanged.

## Project layout

```
app/
  core/
    config.py        # settings (env vars)
    security.py       # password hashing, OTP generation, bearer-token hashing
  db/
    session.py         # SQLAlchemy engine/session/Base
  models/               # SQLAlchemy models, one file per domain
    user.py, token.py, location.py, address.py
    category.py         # car body-type categories (sedan, SUV, ...), parent/child
    brand.py             # car manufacturers (Peugeot, Kia, Iran Khodro, ...)
    car.py               # Car (single physical unit - price/color live here), CarImage
    inquiry.py            # purchase/visit request + sales follow-up pipeline
    favorite.py            # saved/bookmarked cars (wishlist)
    content.py               # contact-us, sliders, stories
  schemas/               # Pydantic request schemas
  api/
    deps.py               # get_current_user / get_current_admin
    v1/
      auth.py               # customer OTP login + admin email/password login
      categories.py
      brands.py
      cars.py                # public listing/filter/search + admin CRUD
      favorites.py            # wishlist
      inquiries.py             # customer submits inquiry, admin manages status
      profile.py                # customer profile, addresses, own inquiries
      users.py, contact.py, sliders.py, stories.py, chat.py
  services/
    sms.py                 # Ghasedak OTP send
    slug.py                 # unique slug generation for cars/brands
    storage.py               # local file upload/serve
    ai_assistant.py           # AI sales assistant (Claude API or GapGPT)
  utils/
    response.py, jalali.py, pagination.py
main.py                       # FastAPI app + router wiring
alembic/                       # migrations, mirrors schema.sql
schema.sql                      # raw SQL schema, same shape as the models
```

## Domain model

- **Brand** — a manufacturer (Peugeot, Kia, Iran Khodro, Toyota, ...).
- **Category** — a car body type (Sedan, SUV, Crossover, Pickup, Hatchback,
  ...), self-referencing for parent/child grouping if needed.
- **Car** — a listing, and each row is exactly **one physical car** — there's
  no quantity/stock field, for new or used. Has a `condition` (new/used),
  `model_year`, `mileage_km` (0 for new), an optional `vin`, a single
  `color`/`color_code` (restricted to the standard palette in
  `app/core/car_constants.py`, so filtering is reliable instead of matching
  free-text like "سفید یخی" vs "سفید" for the same color), `transmission`
  (manual/automatic/CVT), `fuel_type` (gasoline/dual/diesel/hybrid/electric),
  and two chassis/body condition flags (`chassis_healthy`, `body_healthy` —
  plain booleans: sealed/undamaged vs. has damage, replaced parts, or a
  repaint). "نوع خودرو" (coupe/sedan/...) is handled by `Category`, not a
  separate field — see below. **When a deal closes, the `Car` row is
  deleted** (see `Inquiry` below), not decremented.
- **Favorite** — a user bookmarking a car. No quantity, no checkout — just
  a saved-listings list.
- **Inquiry** — a customer's request to buy or visit a specific car:
  contact info, an optional message, and a status pipeline
  (`pending → contacted → negotiating → test-drive scheduled → deal
  closed`, or `cancelled`/`rejected` along the way). A sales agent moves it
  through the pipeline from the admin panel; there's no automated payment
  step. Moving an inquiry to "deal closed" **deletes the underlying `Car`**
  — since each car is a single unit, "sold" means the listing is gone, not
  a decremented count. `car_id` is nullable/`ON DELETE SET NULL`, and
  `car_title`/`car_price`/`car_image` are snapshotted onto the `Inquiry` at
  creation time, so its history stays readable in the admin panel even
  after the car itself no longer exists (and even if other, still-open
  inquiries pointed at the same now-sold car).

This replaces the original shop's `Order`/`OrderItems`/`Coupon`/
`ShippingMethod`/`Transaction`/payment-gateway chain, none of which apply
to a request-and-follow-up sales process, and its `Cart`, which becomes the
simpler `Favorite` wishlist.

## Key endpoints

**Public**
- `GET /api/v1/cars`, `GET /api/v1/menu` (filterable listing: brand,
  category, condition, year range, price range, color, search, sort)
- `GET /api/v1/cars/{slug}`
- `GET /api/v1/filter-options` — brands/categories/price & year ranges/colors
  actually present in the catalog, for building a filter sidebar
- `GET /api/v1/brands`
- `GET /api/v1/random-cars?count=N`
- `POST /api/v1/chat` — AI sales assistant (guests can browse; logged-in
  users can also save favorites and submit inquiries through it)

**Customer (requires `Authorization: Bearer <token>`)**
- `GET/POST /api/v1/favorites`, `DELETE /api/v1/favorites/{car_id}`
- `POST /api/v1/inquiries` — submit a purchase/visit request
- `GET /api/v1/profile/inquiries` — the customer's own inquiries
- `GET/POST /api/v1/profile/addresses`, `GET /api/v1/profile/info`

**Admin panel** (`/api/v1/admin-panel/...`, requires an admin token)
- `cars` — CRUD, including nested color-option management
- `brands`, `categories` — CRUD
- `inquiries` — list/view, `PATCH .../status` to move an inquiry through
  the pipeline (only along the allowed transitions)
- `users`, `sliders`, `stories`, `contact-us`

## Auth flow

1. `POST /api/v1/auth/login {cellphone}` → creates/updates the user,
   generates a 6-digit OTP, sends it via Ghasedak, returns a `login_token`.
2. `POST /api/v1/auth/check-otp {otp, login_token}` → on match, issues a
   bearer token (ability `["user"]`) and the serialized user.
3. `POST /api/v1/auth/resend-otp {login_token}` → new OTP + new
   `login_token`.
4. `GET /api/v1/auth/me`, `POST /api/v1/auth/logout` → require
   `Authorization: Bearer <token>`.
5. Admin: `POST /api/v1/admin-panel/auth/login {email, password}` (only if
   `is_admin`), plus the matching `me`/`logout`.

Tokens are stored as an HMAC-SHA256 hash in `access_tokens`
(`app/core/security.py` / `app/api/deps.py`), never in plaintext.

## AI sales assistant

`app/services/ai_assistant.py` runs a small tool-use agent loop (against
either the Claude API directly, or GapGPT — an OpenAI-compatible proxy,
picked via `AI_PROVIDER`). It's grounded in the real catalog through four
tools:

- `search_cars` / `get_car_details` — the assistant never invents a price,
  color, or stock status; every claim comes from these calls.
- `add_to_favorites`, `create_inquiry` — only work for a logged-in user; the
  assistant is told to explain that when they fail with `login_required`.

`widget/ai-assistant-demo.html` is a self-contained, framework-free demo of
the chat widget — open it directly in a browser (with the API running
locally) to try it, or copy the marked block into the real storefront
frontend.

## Setup

```bash
cp .env.example .env    # fill in DATABASE_URL, TOKEN_SECRET, GHASEDAK_API_KEY, ANTHROPIC_API_KEY, ...
pip install -r requirements.txt --break-system-packages

# either import the raw schema...
mysql -u root -p your_db_name < schema.sql
# ...or run the Alembic migration (same schema, generated the same way)
alembic upgrade head

uvicorn main:app --reload
```

`scripts/seed_iran_locations.py` (or its `.sql` counterpart) seeds
`provinces`/`cities` for the address-book feature — unrelated to cars,
carried over as-is.

`scripts/seed_brands.py` seeds the `brands` table: a curated static list of
brands common in the Iranian market by default, plus an opt-in
`--from-divar` best-effort fetch from Divar's internal brand hierarchy
endpoint (unverified from this environment — see the script's docstring
before relying on it; `--dump-only` prints the raw response so you can
adjust the parser if the shape doesn't match).

## What's deliberately not here

- **No online payment.** There's no `Transaction`/payment-gateway module —
  `Inquiry.status` is moved by a human sales agent, not a payment callback.
- **No stock/quantity field on `Car`.** Each row is one physical car; a
  sold car is deleted, not decremented. There's no "3 in stock" concept
  the way a shop's product catalog would have.
- **No cart/checkout with quantities.** A car listing isn't something you
  buy multiples of in one basket; `Favorite` is a plain save-for-later list,
  and `Inquiry` is a one-car-at-a-time request.
- **No shipping methods or coupons**, for the same reason — they modeled a
  parcel-shipping checkout that doesn't apply to in-person vehicle sales.
- **No separate "car type" (coupe/sedan/...) field.** `Category` already
  covers that (it's an admin-managed, nested list), so it isn't duplicated
  as a fixed enum.
