"""EIF-001 / BATCH-002: 会計連携ファイル出力のテスト。"""

from datetime import date, datetime

import pytest

from app import batch
from app.accounting import HEADER, build_accounting_csv
from app.billing import BillingService

CLOCK = lambda: datetime(2026, 9, 1)  # noqa: E731


@pytest.fixture
def svc():
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
    return s


def _rows(csv_text):
    return [ln.split(",") for ln in csv_text.splitlines() if ln.strip()]


def test_req_009_header_row(svc):
    assert _rows(build_accounting_csv([]))[0] == list(HEADER)


def test_req_009_confirmed_invoice_has_header_and_detail_rows(svc):
    invoice = svc.close_month("2026-08", actor="k1")[0]
    svc.confirm(invoice.invoice_no, actor="k1")

    rows = _rows(build_accounting_csv(svc.list_invoices("2026-08")))
    kinds = [r[0] for r in rows[1:]]
    assert kinds == ["H", "D", "D"]


def test_req_009_detail_rows_carry_tax_breakdown(svc):
    invoice = svc.close_month("2026-08", actor="k1")[0]
    svc.confirm(invoice.invoice_no, actor="k1")

    rows = _rows(build_accounting_csv(svc.list_invoices("2026-08")))
    details = {r[5]: r for r in rows[1:] if r[0] == "D"}
    assert details["8"][6:9] == ["885", "70", "955"]
    assert details["10"][6:9] == ["999", "99", "1098"]


def test_req_009_header_row_carries_totals(svc):
    invoice = svc.close_month("2026-08", actor="k1")[0]
    svc.confirm(invoice.invoice_no, actor="k1")

    header = [
        r
        for r in _rows(build_accounting_csv(svc.list_invoices("2026-08")))
        if r[0] == "H"
    ][0]
    assert header[6:9] == ["1884", "169", "2053"]


def test_uc005_draft_invoices_are_excluded(svc):
    svc.close_month("2026-08", actor="k1")
    rows = _rows(build_accounting_csv(svc.list_invoices("2026-08")))
    assert [r for r in rows[1:]] == []


def test_batch_002_entry_point(svc):
    invoice = batch.run_month_close(svc, "2026-08", actor="k1")[0]
    svc.confirm(invoice.invoice_no, actor="k1")
    assert "H," in batch.run_accounting_export(svc, "2026-08")


def test_batch_001_entry_point(svc):
    assert len(batch.run_month_close(svc, "2026-08", actor="k1")) == 1


def test_req_009_draft_invoice_does_not_stop_later_confirmed_ones(svc):
    """未確定の請求があっても、後続の確定済みは出力される。

    mutation testing で `continue` を `break` に変えたミュータントが生き残った。
    請求番号順に並べたとき先頭が未確定だと、以降の確定済みが丸ごと欠ける。
    """
    svc.register_customer(
        "C002", "ベータ", closing_day=31, payment_terms="NEXT_MONTH_END"
    )
    svc.add_sale(
        record_id="S3",
        customer_code="C002",
        sales_date=date(2026, 8, 5),
        item_name="保守",
        quantity=1,
        unit_price=10000,
        tax_rate=10,
    )
    invoices = svc.close_month("2026-08", actor="k1")
    # C001（INV-...-0001）は未確定のまま、C002（-0002）だけ確定する
    beta = [inv for inv in invoices if inv.customer_code == "C002"][0]
    svc.confirm(beta.invoice_no, actor="k1")

    rows = _rows(build_accounting_csv(svc.list_invoices("2026-08")))
    headers = [r for r in rows if r[0] == "H"]
    assert len(headers) == 1
    assert headers[0][1] == beta.invoice_no


def test_req_009_csv_uses_lf_line_endings(svc):
    """会計連携ファイルの改行は LF に固定する（環境依存にしない）。"""
    invoice = svc.close_month("2026-08", actor="k1")[0]
    svc.confirm(invoice.invoice_no, actor="k1")
    csv_text = build_accounting_csv(svc.list_invoices("2026-08"))
    assert "\r\n" not in csv_text
    assert csv_text.endswith("\n")
