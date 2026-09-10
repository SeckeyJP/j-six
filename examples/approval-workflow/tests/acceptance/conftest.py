"""hold-out 受入テストの共通設定。

HTTP API 経由でのみ検証する。ドメイン層（app.workflow）を直接呼ばないのは、
実装の内部構造に依存しないユーザー視点の監督面を保つため。

成功時のステータスコードは Design Spec が規定していない（規定しているのは
ルール違反 409 / 対象不在 404 のみ）。仕様が定めていない詳細を hold-out で
固定すると、正しい実装まで落としてしまうため、成功判定は 2xx で行う。
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app, service


@pytest.fixture
def client():
    """毎テスト、申請ストアを空にしてから API クライアントを返す。"""
    service._store.clear()
    service._seq = 0
    return TestClient(app)
