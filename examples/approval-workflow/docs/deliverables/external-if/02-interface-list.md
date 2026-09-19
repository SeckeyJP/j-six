# 外部インタフェース一覧

**工程成果物**: 外部インタフェース ② ／ **由来**: **コードから逆生成**
**逆生成元**: `app/main.py`（エンドポイント定義、`status_code`、`response_model`、`_guard`）、FastAPI が生成する OpenAPI（`app.openapi()`）
**対象**: 申請承認ワークフロー（approval-workflow） ／ **版**: 1.0 ／ **日付**: 2026-09-19

本システムが**提供する** HTTP API の一覧。他システムを呼び出す IF は無い
（[外部システム関連図](01-system-relation.md)）。

| IF | 名称 | 相手システム | 方向 | 形式 | 文字コード | 改行 | タイミング | 実装 |
|---|---|---|---|---|---|---|---|---|
| `POST /requests` | 申請の起票（UC-001） | 利用クライアント | 受信 | JSON（`CreateRequestBody`）→ JSON（`RequestView`） | UTF-8 | — | 随時・同期 | `main.create_request` → `WorkflowService.create_request` |
| `GET /requests` | 申請の一覧 | 利用クライアント | 受信 | なし → JSON（`RequestView` の配列） | UTF-8 | — | 随時・同期 | `main.list_requests` → `WorkflowService.list_all` |
| `GET /requests/{request_id}` | 申請の取得 | 利用クライアント | 受信 | なし → JSON（`RequestView`） | UTF-8 | — | 随時・同期 | `main.get_request` → `WorkflowService.get` |
| `POST /requests/{request_id}/submit` | 提出（UC-002） | 利用クライアント | 受信 | JSON（`ActorBody`）→ JSON（`RequestView`） | UTF-8 | — | 随時・同期 | `main.submit` → `WorkflowService.submit` |
| `POST /requests/{request_id}/approve` | 承認（UC-003） | 利用クライアント | 受信 | JSON（`ActorBody`）→ JSON（`RequestView`） | UTF-8 | — | 随時・同期 | `main.approve` → `WorkflowService.approve` |
| `POST /requests/{request_id}/reject` | 却下（UC-004） | 利用クライアント | 受信 | JSON（`ActorBody`）→ JSON（`RequestView`） | UTF-8 | — | 随時・同期 | `main.reject` → `WorkflowService.reject` |
| `POST /requests/{request_id}/remand` | 差し戻し（UC-005） | 利用クライアント | 受信 | JSON（`ActorBody`）→ JSON（`RequestView`） | UTF-8 | — | 随時・同期 | `main.remand` → `WorkflowService.remand` |
| `POST /requests/{request_id}/withdraw` | 取下げ（UC-006） | 利用クライアント | 受信 | JSON（`ActorBody`）→ JSON（`RequestView`） | UTF-8 | — | 随時・同期 | `main.withdraw` → `WorkflowService.withdraw` |

## 応答ステータス

| IF | 成功 | 対象不在 | ルール違反 | 入力不正 |
|---|---|---|---|---|
| `POST /requests` | 201 | —（対象を取らない） | 409 | 422 |
| `GET /requests` | 200 | — | — | —（ボディなし） |
| `GET /requests/{request_id}` | 200 | 404 | — | —（ボディなし） |
| `POST /requests/{request_id}/submit` | 200 | 404 | 409 | 422 |
| `POST /requests/{request_id}/approve` | 200 | 404 | 409 | 422 |
| `POST /requests/{request_id}/reject` | 200 | 404 | 409 | 422 |
| `POST /requests/{request_id}/remand` | 200 | 404 | 409 | 422 |
| `POST /requests/{request_id}/withdraw` | 200 | 404 | 409 | 422 |

成功時のステータスはコード（`status_code=201` の指定と FastAPI の既定値 200）から写した。
Design Spec は成功時のステータスを規定しておらず、受入テストも 2xx としか検証していない
（`tests/acceptance/conftest.py`）。404 / 409 / 422 の対応は ADR-0003 と Design Spec 4.3 のとおり。

**[要確認] OpenAPI に 404 / 409 が載っていない。** FastAPI が自動生成する OpenAPI
（`/openapi.json`、Swagger UI）には、各エンドポイントの応答として成功（200 / 201）と 422 しか
宣言されていない。404 / 409 は `_guard` が `HTTPException` として送出しており、`responses=` で
宣言していないためである。OpenAPI だけを見るクライアントは 404 / 409 を知ることができない。

## 件数・容量

| IF | 想定件数 | 備考 |
|---|---|---|
| 全 IF | [要確認] 要求 Spec・Design Spec に件数の見積りが無い | 性能目標は API レスポンスタイム 200ms 以内（要求 Spec 3.5.2）。Design Spec 5.3 は「インメモリのため計測対象外」 |
| `GET /requests` | 登録済みの全件 | ページング・絞り込みは無い。応答の大きさは申請数と監査ログの件数に比例して増える |

## エラー時の扱い

| IF | 事象 | 動作 | 根拠 |
|---|---|---|---|
| 状態遷移 5本 / 起票 | ボディに未定義の項目がある・型が合わない・必須項目が無い | 422。ハンドラを呼ばず、状態も監査ログも変えない | REQ-012、ADR-0003（Pydantic `extra="forbid"`） |
| 取得 / 状態遷移 5本 | 対象の申請が存在しない | 404（`detail` は「申請が存在しません: {id}」）。何も変えない | REQ-011、ADR-0003 |
| 起票 / 状態遷移 5本 | 業務ルール違反 | 409（`detail` は違反したルールの説明文）。何も変えない | REQ-001〜REQ-009、ADR-0003 |
| 状態遷移 5本 | 存在しない ID に不正なボディを送った | 422（404 より先に判定） | ADR-0003 の判定順序 |
| `GET /requests` | 申請が0件 | 200 で空の配列 `[]` | `list_all` が空リストを返す |

## 環境依存が残っている箇所

**[要確認] 監査ログの時刻にタイムゾーンが無い。** 既定の `clock` は `datetime.now`（ローカル時刻・
タイムゾーン情報なし）で、応答の `audit_log[].at` は `datetime.isoformat()` による
オフセット無しの文字列（例: `2026-09-19T13:47:55.447038`）になる。同じ操作でも、サーバの
タイムゾーン設定によって記録される値が変わる。テストでは `clock` を固定値（`FIXED_NOW`）に
差し替えているため、この環境依存は検出されない。

文字コードは FastAPI（Starlette）の `JSONResponse` が UTF-8 で固定しており、日本語は
エスケープされずにそのまま出力される（`detail` のメッセージ、`title` / `note` の値）。
