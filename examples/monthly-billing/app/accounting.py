"""EIF-001: 会計システムへの仕訳連携ファイル出力。

請求ヘッダ1行（H）＋税率区分ごとの内訳行（D）の構造（REQ-009）。
確定済み（CONFIRMED）の請求だけを出力する。
"""

from __future__ import annotations

import csv
import io
from typing import List

from .models import Invoice, InvoiceStatus

#: EIF-001 のレイアウト
HEADER = (
    "record_type",
    "invoice_no",
    "customer_code",
    "closing_date",
    "due_date",
    "tax_rate",
    "subtotal",
    "tax_amount",
    "total",
)


def build_accounting_csv(invoices: List[Invoice]) -> str:
    """確定済み請求から会計連携 CSV を組み立てる（REQ-009 / EIF-001）。"""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(HEADER)

    for invoice in sorted(invoices, key=lambda inv: inv.invoice_no):
        if invoice.status is not InvoiceStatus.CONFIRMED:
            continue

        writer.writerow(
            [
                "H",
                invoice.invoice_no,
                invoice.customer_code,
                invoice.closing_date.isoformat(),
                invoice.due_date.isoformat(),
                "",
                invoice.subtotal,
                invoice.tax_total,
                invoice.total,
            ]
        )
        for summary in invoice.tax_summaries:
            writer.writerow(
                [
                    "D",
                    invoice.invoice_no,
                    invoice.customer_code,
                    invoice.closing_date.isoformat(),
                    invoice.due_date.isoformat(),
                    summary.tax_rate.percent,
                    summary.subtotal,
                    summary.tax_amount,
                    summary.subtotal + summary.tax_amount,
                ]
            )

    return buffer.getvalue()
