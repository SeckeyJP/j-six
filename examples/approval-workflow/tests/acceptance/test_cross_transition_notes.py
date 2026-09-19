"""UC-002〜UC-006（横断）: 状態遷移コメントの記録（hold-out 受入テスト）。

対応: UC-002, UC-003, UC-004, UC-005, UC-006 / REQ-010 / PROP-007

任意の状態遷移操作（提出・承認・却下・差し戻し・取下げ）と任意のコメントについて、
操作が成功したなら、監査ログ末尾のコメントは送ったコメントと一致する（省略したときは空文字）。
HTTP API 経由でのみ検証する。
"""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# 各操作: (監査ログの action, 操作前に申請を PENDING にするか, 操作者)
OPERATIONS = {
    "submit": ("SUBMIT", False, "alice"),
    "approve": ("APPROVE", True, "bob"),
    "reject": ("REJECT", True, "bob"),
    "remand": ("REMAND", True, "bob"),
    "withdraw": ("WITHDRAW", False, "alice"),
    "withdraw_pending": ("WITHDRAW", True, "alice"),
}


def _prepare(client, pending):
    res = client.post(
        "/requests",
        json={
            "applicant": "alice",
            "amount": 50000,
            "title": "申請",
            "approvers": ["bob"],
        },
    )
    assert res.is_success, res.text
    rid = res.json()["id"]
    if pending:
        sub = client.post(f"/requests/{rid}/submit", json={"actor": "alice"})
        assert sub.is_success, sub.text
    return rid


def _operate(client, op, note):
    expected_action, pending, actor = OPERATIONS[op]
    rid = _prepare(client, pending)
    path = "withdraw" if op == "withdraw_pending" else op
    body = {"actor": actor}
    if note is not None:
        body["note"] = note
    res = client.post(f"/requests/{rid}/{path}", json=body)
    assert res.is_success, (op, res.status_code, res.text)
    return rid, res, expected_action, actor


@pytest.mark.parametrize("op", sorted(OPERATIONS))
def test_req010_every_transition_records_its_note(client, op):
    """UC-002〜UC-006 / REQ-010 / PROP-007: 全状態遷移で、付けたコメントが監査ログに残る。

    却下・差し戻しの理由に限らず、提出・承認・取下げのコメントも記録する。
    """
    rid, res, expected_action, actor = _operate(client, op, f"{op} のコメント")

    for log in (
        res.json()["audit_log"],
        client.get(f"/requests/{rid}").json()["audit_log"],
    ):
        last = log[-1]
        assert last["action"] == expected_action
        assert last["actor"] == actor
        assert last["note"] == f"{op} のコメント"


@pytest.mark.parametrize("op", sorted(OPERATIONS))
def test_req010_omitted_note_is_recorded_as_empty(client, op):
    """UC-002〜UC-006 / REQ-010 / PROP-007: コメントを省略した操作も成功し、空文字で記録される。"""
    rid, _, expected_action, _ = _operate(client, op, None)

    last = client.get(f"/requests/{rid}").json()["audit_log"][-1]
    assert last["action"] == expected_action
    assert last["note"] == ""


@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    op=st.sampled_from(sorted(OPERATIONS)),
    note=st.one_of(st.none(), st.text(max_size=40)),
)
def test_prop007_last_audit_note_equals_sent_note(client, op, note):
    """PROP-007 / REQ-010: 成功した状態遷移の監査ログ末尾のコメントは、送ったコメントと一致する。

    省略したときは空文字。
    """
    rid, _, expected_action, actor = _operate(client, op, note)

    last = client.get(f"/requests/{rid}").json()["audit_log"][-1]
    assert last["action"] == expected_action
    assert last["actor"] == actor
    assert last["note"] == ("" if note is None else note)
