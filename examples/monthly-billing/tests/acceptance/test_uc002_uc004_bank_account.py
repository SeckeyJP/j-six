"""UC-002 / UC-004: 請求書への振込先口座の記載（hold-out 受入テスト）。

対応: UC-002, UC-004 / REQ-011, REQ-012, REQ-013 / PROP-007, PROP-008

公開インタフェース（バッチのエントリポイントと HTTP API）だけで検証する。
"""

from app import batch

from .conftest import invoice_of

BANK = {
    "bank_name": "ジェイシックス銀行",
    "branch_name": "本店営業部",
    "account_type": "普通",
    "account_number": "1234567",
    "account_holder": "カ）ジェイシツクスシヨウジ",
}


def test_uc004_report_shows_bank_account(imported, client):
    """REQ-011: 登録した振込先が請求書に印字される。"""
    imported.set_bank_account("C001", **BANK)
    batch.run_month_close(imported, "2026-08", actor="keiri01")
    invoice = invoice_of(client, "C001")

    body = client.get(f"/invoices/{invoice['invoice_no']}/report").text

    assert "ジェイシックス銀行" in body
    assert "本店営業部" in body
    assert "1234567" in body
    assert "カ）ジェイシツクスシヨウジ" in body


def test_uc002_bank_account_is_snapshot_at_closing(imported, client):
    """REQ-012 / PROP-007: 締め後にマスタを変えても請求書の記載は変わらない。"""
    imported.set_bank_account("C001", **BANK)
    batch.run_month_close(imported, "2026-08", actor="keiri01")
    invoice = invoice_of(client, "C001")

    changed = dict(BANK, bank_name="別銀行", account_number="9999999")
    imported.set_bank_account("C001", **changed)

    body = client.get(f"/invoices/{invoice['invoice_no']}/report").text
    assert "ジェイシックス銀行" in body
    assert "1234567" in body
    assert "別銀行" not in body
    assert "9999999" not in body


def test_uc002_close_succeeds_when_bank_account_is_missing(imported, client):
    """REQ-013 / PROP-008: 未登録の取引先があっても締めは成功し、他社の請求も作られる。"""
    imported.set_bank_account("C001", **BANK)  # C002 は未登録のまま

    created = batch.run_month_close(imported, "2026-08", actor="keiri01")

    assert {inv.customer_code for inv in created} >= {"C001", "C002"}

    missing = invoice_of(client, "C002")
    body = client.get(f"/invoices/{missing['invoice_no']}/report").text
    assert "未登録" in body


def test_uc002_missing_bank_account_is_recorded_as_warning(imported, client):
    """REQ-013: 未登録があった締めは監査記録に警告として残る。"""
    imported.set_bank_account("C001", **BANK)  # C002 は未登録のまま

    batch.run_month_close(imported, "2026-08", actor="keiri01")

    warnings = [
        entry
        for entry in imported.audit_log
        if entry.action == "CLOSE_WARN_NO_BANK_ACCOUNT"
    ]
    assert warnings, "振込先未登録の警告が監査記録に無い"
    assert any(entry.year_month == "2026-08" for entry in warnings)
