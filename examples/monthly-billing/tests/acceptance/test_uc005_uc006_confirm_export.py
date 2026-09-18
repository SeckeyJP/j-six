"""UC-005 / UC-006: 請求の確定と会計連携（hold-out 受入テスト）。

対応: UC-005, UC-006 / REQ-007, REQ-009 / EIF-001, BATCH-002
"""

from app import batch

from .conftest import invoice_of


def _closed(billing, client):
    batch.run_month_close(billing, "2026-08", actor="keiri01")
    return invoice_of(client, "C001")


def test_uc006_confirm_marks_invoice_as_confirmed(imported, client):
    """UC-006 / REQ-007: 請求を確定できる。"""
    invoice = _closed(imported, client)

    res = client.post(
        f"/invoices/{invoice['invoice_no']}/confirm", json={"actor": "keiri01"}
    )
    assert res.is_success, res.text

    assert invoice_of(client, "C001")["status"] == "CONFIRMED"


def test_uc006_confirmed_invoice_cannot_be_reclosed(imported, client):
    """UC-006 / REQ-007: 確定済みを含む期間の再締めは拒否される。"""
    invoice = _closed(imported, client)
    client.post(f"/invoices/{invoice['invoice_no']}/confirm", json={"actor": "keiri01"})

    try:
        batch.run_month_close(imported, "2026-08", actor="keiri01")
    except Exception:
        pass
    else:
        raise AssertionError("確定済みの期間を再締めできてしまった")

    # 金額が変わっていないこと（PROP-006 の例ベース版）
    assert invoice_of(client, "C001")["total"] == 3276


def test_uc006_confirming_twice_is_rejected(imported, client):
    """UC-006: 二重確定は 409（Design Spec 3.2）。"""
    invoice = _closed(imported, client)
    client.post(f"/invoices/{invoice['invoice_no']}/confirm", json={"actor": "keiri01"})

    res = client.post(
        f"/invoices/{invoice['invoice_no']}/confirm", json={"actor": "keiri01"}
    )
    assert res.status_code == 409


def test_uc005_accounting_export_has_header_and_tax_breakdown(imported, client):
    """UC-005 / REQ-009 / EIF-001: 会計連携は請求ヘッダ1行＋税率ごとの内訳行。"""
    invoice = _closed(imported, client)
    client.post(f"/invoices/{invoice['invoice_no']}/confirm", json={"actor": "keiri01"})

    csv_text = batch.run_accounting_export(imported, "2026-08")
    rows = [ln.split(",") for ln in csv_text.splitlines() if ln.strip()]

    kinds = [r[0] for r in rows[1:]]  # 先頭はヘッダ行
    assert kinds.count("H") == 1  # 確定済みは C001 のみ
    assert kinds.count("D") == 2  # 10% と 8% の内訳


def test_uc005_unconfirmed_invoices_are_not_exported(imported, client):
    """UC-005: 未確定の請求は会計連携に出さない。"""
    _closed(imported, client)

    csv_text = batch.run_accounting_export(imported, "2026-08")
    rows = [ln for ln in csv_text.splitlines() if ln.startswith("H")]
    assert rows == []
