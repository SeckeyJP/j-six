"""バッチ処理のエントリポイント。

- BATCH-001 月次請求データ作成（月次）
- BATCH-002 会計連携ファイル出力（日次）

バッチは業務ルールを持たない。`billing` と `accounting` を呼ぶだけである
（CLAUDE.md「業務ルールは app/billing.py に集約する」）。
"""

from __future__ import annotations

from typing import List

from .accounting import build_accounting_csv
from .billing import BillingService
from .models import Invoice


def run_month_close(
    service: BillingService, year_month: str, actor: str
) -> List[Invoice]:
    """BATCH-001: 月次締めを実行する（UC-002）。"""
    return service.close_month(year_month, actor=actor)


def run_accounting_export(service: BillingService, year_month: str) -> str:
    """BATCH-002: 確定済み請求を会計連携 CSV に出力する（UC-005 / EIF-001）。"""
    return build_accounting_csv(service.list_invoices(year_month))
