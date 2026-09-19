"""ドメイン単体テスト（REQ-nnn タグ付き）。"""

from datetime import date, datetime

import pytest

from app.billing import BillingError, BillingService, calc_tax
from app.models import InvoiceStatus, TaxRate

CLOCK = lambda: datetime(2026, 9, 1, 10, 0, 0)  # noqa: E731


@pytest.fixture
def svc():
    s = BillingService(clock=CLOCK)
    s.register_customer(
        "C001", "株式会社アルファ", closing_day=31, payment_terms="NEXT_MONTH_END"
    )
    s.register_customer(
        "C002", "ベータ商事", closing_day=20, payment_terms="MONTH_AFTER_NEXT_END"
    )
    return s


def _sale(svc, code, day, price, qty=1, rate=10, rid=None, month=8):
    svc.add_sale(
        record_id=rid or f"S{code}{month:02d}{day:02d}{price}",
        customer_code=code,
        sales_date=date(2026, month, day),
        item_name="商品",
        quantity=qty,
        unit_price=price,
        tax_rate=rate,
    )


class TestTaxCalculation:
    """REQ-005 / ADR-0001, ADR-0002: 端数処理は税率ごとに1回・切捨て。"""

    def test_req_005_floor_rounding(self):
        assert calc_tax(2110, 10) == 211  # floor(211.0)
        assert calc_tax(885, 8) == 70  # floor(70.8)
        assert calc_tax(999, 10) == 99  # floor(99.9)

    def test_req_005_rounds_once_not_per_line(self):
        """明細ごとに丸めた合計と、まとめて丸めた額は一致しないことがある。"""
        per_line = calc_tax(999, 10) + calc_tax(1111, 10)
        once = calc_tax(999 + 1111, 10)
        assert per_line == 210
        assert once == 211
        assert once != per_line

    def test_req_005_zero_subtotal(self):
        assert calc_tax(0, 10) == 0


class TestClosingPeriod:
    """REQ-001: 締め日から請求対象期間が決まる。"""

    def test_req_001_month_end_closing(self, svc):
        _sale(svc, "C001", 3, 1000)
        invoices = svc.close_month("2026-08", actor="k1")
        inv = invoices[0]
        assert inv.period_from == date(2026, 8, 1)
        assert inv.period_to == date(2026, 8, 31)
        assert inv.closing_date == date(2026, 8, 31)

    def test_req_001_day20_closing(self, svc):
        """20日締めは前月21日〜当月20日。"""
        _sale(svc, "C002", 25, 1000, month=7)  # 前月21日以降 → 対象
        _sale(svc, "C002", 15, 2000)  # 当月20日まで → 対象
        _sale(svc, "C002", 25, 4000)  # 当月21日以降 → 対象外
        invoices = svc.close_month("2026-08", actor="k1")
        inv = invoices[0]
        assert inv.period_from == date(2026, 7, 21)
        assert inv.period_to == date(2026, 8, 20)
        assert inv.subtotal == 3000

    def test_req_001_february_month_end(self, svc):
        """月末締めは月の日数に追随する。"""
        _sale(svc, "C001", 10, 1000, month=2)
        inv = svc.close_month("2026-02", actor="k1")[0]
        assert inv.closing_date == date(2026, 2, 28)


class TestDueDate:
    """REQ-002: 支払期日 = 締め日 + 支払サイト。"""

    def test_req_002_next_month_end(self, svc):
        _sale(svc, "C001", 3, 1000)
        assert svc.close_month("2026-08", actor="k1")[0].due_date == date(2026, 9, 30)

    def test_req_002_month_after_next_end(self, svc):
        _sale(svc, "C002", 15, 1000)
        assert svc.close_month("2026-08", actor="k1")[0].due_date == date(2026, 10, 31)

    def test_req_002_year_boundary(self, svc):
        _sale(svc, "C001", 5, 1000, month=12)
        assert svc.close_month("2026-12", actor="k1")[0].due_date == date(2027, 1, 31)

    def test_req_002_unknown_payment_terms_rejected(self):
        s = BillingService(clock=CLOCK)
        with pytest.raises(BillingError):
            s.register_customer("C9", "X", closing_day=31, payment_terms="SOMEDAY")

    def test_req_001_unknown_closing_day_rejected(self):
        s = BillingService(clock=CLOCK)
        with pytest.raises(BillingError):
            s.register_customer(
                "C9", "X", closing_day=15, payment_terms="NEXT_MONTH_END"
            )


