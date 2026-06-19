"""Pure bill-parsing logic for the Purifier rental billing wrappers.

No platform globals (`context` / `tools`) are referenced here, so this module is
unit-testable in isolation (see tests/test_billing_lib.py). At build/push time it is
inlined verbatim into each tool's python_code.py by build/sync_lib.py.
"""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Tuple, Any

CURRENCY = "KRW"

# Purifier Category mapping. We use English values to avoid encoding issues in python code.
# The LLM will translate these English category names into natural Korean in its responses.
LABELS = {
    "RENTAL_FEES": {"English": "Rental Fees"},
    "SERVICE_FEES": {"English": "Service Fees"},
    "DISCOUNTS": {"English": "Discounts"},
    "OTHER_FEES": {"English": "Other Fees"},
    "REGISTRATION_FEES": {"English": "Registration Fees"},
    "MOBILE_PAYMENTS": {"English": "Mobile Payments"},
    "BALANCE_TRANSFERS": {"English": "Balance Transfers"},
}

# Month names/abbreviations. Kept for English fallback/parsing logic.
EN_MONTHS = ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]
EN_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def normalize_lang(lang: str) -> str:
    return "English"


def label(code: str, lang: str) -> str:
    return LABELS.get(code, {}).get("English", code or "")


def round_money(x: float) -> float:
    # Round to nearest integer for Korean Won (KRW has no decimal/cents).
    return float(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _parse(s: str) -> datetime:
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def format_date(s: str, lang: str) -> str:
    # Format in Korean: "2025년 4월 2일" using Unicode escape sequences to avoid UTF-8 comment/string console errors.
    # 년 = \ub144, 월 = \uc6d4, 일 = \uc77c
    dt = _parse(s)
    return f"{dt.year}\ub144 {dt.month}\uc6d4 {dt.day}\uc77c"


def format_period(bp: Dict[str, Any], lang: str) -> str:
    # Format period in Korean: "2025년 2월 28일 ~ 3월 27일" (or across years: "2024년 12월 28일 ~ 2025년 1월 27일")
    # 년 = \ub144, 월 = \uc6d4, 일 = \uc77c
    s, e = _parse(bp["startDateTime"]), _parse(bp["endDateTime"])
    if s.year == e.year:
        return f"{s.year}\ub144 {s.month}\uc6d4 {s.day}\uc77c ~ {e.month}\uc6d4 {e.day}\uc77c"
    return f"{s.year}\ub144 {s.month}\uc6d4 {s.day}\uc77c ~ {e.year}\ub144 {e.month}\uc6d4 {e.day}\uc77c"


def month_label(bill: Dict[str, Any], lang: str) -> str:
    # Format month label in Korean: "2025년 3월"
    # 년 = \ub144, 월 = \uc6d4
    e = _parse(bill["billingPeriod"]["endDateTime"])
    return f"{e.year}\ub144 {e.month}\uc6d4"


# Lookup mapping for English names (kept to support resolving relative month arguments).
_NAME_TO_NUM = {
    'january': 1, 'jan': 1,
    'february': 2, 'feb': 2,
    'march': 3, 'mar': 3,
    'april': 4, 'apr': 4,
    'may': 5,
    'june': 6, 'jun': 6,
    'july': 7, 'jul': 7,
    'august': 8, 'aug': 8,
    'september': 9, 'sep': 9,
    'october': 10, 'oct': 10,
    'november': 11, 'nov': 11,
    'december': 12, 'dec': 12
}


def sort_desc(bills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(bills, key=lambda b: _parse(b["billDate"]), reverse=True)


def _parse_month_year(text: str) -> Tuple[Optional[int], Optional[int]]:
    month_num, year = None, None
    for tok in text.lower().replace(",", " ").replace("/", " ").replace("-", " ").split():
        tok = tok.rstrip(".")
        if month_num is None and tok in _NAME_TO_NUM:
            month_num = _NAME_TO_NUM[tok]
        elif year is None and len(tok) == 4 and tok.isdigit():
            year = int(tok)
    return month_num, year


def match_month_name(bills: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
    month_num, year = _parse_month_year(name)
    if month_num is None:
        return None
    for b in sort_desc(bills):
        e = _parse(b["billingPeriod"]["endDateTime"])
        if e.month == month_num and (year is None or e.year == year):
            return b
    return None


def resolve_month(bills: List[Dict[str, Any]], month: str) -> Optional[Dict[str, Any]]:
    bills = sort_desc(bills)
    if not bills:
        return None
    m = (month or "latest").strip().lower()
    if m in ("latest", "newest", ""):
        return bills[0]
    if m in ("previous", "prior", "last"):
        return bills[1] if len(bills) > 1 else None
    return match_month_name(bills, m)


def older_than(bills: List[Dict[str, Any]], bill: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    bills = sort_desc(bills)
    ids = [b["id"] for b in bills]
    if bill["id"] not in ids:
        return None
    idx = ids.index(bill["id"])
    return bills[idx + 1] if idx + 1 < len(bills) else None


def account_summary_block(bill: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for b in bill.get("billSummary", []):
        if b.get("logicalResource", {}).get("name") == "ACCOUNT_SUMMARY":
            return b
    return None


def account_breakdown(bill: Dict[str, Any], lang: str) -> List[Dict[str, Any]]:
    block = account_summary_block(bill) or {}
    out = []
    for it in block.get("billSummaryItem", []):
        v = it.get("netAmount", {}).get("value", 0.0)
        if round_money(v) == 0.0:
            continue
        out.append({"category": label(it.get("billSummaryItemCategory"), lang),
                    "amount": round_money(v)})
    return out


def _digits(s: str) -> str:
    return "".join(c for c in s if c.isdigit())


def find_lines(bill: Dict[str, Any], suffix: str) -> List[Dict[str, Any]]:
    suffix = _digits(suffix)
    matches = []
    for sub in bill.get("subscription", []):
        d = _digits(sub.get("relatedParty", {}).get("id", ""))
        if suffix and d.endswith(suffix):
            matches.append(sub)
    return matches


def line_endings(bill: Dict[str, Any]) -> List[str]:
    out = []
    for sub in bill.get("subscription", []):
        d = _digits(sub.get("relatedParty", {}).get("id", ""))
        if d:
            out.append(d[-3:])
    return out


def line_breakdown(sub: Dict[str, Any], lang: str) -> Tuple[List[Dict[str, Any]], float]:
    buckets, order, total = {}, [], 0.0
    for it in sub.get("outOfBundleAmount", []):
        ch = {c["name"]: c["value"] for c in it.get("characteristic", [])}
        ban = ch.get("billSummaryBANItemCategory")
        if ban is None:
            if ch.get("Category") == "TOTAL_AMOUNT":
                total = it.get("value", 0.0)
            continue
        if ban not in buckets:
            buckets[ban] = 0.0
            order.append(ban)
        buckets[ban] += it.get("value", 0.0)
    breakdown = [{"category": label(b, lang), "amount": round_money(buckets[b])}
                 for b in order if round_money(buckets[b]) != 0.0]
    return breakdown, round_money(total)


def _driver_note(prev: float, cur: float, lang: str) -> str:
    # English driver notes. The LLM will translate these to Korean.
    if abs(prev) < 0.005 <= abs(cur):
        return "new this month"
    if prev < 0 and cur < 0 and abs(cur) < abs(prev):
        return "smaller credit"
    if cur > prev:
        return "higher"
    return "lower"


def _cat_nets(bill: Dict[str, Any]) -> Dict[str, float]:
    block = account_summary_block(bill) or {}
    return {it.get("billSummaryItemCategory"): it.get("netAmount", {}).get("value", 0.0)
            for it in block.get("billSummaryItem", [])}


# === GECX Platform Glue ===
_LIST_FIELDS = "id,billDate,billingPeriod,amountDue,paymentDueDate"


def _unwrap(resp):
    # Step 1: Check if the response is an HTTP Response object (has a .json() method)
    if hasattr(resp, "json") and callable(getattr(resp, "json")):
        try:
            # If so, parse the JSON body out of it
            resp = resp.json()
        except Exception:
            # If JSON parsing fails, return an empty list immediately
            return []

    # Step 2: Unwrap nested dictionary envelopes (e.g. {"result": [...]}) to find the raw list
    for _ in range(5):  # Loop at most 5 times to prevent infinite loops on circular data
        if isinstance(resp, list):
            # If we successfully reached a list, return it immediately
            return resp
        if not isinstance(resp, dict):
            # If the current level is not a list and not a dict, it is invalid
            return []
        
        # Look for typical envelope key wrappers and dive inside them
        for k in ("output", "result", "response", "results", "data", "body"):
            if k in resp:
                resp = resp[k]  # Go one level deeper
                break
        else:
            # If none of the wrapper keys exist in the dict, we cannot unwrap further
            return []
            
    # Step 3: Return the final extracted list, or [] if it's still not a list
    return resp if isinstance(resp, list) else []


def _get_bills(account_id, bill_id=""):
    args = {"customer_id": account_id}
    if bill_id:
        args["bill_id"] = bill_id           # detail fetch: one full bill
    else:
        args["fields"] = _LIST_FIELDS       # list: trimmed projection of all bills
    return _unwrap(tools.purifier_billing_getInvoices(args))


def _auth_error():
    return {"status": "error", "error": "unauthenticated",
            "agent_action": ("Explain you cannot share billing details without "
                             "verification, then escalate.")}


def _api_error():
    return {"status": "error", "error": "billing system unavailable",
            "agent_action": "Apologise and offer to connect them to a specialist."}


# === Entrypoint ===
def get_invoice_breakdown(month: str = "latest", line: str = "") -> dict:
    """Break an authenticated customer's rental invoice into charge categories.

    Args:
        month: 'latest' (default), 'previous', or a month name.
        line: empty for whole account, or last digits of product serial (e.g. '843').

    Returns:
        dict: breakdown result or error details.
    """
    if context.state.get("auth_status", "") != "authenticated":
        return _auth_error()
    account_id = context.state.get("account_id", "")
    if not account_id:
        return {"status": "error", "error": "no account",
                "agent_action": "Treat the caller as unverified and escalate."}
    lang = context.state.get("active_language", "") or "English"

    try:
        summaries = _get_bills(account_id)
    except Exception as e:
        context.state["api_failed"] = "true"
        context.state["api_error_detail"] = str(e)
        return _api_error()
    target = resolve_month(summaries, month)
    if target is None:
        avail = ", ".join(s["month"] for s in summarize_bills(summaries, lang)) or "none"
        return {"status": "error", "error": "month not found",
                "agent_action": ("Tell the customer you have these invoices: "
                                 + avail + ". Ask which they'd like.")}

    try:
        detail = (_get_bills(account_id, bill_id=target["id"]) or [None])[0]
    except Exception as e:
        context.state["api_failed"] = "true"
        context.state["api_error_detail"] = str(e)
        return _api_error()
    if detail is None:
        return _api_error()

    base = {"status": "success", "currency": CURRENCY,
            "month": month_label(detail, lang),
            "period": format_period(detail["billingPeriod"], lang),
            "bill_date": format_date(detail["billDate"], lang),
            "payment_due": format_date(detail["paymentDueDate"], lang)}

    if line:
        matches = find_lines(detail, line)
        if len(matches) != 1:
            return {"status": "error", "error": "product not matched",
                    "product_endings": line_endings(detail),
                    "agent_action": ("Offer the products using their endings in "
                                     "product_endings and ask which one the customer "
                                     "means — never invent a product serial number.")}
        bd, total = line_breakdown(matches[0], lang)
        last3 = "".join(c for c in matches[0]["relatedParty"]["id"] if c.isdigit())[-3:]
        base.update({"scope": "product", "product": "…" + last3, "total": total, "breakdown": bd,
                     "agent_action": ("State this product's net total; if it is near "
                                      "zero, explain charges are offset by a credit.")})
        return base

    base.update({"scope": "account",
                 "total": round_money(detail.get("amountDue", {}).get("value", 0.0)),
                 "products": len(detail.get("subscription", [])),
                 "product_endings": line_endings(detail),
                 "breakdown": account_breakdown(detail, lang),
                 "agent_action": ("Give the total, then the main categories. If the "
                                  "customer wants per-product detail, offer the products "
                                  "using the endings in product_endings (e.g. 'the product "
                                  "ending 843') — never invent product serial numbers.")})
    return base
