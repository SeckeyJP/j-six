"""Property-based tests（PROP-001〜006）。

要求 Spec「3.3 受入条件と Property」で定義した性質を、Hypothesis で入力空間全体に
対して検証する。例ベースのテスト（test_billing.py）を置き換えるものではなく併用する。

PROP-002 がこのサンプルの中心。素朴な実装（明細ごとに丸めて合計）は明細1件や端数の
出ない入力では正しい実装と同じ結果になるため、例ベースでは検出しにくい。
Hypothesis に端数の出る組合せを探させることで初めて差が出る。
"""

from datetime import date, datetime

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from app.billing import BillingService, calc_tax
from app.models import InvoiceStatus, TaxRate

CLOCK = lambda: datetime(2026, 9, 1, 10, 0, 0)  # noqa: E731

# 端数が出る組合せを引き当てるため、10 で割り切れない額も生成されるようにする
AMOUNT = st.integers(min_value=1, max_value=1_000_000)
QTY = st.integers(min_value=1, max_value=20)
RATE = st.sampled_from([8, 10])
CLOSING_DAY = st.sampled_from([20, 31])
TERMS = st.sampled_from(["NEXT_MONTH_END", "MONTH_AFTER_NEXT_END"])
#: 月末締めの期間に確実に収まる日
DAY_IN_PERIOD = st.integers(min_value=1, max_value=20)

LineSpec = st.tuples(QTY, AMOUNT, RATE)


def _service_with(lines, closing_day=31, terms="NEXT_MONTH_END"):
    svc = BillingService(clock=CLOCK)
    svc.register_customer(
        "C001", "株式会社アルファ", closing_day=closing_day, payment_terms=terms
    )
    for i, (qty, price, rate) in enumerate(lines):
        svc.add_sale(
            record_id=f"S{i}",
            customer_code="C001",
            sales_date=date(2026, 8, 10),
            item_name=f"商品{i}",
            quantity=qty,
            unit_price=price,
            tax_rate=rate,
        )
    return svc


@given(lines=st.lists(LineSpec, min_size=1, max_size=20))
@settings(max_examples=100)
def test_prop_001_subtotal_equals_sum_of_lines(lines):
    """PROP-001 / REQ-003: 請求の税抜合計 = 明細の税抜金額の総和。"""
    invoice = _service_with(lines).close_month("2026-08", actor="k1")[0]

    assert invoice.subtotal == sum(ln.amount for ln in invoice.lines)
    assert invoice.subtotal == sum(qty * price for qty, price, _ in lines)


@given(lines=st.lists(LineSpec, min_size=1, max_size=20))
@settings(max_examples=200)
def test_prop_002_tax_is_rounded_once_per_rate(lines):
    """PROP-002 / REQ-005 / ADR-0001: 端数処理は税率ごとに1回。

    「税率ごとの税抜合計をまとめて丸めた額」が正である。明細ごとに丸めて合計した
    額とは一致しないことがあるが、**一致しない場合に正しいのは前者**。
    """
    invoice = _service_with(lines).close_month("2026-08", actor="k1")[0]

    for summary in invoice.tax_summaries:
        expected = calc_tax(summary.subtotal, summary.tax_rate.percent)
        assert summary.tax_amount == expected

        # 明細ごとに丸めて合計した額（＝誤った実装の結果）以上になる
        per_line = sum(
            calc_tax(ln.amount, ln.tax_rate.percent)
            for ln in invoice.lines
            if ln.tax_rate is summary.tax_rate
        )
        assert summary.tax_amount >= per_line


@given(lines=st.lists(LineSpec, min_size=2, max_size=20))
@settings(max_examples=300)
def test_prop_002_detects_per_line_rounding(lines):
    """PROP-002: 明細ごとに丸める実装との差が実際に生じる入力が存在する。

    この性質は「必ず差が出る」ではなく「差が出る入力で正しい側を選んでいる」こと。
    差が出ない入力では何も検証できないため assume で絞り込む。
    """
    invoice = _service_with(lines).close_month("2026-08", actor="k1")[0]

    for summary in invoice.tax_summaries:
        per_line = sum(
            calc_tax(ln.amount, ln.tax_rate.percent)
            for ln in invoice.lines
            if ln.tax_rate is summary.tax_rate
        )
        assume(per_line != summary.tax_amount)
        # 差が出るなら、請求単位で丸めた側が大きい（切捨てのため）
        assert summary.tax_amount > per_line


@given(lines=st.lists(LineSpec, min_size=1, max_size=20))
@settings(max_examples=100)
def test_prop_003_rate_subtotals_sum_to_invoice_subtotal(lines):
    """PROP-003 / REQ-004: 税率ごとの対価の額の総和 = 請求の税抜合計。"""
    invoice = _service_with(lines).close_month("2026-08", actor="k1")[0]

    assert sum(s.subtotal for s in invoice.tax_summaries) == invoice.subtotal
    assert sum(s.tax_amount for s in invoice.tax_summaries) == invoice.tax_total
    assert invoice.total == invoice.subtotal + invoice.tax_total