class TestAggregation:
    """REQ-003 / REQ-008: 取引先ごとに1請求。売上が無ければ作らない。"""

    def test_req_003_one_invoice_per_customer(self, svc):
        _sale(svc, "C001", 3, 100)
        _sale(svc, "C001", 5, 200)
        _sale(svc, "C002", 5, 300)
        invoices = svc.close_month("2026-08", actor="k1")
        assert len(invoices) == 2
        assert sorted(i.customer_code for i in invoices) == ["C001", "C002"]

    def test_req_003_lines_are_kept(self, svc):
        _sale(svc, "C001", 3, 100, qty=2)
        _sale(svc, "C001", 5, 200)
        inv = svc.close_month("2026-08", actor="k1")[0]
        assert [ln.amount for ln in inv.lines] == [200, 200]
        assert inv.subtotal == 400

    def test_req_008_no_sales_no_invoice(self, svc):
        assert svc.close_month("2026-08", actor="k1") == []

    def test_req_008_sales_outside_period_excluded(self, svc):
        _sale(svc, "C001", 15, 1000, month=7)
        assert svc.close_month("2026-08", actor="k1") == []

    def test_req_003_unknown_customer_sale_is_rejected(self, svc):
        with pytest.raises(BillingError):
            _sale(svc, "C999", 3, 100)


class TestTaxSummary:
    """REQ-004: 税率区分ごとに対価の額を区分する。"""

    def test_req_004_splits_by_rate(self, svc):
        _sale(svc, "C001", 3, 999, rate=10)
        _sale(svc, "C001", 5, 885, rate=8)
        inv = svc.close_month("2026-08", actor="k1")[0]
        by_rate = {s.tax_rate: s for s in inv.tax_summaries}
        assert by_rate[TaxRate.STANDARD].subtotal == 999
        assert by_rate[TaxRate.REDUCED].subtotal == 885
        assert by_rate[TaxRate.STANDARD].tax_amount == 99
        assert by_rate[TaxRate.REDUCED].tax_amount == 70

    def test_req_004_single_rate_has_one_summary(self, svc):
        _sale(svc, "C001", 3, 1000, rate=10)
        inv = svc.close_month("2026-08", actor="k1")[0]
        assert len(inv.tax_summaries) == 1

    def test_req_004_summaries_are_sorted_by_rate(self, svc):
        _sale(svc, "C001", 3, 1000, rate=10)
        _sale(svc, "C001", 4, 500, rate=8)
        inv = svc.close_month("2026-08", actor="k1")[0]
        assert [s.tax_rate.percent for s in inv.tax_summaries] == [8, 10]

    def test_req_004_invalid_rate_rejected(self, svc):
        with pytest.raises(BillingError):
            _sale(svc, "C001", 3, 1000, rate=5)

    def test_req_005_totals(self, svc):
        _sale(svc, "C001", 3, 999, rate=10)
        _sale(svc, "C001", 4, 1111, rate=10)
        _sale(svc, "C001", 5, 885, rate=8)
        inv = svc.close_month("2026-08", actor="k1")[0]
        assert inv.subtotal == 2995
        assert inv.tax_total == 281
        assert inv.total == 3276


class TestConfirmation:
    """REQ-007: 確定済みは変更不可。"""

    def test_req_007_confirm(self, svc):
        _sale(svc, "C001", 3, 1000)
        inv = svc.close_month("2026-08", actor="k1")[0]
        svc.confirm(inv.invoice_no, actor="k1")
        assert svc.get_invoice(inv.invoice_no).status is InvoiceStatus.CONFIRMED

    def test_req_007_double_confirm_rejected(self, svc):
        _sale(svc, "C001", 3, 1000)
        inv = svc.close_month("2026-08", actor="k1")[0]
        svc.confirm(inv.invoice_no, actor="k1")
        with pytest.raises(BillingError):
            svc.confirm(inv.invoice_no, actor="k1")

    def test_req_007_reclose_rejected_when_confirmed(self, svc):
        _sale(svc, "C001", 3, 1000)
        inv = svc.close_month("2026-08", actor="k1")[0]
        svc.confirm(inv.invoice_no, actor="k1")
        with pytest.raises(BillingError):
            svc.close_month("2026-08", actor="k1")

    def test_req_007_reclose_allowed_while_draft(self, svc):
        _sale(svc, "C001", 3, 1000)
        svc.close_month("2026-08", actor="k1")
        again = svc.close_month("2026-08", actor="k1")
        assert len(again) == 1

    def test_req_007_unknown_invoice(self, svc):
        with pytest.raises(BillingError):
            svc.get_invoice("NOPE")


