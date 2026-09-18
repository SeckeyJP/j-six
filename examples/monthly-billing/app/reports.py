"""帳票出力。

- RPT-001 請求書（印刷用 HTML）
- RPT-002 請求一覧表（CSV）

PDF は生成しない（ADR-0003）。帳票レイアウトは Jinja2 テンプレートに置き、
帳票設計書（帳票レイアウト / 帳票項目説明）の逆生成元とする。
"""

from __future__ import annotations

import csv
import io
from typing import List

from .models import Invoice

#: 適格請求書発行事業者の登録番号（REQ-006）。実運用では設定値から読む。
ISSUER_NAME = "J-SIX 商事株式会社"
ISSUER_REGISTRATION_NO = "T1234567890123"

#: RPT-002 のレイアウト
INVOICE_LIST_COLUMNS = (
    "invoice_no",
    "customer_code",
    "customer_name",
    "closing_date",
    "due_date",
    "subtotal",
    "tax_total",
    "total",
    "status",
)


def build_invoice_list_csv(invoices: List[Invoice]) -> str:
    """RPT-002: 請求一覧表（CSV）を組み立てる。"""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(INVOICE_LIST_COLUMNS)

    for invoice in invoices:
        writer.writerow(
            [
                invoice.invoice_no,
                invoice.customer_code,
                invoice.customer_name,
                invoice.closing_date.isoformat(),
                invoice.due_date.isoformat(),
                invoice.subtotal,
                invoice.tax_total,
                invoice.total,
                invoice.status.value,
            ]
        )

    return buffer.getvalue()


def invoice_view(invoice: Invoice) -> dict:
    """請求を画面・帳票・JSON で共通に使う辞書へ変換する。

    画面（HTML）と受入テスト（JSON）が同じデータ源を見るようにするため
    （Design Spec 3.1）。
    """
    return {
        "invoice_no": invoice.invoice_no,
        "customer_code": invoice.customer_code,
        "customer_name": invoice.customer_name,
        "year_month": invoice.year_month,
        "period_from": invoice.period_from.isoformat(),
        "period_to": invoice.period_to.isoformat(),
        "closing_date": invoice.closing_date.isoformat(),
        "due_date": invoice.due_date.isoformat(),
        "subtotal": invoice.subtotal,
        "tax_total": invoice.tax_total,
        "total": invoice.total,
        "status": invoice.status.value,
        "lines": [
            {
                "line_no": line.line_no,
                "item_name": line.item_name,
                "quantity": line.quantity,
                "unit_price": line.unit_price,
                "amount": line.amount,
                "tax_rate": line.tax_rate.percent,
                "is_reduced": line.tax_rate.is_reduced,
            }
            for line in invoice.lines
        ],
        "tax_summaries": [
            {
                "tax_rate": summary.tax_rate.percent,
                "is_reduced": summary.tax_rate.is_reduced,
                "subtotal": summary.subtotal,
                "tax_amount": summary.tax_amount,
            }
            for summary in invoice.tax_summaries
        ],
    }
