"""UC-004 / UC-005: 却下と差し戻し（hold-out 受入テスト）。

対応: UC-004, UC-005 / REQ-004, REQ-005, REQ-009
"""


def _submitted(client, amount=50000, approvers=("bob",)):
    res = client.post(
        "/requests",
        json={"applicant": "alice", "amount": amount, "title": "申請", "approvers": list(approvers)},
    )
    rid = res.json()["id"]
    client.post(f"/requests/{rid}/submit", json={"actor": "alice"})
    return rid


def test_uc004_approver_rejects_and_it_is_terminal(client):
    """UC-004 / REQ-004, REQ-009: 却下は終了状態であり、以降の操作を受け付けない。"""
    rid = _submitted(client)

    res = client.post(f"/requests/{rid}/reject", json={"actor": "bob", "note": "予算超過"})
    assert res.is_success, res.text
    assert res.json()["status"] == "REJECTED"

    # 終了状態への操作はエラー（REQ-009）
    assert client.post(f"/requests/{rid}/approve", json={"actor": "bob"}).status_code == 409
    assert client.post(f"/requests/{rid}/withdraw", json={"actor": "alice"}).status_code == 409


def test_uc005_remand_returns_to_draft_and_restarts(client):
    """UC-005 / REQ-005: 差し戻すと DRAFT に戻り、再提出は最初の承認者からやり直す。"""
    rid = _submitted(client, amount=300000, approvers=("bob", "carol"))
    client.post(f"/requests/{rid}/approve", json={"actor": "bob"})

    res = client.post(f"/requests/{rid}/remand", json={"actor": "carol", "note": "見積添付漏れ"})
    assert res.is_success, res.text
    assert res.json()["status"] == "DRAFT"

    again = client.post(f"/requests/{rid}/submit", json={"actor": "alice"})
    assert again.is_success, again.text
    assert again.json()["next_approver"] == "bob"
