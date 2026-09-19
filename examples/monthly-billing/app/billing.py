"""ドメインロジック — 月次締めと消費税計算。

**業務ルールはこのモジュールに集約する**（CLAUDE.md）。画面・帳票・バッチ・会計連携は
ここを呼ぶだけで、同じルールを再実装しない。4つの入口があるため、ルールを1箇所に
置かないと入口ごとに実装がずれる（Design Spec 1.1）。
"""

from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Callable, Dict, List, Optional

from .models import (
    ALLOWED_CLOSING_DAYS,
    AuditEntry,
    Customer,
    Invoice,
    InvoiceLine,
    InvoiceStatus,
    PaymentTerms,
    SalesRecord,
    TaxRate,
    TaxSummary,
)


class BillingError(Exception):
    """業務ルール違反。API 層で HTTP 409 に変換する（Design Spec 3.2）。"""


def calc_tax(subtotal: int, rate_percent: int) -> int:
    """税抜合計から消費税額を求める（REQ-005 / ADR-0001, ADR-0002）。

    **引数は「税率ごとの税抜合計」であって明細金額ではない。** 端数処理は一の請求に
    つき税率ごとに1回であり、明細ごとに丸めて合計することは制度上認められない
    （国税庁「インボイス制度に関するQ&A」問57）。

    端数処理は切捨て。整数演算だけで行い、浮動小数点の誤差を持ち込まない。
    """
    return subtotal * rate_percent // 100


