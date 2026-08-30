from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.auth import router as auth_router, admin_router as auth_admin_router
from app.api.v1.categories import router as categories_router, admin_router as categories_admin_router
from app.api.v1.brands import router as brands_router, admin_router as brands_admin_router
from app.api.v1.cars import router as cars_router, admin_router as cars_admin_router
from app.api.v1.favorites import router as favorites_router
from app.api.v1.inquiries import router as inquiries_router, admin_router as inquiries_admin_router
from app.api.v1.profile import router as profile_router, user_router as profile_user_router
from app.api.v1.sliders import router as sliders_router, admin_router as sliders_admin_router
from app.api.v1.stories import router as stories_router, admin_router as stories_admin_router
from app.api.v1.users import admin_router as users_admin_router
from app.api.v1.contact import router as contact_router, admin_router as contact_admin_router
from app.api.v1.chat import router as chat_router
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME, debug=settings.APP_DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uploaded car/brand/category images - equivalent to Laravel's public/storage symlink
storage_dir = Path(__file__).resolve().parent.parent / "storage"
storage_dir.mkdir(exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(storage_dir)), name="storage")

app.include_router(auth_router, prefix="/api/v1")
app.include_router(auth_admin_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(categories_admin_router, prefix="/api/v1")
app.include_router(brands_router, prefix="/api/v1")
app.include_router(brands_admin_router, prefix="/api/v1")
app.include_router(cars_router, prefix="/api/v1")
app.include_router(cars_admin_router, prefix="/api/v1")
app.include_router(favorites_router, prefix="/api/v1")
app.include_router(inquiries_router, prefix="/api/v1")
app.include_router(inquiries_admin_router, prefix="/api/v1")
app.include_router(profile_router, prefix="/api/v1")
app.include_router(profile_user_router, prefix="/api/v1")
app.include_router(sliders_router, prefix="/api/v1")
app.include_router(sliders_admin_router, prefix="/api/v1")
app.include_router(stories_router, prefix="/api/v1")
app.include_router(stories_admin_router, prefix="/api/v1")
app.include_router(users_admin_router, prefix="/api/v1")
app.include_router(contact_router, prefix="/api/v1")
app.include_router(contact_admin_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}
