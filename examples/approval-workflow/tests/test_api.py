"""API レベルの結合テスト（FastAPI TestClient）。

ドメインルールは test_workflow.py で網羅。ここでは HTTP 結線とステータスコード変換を検証する。
"""
import pytest
from fastapi.testclient import TestClient

from app import main


@pytest.fixture
def client(monkeypatch) -> TestClient:
    # 各テストで状態を分離するため WorkflowService を作り直す
    from app.workflow import WorkflowService

    monkeypatch.setattr(main, "service", WorkflowService())
    return TestClient(main.app)


def _create(client, amount=50_000, approvers=("bob",)):
    return client.post(
        "/requests",
        json={
            "applicant": "alice",
            "amount": amount,
            "title": "備品購入",
            "approvers": list(approvers),
        },
    )


def test_create_returns_201(client):
    res = _create(client)
    assert res.status_code == 201
    body = res.json()
    assert body["id"] == "REQ-0001"
    assert body["status"] == "DRAFT"


def test_create_invalid_returns_409(client):
    res = _create(client, amount=1_000_000, approvers=("bob",))  # 3段必要
    assert res.status_code == 409
    assert "承認者が必要" in res.json()["detail"]


def test_happy_path_submit_and_approve(client):
    rid = _create(client).json()["id"]
    assert client.post(f"/requests/{rid}/submit", json={"actor": "alice"}).status_code == 200
    res = client.post(f"/requests/{rid}/approve", json={"actor": "bob"})
    assert res.status_code == 200
    assert res.json()["status"] == "APPROVED"


def test_out_of_order_returns_409(client):
    rid = _create(client, amount=500_000, approvers=("bob", "carol")).json()["id"]
    client.post(f"/requests/{rid}/submit", json={"actor": "alice"})
    res = client.post(f"/requests/{rid}/approve", json={"actor": "carol"})
    assert res.status_code == 409


def test_get_unknown_returns_404(client):
    assert client.get("/requests/REQ-9999").status_code == 404


def test_list_requests(client):
    _create(client)
    _create(client)
    res = client.get("/requests")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_reject_endpoint(client):
    rid = _create(client).json()["id"]
    client.post(f"/requests/{rid}/submit", json={"actor": "alice"})
    res = client.post(f"/requests/{rid}/reject", json={"actor": "bob", "note": "却下理由"})
    assert res.status_code == 200
    assert res.json()["status"] == "REJECTED"


def test_remand_endpoint(client):
    rid = _create(client).json()["id"]
    client.post(f"/requests/{rid}/submit", json={"actor": "alice"})
    res = client.post(f"/requests/{rid}/remand", json={"actor": "bob", "note": "再提出を"})
    assert res.status_code == 200
    assert res.json()["status"] == "DRAFT"


def test_withdraw_endpoint(client):
    rid = _create(client).json()["id"]
    res = client.post(f"/requests/{rid}/withdraw", json={"actor": "alice"})
    assert res.status_code == 200
    assert res.json()["status"] == "WITHDRAWN"
