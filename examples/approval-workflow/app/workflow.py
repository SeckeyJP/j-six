"""申請承認ワークフロー — ドメインロジック（ステートマシン）

状態遷移と承認順序・権限ルールを集約する。永続化やHTTPには依存しない純粋ロジック。
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional

from .models import Action, ApprovalRequest, AuditEntry, Status


class WorkflowError(Exception):
    """ドメインルール違反。API 層で 400/409 に変換する。"""


def required_approval_levels(amount: int) -> int:
    """金額に応じた必要承認段数。

    - 10万円未満      : 1段
    - 10万〜100万円未満: 2段
    - 100万円以上     : 3段
    """
    if amount < 100_000:
        return 1
    if amount < 1_000_000:
        return 2
    return 3


class WorkflowService:
    """申請のライフサイクルを管理する。

    Repository を兼ねた最小実装（インメモリ）。clock を注入してテスト容易性を確保する。
    """

    def __init__(self, clock: Optional[Callable[[], datetime]] = None) -> None:
        self._store: dict[str, ApprovalRequest] = {}
        self._seq = 0
        self._clock = clock or datetime.now

    # --- 取得 ---------------------------------------------------------------
    def get(self, request_id: str) -> ApprovalRequest:
        req = self._store.get(request_id)
        if req is None:
            raise WorkflowError(f"申請が存在しません: {request_id}")
        return req

    def list_all(self) -> list[ApprovalRequest]:
        return list(self._store.values())

    # --- 生成 ---------------------------------------------------------------
    def create_request(
        self, applicant: str, amount: int, title: str, approvers: list[str]
    ) -> ApprovalRequest:
        if amount <= 0:
            raise WorkflowError("金額は1以上で指定してください")
        if not title.strip():
            raise WorkflowError("タイトルは必須です")
        if applicant in approvers:
            raise WorkflowError("申請者は自身の承認者になれません")
        if len(set(approvers)) != len(approvers):
            raise WorkflowError("承認者が重複しています")
        needed = required_approval_levels(amount)
        if len(approvers) != needed:
            raise WorkflowError(
                f"金額 {amount:,} 円には {needed} 名の承認者が必要です（指定: {len(approvers)} 名）"
            )

        self._seq += 1
        request_id = f"REQ-{self._seq:04d}"
        req = ApprovalRequest(
            id=request_id,
            applicant=applicant,
            amount=amount,
            title=title,
            approvers=list(approvers),
        )
        self._log(req, Action.CREATE, applicant)
        self._store[request_id] = req
        return req

    # --- 状態遷移 -----------------------------------------------------------
    def submit(self, request_id: str, actor: str) -> ApprovalRequest:
        req = self.get(request_id)
        self._ensure_active(req)
        if req.status != Status.DRAFT:
            raise WorkflowError("起票中の申請のみ提出できます")
        if actor != req.applicant:
            raise WorkflowError("提出できるのは申請者のみです")
        req.status = Status.PENDING
        req.current_step = 0
        self._log(req, Action.SUBMIT, actor)
        return req

    def approve(self, request_id: str, actor: str) -> ApprovalRequest:
        req = self.get(request_id)
        self._ensure_pending(req)
        if actor != req.next_approver:
            raise WorkflowError(
                f"承認順序が不正です。現在の承認者は {req.next_approver} です"
            )
        req.current_step += 1
        if req.current_step >= len(req.approvers):
            req.status = Status.APPROVED
        self._log(req, Action.APPROVE, actor)
        return req

    def reject(self, request_id: str, actor: str, note: str = "") -> ApprovalRequest:
        req = self.get(request_id)
        self._ensure_pending(req)
        if actor != req.next_approver:
            raise WorkflowError(
                f"却下できるのは現在の承認者 {req.next_approver} のみです"
            )
        req.status = Status.REJECTED
        self._log(req, Action.REJECT, actor, note)
        return req

    def remand(self, request_id: str, actor: str, note: str = "") -> ApprovalRequest:
        """差し戻し。現在の承認者が起票中（DRAFT）へ戻す。"""
        req = self.get(request_id)
        self._ensure_pending(req)
        if actor != req.next_approver:
            raise WorkflowError(
                f"差し戻しできるのは現在の承認者 {req.next_approver} のみです"
            )
        req.status = Status.DRAFT
        req.current_step = 0
        self._log(req, Action.REMAND, actor, note)
        return req

    def withdraw(self, request_id: str, actor: str) -> ApprovalRequest:
        """取下げ。申請者が DRAFT / PENDING から取り下げる。"""
        req = self.get(request_id)
        self._ensure_active(req)
        if actor != req.applicant:
            raise WorkflowError("取下げできるのは申請者のみです")
        req.status = Status.WITHDRAWN
        self._log(req, Action.WITHDRAW, actor)
        return req

    # --- 内部ヘルパ ---------------------------------------------------------
    def _ensure_active(self, req: ApprovalRequest) -> None:
        if req.status.is_terminal:
            raise WorkflowError(f"終了済みの申請は操作できません（状態: {req.status.value}）")

    def _ensure_pending(self, req: ApprovalRequest) -> None:
        self._ensure_active(req)
        if req.status != Status.PENDING:
            raise WorkflowError("承認待ちの申請のみ操作できます")

    def _log(self, req: ApprovalRequest, action: Action, actor: str, note: str = "") -> None:
        req.audit_log.append(
            AuditEntry(action=action, actor=actor, at=self._clock(), note=note)
        )
