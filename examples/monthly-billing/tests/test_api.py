"""HTTP 層の結線テスト（画面 SCR / 帳票 RPT）。"""

from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app, service

CLOCK = lambda: datetime(2026, 9, 1, 10, 0, 0)  # noqa: E731


@pytest.fixture
def client():
    service.reset(clock=CLOCK)
    service.register_customer(
        "C001", "株式会社アルファ", closing_day=31, payment_terms="NEXT_MONTH_END"
    )
    service.add_sale(
        record_id="S1",
        customer_code="C001",
        sales_date=date(2026, 8, 3),
        item_name="事務用品",
        quantity=3,
        unit_price=333,
        tax_rate=10,
    )
    service.add_sale(
        record_id="S2",
        customer_code="C001",
        sales_date=date(2026, 8, 20),
        item_name="来客用茶菓",
        quantity=5,
        unit_price=177,
        tax_rate=8,
    )
    return TestClient(app)


@pytest.fixture
def closed(client):
    service.close_month("2026-08", actor="k1")
    return client


def _no(client):
    return client.get("/invoices.json").json()[0]["invoice_no"]


def test_json_routes_are_declared_before_html_detail(closed):
    """REQ-006: `/invoices/{no}.json` が HTML ルートに吸われないこと。

    パスパラメータは "." にも一致するため、宣言順を誤ると
    invoice_no="INV-....json" として HTML 側に流れ 404 になる。
    hold-out 受入テストが実際にこの不具合を検出したため、回帰として固定する。
    """
    res = closed.get(f"/invoices/{_no(closed)}.json")
    assert res.is_success
    assert res.headers["content-type"].startswith("application/json")


class TestScreens:
    def test_scr_001_list(self, closed):
        res = closed.get("/invoices?year_month=2026-08")
        assert res.is_success
        assert "株式会社アルファ" in res.text

    def test_scr_001_empty(self, client):
        assert "対象の請求がありません" in client.get("/invoices").text

    def test_scr_002_detail(self, closed):
        body = closed.get(f"/invoices/{_no(closed)}").text
        assert "事務用品" in body and "来客用茶菓" in body

    def test_scr_003_preview(self, closed):
        assert "株式会社アルファ" in closed.get(f"/invoices/{_no(closed)}/preview").text

    def test_scr_002_unknown_is_404(self, closed):
        assert closed.get("/invoices/NOPE").status_code == 404

    def test_scr_003_unknown_is_404(self, closed):
        assert closed.get("/invoices/NOPE/preview").status_code == 404


class TestReports:
    def test_rpt_001_report(self, closed):
        body = closed.get(f"/invoices/{_no(closed)}/report").text
        assert "T1234567890123" in body  # REQ-006 登録番号
        assert "軽減" in body

    def test_rpt_001_unknown_is_404(self, closed):
        assert closed.get("/invoices/NOPE/report").status_code == 404

    def test_rpt_002_csv(self, closed):
        res = closed.get("/invoices.csv?year_month=2026-08")
        assert res.is_success
        assert res.headers["content-type"].startswith("text/csv")
        assert len(res.text.strip().splitlines()) == 2

    def test_rpt_002_csv_empty(self, client):
        assert len(client.get("/invoices.csv").text.strip().splitlines()) == 1


class TestConfirm:
    def test_uc006_confirm_redirects(self, closed):
        res = closed.post(
            f"/invoices/{_no(closed)}/confirm",
            data={"actor": "k1"},
            follow_redirects=False,
        )
        assert res.status_code == 303

    def test_uc006_confirm_default_actor(self, closed):
        assert closed.post(f"/invoices/{_no(closed)}/confirm").is_success

    def test_uc006_double_confirm_is_409(self, closed):
        no = _no(closed)
        closed.post(f"/invoices/{no}/confirm", data={"actor": "k1"})
        assert (
            closed.post(f"/invoices/{no}/confirm", data={"actor": "k1"}).status_code
            == 409
        )

    def test_uc006_unknown_is_404(self, closed):
        assert (
            closed.post("/invoices/NOPE/confirm", data={"actor": "k1"}).status_code
            == 404
        )


class TestJsonData:
    def test_list_json(self, closed):
        rows = closed.get("/invoices.json?year_month=2026-08").json()
        assert len(rows) == 1
        assert rows[0]["total"] == 999 + 885 + 99 + 70

    def test_detail_json_has_tax_summaries(self, closed):
        detail = closed.get(f"/invoices/{_no(closed)}.json").json()
        by_rate = {s["tax_rate"]: s for s in detail["tax_summaries"]}
        assert by_rate[10]["tax_amount"] == 99
        assert by_rate[8]["tax_amount"] == 70
        assert by_rate[8]["is_reduced"] is True

    def test_detail_json_unknown_is_404(self, closed):
        assert closed.get("/invoices/NOPE.json").status_code == 404


class TestConfirmActor:
    """UC-006 / REQ-010: 操作者がどの形式でも監査ログに記録される。

    G3 judge が「JSON ボディの actor が無視され既定値が記録される」ことを指摘した。
    hold-out は既定値と同じ値を送っていたため偶然通っていた。
    """

    def test_actor_from_form(self, closed):
        closed.post(f"/invoices/{_no(closed)}/confirm", data={"actor": "keiri-form"})
        assert service.audit_log[-1].actor == "keiri-form"

    def test_actor_from_json(self, closed):
        closed.post(f"/invoices/{_no(closed)}/confirm", json={"actor": "keiri-json"})
        assert service.audit_log[-1].actor == "keiri-json"

    def test_actor_defaults_without_body(self, closed):
        closed.post(f"/invoices/{_no(closed)}/confirm")
        assert service.audit_log[-1].actor == "keiri01"

    def test_actor_defaults_on_broken_json(self, closed):
        closed.post(
            f"/invoices/{_no(closed)}/confirm",
            content=b"{not json",
            headers={"content-type": "application/json"},
        )
        assert service.audit_log[-1].actor == "keiri01"

    def test_actor_defaults_on_empty_value(self, closed):
        closed.post(f"/invoices/{_no(closed)}/confirm", json={"actor": ""})
        assert service.audit_log[-1].actor == "keiri01"

    def test_multipart_is_rejected_not_defaulted(self, closed):
        """multipart/form-data は受け付けず 415 にする（ADR-0004）。

        受け付けない形式を黙って既定値の操作者で確定すると、監査ログ（REQ-010）に
        誤った操作者が残る。確定もしない。
        """
        no = _no(closed)
        res = closed.post(
            f"/invoices/{no}/confirm",
            files={"actor": (None, "keiri-multipart")},
        )
        assert res.status_code == 415
        assert service.get_invoice(no).status.value == "DRAFT"
