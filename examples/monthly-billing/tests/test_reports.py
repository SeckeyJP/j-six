"""RPT-002 / 表示用ビューのテスト。"""

from datetime import date, datetime

import pytest

from app.billing import BillingService
from app.reports import INVOICE_LIST_COLUMNS, build_invoice_list_csv, invoice_view

CLOCK = lambda: datetime(2026, 9, 1)  # noqa: E731


@pytest.fixture
def invoice():
    s = BillingService(clock=CLOCK)
    s.register_customer(
        "C001", "アルファ", closing_day=31, payment_terms="NEXT_MONTH_END"
    )
    s.add_sale(
        record_id="S1",
        customer_code="C001",
        sales_date=date(2026, 8, 3),
        item_name="事務用品",
        quantity=3,
        unit_price=333,
        tax_rate=10,
    )
    s.add_sale(
        record_id="S2",
        customer_code="C001",
        sales_date=date(2026, 8, 20),
        item_name="茶菓",
        quantity=5,
        unit_price=177,
        tax_rate=8,
    )
    return s.close_month("2026-08", actor="k1")[0]


def test_rpt_002_header(invoice):
    assert build_invoice_list_csv([]).strip() == ",".join(INVOICE_LIST_COLUMNS)


def test_rpt_002_row(invoice):
    rows = build_invoice_list_csv([invoice]).splitlines()
    assert len(rows) == 2
    assert rows[1].split(",")[2] == "アルファ"
    assert rows[1].split(",")[-1] == "DRAFT"


def test_req_004_view_exposes_tax_summaries(invoice):
    view = invoice_view(invoice)
    by_rate = {s["tax_rate"]: s for s in view["tax_summaries"]}
    assert by_rate[8]["is_reduced"] is True
    assert by_rate[10]["is_reduced"] is False


def test_req_003_view_exposes_lines(invoice):
    view = invoice_view(invoice)
    assert [ln["item_name"] for ln in view["lines"]] == ["事務用品", "茶菓"]
    assert view["lines"][0]["amount"] == 999


def test_view_dates_are_iso_strings(invoice):
    view = invoice_view(invoice)
    assert view["closing_date"] == "2026-08-31"
    assert view["due_date"] == "2026-09-30"
    assert view["period_from"] == "2026-08-01"


def test_req_005_view_totals(invoice):
    view = invoice_view(invoice)
    assert (view["subtotal"], view["tax_total"], view["total"]) == (1884, 169, 2053)


def test_rpt_002_csv_uses_lf_line_endings(invoice):
    """請求一覧表の改行も LF に固定する。"""
    csv_text = build_invoice_list_csv([invoice])
    assert "\r\n" not in csv_text


def test_rpt_002_rows_follow_invoice_order():
    """一覧は請求番号順（list_invoices の順序）をそのまま保つ。"""
    s = BillingService(clock=CLOCK)
    for code, name in (("C002", "ベータ"), ("C001", "アルファ")):
        s.register_customer(code, name, closing_day=31, payment_terms="NEXT_MONTH_END")
        s.add_sale(
            record_id=f"S{code}",
            customer_code=code,
            sales_date=date(2026, 8, 3),
            item_name="商品",
            quantity=1,
            unit_price=1000,
            tax_rate=10,
        )
    invoices = s.close_month("2026-08", actor="k1")
    rows = build_invoice_list_csv(invoices).splitlines()[1:]
    assert [r.split(",")[0] for r in rows] == [inv.invoice_no for inv in invoices]
