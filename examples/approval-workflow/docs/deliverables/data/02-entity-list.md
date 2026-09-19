# エンティティ一覧

**工程成果物**: データモデル ② ／ **由来**: **コードから逆生成**
**逆生成元**: `app/models.py`（`ApprovalRequest`, `AuditEntry`, `Status`, `Action`）、`app/workflow.py`（`WorkflowService._store`）
**対象**: 申請承認ワークフロー（approval-workflow） ／ **版**: 1.0 ／ **日付**: 2026-09-19

| # | エンティティ | 論理名 | 役割 | 主キー | 永続化 |
|---|---|---|---|---|---|
| 1 | `ApprovalRequest` | 申請 | 備品・経費の申請1件。状態と承認の進捗を持つ | `id`（`REQ-` ＋ 4桁の連番） | インメモリの dict（`WorkflowService._store`、キーは `id`） |
| 2 | `AuditEntry` | 監査ログのエントリ | 申請に対する1回の操作（起票・状態遷移）の記録。不変 | なし | 親（`ApprovalRequest.audit_log`）に内包 |

## 区分（列挙型）

| # | 列挙型 | 論理名 | 値 |
|---|---|---|---|
| 1 | `Status` | 申請の状態 | `DRAFT` 起票中 ／ `PENDING` 承認待ち ／ `APPROVED` 承認完了（終了状態） ／ `REJECTED` 却下（終了状態） ／ `WITHDRAWN` 取下げ（終了状態） |
| 2 | `Action` | 監査ログの操作種別 | `CREATE` 起票 ／ `SUBMIT` 提出 ／ `APPROVE` 承認 ／ `REJECT` 却下 ／ `REMAND` 差し戻し ／ `WITHDRAW` 取下げ |

どちらも `str` を継承した `Enum` で、値は名前と同じ文字列である。API の応答にはこの文字列が
そのまま出る（`status` / `audit_log[].action`）。終了状態の判定は `Status.is_terminal`
（APPROVED / REJECTED / WITHDRAWN のとき真）に集約している（ADR-0001）。

## 永続化について

永続化は行わない。`WorkflowService` がインメモリの dict（`_store`）を内包し、Repository を
兼ねている（`app/workflow.py` の docstring「Repository を兼ねた最小実装（インメモリ）」）。
プロセスを再起動すると申請も監査ログも失われる（Design Spec 5.3 可用性、ADR-0002「影響」）。

永続化は要求 Spec 2.2 で対象外としている。RDB へ差し替える場合は `current_step` と `audit_log`
を永続化すればよい（Design Spec 5.2）。差し替え時のテーブル構成は Spec・ADR に無く、
コードからも決まらない [要確認: 物理設計は未着手]。
