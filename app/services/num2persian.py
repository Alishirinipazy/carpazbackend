"""تبدیل عدد به حروف فارسی - برای فیلد «ثمن معامله ... به حروف» در قرارداد."""

_YEKAN = ["", "یک", "دو", "سه", "چهار", "پنج", "شش", "هفت", "هشت", "نه"]
_DAHGAN_2 = [
    "ده", "یازده", "دوازده", "سیزده", "چهارده", "پانزده",
    "شانزده", "هفده", "هجده", "نوزده",
]
_DAHGAN = ["", "", "بیست", "سی", "چهل", "پنجاه", "شصت", "هفتاد", "هشتاد", "نود"]
_SADGAN = [
    "", "صد", "دویست", "سیصد", "چهارصد", "پانصد",
    "ششصد", "هفتصد", "هشتصد", "نهصد",
]
_MAGNITUDE = ["", " هزار", " میلیون", " میلیارد", " هزار میلیارد", " میلیون میلیارد"]


def _three_digits_to_words(n: int) -> str:
    if n == 0:
        return ""
    parts = []
    sad, baghimande = divmod(n, 100)
    if sad:
        parts.append(_SADGAN[sad])
    if baghimande >= 10 and baghimande <= 19:
        parts.append(_DAHGAN_2[baghimande - 10])
    else:
        dah, yek = divmod(baghimande, 10)
        if dah:
            parts.append(_DAHGAN[dah])
        if yek:
            parts.append(_YEKAN[yek])
    return " و ".join(parts)


def number_to_persian_words(n: int) -> str:
    """۱۲۳۴۵۶ -> 'یکصد و بیست و سه هزار و چهارصد و پنجاه و شش'"""
    if n == 0:
        return "صفر"
    if n < 0:
        return "منفی " + number_to_persian_words(-n)

    groups = []
    while n > 0:
        n, rem = divmod(n, 1000)
        groups.append(rem)

    parts = []
    for i in range(len(groups) - 1, -1, -1):
        if groups[i] == 0:
            continue
        words = _three_digits_to_words(groups[i])
        parts.append(words + _MAGNITUDE[i])

    return " و ".join(parts)


def rial_to_toman_words(rial: int) -> str:
    """مبلغ ریالی را به تومان (تقسیم بر ۱۰) تبدیل و به حروف برمی‌گرداند."""
    return number_to_persian_words(rial // 10)
