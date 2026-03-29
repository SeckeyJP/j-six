# CLAUDE.md 追加セクション — API / バックエンドサービス向け

> base.md の内容に加え、以下のセクションを CLAUDE.md に追記してください。

---

## API 設計ルール

### 基本方針

- API スタイル: [TODO: REST / GraphQL / gRPC]
- API 仕様管理: [TODO: OpenAPI (Swagger) / GraphQL Schema 等]
- API 仕様ファイル: [TODO: docs/openapi.yaml 等]
- バージョニング: [TODO: URL パス (/v1/) / ヘッダー 等]

### エンドポイント命名

- リソース名は複数形（`/users`, `/orders`）
- ネストは2階層まで（`/users/{id}/orders` は OK、`/users/{id}/orders/{id}/items` は避ける）
- アクションは HTTP メソッドで表現（POST /users で作成、DELETE /users/{id} で削除）
- 検索・フィルタはクエリパラメータ（`/users?status=active&sort=name`）

### リクエスト・レスポンス

- リクエスト/レスポンスは JSON 形式
- 日時フォーマット: ISO 8601（`2026-03-29T12:00:00+09:00`）
- ページネーション: [TODO: offset-limit / cursor-based]
- エラーレスポンス形式:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "ユーザー向けメッセージ",
    "details": [
      { "field": "email", "message": "メールアドレスの形式が不正です" }
    ]
  }
}
```

### HTTP ステータスコード

- 200: 成功（GET, PUT, PATCH）
- 201: 作成成功（POST）
- 204: 削除成功（DELETE）
- 400: バリデーションエラー
- 401: 認証エラー
- 403: 認可エラー
- 404: リソース未検出
- 409: 競合（楽観ロック衝突等）
- 500: サーバーエラー

---

## DB 設計ルール

### テーブル設計

- テーブル名: [TODO: snake_case 複数形（users, orders）等]
- カラム名: [TODO: snake_case]
- 主キー: [TODO: UUID / SERIAL / ULID]
- 共通カラム: 全テーブルに `created_at`, `updated_at` を付与
- 論理削除: [TODO: `deleted_at` カラム / 物理削除]
- マイグレーション: [TODO: Prisma / Flyway / Alembic 等]

```bash
# マイグレーション実行
[TODO: コマンド]

# マイグレーション作成
[TODO: コマンド]

# シード実行
[TODO: コマンド]
```

### インデックス

- 外部キーには必ずインデックスを張る
- 検索条件に頻繁に使われるカラムにはインデックスを検討
- 複合インデックスはカーディナリティの高いカラムを先に
- インデックス追加は ADR に記録する（パフォーマンス影響のため）

### トランザクション

- データ整合性が求められる操作は必ずトランザクションで囲む
- トランザクション分離レベル: [TODO: READ COMMITTED 等]
- 楽観ロック: [TODO: version カラム / updated_at 比較]

---

## 外部連携（IF）設計ルール

### API クライアント

- 外部 API 呼び出しは専用のクライアントクラスに集約する
- タイムアウト: [TODO: 接続 5秒 / 読取 30秒 等]
- リトライ: [TODO: 最大3回、指数バックオフ 等]
- サーキットブレーカー: [TODO: 使用する場合のツール・設定]

### メッセージキュー

- [TODO: 使用する場合のみ。RabbitMQ / SQS / Kafka 等]
- メッセージ形式: JSON
- 冪等性: コンシューマは冪等に実装すること

### 外部 IF 仕様

- 外部 IF 仕様書: `docs/specs/if-spec/` 配下
- 外部 IF の変更が必要な場合は、**必ず人間に確認を求めること**（J-SIX エスカレーション条件）

---

## 認証・認可

- 認証方式: [TODO: API Key / OAuth2 Bearer Token / JWT 等]
- 認証ヘッダー: `Authorization: Bearer <token>`
- 認可モデル: [TODO: RBAC / スコープベース 等]
- 認可チェックの実装箇所: [TODO: ミドルウェア / デコレータ / ガード]

---

## ロギング・監視

### ログ

- ログライブラリ: [TODO: winston / pino / loguru 等]
- ログレベル: ERROR > WARN > INFO > DEBUG
- 本番環境: INFO 以上を出力
- 開発環境: DEBUG 以上を出力
- ログ形式: [TODO: 構造化JSON / テキスト]
- リクエストログ: 全リクエストの開始・終了をINFOレベルで記録
- 機密情報はログに出力しない（パスワード、トークン、個人情報）

### ヘルスチェック

- エンドポイント: `GET /health`
- レスポンス: DB 接続、外部サービス接続の状態を含む

### メトリクス

- [TODO: Prometheus / CloudWatch / Datadog 等]
- 収集するメトリクス: リクエスト数、レスポンスタイム、エラー率

---

## バッチ処理（該当する場合）

- スケジューラ: [TODO: cron / Cloud Scheduler / Step Functions 等]
- バッチ一覧: `docs/specs/design-spec.md#バッチ処理` を参照
- 冪等性: 全バッチは冪等に実装すること（再実行しても同じ結果）
- タイムアウト: [TODO: バッチごとの最大実行時間]
- 排他制御: [TODO: 同時実行の制御方法]
