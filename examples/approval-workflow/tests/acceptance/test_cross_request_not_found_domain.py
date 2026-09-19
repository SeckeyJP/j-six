"""UC-002〜UC-006（横断）: 対象不在の例外（hold-out 受入テスト、ドメイン層の公開インタフェース）。

対応: REQ-011 / PROP-008 / ADR-0003

Design Spec 3 章と ADR-0003 が、ドメイン層の公開された例外として `RequestNotFound`
（`WorkflowError` のサブクラスではない）を規定している。この契約だけを検証する。
`except WorkflowError` が不在まで捕まえる事故（設計レビュー C-1 の再発）を型の上で防ぐため。

例外クラスは未実装の段階でも収集エラーにならないよう、各テスト内で import する。
"""

import pytest


def test_request_not_found_is_not_a_workflow_error():
    """REQ-011 / ADR-0003: RequestNotFound は WorkflowError のサブクラスではない。"""
    from app.workflow import RequestNotFound, WorkflowError

    assert issubclass(RequestNotFound, Exception)
    assert not issubclass(RequestNotFound, WorkflowError)
    assert not issubclass(WorkflowError, RequestNotFound)


def test_get_unknown_request_raises_request_not_found():
    """REQ-011 / PROP-008: 存在しない申請の取得は RequestNotFound（WorkflowError ではない）。"""
    from app.workflow import RequestNotFound, WorkflowError, WorkflowService

    service = WorkflowService()
    with pytest.raises(RequestNotFound) as exc:
        service.get("REQ-9999")
    assert not isinstance(exc.value, WorkflowError)


@pytest.mark.parametrize(
    "action", ["submit", "approve", "reject", "remand", "withdraw"]
)
def test_transition_on_unknown_request_raises_request_not_found(action):
    """UC-002〜UC-006 / REQ-011 / PROP-008: 存在しない申請への状態遷移は RequestNotFound。

    登録済みの申請の状態と監査ログは変わらない。
    """
    from app.workflow import RequestNotFound, WorkflowError, WorkflowService

    service = WorkflowService()
    existing = service.create_request("alice", 50000, "申請", ["bob"])
    service.submit(existing.id, "alice")
    status_before = existing.status
    log_before = list(existing.audit_log)

    with pytest.raises(RequestNotFound) as exc:
        getattr(service, action)("REQ-9999", "alice")
    assert not isinstance(exc.value, WorkflowError)

    after = service.get(existing.id)
    assert after.status == status_before
    assert list(after.audit_log) == log_before
