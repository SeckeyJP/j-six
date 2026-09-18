"""UC-003: 請求一覧・明細の画面照会（hold-out 受入テスト）。

対応: UC-003 / SCR-001, SCR-002, SCR-003
"""

from app import batch

from .conftest import invoice_of


def _closed(billing, client):
    batch.run_month_close(billing, "2026-08", actor="keiri01")
    return invoice_of(client, "C001")


def test_uc003_invoice_list_screen_shows_closed_invoices(imported, client):
    """UC-003 / SCR-001: 請求一覧画面に締め結果が出る。"""
    _closed(imported, client)

    res = client.get("/invoices?year_month=2026-08")
    assert res.is_success, res.text
    body = res.text
    assert "株式会社アルファ" in body
    assert "ベータ商事株式会社" in body


def test_uc003_invoice_detail_screen_shows_lines_and_tax_summary(imported, client):
    """UC-003 / SCR-002: 明細画面に明細行と税率別内訳が出る。"""
    invoice = _closed(imported, client)

    res = client.get(f"/invoices/{invoice['invoice_no']}")
    assert res.is_success, res.text
    body = res.text
    assert "事務用品" in body
    assert "来客用茶菓" in body
    # 税率別の内訳が表示される（REQ-004）
    assert "8%" in body and "10%" in body


def test_uc003_preview_screen_is_reachable(imported, client):
    """UC-003 / SCR-003: 明細から請求書プレビューへ遷移できる。"""
    invoice = _closed(imported, client)

    res = client.get(f"/invoices/{invoice['invoice_no']}/preview")
    assert res.is_success, res.text
    assert "株式会社アルファ" in res.text


def test_uc003_unknown_invoice_returns_404(imported, client):
    """UC-003: 存在しない請求番号は 404（Design Spec 3.2）。"""
    assert client.get("/invoices/NOPE").status_code == 404
    assert client.get("/invoices/NOPE.json").status_code == 404