class TestAudit:
    """REQ-010: 締め処理を監査記録する。"""

    def test_req_010_close_is_logged(self, svc):
        _sale(svc, "C001", 3, 1000)
        svc.close_month("2026-08", actor="keiri01")
        entry = svc.audit_log[-1]
        assert (entry.action, entry.actor, entry.year_month, entry.created_count) == (
            "CLOSE",
            "keiri01",
            "2026-08",
            1,
        )
        assert entry.at == CLOCK()

    def test_req_010_confirm_is_logged(self, svc):
        _sale(svc, "C001", 3, 1000)
        inv = svc.close_month("2026-08", actor="k1")[0]
        svc.confirm(inv.invoice_no, actor="keiri02")
        assert svc.audit_log[-1].action == "CONFIRM"
        assert svc.audit_log[-1].actor == "keiri02"

    def test_req_010_log_has_no_line_details(self, svc):
        """Design Spec 6.2: 監査ログに明細内容を出さない。"""
        _sale(svc, "C001", 3, 1000)
        svc.close_month("2026-08", actor="k1")
        assert not hasattr(svc.audit_log[-1], "lines")


def test_reset_clears_store(svc):
    _sale(svc, "C001", 3, 1000)
    svc.close_month("2026-08", actor="k1")
    svc.reset(clock=CLOCK)
    assert svc.list_invoices() == []


class TestYearBoundary:
    """REQ-001: 1月締めは前年12月から期間が始まる。

    mutation testing で `month > 1` の分岐（前月が前年になる경路）が
    検証されていないことが判明したため追加した。
    """

    def test_req_001_january_period_starts_in_previous_year(self, svc):
        _sale(svc, "C001", 10, 1000, month=1, rid="S-jan")
        inv = svc.close_month("2026-01", actor="k1")[0]
        assert inv.period_from == date(2026, 1, 1)
        assert inv.closing_date == date(2026, 1, 31)

    def test_req_001_january_day20_closing_spans_year_boundary(self):
        s = BillingService(clock=CLOCK)
        s.register_customer("C1", "X", closing_day=20, payment_terms="NEXT_MONTH_END")
        s.add_sale(
            record_id="S1",
            customer_code="C1",
            sales_date=date(2025, 12, 25),
            item_name="年末分",
            quantity=1,
            unit_price=1000,
            tax_rate=10,
        )
        inv = s.close_month("2026-01", actor="k1")[0]
        assert inv.period_from == date(2025, 12, 21)
        assert inv.period_to == date(2026, 1, 20)
        assert inv.subtotal == 1000


class TestInvoiceLines:
    """REQ-003: 明細の採番と転記。"""

    def test_req_003_line_no_starts_at_1_and_increments(self, svc):
        _sale(svc, "C001", 3, 100, rid="A")
        _sale(svc, "C001", 5, 200, rid="B")
        _sale(svc, "C001", 7, 300, rid="C")
        inv = svc.close_month("2026-08", actor="k1")[0]
        assert [ln.line_no for ln in inv.lines] == [1, 2, 3]

    def test_req_003_line_carries_quantity_and_unit_price(self, svc):
        _sale(svc, "C001", 3, 250, qty=4)
        line = svc.close_month("2026-08", actor="k1")[0].lines[0]
        assert (line.quantity, line.unit_price, line.amount) == (4, 250, 1000)

    def test_req_003_lines_are_ordered_by_sales_date(self, svc):
        _sale(svc, "C001", 20, 100, rid="late")
        _sale(svc, "C001", 3, 200, rid="early")
        inv = svc.close_month("2026-08", actor="k1")[0]
        assert [ln.amount for ln in inv.lines] == [200, 100]


class TestInvoiceNumbering:
    """請求番号の採番（再締めで変わらないこと）。"""

    def test_invoice_no_format(self, svc):
        _sale(svc, "C001", 3, 1000)
        assert svc.close_month("2026-08", actor="k1")[0].invoice_no == "INV-202608-0001"

    def test_invoice_no_increments_per_customer(self, svc):
        _sale(svc, "C001", 3, 1000)
        _sale(svc, "C002", 15, 1000)
        nos = sorted(i.invoice_no for i in svc.close_month("2026-08", actor="k1"))
        assert nos == ["INV-202608-0001", "INV-202608-0002"]

    def test_req_007_reclose_keeps_the_same_invoice_no(self, svc):
        """未確定の請求を作り直しても番号は変わらない。

        mutation testing で `_find_invoice` の再利用経路が未検証と判明したため追加。
        番号が変わると、先に通知した請求番号と食い違う。
        """
        _sale(svc, "C001", 3, 1000)
        first = svc.close_month("2026-08", actor="k1")[0].invoice_no
        _sale(svc, "C001", 5, 2000, rid="extra")
        second = svc.close_month("2026-08", actor="k1")[0]
        assert second.invoice_no == first
        assert second.subtotal == 3000

    def test_reset_restarts_numbering(self, svc):
        _sale(svc, "C001", 3, 1000)
        svc.close_month("2026-08", actor="k1")
        svc.reset(clock=CLOCK)
        svc.register_customer(
            "C001", "X", closing_day=31, payment_terms="NEXT_MONTH_END"
        )
        _sale(svc, "C001", 3, 1000)
        assert svc.close_month("2026-08", actor="k1")[0].invoice_no == "INV-202608-0001"
