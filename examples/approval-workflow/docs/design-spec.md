# Design Spec — 申請承認ワークフロー

> J-SIX Phase 2（技術設計）。テンプレート `templates/spec/design-spec.md` の記入済み実例。

**Version**: 1.1 | **Date**: 2026-09-19 | **Author**: H.Sekita
**Status**: 承認済み
**前提**: [要求 Spec](requirement-spec.md)（1.1）が承認済みであること

---

## 1. アーキテクチャ概要

モジュラーモノリス。ドメインロジックを HTTP/永続化から分離する。

```
app/
├── models.py    … ドメインモデル（Status / Action / ApprovalRequest / AuditEntry）
├── workflow.py  … ステートマシン（WorkflowService）★ビジネスルールの単一の置き場所
│                  不在は RequestNotFound、ルール違反は WorkflowError を送出（ADR-0003）
└── main.py      … FastAPI 層（薄いラッパー）。例外を HTTP ステータスへ変換する
                   RequestNotFound → 404 / WorkflowError → 409 / 入力不正（Pydantic）→ 422
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
| エラー分類 | 不在 / ルール違反 / 入力不正を例外の型で分ける | ADR-0003 |
| 永続化 | インメモリ dict（差し替え可能） | — |

## 3. ドメインモデル

```
ApprovalRequest
  id, applicant, amount, title
  approvers: [承認者IDの順序付きリスト]
  status: DRAFT | PENDING | APPROVED | REJECTED | WITHDRAWN
  current_step: 次に承認すべき approvers のインデックス
  audit_log: [AuditEntry...]

AuditEntry（不変）
  action: CREATE | SUBMIT | APPROVE | REJECT | REMAND | WITHDRAW
  actor:  操作者ID
  at:     操作時刻（注入された clock から取得）
  note:   操作者のコメント。状態遷移では API で受けた note をそのまま記録する（省略時は空文字）。
          CREATE は空文字
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

### ドメイン層の例外（ADR-0003）

| 例外 | 意味 | 送出する箇所 |
|---|---|---|
| `RequestNotFound` | 対象の申請が存在しない（REQ-011） | `WorkflowService.get()`。状態遷移メソッドは `get()` を通して対象を取るため、すべて同じ例外になる |
| `WorkflowError` | ドメインルール違反（REQ-001〜REQ-009） | 起票・状態遷移の各メソッド |

`RequestNotFound` は `WorkflowError` のサブクラスにしない（理由は ADR-0003）。

状態遷移メソッド（`submit` / `approve` / `reject` / `remand` / `withdraw`）は、すべて任意の
`note`（既定値は空文字）を受け取り、`_log()` に渡して監査ログに記録する（REQ-010）。

## 4. API 設計

### 4.1 エンドポイント一覧

| メソッド | パス | 概要 | 対応 UC |
|---|---|---|---|
| POST | `/requests` | 申請の起票 | UC-001 |
| GET | `/requests` | 一覧 | — |
| GET | `/requests/{id}` | 取得 | — |
| POST | `/requests/{id}/submit` | 提出 | UC-002 |
| POST | `/requests/{id}/approve` | 承認 | UC-003 |
| POST | `/requests/{id}/reject` | 却下 | UC-004 |
| POST | `/requests/{id}/remand` | 差し戻し | UC-005 |
| POST | `/requests/{id}/withdraw` | 取下げ | UC-006 |

### 4.2 入力項目

すべてのリクエストボディで**未定義キーは 422 で拒否する**（REQ-012。Pydantic の
`extra="forbid"`）。型の不一致・必須項目の欠落も 422 とする。

**`POST /requests`（起票）**

| 項目 | 型 | 必須/任意 | 説明 |
|---|---|---|---|
| `applicant` | string | 必須 | 申請者ID |
| `amount` | integer | 必須 | 申請金額（円） |
| `title` | string | 必須 | 申請タイトル |
| `approvers` | array of string | 必須 | 承認者IDの順序付きリスト |

**`POST /requests/{id}/submit` / `approve` / `reject` / `remand` / `withdraw`（状態遷移）**

5 本とも同じ入力項目とする。

| 項目 | 型 | 必須/任意 | 説明 |
|---|---|---|---|
| `actor` | string | 必須 | 操作者ID |
| `note` | string | 任意（既定値は空文字） | コメント。監査ログの当該操作の `note` にそのまま記録する（REQ-010） |

**`GET /requests` / `GET /requests/{id}`**: リクエストボディなし。`{id}` はパスパラメータ（string）。

### 4.3 異常時のステータス

分類と例外の対応は ADR-0003 による。

| 分類 | HTTP | 原因 |
|---|---|---|
| 入力不正 | 422 | 型の不一致、必須項目の欠落、未定義キー（Pydantic の検証エラー） |
| 不在 | 404 | 対象の申請が存在しない（`RequestNotFound`） |
| ルール違反 | 409 | ドメインルール違反（`WorkflowError`） |

判定の順序は 入力不正（422）→ 不在（404）→ ルール違反（409）とする。FastAPI はハンドラを呼ぶ前に
ボディを検証するため、存在しない ID に不正なボディを送った場合は 422 になる。

