"""EIF-002: 販売管理システムからの売上データ取込。

取込は冪等とし、同一 record_id の再取込は無視する（Design Spec 5.2 / UC-001）。
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from typing import List

from .billing import BillingError, BillingService

#: EIF-002 のレイアウト（CSV ヘッダ）
COLUMNS = (
    "record_id",
    "customer_code",
    "sales_date",
    "item_name",
    "quantity",
    "unit_price",
    "tax_rate",
)


@dataclass
class ImportResult:
    """取込結果。"""

    imported: int = 0
    skipped: int = 0
    errors: List[str] = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []


def import_sales(service: BillingService, csv_text: str) -> ImportResult:
    """CSV を取り込む（UC-001 / EIF-002）。

    取込済みの record_id は skipped に数え、エラー行は errors に記録して継続する。
    1行の不備で日次取込全体を止めないため。
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    missing = [column for column in COLUMNS if column not in (reader.fieldnames or [])]
    if missing:
        raise BillingError(f"EIF-002 の列が不足しています: {', '.join(missing)}")

    result = ImportResult()
    for row_no, row in enumerate(reader, start=2):
        # DictReader は不足列を None で埋め、余分な値を None キーに入れる。
        # どちらも変換まで進めると TypeError で取込全体が止まる／黙って取り込まれるため、
        # 列数の不一致はここでエラー行にする。
        if None in row or any(row[column] is None for column in COLUMNS):
            result.errors.append(f"{row_no}行目: 列数がヘッダと一致しません")
            continue
        try:
            added = service.add_sale(
                record_id=row["record_id"],
                customer_code=row["customer_code"],
                sales_date=datetime.strptime(row["sales_date"], "%Y-%m-%d").date(),
                item_name=row["item_name"],
                quantity=int(row["quantity"]),
                unit_price=int(row["unit_price"]),
                tax_rate=int(row["tax_rate"]),
            )
        except (BillingError, ValueError) as exc:
            result.errors.append(f"{row_no}行目: {exc}")
            continue

        if added:
            result.imported += 1
        else:
            result.skipped += 1

    return result
