"""
Standard reference values for car listings - kept as plain Python constants
(not DB tables) since they're small, fixed vocabularies used purely for
validation and building filter dropdowns.
"""

# Standard car color palette (name -> hex). Car colors are restricted to this
# list so "رنگ" can be filtered reliably instead of matching free-text like
# "سفید یخی" vs "سفید" vs "White" for the same actual color.
STANDARD_COLORS: dict[str, str] = {
    "سفید": "#FFFFFF",
    "مشکی": "#000000",
    "نقره‌ای": "#C0C0C0",
    "خاکستری": "#808080",
    "قرمز": "#D32F2F",
    "آبی": "#1976D2",
    "سرمه‌ای": "#1A237E",
    "سبز": "#2E7D32",
    "زرد": "#FBC02D",
    "نارنجی": "#F57C00",
    "قهوه‌ای": "#5D4037",
    "بژ": "#D7C4A3",
    "طلایی": "#C9A227",
    "یشمی": "#00897B",
    "بنفش": "#7B1FA2",
}


def validate_color(name: str) -> str:
    """Returns the hex code for a standard color name, or raises ValueError."""
    if name not in STANDARD_COLORS:
        allowed = "، ".join(STANDARD_COLORS.keys())
        raise ValueError(f"رنگ باید یکی از این‌ها باشد: {allowed}")
    return STANDARD_COLORS[name]

# نوع گیربکس
TRANSMISSION_TYPES: dict[str, str] = {
    "manual": "دنده‌ای",
    "automatic": "اتوماتیک",
    "cvt": "نیمه‌اتوماتیک (CVT)",
}

# نوع سوخت
FUEL_TYPES: dict[str, str] = {
    "gasoline": "بنزینی",
    "dual": "دوگانه‌سوز (بنزین/CNG)",
    "diesel": "دیزلی",
    "hybrid": "هیبریدی",
    "electric": "برقی",
}
