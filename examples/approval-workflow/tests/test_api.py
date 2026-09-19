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
    assert (
        client.post(f"/requests/{rid}/submit", json={"actor": "alice"}).status_code
        == 200
    )
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
    res = client.post(
        f"/requests/{rid}/reject", json={"actor": "bob", "note": "却下理由"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "REJECTED"


def test_remand_endpoint(client):
    rid = _create(client).json()["id"]
    client.post(f"/requests/{rid}/submit", json={"actor": "alice"})
    res = client.post(
        f"/requests/{rid}/remand", json={"actor": "bob", "note": "再提出を"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "DRAFT"


def test_withdraw_endpoint(client):
    rid = _create(client).json()["id"]
    res = client.post(f"/requests/{rid}/withdraw", json={"actor": "alice"})
    assert res.status_code == 200
    assert res.json()["status"] == "WITHDRAWN"


# --- REQ-011: 対象不在は 404（ルール違反の 409 と区別する。ADR-0003） --------
TRANSITION_ENDPOINTS = ["submit", "approve", "reject", "remand", "withdraw"]


@pytest.mark.parametrize("endpoint", TRANSITION_ENDPOINTS)
def test_unknown_request_transition_returns_404_not_409(client, endpoint):
    """REQ-011: 未登録 ID への状態遷移は 404 になる（409 ではない）。"""
    res = client.post(f"/requests/REQ-9999/{endpoint}", json={"actor": "alice"})
    assert res.status_code == 404


def test_unknown_request_get_returns_404(client):
    """REQ-011: 未登録 ID の取得は 404。"""
    assert client.get("/requests/REQ-9999").status_code == 404


def test_operating_on_terminal_request_returns_409_not_404(client):
    """ADR-0003: 終了済み申請への操作はルール違反として 409 になる（不在の 404 ではない）。"""
    rid = _create(client).json()["id"]
    client.post(f"/requests/{rid}/submit", json={"actor": "alice"})
    client.post(f"/requests/{rid}/approve", json={"actor": "bob"})  # APPROVED
    res = client.post(f"/requests/{rid}/withdraw", json={"actor": "alice"})
    assert res.status_code == 409


# --- REQ-012: 未定義の入力項目は入力不正（422）として拒否する ---------------
@pytest.mark.parametrize("endpoint", TRANSITION_ENDPOINTS)
def test_transition_body_with_undefined_key_returns_422(client, endpoint):
    """REQ-012: 状態遷移ボディの未定義キー（例: nte）は 422 で拒否され、
    申請の状態も監査ログも変わらない。
    """
    rid = _create(client, amount=500_000, approvers=("bob", "carol")).json()["id"]
    client.post(f"/requests/{rid}/submit", json={"actor": "alice"})
    before = client.get(f"/requests/{rid}").json()

    res = client.post(
        f"/requests/{rid}/{endpoint}", json={"actor": "bob", "nte": "誤字"}
    )
    assert res.status_code == 422

    after = client.get(f"/requests/{rid}").json()
    assert after == before


def test_create_body_with_undefined_key_returns_422(client):
    """REQ-012: 起票ボディの未定義キーは 422 で拒否され、申請が作られない。"""
    res = client.post(
        "/requests",
        json={
            "applicant": "alice",
            "amount": 50_000,
            "title": "備品購入",
            "approvers": ["bob"],
            "nte": "誤字",
        },
    )
    assert res.status_code == 422
    assert client.get("/requests").json() == []


def test_unknown_id_with_invalid_body_returns_422_not_404(client):
    """REQ-012 / ADR-0003: 判定順序は 入力不正（422）→ 不在（404）→ ルール違反（409）。

    存在しない ID に未定義キーを含む不正なボディを送った場合、422 になる（404 ではない）。
    """
    res = client.post(
        "/requests/REQ-9999/submit", json={"actor": "alice", "nte": "誤字"}
    )
    assert res.status_code == 422


# --- REQ-010: note が API から監査ログまで届く ------------------------------
def test_submit_note_reaches_audit_log(client):
    """REQ-010: submit の note が API から監査ログまで届く。"""
    rid = _create(client).json()["id"]
    client.post(
        f"/requests/{rid}/submit", json={"actor": "alice", "note": "提出コメント"}
    )
    log = client.get(f"/requests/{rid}").json()["audit_log"]
    assert log[-1]["note"] == "提出コメント"


def test_approve_note_reaches_audit_log(client):
    """REQ-010: approve の note が API から監査ログまで届く。"""
    rid = _create(client).json()["id"]
    client.post(f"/requests/{rid}/submit", json={"actor": "alice"})
    client.post(
        f"/requests/{rid}/approve", json={"actor": "bob", "note": "承認コメント"}
    )
    log = client.get(f"/requests/{rid}").json()["audit_log"]
    assert log[-1]["note"] == "承認コメント"


def test_withdraw_note_reaches_audit_log(client):
    """REQ-010: withdraw の note が API から監査ログまで届く。"""
    rid = _create(client).json()["id"]
    client.post(
        f"/requests/{rid}/withdraw", json={"actor": "alice", "note": "取下げ理由"}
    )
    log = client.get(f"/requests/{rid}").json()["audit_log"]
    assert log[-1]["note"] == "取下げ理由"
