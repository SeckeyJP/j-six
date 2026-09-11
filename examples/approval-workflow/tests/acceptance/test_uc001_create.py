"""UC-001: 申請を起票する（hold-out 受入テスト）。

対応: UC-001 / REQ-001（承認段数は金額で決まる）/ REQ-007（自己承認の禁止）
"""


def test_uc001_applicant_creates_draft_request(client):
    """UC-001 / REQ-001: 金額に応じた承認段数で DRAFT の申請が起票できる。"""
    res = client.post(
        "/requests",
        json={
            "applicant": "alice",
            "amount": 50000,
            "title": "備品購入",
            "approvers": ["bob"],
        },
    )
    assert res.is_success, res.text

    body = res.json()
    assert body["status"] == "DRAFT"
    assert body["applicant"] == "alice"
    assert body["amount"] == 50000
    assert body["approvers"] == ["bob"]
    # REQ-010: 起票も監査ログに残る
    assert [e["action"] for e in body["audit_log"]] == ["CREATE"]

    # 起票した申請は取得できる
    got = client.get(f"/requests/{body['id']}")
    assert got.is_success, got.text
    assert got.json()["id"] == body["id"]


def test_uc001_rejects_self_approval(client):
    """UC-001 / REQ-007: 申請者を承認者に含む起票は受け付けられない。"""
    res = client.post(
        "/requests",
        json={
            "applicant": "alice",
            "amount": 50000,
            "title": "備品購入",
            "approvers": ["alice"],
        },
    )
    assert res.status_code == 409