| エンドポイント | 不在 404 | ルール違反 409 | 入力不正 422 |
|---|---|---|---|
| `POST /requests` | —（対象を取らない） | 金額が 1 未満 / タイトルが空 / 申請者が承認者に含まれる（REQ-007） / 承認者の重複 / 承認者数が段数と不一致（REQ-001） | 4.2 の条件 |
| `GET /requests` | — | — | —（ボディなし） |
| `GET /requests/{id}` | 対象不在（REQ-011） | — | —（ボディなし） |
| `POST /requests/{id}/submit` | 対象不在（REQ-011） | 終了済み（REQ-009） / DRAFT 以外 / 申請者以外（REQ-002） | 4.2 の条件 |
| `POST /requests/{id}/approve` | 対象不在（REQ-011） | 終了済み（REQ-009） / PENDING 以外 / 現在の承認者以外（REQ-008） | 4.2 の条件 |
| `POST /requests/{id}/reject` | 対象不在（REQ-011） | 終了済み（REQ-009） / PENDING 以外 / 現在の承認者以外（REQ-008） | 4.2 の条件 |
| `POST /requests/{id}/remand` | 対象不在（REQ-011） | 終了済み（REQ-009） / PENDING 以外 / 現在の承認者以外（REQ-008） | 4.2 の条件 |
| `POST /requests/{id}/withdraw` | 対象不在（REQ-011） | 終了済み（REQ-009） / 申請者以外（REQ-006） | 4.2 の条件 |

いずれの異常時も、申請の状態と監査ログは変更しない。

**未確定**: 金額が 1 未満・タイトルが空の入力は、型としては正しいのでドメイン層で判定し、
本版では 409 とする。これらを入力制約として 422 に寄せるかは設計レビュー W-1 の検討事項として
未確定である（確定: 次回の Design Spec 改訂時 / 担当: アーキテクト）。

## 5. 非機能設計

### 5.1 テスト容易性

`WorkflowService` は `clock` を注入可能にし、監査ログのタイムスタンプを決定論的に検証する
（`test_workflow.py` の `FIXED_NOW`）。

### 5.2 永続化の差し替え

現状 `WorkflowService` が dict を内包。将来は Repository インタフェースを切り出し、
RDB 実装に差し替える（`current_step` と `audit_log` を永続化すればよい）。

### 5.3 要求 Spec 3.5（非機能要求グレード）との対応

本書は旧テンプレートの構成で作成しており、非機能設計の節は6大項目に揃えていない（5.1・5.2 は
テスト容易性と永続化の方針）。6大項目ごとの扱いは次のとおり。

| 大項目 | 本サンプルでの扱い |
|---|---|
| 可用性 | 冗長化しない。インメモリのため再起動で状態が失われる（5.2 で永続化へ差し替える前提） |
| 性能・拡張性 | インメモリのため計測対象外 |
| 運用・保守性 | 全状態遷移を監査ログに記録（REQ-010）。状態遷移のコメントも記録する。タイムスタンプは `clock` 注入で検証可能（5.1） |
| 移行性 | 過去の申請データは移行しない |
| セキュリティ | 自己承認の禁止（REQ-007）と承認順序の強制（REQ-008）をドメイン層で強制。未定義の入力項目は 422 で拒否（REQ-012）。認証は対象外 |
| システム環境・エコロジー | 対象外 |

## 承認

| 役割 | 氏名 | 日付 | 承認 |
|---|---|---|---|
| アーキテクト | （サンプル） | 2026-09-19 | ✅ |
| PM | H.Sekita | 2026-09-19 | ✅ |

**合意成熟度の確認**（Phase 2 品質ゲートの判定基準。J-SIX.md Phase 2 参照）

- [ ] 本書・ADR・実動プロトタイプ・人手で書く工程成果物（業務共通ルール等）が双方で確認済み（**完成レベル**）
      ※ 本書と ADR-0003 は確認済み。実動プロトタイプ（`app/`）は本版の 4 章とまだ合っていない。
      Phase 4 で TDD により合わせてから確認する（担当: 開発者）
- [ ] 実装から逆生成する工程成果物は、プロトタイプ等の代替物で確認済み（**充実レベル**）で、
      Phase 6 で逆生成版に差し替えることが合意されている（設計レビュー W-5。未対応）
- [ ] 顧客に提出する設計書の目次（組立定義）が合意されている（`templates/deliverables/assembly/`）
      （設計レビュー W-5。未対応）

## 改訂履歴

| 版 | 日付 | 内容 |
|---|---|---|
| 1.0 | 2026-06-14 | 初版 |
| 1.1 | 2026-09-19 | 設計レビュー（`docs/reviews/design-review-2026-09-19.md`）の C-1 / C-2 を受けて改訂。エラーを不在 404 / ルール違反 409 / 入力不正 422 に分類（ADR-0003）。4 章にエンドポイントごとの入力項目と異常時ステータスを追加。全状態遷移で `note` を受け付けて監査ログに記録。未定義キーを 422 で拒否。3 章に `AuditEntry` の項目と例外を追加。承認欄を追加 |
