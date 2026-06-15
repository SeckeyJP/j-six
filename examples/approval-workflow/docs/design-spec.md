# Design Spec — 申請承認ワークフロー

> J-SIX Phase 2（技術設計）。テンプレート `templates/spec/design-spec.md` の記入済み実例。

**Version**: 1.0 | **Date**: 2026-06-14 | **Author**: H.Sekita

---

## 1. アーキテクチャ概要

モジュラーモノリス。ドメインロジックを HTTP/永続化から分離する。

```
app/
├── models.py    … ドメインモデル（Status / Action / ApprovalRequest / AuditEntry）
├── workflow.py  … ステートマシン（WorkflowService）★ビジネスルールの単一の置き場所
└── main.py      … FastAPI 層（薄いラッパー。WorkflowError → HTTP 409/404 へ変換）
```

設計の要は **ビジネスルールを `workflow.py` に集約**し、HTTP もDBも知らない純粋ロジックに
すること。これにより TDD（Phase 4）は `workflow.py` を高速・網羅的に検証でき、API 層は
結線テストのみで足りる。

## 2. 技術スタック

| レイヤ | 技術 | 関連 ADR |
|---|---|---|
| API | FastAPI | — |
| バリデーション | Pydantic v2 | — |
| 状態管理 | 明示的ステートマシン | ADR-0001 |
| 監査 | イミュータブルな AuditEntry の append | ADR-0002 |
| 永続化 | インメモリ dict（差し替え可能） | — |

## 3. ドメインモデル

```
ApprovalRequest
  id, applicant, amount, title
  approvers: [承認者IDの順序付きリスト]
  status: DRAFT | PENDING | APPROVED | REJECTED | WITHDRAWN
  current_step: 次に承認すべき approvers のインデックス
  audit_log: [AuditEntry...]
```

### 状態遷移図

```
        submit            approve(最終段)
DRAFT ─────────▶ PENDING ─────────────▶ APPROVED
  ▲                │  │
  │ remand         │  │ reject
  └────────────────┘  └────────────────▶ REJECTED
  │                │
  │ withdraw       │ withdraw
  ▼                ▼
WITHDRAWN ◀────────┘
```

## 4. API 設計

| メソッド | パス | 概要 | 異常時 |
|---|---|---|---|
| POST | `/requests` | 申請の起票 | ルール違反は 409 |
| GET | `/requests` | 一覧 | — |
| GET | `/requests/{id}` | 取得 | 不在は 404 |
| POST | `/requests/{id}/submit` | 提出 | 409 |
| POST | `/requests/{id}/approve` | 承認 | 順序違反は 409 |
| POST | `/requests/{id}/reject` | 却下 | 409 |
| POST | `/requests/{id}/remand` | 差し戻し | 409 |
| POST | `/requests/{id}/withdraw` | 取下げ | 409 |

エラー方針: ドメインルール違反（`WorkflowError`）は HTTP 409 Conflict、対象不在は 404。

## 5. 非機能設計

### 5.1 テスト容易性

`WorkflowService` は `clock` を注入可能にし、監査ログのタイムスタンプを決定論的に検証する
（`test_workflow.py` の `FIXED_NOW`）。

### 5.2 永続化の差し替え

現状 `WorkflowService` が dict を内包。将来は Repository インタフェースを切り出し、
RDB 実装に差し替える（`current_step` と `audit_log` を永続化すればよい）。