def _month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def _add_months(base: date, months: int) -> date:
    """base の月末から months か月後の月末を返す。"""
    total = base.year * 12 + (base.month - 1) + months
    return _month_end(total // 12, total % 12 + 1)


def closing_date_of(year_month: str, closing_day: int) -> date:
    """対象年月と締め日から締め日（日付）を求める（REQ-001）。"""
    year, month = (int(part) for part in year_month.split("-"))
    if closing_day == 31:
        return _month_end(year, month)
    return date(year, month, closing_day)


def period_of(year_month: str, closing_day: int) -> tuple:
    """請求対象期間（前回締め日の翌日 〜 今回締め日）を求める（REQ-001）。"""
    to_date = closing_date_of(year_month, closing_day)
    year, month = (int(part) for part in year_month.split("-"))
    prev_year, prev_month = (year, month - 1) if month > 1 else (year - 1, 12)
    prev_close = closing_date_of(f"{prev_year:04d}-{prev_month:02d}", closing_day)
    return date.fromordinal(prev_close.toordinal() + 1), to_date


def due_date_of(closing: date, terms: PaymentTerms) -> date:
    """締め日と支払サイトから支払期日を求める（REQ-002 / PROP-004）。"""
    months = 1 if terms is PaymentTerms.NEXT_MONTH_END else 2
    return _add_months(closing, months)


def summarize_tax(lines: List[InvoiceLine]) -> List[TaxSummary]:
    """明細を税率区分ごとに集計する（REQ-004, REQ-005）。

    税率ごとに税抜合計を出してから **1回だけ** 端数処理する。
    """
    subtotals: Dict[TaxRate, int] = {}
    for line in lines:
        subtotals[line.tax_rate] = subtotals.get(line.tax_rate, 0) + line.amount

    return [
        TaxSummary(
            tax_rate=rate,
            subtotal=subtotal,
            tax_amount=calc_tax(subtotal, rate.percent),
        )
        for rate, subtotal in sorted(subtotals.items(), key=lambda kv: kv[0].percent)
    ]


class BillingService:
    """請求業務のサービス。インメモリのストアを持つ（Design Spec 1.3）。"""

    def __init__(self, clock: Optional[Callable[[], datetime]] = None) -> None:
        self.reset(clock=clock)

    def reset(self, clock: Optional[Callable[[], datetime]] = None) -> None:
        """ストアを初期化する。

        インメモリ実装の公開メソッド（Design Spec 1.3）。永続化実装に差し替えた
        場合は未サポートとしてよい。
        """
        self._clock = clock or datetime.now
        self._customers: Dict[str, Customer] = {}
        self._sales: Dict[str, SalesRecord] = {}
        self._invoices: Dict[str, Invoice] = {}
        self._seq = 0
        self.audit_log: List[AuditEntry] = []

    # --- 登録 --------------------------------------------------------------
    def register_customer(
        self, customer_code: str, name: str, closing_day: int, payment_terms: str
    ) -> Customer:
        """取引先を登録する（REQ-001, REQ-002）。"""
        if closing_day not in ALLOWED_CLOSING_DAYS:
            raise BillingError(
                f"締め日は {ALLOWED_CLOSING_DAYS} のいずれかで指定してください: {closing_day}"
            )
        try:
            terms = PaymentTerms(payment_terms)
        except ValueError as exc:
            raise BillingError(f"支払サイトが不正です: {payment_terms}") from exc

        customer = Customer(
            customer_code=customer_code,
            name=name,
            closing_day=closing_day,
            payment_terms=terms,
        )
        self._customers[customer_code] = customer
        return customer

    def add_sale(
        self,
        record_id: str,
        customer_code: str,
        sales_date: date,
        item_name: str,
        quantity: int,
        unit_price: int,
        tax_rate: int,
    ) -> bool:
        """売上を登録する。同一 record_id は無視する（冪等。UC-001）。"""
        if customer_code not in self._customers:
            raise BillingError(f"未登録の取引先です: {customer_code}")
        try:
            rate = TaxRate(tax_rate)
        except ValueError as exc:
            raise BillingError(f"税率が不正です: {tax_rate}") from exc

        if record_id in self._sales:
            return False

        self._sales[record_id] = SalesRecord(
            record_id=record_id,
            customer_code=customer_code,
            sales_date=sales_date,
            item_name=item_name,
            quantity=quantity,
            unit_price=unit_price,
            tax_rate=rate,
        )
        return True

    # --- 締め --------------------------------------------------------------
    def close_month(self, year_month: str, actor: str) -> List[Invoice]:
        """月次締めを実行し、取引先ごとの請求を作る（UC-002 / REQ-003, REQ-008）。

        既に確定済みの請求がある期間は再締めできない（REQ-007）。
        未確定の請求は作り直す。
        """
        self._ensure_not_confirmed(year_month)

        created: List[Invoice] = []
        for code in sorted(self._customers):
            invoice = self._build_invoice(code, year_month)
            if invoice is not None:
                self._invoices[invoice.invoice_no] = invoice
                created.append(invoice)

        self._log(
            AuditEntry(
                action="CLOSE",
                actor=actor,
                at=self._clock(),
                year_month=year_month,
                created_count=len(created),
            )
        )
        return created

    def _ensure_not_confirmed(self, year_month: str) -> None:
        confirmed = [
            inv
            for inv in self._invoices.values()
            if inv.year_month == year_month and inv.status is InvoiceStatus.CONFIRMED
        ]
        if confirmed:
            raise BillingError(
                f"確定済みの請求があるため再締めできません: {year_month}"
            )

    def _build_invoice(self, customer_code: str, year_month: str) -> Optional[Invoice]:
        customer = self._customers[customer_code]
        period_from, period_to = period_of(year_month, customer.closing_day)

        sales = sorted(
            (
                sale
                for sale in self._sales.values()
                if sale.customer_code == customer_code
                and period_from <= sale.sales_date <= period_to
            ),
            key=lambda s: (s.sales_date, s.record_id),
        )
        if not sales:
            return None  # REQ-008

        lines = [
            InvoiceLine(
                line_no=i + 1,
                item_name=sale.item_name,
                quantity=sale.quantity,
                unit_price=sale.unit_price,
                amount=sale.amount,
                tax_rate=sale.tax_rate,
            )
            for i, sale in enumerate(sales)
        ]

        existing = self._find_invoice(customer_code, year_month)
        invoice_no = (
            existing.invoice_no if existing else self._next_invoice_no(year_month)
        )

        return Invoice(
            invoice_no=invoice_no,
            customer_code=customer_code,
            customer_name=customer.name,
            year_month=year_month,
            period_from=period_from,
            period_to=period_to,
            closing_date=period_to,
            due_date=due_date_of(period_to, customer.payment_terms),
            lines=lines,
            tax_summaries=summarize_tax(lines),
        )

    def _find_invoice(self, customer_code: str, year_month: str) -> Optional[Invoice]:
        for invoice in self._invoices.values():
            if (
                invoice.customer_code == customer_code
                and invoice.year_month == year_month
            ):
                return invoice
        return None

    def _next_invoice_no(self, year_month: str) -> str:
        self._seq += 1
        return f"INV-{year_month.replace('-', '')}-{self._seq:04d}"

    # --- 確定 --------------------------------------------------------------
    def confirm(self, invoice_no: str, actor: str) -> Invoice:
        """請求を確定する（UC-006 / REQ-007）。"""
        invoice = self.get_invoice(invoice_no)
        if invoice.status is InvoiceStatus.CONFIRMED:
            raise BillingError(f"既に確定済みです: {invoice_no}")

        invoice.status = InvoiceStatus.CONFIRMED
        self._log(
            AuditEntry(
                action="CONFIRM",
                actor=actor,
                at=self._clock(),
                year_month=invoice.year_month,
                invoice_no=invoice_no,
            )
        )
        return invoice

    # --- 照会 --------------------------------------------------------------
    def get_invoice(self, invoice_no: str) -> Invoice:
        if invoice_no not in self._invoices:
            raise BillingError(f"請求が見つかりません: {invoice_no}")
        return self._invoices[invoice_no]

    def list_invoices(self, year_month: Optional[str] = None) -> List[Invoice]:
        invoices = [
            inv
            for inv in self._invoices.values()
            if year_month is None or inv.year_month == year_month
        ]
        return sorted(invoices, key=lambda inv: inv.invoice_no)

    def get_customer(self, customer_code: str) -> Customer:
        if customer_code not in self._customers:
            raise BillingError(f"未登録の取引先です: {customer_code}")
        return self._customers[customer_code]

    def _log(self, entry: AuditEntry) -> None:
        self.audit_log.append(entry)
