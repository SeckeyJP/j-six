# CLAUDE.md — 月次請求書発行

> J-SIX テンプレート `templates/claude-md/base.md` + `api-service.md` を実プロジェクトで
> 埋めた**記入済み実例**。Claude Code はこのファイルを「プロジェクト憲法」として参照する。

## プロジェクト概要

- **システム名**: 月次請求書発行（monthly-billing）
- **目的**: 売上データから月次締め・請求書発行・会計連携を自動化し、消費税の端数処理を
  適格請求書等保存方式の要件どおりに機械的に保証する
- **主要ステークホルダー**: 経理担当者 / 取引先 / 会計部門 / 内部監査
- **開発体制**: サンプル（1名）
- **J-SIX Stage**: Stage 3（J-SIX 全面適用）
- **このサンプルの役割**: 画面・帳票・バッチを含む**設計書テンプレートの記入済み実例**を
  提供する（`templates/deliverables/`）。品質ゲートの実証は
  `examples/approval-workflow/` が担当する

## 技術スタック

- **言語**: Python 3.9+
- **フレームワーク**: FastAPI
- **画面**: Jinja2（サーバサイドレンダリング）
- **テスト**: pytest / pytest-cov / Hypothesis
- **DB**: なし（インメモリ。Repository を切り出して差し替え可能）

## ビルド・テストコマンド

```bash
make setup                    # venv 作成 + 依存インストール
make test                     # 単体・結合・性質テスト
make test-acceptance          # hold-out 受入テスト
make gate                     # 品質ゲート G1→G4
```

## 命名規則

- **ファイル名 / 関数名 / 変数名**: snake_case
- **クラス名**: PascalCase
- **定数**: UPPER_SNAKE_CASE
- **ID 体系**: 要件 `REQ-nnn` / 性質 `PROP-nnn` / ユースケース `UC-nnn` /
  画面 `SCR-nnn` / 帳票 `RPT-nnn` / バッチ `BATCH-nnn` / 外部IF `EIF-nnn`

## コーディング規約

- **業務ルールは `app/billing.py` に集約する**。画面・帳票・バッチ・会計連携はそれを呼ぶだけ
- **金額は `int`（円単位）で扱う**。`float` / `Decimal` を金額に使わない（ADR-0002）
- **消費税額を明細（InvoiceLine）に持たせない**。端数処理は請求単位・税率ごとに1回（ADR-0001）
- ドメインルール違反は `BillingError` を送出し、API 層で HTTP 409 に変換する
- 時刻取得は注入された `clock` を使い、`datetime.now()` を直接呼ばない
- インデント: スペース4

## J-SIX プロセス上の約束

- **テストファースト**: 新しい業務ルールは `tests/` に REQ-nnn / PROP-nnn タグ付きで
  先に書いてから実装する（Phase 4 / TDD）
- **hold-out**: `tests/acceptance/` は実装を書く工程からは読まない・触らない
- **ADR**: 税計算・帳票形式・外部連携に関わる判断は `docs/adr/` に記録する
- **トレーサビリティ**: REQ / PROP ⇔ テストの対応を `docs/traceability.md` に維持する
- **品質ゲート**: カバレッジ 95% 以上、mutation score 90% 以上

## 禁止事項

- 明細ごとに消費税を計算して端数処理し、合計すること（ADR-0001。制度上認められない）
- 金額計算に浮動小数点を使うこと
- 確定済み（CONFIRMED）の請求の金額を変更すること（REQ-007）
- 監査ログに明細の内容を出力すること（Design Spec 6.2）
