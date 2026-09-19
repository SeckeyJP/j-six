"""UC-001 / UC-002: 売上取込 → 月次締め（hold-out 受入テスト）。

対応: UC-001, UC-002 / REQ-001, REQ-003, REQ-008, REQ-010
"""

from app import batch, importer

from .conftest import SALES_CSV, invoice_of


def test_uc001_imports_sales_from_sales_management_system(billing):
    """UC-001 / EIF-002: 販売管理システムの CSV を取り込める。"""
    result = importer.import_sales(billing, SALES_CSV)
    assert result.imported == 5
    assert result.skipped == 0


def test_uc001_import_is_idempotent(billing):
    """UC-001: 同じ record_id の再取込は無視される（冪等）。"""
    importer.import_sales(billing, SALES_CSV)
    again = importer.import_sales(billing, SALES_CSV)
    assert again.imported == 0
    assert again.skipped == 5


def test_uc002_creates_one_invoice_per_customer_with_sales(imported):
    """UC-002 / REQ-003, REQ-008: 対象期間に売上がある取引先ごとに請求が1件できる。

    C001 は3件・C002 は1件の売上がある。C003 は7月の売上しか無いため
    8月締めでは請求が作られない（REQ-008）。
    """
    invoices = batch.run_month_close(imported, "2026-08", actor="keiri01")

    assert sorted(inv.customer_code for inv in invoices) == ["C001", "C002"]


def test_uc002_invoice_aggregates_all_sales_in_period(imported, client):
    """UC-002 / REQ-003: 期間内の売上がすべて1請求にまとまる。"""
    batch.run_month_close(imported, "2026-08", actor="keiri01")

    detail = invoice_of(client, "C001")
    # 事務用品 333×3=999 / 配送料 1111×1=1111 / 来客用茶菓 177×5=885
    assert detail["subtotal"] == 999 + 1111 + 885
    assert len(detail["lines"]) == 3


def test_uc002_close_is_recorded_in_audit_log(imported):
    """UC-002 / REQ-010: 締め処理が実行日時・操作者・対象年月・件数とともに残る。"""
    batch.run_month_close(imported, "2026-08", actor="keiri01")

    entry = imported.audit_log[-1]
    assert entry.action == "CLOSE"
    assert entry.actor == "keiri01"
    assert entry.year_month == "2026-08"
    assert entry.created_count == 2
    assert entry.at is not None


def test_uc002_due_date_follows_payment_terms(imported, client):
    """UC-002 / REQ-001, REQ-002: 締め日と支払サイトから支払期日が決まる。

    どちらも月末締め。C001 は翌月末払い、C002 は翌々月末払い。
    """
    batch.run_month_close(imported, "2026-08", actor="keiri01")

    assert invoice_of(client, "C001")["closing_date"] == "2026-08-31"
    assert invoice_of(client, "C001")["due_date"] == "2026-09-30"
    assert invoice_of(client, "C002")["due_date"] == "2026-10-31"
