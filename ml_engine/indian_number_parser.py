"""
Indian Number Format Parser
Handles: 3,85,00,000 | 58,00,000 | ₹42.5Cr | 6.1 crore | 12,45,230
"""
import re


def parse_indian_number(s: str) -> float:
    """
    Convert an Indian-formatted number string to a float.

    Examples:
        "3,85,00,000"  -> 38500000.0
        "58,00,000"    -> 5800000.0
        "₹42.5Cr"      -> 42500000.0
        "12,45,230"    -> 1245230.0
        "6.1 crore"    -> 61000000.0
        "₹69.3L"       -> 6930000.0
    """
    if not s:
        return 0.0

    s = str(s).strip()

    # Remove currency symbols and whitespace
    s = re.sub(r'[₹\$£€\s]', '', s)

    # Check for crore/lakh suffix BEFORE removing commas
    multiplier = 1.0
    s_lower = s.lower()

    if re.search(r'cr(ore)?s?$', s_lower):
        multiplier = 1e7
        s = re.sub(r'cr(ore)?s?$', '', s, flags=re.IGNORECASE).strip()
    elif re.search(r'l(akh)?s?$', s_lower):
        multiplier = 1e5
        s = re.sub(r'l(akh)?s?$', '', s, flags=re.IGNORECASE).strip()

    # Remove Indian-format commas (all commas are thousands separators here)
    s = s.replace(',', '')

    try:
        return float(s) * multiplier
    except ValueError:
        return 0.0


def find_amount(text: str, pattern: str, group: int = 1) -> float:
    """
    Search for `pattern` in `text` and parse the captured group as an
    Indian-format number.

    The pattern should capture the raw number string in group `group`.
    """
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return 0.0
    return parse_indian_number(match.group(group))


def format_inr(amount: float) -> str:
    """
    Format a raw float (rupees) into a readable Indian string.

    Examples:
        42500000  -> "₹42.5Cr"
        5800000   -> "₹58L"
        1245230   -> "₹12.45L"
        500       -> "₹500"
    """
    if amount == 0:
        return "₹0"
    if amount >= 1e7:
        val = amount / 1e7
        return f"₹{val:.2f}Cr".rstrip('0').rstrip('.')
    if amount >= 1e5:
        val = amount / 1e5
        return f"₹{val:.2f}L".rstrip('0').rstrip('.')
    return f"₹{int(amount):,}"


# ── Unit tests (run directly: python ml_engine/indian_number_parser.py) ──
if __name__ == "__main__":
    cases = [
        ("3,85,00,000",    38500000.0),
        ("58,00,000",       5800000.0),
        ("42,00,000",       4200000.0),
        ("5,00,00,000",    50000000.0),
        ("₹42.5Cr",        42500000.0),
        ("6.1 crore",      61000000.0),
        ("₹69.3L",          6930000.0),
        ("12,45,230",       1245230.0),
        ("11.5",                 11.5),   # percentage — no multiplier
    ]

    all_pass = True
    for raw, expected in cases:
        result = parse_indian_number(raw)
        status = "PASS" if abs(result - expected) < 0.01 else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"{status}  parse_indian_number({raw!r:20}) = {result:>15,.1f}  (expected {expected:,.1f})")

    print()
    fmt_cases = [42500000, 5800000, 1245230, 69300000, 500]
    for v in fmt_cases:
        print(f"  format_inr({v:>12,}) = {format_inr(v)}")

    print("\n" + ("ALL TESTS PASSED ✅" if all_pass else "SOME TESTS FAILED ❌"))
