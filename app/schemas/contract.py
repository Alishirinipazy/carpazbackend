from datetime import date

from pydantic import BaseModel


class ContractDetails(BaseModel):
    """همه‌ی فیلدهای متنی/تاریخی قرارداد - همه اختیاری، چون قرارداد می‌تونه
    مرحله‌به‌مرحله (پیش‌نویس) تکمیل بشه."""

    # فروشنده
    seller_name: str | None = None
    seller_father_name: str | None = None
    seller_national_id: str | None = None
    seller_id_issued_from: str | None = None
    seller_birth_date: str | None = None
    seller_address: str | None = None
    seller_phone: str | None = None

    # خریدار
    buyer_name: str | None = None
    buyer_father_name: str | None = None
    buyer_national_id: str | None = None
    buyer_id_issued_from: str | None = None
    buyer_birth_date: str | None = None
    buyer_address: str | None = None
    buyer_phone: str | None = None

    # مشخصات خودرو
    vehicle_type: str | None = None
    vehicle_brand_model: str | None = None
    vehicle_model_year: str | None = None
    vehicle_system: str | None = None
    vehicle_color: str | None = None
    plate_number: str | None = None
    engine_number: str | None = None
    chassis_number: str | None = None
    vin_code: str | None = None
    fuel_card_number: str | None = None
    third_party_insurance_expiry: str | None = None
    technical_inspection_expiry: str | None = None
    accessories: str | None = None
    documents: str | None = None

    # اظهارات فروشنده
    mileage_km: int | None = None
    has_paint_damage: bool | None = None
    paint_damage_location: str | None = None
    technical_completeness: str | None = None

    # پرداخت
    deposit_amount: int | None = None
    deposit_date: str | None = None
    deposit_method: str | None = None
    deposit_tracking_number: str | None = None
    remaining_amount: int | None = None
    remaining_method: str | None = None
    remaining_account_number: str | None = None
    remaining_check_due_date: str | None = None
    remaining_bank_name: str | None = None

    # شرایط و تعهدات
    plate_transfer_date: str | None = None
    plate_transfer_time: str | None = None
    plate_transfer_location: str | None = None
    delivery_date: str | None = None
    delivery_time: str | None = None
    daily_penalty_amount: int | None = None
    seller_bank_account: str | None = None
    buyer_bank_account: str | None = None
    notes: str | None = None


class ContractIn(BaseModel):
    car_id: int | None = None
    contract_date: date | None = None
    price: int | None = None
    price_text: str | None = None
    status: int = 0
    details: ContractDetails = ContractDetails()