@given(closing_day=CLOSING_DAY, terms=TERMS, day=DAY_IN_PERIOD, amount=AMOUNT)
@settings(max_examples=100)
def test_prop_004_due_date_is_not_before_closing_date(closing_day, terms, day, amount):
    """PROP-004 / REQ-002: 支払期日 ≥ 締め日。"""
    svc = BillingService(clock=CLOCK)
    svc.register_customer("C001", "X", closing_day=closing_day, payment_terms=terms)
    svc.add_sale(
        record_id="S1",
        customer_code="C001",
        sales_date=date(2026, 8, day),
        item_name="商品",
        quantity=1,
        unit_price=amount,
        tax_rate=10,
    )
    invoice = svc.close_month("2026-08", actor="k1")[0]
    assert invoice.due_date >= invoice.closing_date


@given(
    per_customer=st.lists(
        st.lists(LineSpec, min_size=0, max_size=5), min_size=1, max_size=4
    ),
)
@settings(max_examples=100)
def test_prop_005_at_most_one_invoice_per_customer(per_customer):
    """PROP-005 / REQ-003, REQ-008: 請求は取引先ごとに高々1件。売上0件なら作らない。"""
    svc = BillingService(clock=CLOCK)
    expected_with_sales = set()
    for c, lines in enumerate(per_customer):
        code = f"C{c:03d}"
        svc.register_customer(
            code, f"取引先{c}", closing_day=31, payment_terms="NEXT_MONTH_END"
        )
        for i, (qty, price, rate) in enumerate(lines):
            svc.add_sale(
                record_id=f"S{c}-{i}",
                customer_code=code,
                sales_date=date(2026, 8, 10),
                item_name="商品",
                quantity=qty,
                unit_price=price,
                tax_rate=rate,
            )
        if lines:
            expected_with_sales.add(code)

    invoices = svc.close_month("2026-08", actor="k1")
    codes = [inv.customer_code for inv in invoices]

    assert len(codes) == len(set(codes))
    assert set(codes) == expected_with_sales


@given(lines=st.lists(LineSpec, min_size=1, max_size=10))
@settings(max_examples=100)
def test_prop_006_confirmed_invoice_amount_never_changes(lines):
    """PROP-006 / REQ-007: 確定済みの請求は、以降どの操作でも金額が変わらない。"""
    from app.billing import BillingError

    svc = _service_with(lines)
    invoice = svc.close_month("2026-08", actor="k1")[0]
    svc.confirm(invoice.invoice_no, actor="k1")

    before = (invoice.subtotal, invoice.tax_total, invoice.total)

    for attempt in (
        lambda: svc.close_month("2026-08", actor="k1"),
        lambda: svc.confirm(invoice.invoice_no, actor="k1"),
    ):
        try:
            attempt()
        except BillingError:
            pass

    after = svc.get_invoice(invoice.invoice_no)
    assert (after.subtotal, after.tax_total, after.total) == before
    assert after.status is InvoiceStatus.CONFIRMED


@given(subtotal=st.integers(min_value=0, max_value=10_000_000), rate=RATE)
def test_prop_002_calc_tax_is_floor(subtotal, rate):
    """PROP-002 / ADR-0002: 端数処理は切捨て。"""
    tax = calc_tax(subtotal, rate)
    assert tax * 100 <= subtotal * rate
    assert (tax + 1) * 100 > subtotal * rate


@given(amount=AMOUNT)
def test_tax_rate_enum_covers_declared_rates(amount):
    """REQ-004: 税率区分は 10% と 8% の2つ。"""
    assert {r.percent for r in TaxRate} == {8, 10}


@given(lines=st.lists(LineSpec, min_size=1, max_size=8), extra=LineSpec)
@settings(max_examples=100)
def test_prop_005_reclose_keeps_invoice_number(lines, extra):
    """PROP-005 / REQ-003: 未確定の再締めでは請求番号が変わらない。

    請求は取引先 × 対象期間で1件（PROP-005）である以上、作り直しても同一の請求を
    指し続ける必要がある。番号が変われば先に通知した番号と食い違う。
    """
    svc = _service_with(lines)
    first = svc.close_month("2026-08", actor="k1")[0].invoice_no

    qty, price, rate = extra
    svc.add_sale(
        record_id="S-extra",
        customer_code="C001",
        sales_date=date(2026, 8, 11),
        item_name="追加",
        quantity=qty,
        unit_price=price,
        tax_rate=rate,
    )
    second = svc.close_month("2026-08", actor="k1")[0]

    assert second.invoice_no == first
    assert second.subtotal == sum(q * p for q, p, _ in lines) + qty * price


@given(month=st.integers(min_value=1, max_value=12), closing_day=CLOSING_DAY)
@settings(max_examples=100)
def test_prop_004_period_is_contiguous_and_ends_on_closing_date(month, closing_day):
    """PROP-004 / REQ-001: 対象期間は締め日で終わり、前月の締め日の翌日から始まる。

    1月（前月が前年12月になる）を含む全月で成り立つ。
    """
    from app.billing import closing_date_of, period_of

    year_month = f"2026-{month:02d}"
    period_from, period_to = period_of(year_month, closing_day)

    assert period_to == closing_date_of(year_month, closing_day)
    assert period_from <= period_to

    prev_month, prev_year = (month - 1, 2026) if month > 1 else (12, 2025)
    prev_close = closing_date_of(f"{prev_year:04d}-{prev_month:02d}", closing_day)
    assert period_from == date.fromordinal(prev_close.toordinal() + 1)
