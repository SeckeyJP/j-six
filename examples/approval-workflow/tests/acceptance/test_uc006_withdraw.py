"""UC-006: 申請を取下げる（hold-out 受入テスト）。

対応: UC-006 / REQ-006, REQ-009, REQ-010 / PROP-007
"""


def _create(client, approvers=("bob",)):
    res = client.post(
        "/requests",
        json={
            "applicant": "alice",
            "amount": 50000,
            "title": "申請",
            "approvers": list(approvers),
        },
    )
    return res.json()["id"]


def test_uc006_applicant_withdraws_from_draft(client):
    """UC-006 / REQ-006: 申請者は DRAFT の申請を取下げられる。"""
    rid = _create(client)
    res = client.post(f"/requests/{rid}/withdraw", json={"actor": "alice"})
    assert res.is_success, res.text
    assert res.json()["status"] == "WITHDRAWN"


def test_uc006_applicant_withdraws_from_pending(client):
    """UC-006 / REQ-006: 承認待ちの申請も申請者なら取下げられる。"""
    rid = _create(client)
    client.post(f"/requests/{rid}/submit", json={"actor": "alice"})

    res = client.post(f"/requests/{rid}/withdraw", json={"actor": "alice"})
    assert res.is_success, res.text
    assert res.json()["status"] == "WITHDRAWN"


def test_uc006_others_cannot_withdraw(client):
    """UC-006 / REQ-006: 申請者以外は取下げられない。"""
    rid = _create(client)
    assert (
        client.post(f"/requests/{rid}/withdraw", json={"actor": "bob"}).status_code
        == 409
    )


def test_uc006_withdraw_note_is_recorded_from_draft(client):
    """UC-006 / REQ-006, REQ-010 / PROP-007: DRAFT からの取下げコメントが監査ログに残る。"""
    rid = _create(client)

    res = client.post(
        f"/requests/{rid}/withdraw", json={"actor": "alice", "note": "購入不要になった"}
    )
    assert res.is_success, res.text
    assert res.json()["status"] == "WITHDRAWN"

    log = client.get(f"/requests/{rid}").json()["audit_log"]
    assert [(e["action"], e["actor"], e["note"]) for e in log] == [
        ("CREATE", "alice", ""),
        ("WITHDRAW", "alice", "購入不要になった"),
    ]


def test_uc006_withdraw_note_is_recorded_from_pending(client):
    """UC-006 / REQ-006, REQ-010 / PROP-007: PENDING からの取下げコメントが監査ログに残る。"""
    rid = _create(client)
    client.post(f"/requests/{rid}/submit", json={"actor": "alice"})

    res = client.post(
        f"/requests/{rid}/withdraw", json={"actor": "alice", "note": "金額を誤った"}
    )
    assert res.is_success, res.text
    assert res.json()["status"] == "WITHDRAWN"

    last = client.get(f"/requests/{rid}").json()["audit_log"][-1]
    assert last["action"] == "WITHDRAW"
    assert last["actor"] == "alice"
    assert last["note"] == "金額を誤った"
