# tests/test_wrappers.py
import importlib.util
import json
import os
import sys
import types

ROOT = os.path.join(os.path.dirname(__file__), "..")
FEB = json.load(open(os.path.join(ROOT, "mock_data", "Bill-Feb-2026.json")))
MAR = json.load(open(os.path.join(ROOT, "mock_data", "Bill-Mar-2026.json")))
LIST_FIELDS = ["id", "billDate", "billingPeriod", "amountDue", "paymentDueDate"]
SUMMARIES = [{k: b[k] for k in LIST_FIELDS} for b in (MAR, FEB)]


def _load(tool):
    """Load a console-kit flat python tool as an isolated module."""
    path = os.path.join(ROOT, "tools", f"{tool}.py")
    spec = importlib.util.spec_from_file_location(f"pc_{tool}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"pc_{tool}"] = mod
    spec.loader.exec_module(mod)
    return mod


class FakeTools:
    # GECX API proxy takes a single positional dict of OpenAPI args.
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def purifier_billing_getInvoices(self, params=None, **kwargs):
        self.calls.append(params if params is not None else kwargs)
        return self._responses.pop(0)


def _ctx(state):
    return types.SimpleNamespace(state=dict(state))


AUTHED = {"auth_status": "authenticated",
          "account_id": "urn:purifier:rental:product:ban:115720204", "active_language": "English"}


def test_breakdown_account_en():
    mod = _load("get_invoice_breakdown")
    mod.context = _ctx(AUTHED)
    mod.tools = FakeTools([SUMMARIES, [MAR]])   # list call, then detail call
    out = mod.get_invoice_breakdown(month="latest")
    assert out["status"] == "success" and out["scope"] == "account"
    assert out["total"] == 5370.0 and out["bill_date"] == "2026년 4월 2일" and out["products"] == 3
    assert out["product_endings"] == ["048", "703", "843"]
    assert {"category": "Rental Fees", "amount": 167837.0} in out["breakdown"]


def test_breakdown_passes_snake_case_args_to_toolset():
    mod = _load("get_invoice_breakdown")
    mod.context = _ctx(AUTHED)
    ft = FakeTools([SUMMARIES, [MAR]])
    mod.tools = ft
    mod.get_invoice_breakdown()
    # Check that it calls with customer_id (not related_party_id) and field projection
    assert ft.calls[0] == {"customer_id": "urn:purifier:rental:product:ban:115720204",
                           "fields": "id,billDate,billingPeriod,amountDue,paymentDueDate"}
    assert ft.calls[1] == {"customer_id": "urn:purifier:rental:product:ban:115720204",
                           "bill_id": MAR["id"]}


def test_breakdown_product_843_en():
    mod = _load("get_invoice_breakdown")
    mod.context = _ctx(AUTHED)
    mod.tools = FakeTools([SUMMARIES, [MAR]])
    out = mod.get_invoice_breakdown(month="latest", line="843")
    assert out["status"] == "success" and out["scope"] == "product"
    assert out["product"] == "…843" and out["total"] == 1500.0
    assert {"category": "Rental Fees", "amount": 56946.0} in out["breakdown"]
    assert {"category": "Discounts", "amount": -55445.0} in out["breakdown"]


def test_breakdown_product_not_matched_en():
    mod = _load("get_invoice_breakdown")
    mod.context = _ctx(AUTHED)
    mod.tools = FakeTools([SUMMARIES, [MAR]])
    out = mod.get_invoice_breakdown(month="latest", line="999")
    assert out["status"] == "error" and out["error"] == "product not matched"
    assert out["product_endings"] == ["048", "703", "843"]


def test_breakdown_unauthenticated():
    mod = _load("get_invoice_breakdown")
    mod.context = _ctx({"auth_status": "unauthenticated"})
    mod.tools = FakeTools([])
    out = mod.get_invoice_breakdown()
    assert out["status"] == "error" and "agent_action" in out


def test_breakdown_unknown_month():
    mod = _load("get_invoice_breakdown")
    mod.context = _ctx(AUTHED)
    mod.tools = FakeTools([SUMMARIES])
    out = mod.get_invoice_breakdown(month="december")
    assert out["status"] == "error" and "2026년 2월" in out["agent_action"]


def test_compare_feb_mar():
    mod = _load("compare_invoices")
    mod.context = _ctx(AUTHED)
    # list, then detail(current=MAR), then detail(previous=FEB)
    mod.tools = FakeTools([SUMMARIES, [MAR], [FEB]])
    out = mod.compare_invoices(month="latest", compare_to="previous")
    assert out["status"] == "success"
    assert out["difference"] == {"amount": 7160.0, "direction": "higher"}
    assert out["top_drivers"][0]["category"] == "Other Fees"


def test_compare_with_year_in_month_args():
    mod = _load("compare_invoices")
    mod.context = _ctx(AUTHED)
    mod.tools = FakeTools([SUMMARIES, [MAR], [FEB]])
    out = mod.compare_invoices(month="March 2026", compare_to="February 2026")
    assert out["status"] == "success"
    assert out["difference"] == {"amount": 7160.0, "direction": "higher"}
    assert out["current"]["month"] == "2026년 3월"
    assert out["previous"]["month"] == "2026년 2월"


def test_compare_no_previous():
    mod = _load("compare_invoices")
    mod.context = _ctx(AUTHED)
    mod.tools = FakeTools([SUMMARIES])
    out = mod.compare_invoices(month="february", compare_to="previous")
    assert out["status"] == "error" and "nothing earlier" in out["agent_action"].lower()


def test_list_bills():
    mod = _load("list_invoices")
    mod.context = _ctx(AUTHED)
    mod.tools = FakeTools([SUMMARIES])
    out = mod.list_invoices()
    assert out["status"] == "success"
    assert [b["month"] for b in out["invoices"]] == ["2026년 3월", "2026년 2월"]
    assert out["invoices"][0]["total"] == 5370.0


def test_update_language_korean():
    mod = _load("update_language")
    mod.context = _ctx({"active_language": "English"})
    out = mod.update_language(new_language="Korean")
    assert out["status"] == "success"
    assert out["active_language"] == "Korean"
    # Verify that the session state was updated
    assert mod.context.state["active_language"] == "Korean"
