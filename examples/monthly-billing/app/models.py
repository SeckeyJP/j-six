"""ドメインモデル — 月次請求書発行。

設計判断は以下の ADR に記録している。
- ADR-0001: 消費税の端数処理を「請求単位・税率ごとに1回」で行う
- ADR-0002: 端数処理の方法として「切捨て」を採用する
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional


class TaxRate(Enum):
    """税率区分（REQ-004）。

    軽減税率（8%）と標準税率（10%）を区別する。値は百分率の整数で持ち、
    金額計算に浮動小数点を持ち込まない（ADR-0002）。
    """

    REDUCED = 8  # 軽減税率
    STANDARD = 10  # 標準税率

    @property
    def percent(self) -> int:
        return self.value

    @property
    def is_reduced(self) -> bool:
        return self is TaxRate.REDUCED

    @property
    def label(self) -> str:
        return f"{self.percent}%" + ("（軽減）" if self.is_reduced else "")


class InvoiceStatus(str, Enum):
    """請求の状態（REQ-007）。"""

    DRAFT = "DRAFT"  # 締め済み・未確定（再締め可能）
    CONFIRMED = "CONFIRMED"  # 確定済み（金額変更不可）


class PaymentTerms(str, Enum):
    """支払サイト（REQ-002）。"""

    NEXT_MONTH_END = "NEXT_MONTH_END"  # 翌月末払い
    MONTH_AFTER_NEXT_END = "MONTH_AFTER_NEXT_END"  # 翌々月末払い


#: 締め日として許容する値（REQ-001）。31 は月末を表す。
ALLOWED_CLOSING_DAYS = (20, 31)


#: 預金種別として許容する値（REQ-011）。
ALLOWED_ACCOUNT_TYPES = ("普通", "当座")


@dataclass(frozen=True)
class BankAccount:
    """振込先口座（REQ-011）。

    **不変**にしてある。請求は締め時点の口座を保存し（REQ-012）、後からマスタを
    変更しても作成済みの請求書の記載が変わってはならない。可変にすると、
    同じインスタンスを共有した時点でスナップショットが崩れる。
    """

    bank_name: str
    branch_name: str
    account_type: str
    account_number: str
    account_holder: str


@dataclass
class Customer:
    """取引先。締め日と支払サイトを持つ（REQ-001, REQ-002）。

    振込先口座は任意（REQ-013。未登録でも締めは止めない）。
    """

    customer_code: str
    name: str
    closing_day: int
    payment_terms: PaymentTerms
    bank_account: Optional[BankAccount] = None


@dataclass
class SalesRecord:
    """販売管理システムから取り込んだ売上明細（EIF-002）。"""

    record_id: str
    customer_code: str
    sales_date: date
    item_name: str
    quantity: int
    unit_price: int
    tax_rate: TaxRate

    @property
    def amount(self) -> int:
        """税抜金額。"""
        return self.quantity * self.unit_price


@dataclass
class InvoiceLine:
    """請求明細。

    **消費税額を持たない**（ADR-0001）。端数処理は請求単位・税率ごとに1回であり、
    明細ごとの税額を保持すると、それを合計したくなる誘因を構造として残してしまう。
    """

    line_no: int
    item_name: str
    quantity: int
    unit_price: int
    amount: int
    tax_rate: TaxRate


@dataclass
class TaxSummary:
    """税率区分ごとの対価の額と消費税額（REQ-004, REQ-005）。

    端数処理の単位がこの粒度と一致する。
    """

    tax_rate: TaxRate
    subtotal: int
    tax_amount: int


@dataclass
class Invoice:
    """請求。取引先 × 対象期間で1件（REQ-003）。"""

    invoice_no: str
    customer_code: str
    customer_name: str
    year_month: str
    period_from: date
    period_to: date
    closing_date: date
    due_date: date
    lines: List[InvoiceLine] = field(default_factory=list)
    tax_summaries: List[TaxSummary] = field(default_factory=list)
    status: InvoiceStatus = InvoiceStatus.DRAFT
    #: 締め時点の振込先（REQ-012）。交付先名称と同じくスナップショットで持つ。
    #: 未登録の取引先では None（REQ-013）。
    bank_account: Optional[BankAccount] = None

    @property
    def subtotal(self) -> int:
        """税抜合計（PROP-001）。"""
        return sum(line.amount for line in self.lines)

    @property
    def tax_total(self) -> int:
        """消費税合計（PROP-003）。税率ごとに1回丸めた額の総和。"""
        return sum(summary.tax_amount for summary in self.tax_summaries)

    @property
    def total(self) -> int:
        """請求合計。"""
        return self.subtotal + self.tax_total


@dataclass
class AuditEntry:
    """締め・確定の監査記録（REQ-010）。

    明細の内容は持たない（Design Spec 6.2）。
    """

    action: str
    actor: str
    at: datetime
    year_month: str
    created_count: int = 0
    invoice_no: Optional[str] = None
