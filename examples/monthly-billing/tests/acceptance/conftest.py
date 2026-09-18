"""hold-out 受入テストの共通設定。

公開インタフェース（バッチのエントリポイントと HTTP API）経由でのみ検証する。
ドメイン層の内部構造に依存しない、ユーザー視点の監督面を保つため。

仕様が規定していない詳細は固定しない。Design Spec 3.2 が規定しているのは
ルール違反 409 / 対象不在 404 だけであり、成功時のステータスコードや HTML の
細かな文言は規定されていない。表示内容の検証は JSON エンドポイント
（Design Spec 3.1）を使う。
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app import importer
from app.main import app, service

#: 販売管理システムからの売上データ（EIF-002 の形式）。
#: 10% 対象と 8% 対象（軽減税率）を混在させ、端数が出る単価にしてある。
SALES_CSV = """record_id,customer_code,sales_date,item_name,quantity,unit_price,tax_rate
S001,C001,2026-08-03,事務用品,3,333,10
S002,C001,2026-08-15,配送料,1,1111,10
S003,C001,2026-08-20,来客用茶菓,5,177,8
S004,C002,2026-08-10,保守作業,2,55555,10
S005,C003,2026-07-31,前月分,1,1000,10
"""


@pytest.fixture
def billing():
    """取引先を登録した空のサービス。"""
    service.reset(clock=lambda: datetime(2026, 9, 1, 10, 0, 0))
    service.register_customer(
        "C001", "株式会社アルファ", closing_day=31, payment_terms="NEXT_MONTH_END"
    )
    service.register_customer(
        "C002", "ベータ商事株式会社", closing_day=31, payment_terms="MONTH_AFTER_NEXT_END"
    )
    service.register_customer(
        "C003", "ガンマ工業株式会社", closing_day=31, payment_terms="NEXT_MONTH_END"
    )
    return service


@pytest.fixture
def client(billing):
    return TestClient(app)


@pytest.fixture
def imported(billing):
    """売上を取り込んだ状態（UC-001 まで完了）。"""
    importer.import_sales(billing, SALES_CSV)
    return billing


def invoice_of(client, customer_code, year_month="2026-08"):
    """取引先コードから請求明細（JSON）を取る。"""
    listing = client.get(f"/invoices.json?year_month={year_month}")
    assert listing.is_success, listing.text
    for row in listing.json():
        if row["customer_code"] == customer_code:
            detail = client.get(f"/invoices/{row['invoice_no']}.json")
            assert detail.is_success, detail.text
            return detail.json()
    raise AssertionError(f"{customer_code} の請求が見つかりません")
