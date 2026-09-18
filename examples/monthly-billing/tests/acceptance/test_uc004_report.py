"""UC-004: 請求書の出力（hold-out 受入テスト）。

対応: UC-004 / REQ-004, REQ-005, REQ-006 / RPT-001, RPT-002
"""

from app import batch

from .conftest import invoice_of


def _closed(billing, client, customer_code="C001"):
    batch.run_month_close(billing, "2026-08", actor="keiri01")
    return invoice_of(client, customer_code)


def test_uc004_report_has_qualified_invoice_items(imported, client):
    """UC-004 / REQ-006: 適格請求書の記載事項が揃っている。

    (1) 発行者の氏名または名称と登録番号 (2) 取引年月日 (3) 取引内容
    (4) 税率ごとに区分した対価の額と消費税額 (5) 交付を受ける事業者の名称
    """
    invoice = _closed(imported, client)

    res = client.get(f"/invoices/{invoice['invoice_no']}/report")
    assert res.is_success, res.text
    body = res.text

    assert "T" in body and "登録番号" in body  # (1) 適格請求書発行事業者の登録番号
    assert "2026-08-31" in body  # (2) 取引年月日（締め日）
    assert "事務用品" in body  # (3) 取引内容
    assert "10%" in body and "8%" in body  # (4) 税率ごとの区分
    assert "株式会社アルファ" in body  # (5) 交付先の名称


def test_uc004_report_marks_reduced_tax_items(imported, client):
    """UC-004 / REQ-006: 軽減税率の対象である旨がわかる。"""
    invoice = _closed(imported, client)

    body = client.get(f"/invoices/{invoice['invoice_no']}/report").text
    assert "軽減" in body


def test_uc004_tax_is_rounded_once_per_rate(imported, client):
    """UC-004 / REQ-005: 端数処理は請求単位・税率ごとに1回（ADR-0001）。

    10% 対象は 999 + 1111 = 2110 → 消費税 211（floor(2110 × 0.1)）
    8% 対象は 885 → 消費税 70（floor(885 × 0.08) = floor(70.8)）

    明細ごとに丸めて合計すると 10% は floor(99.9)+floor(111.1)=99+111=210 となり
    1円ずれる。請求単位で丸めた 211 が正しい。
    """
    invoice = _closed(imported, client)

    by_rate = {s["tax_rate"]: s for s in invoice["tax_summaries"]}
    assert by_rate[10]["subtotal"] == 2110
    assert by_rate[10]["tax_amount"] == 211
    assert by_rate[8]["subtotal"] == 885
    assert by_rate[8]["tax_amount"] == 70

    assert invoice["subtotal"] == 2995
    assert invoice["tax_total"] == 281
    assert invoice["total"] == 3276


def test_uc004_invoice_list_csv_is_downloadable(imported, client):
    """UC-004 / RPT-002: 請求一覧表を CSV で出力できる。"""
    _closed(imported, client)

    res = client.get("/invoices.csv?year_month=2026-08")
    assert res.is_success, res.text
    lines = [ln for ln in res.text.splitlines() if ln.strip()]
    assert len(lines) == 3  # ヘッダ + 2件
    assert "株式会社アルファ" in res.text
