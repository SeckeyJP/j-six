"""申請承認ワークフロー — ドメインモデル

J-SIX ケーススタディ（A1）/ テンプレ実例（B）/ Plugin デモ（C2）で共有する
サンプルアプリのドメイン定義。

設計判断は docs/adr/ を参照:
- ADR-0001: 状態遷移を明示的なステートマシンで表現する
- ADR-0002: 監査ログを全状態遷移で必須化する
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Status(str, Enum):
    """申請の状態。"""

    DRAFT = "DRAFT"          # 起票中（申請者が編集可能）
    PENDING = "PENDING"      # 承認待ち
    APPROVED = "APPROVED"    # 承認完了（終了状態）
    REJECTED = "REJECTED"    # 却下（終了状態）
    WITHDRAWN = "WITHDRAWN"  # 取下げ（終了状態）

    @property
    def is_terminal(self) -> bool:
        return self in (Status.APPROVED, Status.REJECTED, Status.WITHDRAWN)


class Action(str, Enum):
    """監査ログに記録する操作種別。"""

    CREATE = "CREATE"
    SUBMIT = "SUBMIT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REMAND = "REMAND"      # 差し戻し
    WITHDRAW = "WITHDRAW"  # 取下げ


@dataclass(frozen=True)
class AuditEntry:
    """監査ログの1エントリ（不変）。"""

    action: Action
    actor: str
    at: datetime
    note: str = ""


@dataclass
class ApprovalRequest:
    """申請。承認は approvers の順序どおりに行う。"""

    id: str
    applicant: str
    amount: int
    title: str
    approvers: list[str]
    status: Status = Status.DRAFT
    current_step: int = 0  # 次に承認すべき approvers のインデックス
    audit_log: list[AuditEntry] = field(default_factory=list)

    @property
    def next_approver(self) -> Optional[str]:
        if self.status != Status.PENDING:
            return None
        if self.current_step >= len(self.approvers):
            return None
        return self.approvers[self.current_step]
