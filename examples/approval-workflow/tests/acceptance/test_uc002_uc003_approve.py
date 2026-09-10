"""UC-002 / UC-003: 申請の提出と承認（hold-out 受入テスト）。

対応: UC-002, UC-003 / REQ-001, REQ-002, REQ-003, REQ-008, REQ-010
"""


def _create(client, amount, approvers, applicant="alice"):
    res = client.post(
        "/requests",
        json={"applicant": applicant, "amount": amount, "title": "申請", "approvers": approvers},
    )
    assert res.is_success, res.text
    return res.json()["id"]


def test_uc002_applicant_submits_draft(client):
    """UC-002 / REQ-002: 申請者が提出すると PENDING になり、次の承認者が決まる。"""
    rid = _create(client, 50000, ["bob"])

    res = client.post(f"/requests/{rid}/submit", json={"actor": "alice"})
    assert res.is_success, res.text

    body = res.json()
    assert body["status"] == "PENDING"
    assert body["next_approver"] == "bob"


def test_uc003_single_step_approval_completes(client):
    """UC-003 / REQ-001: 10万円未満は1段承認で APPROVED になる。"""
    rid = _create(client, 50000, ["bob"])
    client.post(f"/requests/{rid}/submit", json={"actor": "alice"})

    res = client.post(f"/requests/{rid}/approve", json={"actor": "bob"})
    assert res.is_success, res.text
    assert res.json()["status"] == "APPROVED"


def test_uc003_two_step_approval_requires_both_in_order(client):
    """UC-003 / REQ-001, REQ-003, REQ-008: 10万〜100万未満は2段。順序どおりでのみ進む。"""
    rid = _create(client, 300000, ["bob", "carol"])
    client.post(f"/requests/{rid}/submit", json={"actor": "alice"})

    # 2人目が先に承認しようとしても通らない（REQ-008）
    assert client.post(f"/requests/{rid}/approve", json={"actor": "carol"}).status_code == 409

    first = client.post(f"/requests/{rid}/approve", json={"actor": "bob"})
    assert first.is_success, first.text
    assert first.json()["status"] == "PENDING"
    assert first.json()["next_approver"] == "carol"

    second = client.post(f"/requests/{rid}/approve", json={"actor": "carol"})
    assert second.is_success, second.text
    assert second.json()["status"] == "APPROVED"

    # REQ-010: 一連の操作がすべて監査ログに残る
    actions = [e["action"] for e in second.json()["audit_log"]]
    assert actions == ["CREATE", "SUBMIT", "APPROVE", "APPROVE"]
