from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings

# pool_recycle: بعضی هاست‌های رایگان/اشتراکی MySQL (مثل سرویس‌های رایگان
# ابری) کانکشن‌های بی‌کار رو بعد از چند دقیقه خودشون از سمت سرور می‌بندن.
# pool_pre_ping فقط قبل از گرفتن کانکشن از pool تستش می‌کنه (کمکی به قطعی
# *وسط* یک کوئری نمی‌کنه)، پس علاوه بر اون pool_recycle هم گذاشتیم تا
# SQLAlchemy خودش کانکشن‌های قدیمی‌تر از ۵ دقیقه رو، قبل از اینکه سرور
# ببندتشون، دور بریزه و تازه بسازه - رفع "Lost connection to server
# during query" / "MySQL server has gone away".
engine = create_engine(settings.sqlalchemy_database_url, pool_pre_ping=True, pool_recycle=280)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency - one DB session per request, closed after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
