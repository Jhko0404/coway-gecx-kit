"""Pure bill-parsing logic for the Coway rental billing wrappers.

No platform globals (`context` / `tools`) are referenced here, so this module is
unit-testable in isolation (see tests/test_billing_lib.py). At build/push time it is
inlined verbatim into each tool's python_code.py by build/sync_lib.py.
"""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Tuple, Any

CURRENCY = "KRW"

# Coway Category mapping. We use English values to avoid encoding issues in python code.
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


def compare(current: Dict[str, Any], previous: Dict[str, Any], lang: str) -> Dict[str, Any]:
    cur, prev = _cat_nets(current), _cat_nets(previous)
    rows = []
    for code in set(cur) | set(prev):
        change = cur.get(code, 0.0) - prev.get(code, 0.0)
        if round_money(change) == 0.0:
            continue
        rows.append((abs(change), change, code,
                     {"category": label(code, lang), "change": round_money(change),
                      "note": _driver_note(prev.get(code, 0.0), cur.get(code, 0.0), lang)}))
    rows.sort(key=lambda r: (-r[0], -r[1], r[2]))
    ct = current.get("amountDue", {}).get("value", 0.0)
    pt = previous.get("amountDue", {}).get("value", 0.0)
    diff = round_money(ct - pt)
    direction = "higher" if diff > 0 else ("lower" if diff < 0 else "the same")
    return {
        "current": {"month": month_label(current, lang), "total": round_money(ct)},
        "previous": {"month": month_label(previous, lang), "total": round_money(pt)},
        "difference": {"amount": abs(diff), "direction": direction},
        "top_drivers": [r[3] for r in rows[:3]],
    }


def summarize_bills(bills: List[Dict[str, Any]], lang: str) -> List[Dict[str, Any]]:
    return [{"month": month_label(b, lang),
             "period": format_period(b["billingPeriod"], lang),
             "total": round_money(b.get("amountDue", {}).get("value", 0.0))}
            for b in sort_desc(bills)]


# === GECX Platform Glue ===
# Fields we ask the list endpoint to return. TMF "field narrowing" optimization.
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
    return _unwrap(tools.coway_billing_getInvoices(args))


def _auth_error():
    return {"status": "error", "error": "unauthenticated",
            "agent_action": ("Explain you cannot share billing details without "
                             "verification, then escalate.")}


def _api_error():
    return {"status": "error", "error": "billing system unavailable",
            "agent_action": "Apologise and offer to connect them to a specialist."}


# === Entrypoint ===
def compare_invoices(month: str = "latest", compare_to: str = "previous") -> dict:
    """Compare two invoices and explain the difference.

    Args:
        month: the invoice to explain — 'latest' (default), 'previous', or a month name.
        compare_to: 'previous' (default) or a month name.

    Returns:
        dict: comparison result or error details.
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
    current = resolve_month(summaries, month)
    if current is None:
        avail = ", ".join(s["month"] for s in summarize_bills(summaries, lang)) or "none"
        return {"status": "error", "error": "month not found",
                "agent_action": "Tell the customer you have these invoices: " + avail + "."}

    if (compare_to or "previous").strip().lower() in ("previous", "prior", "last", ""):
        other = older_than(summaries, current)
    else:
        other = resolve_month(summaries, compare_to)
        
    if other is None:
        return {"status": "error", "error": "no comparison invoice",
                "agent_action": ("Say you only have the February and March invoices, "
                                 "so there is nothing earlier to compare.")}
    if other["id"] == current["id"]:
        return {"status": "error", "error": "same invoice",
                "agent_action": ("Those are the same invoice — ask whether they meant "
                                 "two different months.")}

    try:
        cur_d = (_get_bills(account_id, bill_id=current["id"]) or [None])[0]
        oth_d = (_get_bills(account_id, bill_id=other["id"]) or [None])[0]
    except Exception as e:
        context.state["api_failed"] = "true"
        context.state["api_error_detail"] = str(e)
        return _api_error()
    if cur_d is None or oth_d is None:
        return _api_error()

    result = compare(cur_d, oth_d, lang)
    result["status"] = "success"
    result["currency"] = CURRENCY
    result["agent_action"] = ("State the difference and name the top one or two "
                              "drivers.")
    return result
