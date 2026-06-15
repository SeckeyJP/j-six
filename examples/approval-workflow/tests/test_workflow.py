"""ドメインロジックの単体テスト。

各テストは要求Spec の REQ-NNN に対応する（トレーサビリティ用タグ）。
"""
from datetime import datetime

import pytest

from app.models import Action, Status
from app.workflow import WorkflowError, WorkflowService, required_approval_levels


FIXED_NOW = datetime(2026, 6, 14, 10, 0, 0)


@pytest.fixture
def service() -> WorkflowService:
    return WorkflowService(clock=lambda: FIXED_NOW)


# --- REQ-001: 金額に応じた承認段数 ----------------------------------------
@pytest.mark.parametrize(
    "amount,levels",
    [(1, 1), (99_999, 1), (100_000, 2), (999_999, 2), (1_000_000, 3), (5_000_000, 3)],
)
def test_required_levels_by_amount(amount, levels):
    assert required_approval_levels(amount) == levels


def test_create_request_sets_draft_and_audit(service):
    req = service.create_request("alice", 50_000, "備品購入", ["bob"])
    assert req.id == "REQ-0001"
    assert req.status == Status.DRAFT
    assert req.amount == 50_000
    assert [e.action for e in req.audit_log] == [Action.CREATE]


def test_create_request_rejects_wrong_approver_count(service):
    # 100万円以上は3段必要なのに2名 → エラー
    with pytest.raises(WorkflowError, match="3 名の承認者が必要"):
        service.create_request("alice", 1_000_000, "サーバ購入", ["bob", "carol"])


def test_create_request_rejects_zero_amount(service):
    with pytest.raises(WorkflowError, match="金額は1以上"):
        service.create_request("alice", 0, "x", ["bob"])


def test_create_request_rejects_empty_title(service):
    with pytest.raises(WorkflowError, match="タイトルは必須"):
        service.create_request("alice", 5_000, "   ", ["bob"])


# --- REQ-007: 自己承認の禁止 ----------------------------------------------
def test_applicant_cannot_be_approver(service):
    with pytest.raises(WorkflowError, match="自身の承認者"):
        service.create_request("alice", 50_000, "x", ["alice"])


def test_duplicate_approvers_rejected(service):
    with pytest.raises(WorkflowError, match="重複"):
        service.create_request("alice", 500_000, "x", ["bob", "bob"])


# --- REQ-002: 提出 ---------------------------------------------------------
def test_submit_moves_draft_to_pending(service):
    req = service.create_request("alice", 50_000, "x", ["bob"])
    service.submit(req.id, "alice")
    assert req.status == Status.PENDING
    assert req.next_approver == "bob"


def test_only_applicant_can_submit(service):
    req = service.create_request("alice", 50_000, "x", ["bob"])
    with pytest.raises(WorkflowError, match="申請者のみ"):
        service.submit(req.id, "bob")


def test_cannot_submit_twice(service):
    req = service.create_request("alice", 50_000, "x", ["bob"])
    service.submit(req.id, "alice")
    with pytest.raises(WorkflowError, match="起票中の申請のみ"):
        service.submit(req.id, "alice")


# --- REQ-003: 順序どおりの多段承認 ----------------------------------------
def test_two_step_approval_completes(service):
    req = service.create_request("alice", 500_000, "x", ["bob", "carol"])
    service.submit(req.id, "alice")
    service.approve(req.id, "bob")
    assert req.status == Status.PENDING  # まだ1段目のみ
    assert req.next_approver == "carol"
    service.approve(req.id, "carol")
    assert req.status == Status.APPROVED
    assert req.next_approver is None


def test_single_step_approval_completes(service):
    req = service.create_request("alice", 50_000, "x", ["bob"])
    service.submit(req.id, "alice")
    service.approve(req.id, "bob")
    assert req.status == Status.APPROVED


# --- REQ-008: 承認順序の強制 ----------------------------------------------
def test_out_of_order_approval_rejected(service):
    req = service.create_request("alice", 500_000, "x", ["bob", "carol"])
    service.submit(req.id, "alice")
    with pytest.raises(WorkflowError, match="承認順序が不正"):
        service.approve(req.id, "carol")  # bob より先に carol は不可


def test_cannot_approve_draft(service):
    req = service.create_request("alice", 50_000, "x", ["bob"])
    with pytest.raises(WorkflowError, match="承認待ちの申請のみ"):
        service.approve(req.id, "bob")


# --- REQ-004: 却下 ---------------------------------------------------------
def test_reject_terminates(service):
    req = service.create_request("alice", 500_000, "x", ["bob", "carol"])
    service.submit(req.id, "alice")
    service.reject(req.id, "bob", note="予算超過")
    assert req.status == Status.REJECTED
    assert req.audit_log[-1].note == "予算超過"


def test_only_current_approver_can_reject(service):
    req = service.create_request("alice", 500_000, "x", ["bob", "carol"])
    service.submit(req.id, "alice")
    with pytest.raises(WorkflowError, match="現在の承認者"):
        service.reject(req.id, "carol")


# --- REQ-005: 差し戻し -----------------------------------------------------
def test_remand_returns_to_draft_and_resets_step(service):
    req = service.create_request("alice", 500_000, "x", ["bob", "carol"])
    service.submit(req.id, "alice")
    service.approve(req.id, "bob")  # 1段目承認済み
    service.remand(req.id, "carol", note="証憑添付してください")
    assert req.status == Status.DRAFT
    assert req.current_step == 0
    # 再提出すると承認は最初からやり直し
    service.submit(req.id, "alice")
    assert req.next_approver == "bob"


# --- REQ-006: 取下げ -------------------------------------------------------
def test_withdraw_from_draft(service):
    req = service.create_request("alice", 50_000, "x", ["bob"])
    service.withdraw(req.id, "alice")
    assert req.status == Status.WITHDRAWN


def test_withdraw_from_pending(service):
    req = service.create_request("alice", 50_000, "x", ["bob"])
    service.submit(req.id, "alice")
    service.withdraw(req.id, "alice")
    assert req.status == Status.WITHDRAWN


def test_only_applicant_can_withdraw(service):
    req = service.create_request("alice", 50_000, "x", ["bob"])
    service.submit(req.id, "alice")
    with pytest.raises(WorkflowError, match="申請者のみ"):
        service.withdraw(req.id, "bob")


# --- REQ-009: 終了済み申請の操作不可 --------------------------------------
def test_cannot_operate_on_terminal_request(service):
    req = service.create_request("alice", 50_000, "x", ["bob"])
    service.submit(req.id, "alice")
    service.approve(req.id, "bob")  # APPROVED
    for op in (
        lambda: service.submit(req.id, "alice"),
        lambda: service.approve(req.id, "bob"),
        lambda: service.reject(req.id, "bob"),
        lambda: service.withdraw(req.id, "alice"),
    ):
        with pytest.raises(WorkflowError, match="終了|承認待ち|起票中"):
            op()


# --- REQ-010: 全状態遷移の監査ログ ----------------------------------------
def test_full_audit_trail(service):
    req = service.create_request("alice", 500_000, "x", ["bob", "carol"])
    service.submit(req.id, "alice")
    service.approve(req.id, "bob")
    service.approve(req.id, "carol")
    actions = [e.action for e in req.audit_log]
    assert actions == [Action.CREATE, Action.SUBMIT, Action.APPROVE, Action.APPROVE]
    assert all(e.at == FIXED_NOW for e in req.audit_log)


def test_get_unknown_request_raises(service):
    with pytest.raises(WorkflowError, match="存在しません"):
        service.get("REQ-9999")
