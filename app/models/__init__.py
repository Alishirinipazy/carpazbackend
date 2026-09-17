# Import every model here so that:
#   1) string-based relationship() references (e.g. "User", "Car") resolve correctly
#   2) Base.metadata has every table registered for Alembic autogenerate / create_all
from app.models.user import User
from app.models.token import AccessToken
from app.models.location import Province, City
from app.models.address import UserAddress
from app.models.category import Category
from app.models.brand import Brand
from app.models.car_catalog import CarModel, CarTrim
from app.models.car import Car, CarImage
from app.models.inquiry import Inquiry
from app.models.favorite import Favorite
from app.models.content import ContactUs, Slider, Story
from app.models.sell_request import SellRequest
from app.models.price_guide import PriceGuideEntry
from app.models.inspection import CarInspection
from app.models.contract import Contract

__all__ = [
    "User",
    "AccessToken",
    "Province",
    "City",
    "UserAddress",
    "Category",
    "Brand",
    "CarModel",
    "CarTrim",
    "Car",
    "CarImage",
    "Inquiry",
    "Favorite",
    "ContactUs",
    "Slider",
    "Story",
    "SellRequest",
    "PriceGuideEntry",
    "CarInspection",
    "Contract",
]
