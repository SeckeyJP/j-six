# CRUD図

**工程成果物**: データモデル ④ ／ **由来**: **コードから逆生成**
**逆生成元**: `app/workflow.py`（`WorkflowService` の各メソッドと `_store` / `audit_log` へのアクセス）、`app/main.py`（エンドポイントとメソッドの対応）
**対象**: 申請承認ワークフロー（approval-workflow） ／ **版**: 1.0 ／ **日付**: 2026-09-19

> 業務機能とエンティティの関係を表現したもの。C=生成 R=参照 U=更新 D=削除。

## 機能 × エンティティ

| 機能（実現手段） | UC | ApprovalRequest | AuditEntry | 更新する属性 |
|---|---|---|---|---|
| 起票（`POST /requests` → `create_request`） | UC-001 | **C** | **C** | — |
| 一覧（`GET /requests` → `list_all`） | — | R | R | — |
| 取得（`GET /requests/{id}` → `get`） | — | R | R | — |
| 提出（`POST /requests/{id}/submit` → `submit`） | UC-002 | R/**U** | **C** | `status`（→ PENDING）, `current_step`（→ 0） |
| 承認（`POST /requests/{id}/approve` → `approve`） | UC-003 | R/**U** | **C** | `current_step`（+1）, 最終段のみ `status`（→ APPROVED） |
| 却下（`POST /requests/{id}/reject` → `reject`） | UC-004 | R/**U** | **C** | `status`（→ REJECTED） |
| 差し戻し（`POST /requests/{id}/remand` → `remand`） | UC-005 | R/**U** | **C** | `status`（→ DRAFT）, `current_step`（→ 0） |
| 取下げ（`POST /requests/{id}/withdraw` → `withdraw`） | UC-006 | R/**U** | **C** | `status`（→ WITHDRAWN） |

表の C/U は操作が成功した場合である。検証に失敗した操作（404 / 409 / 422）は何も書き込まない。

## 読み取り方

### D（削除）が1つも無い

申請も監査ログも削除されない。**全操作の証跡を残す要件（REQ-010、ADR-0002）と、終了状態を
操作不可にする要件（REQ-009）から、削除操作を持たない設計になっている。** 終了した申請も
一覧・取得で参照できる。

### ApprovalRequest の U は `status` と `current_step` だけ

`id` / `applicant` / `amount` / `title` / `approvers` を更新する機能は無い。起票時に検証した
「承認者の人数 = 金額から決まる段数」（REQ-001）と「申請者は承認者でない」（REQ-007、PROP-003）が、
起票後に崩れる経路が存在しないことがこの表から読み取れる。
その裏返しとして、差し戻された申請の内容を直す経路も無い（[要確認]。
[システム化業務一覧](../behavior/01-system-function-list.md) 参照）。

### U の行には必ず AuditEntry の C がある

`ApprovalRequest` を更新する5機能すべてが、同じメソッドの末尾で `AuditEntry` を1件生成する
（`_log`）。状態が変わったのに記録が無い、という経路が無い（ADR-0002、PROP-004）。

### AuditEntry が C のみ

監査ログは追記のみで、更新・削除の経路を持たない。エントリ自体も `frozen=True` で書き換えられない（ADR-0002）。

### 検証が書き込みより先にある

どのメソッドも、存在確認（`get`）→ 状態の確認（`_ensure_active` / `_ensure_pending`）→ 操作者の
確認 → 書き込み → `_log` の順に並んでいる。起票も、全検証を通ってから `_seq` を進めて登録する。
このため拒否された操作は申請の状態・監査ログ・採番のいずれも変えない（Design Spec 4.3、PROP-008）。

## 逆生成の方法

`WorkflowService` の各メソッドが `_store`（申請）と `req.audit_log`（監査ログ）に触れる箇所を
静的に追跡して作成した。データアクセスは `app/workflow.py` の `WorkflowService` 1クラスに集約されており
（CLAUDE.md「ビジネスルールは `app/workflow.py` に集約する」）、`app/main.py` は `service` のメソッドを
呼ぶだけでストアに直接触れないため、追跡は容易である。

**除外したもの**: `tests/acceptance/conftest.py` の fixture は `service._store.clear()` /
`service._seq = 0` でストアを初期化し、`tests/test_api.py` の fixture は `WorkflowService` を
作り直して差し替えている。いずれもテストのための操作で、業務機能ではないため表に載せていない。
