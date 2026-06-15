# CLAUDE.md — 申請承認ワークフロー

> J-SIX テンプレート `templates/claude-md/base.md` + `api-service.md` を実プロジェクトで
> 埋めた**記入済み実例**。Claude Code はこのファイルを「プロジェクト憲法」として参照する。

## プロジェクト概要

- **システム名**: 申請承認ワークフロー（approval-workflow）
- **目的**: 備品・経費申請の承認を、承認順序と監査証跡を強制してシステム化する
- **主要ステークホルダー**: 申請者（一般社員）/ 承認者（上長）/ 内部監査
- **開発体制**: サンプル（1名）
- **J-SIX Stage**: Stage 3（J-SIX 全面適用）

## 技術スタック

- **言語**: Python 3.9+
- **フレームワーク**: FastAPI
- **バリデーション**: Pydantic v2
- **テスト**: pytest / pytest-cov
- **DB**: なし（インメモリ。Repository を切り出して差し替え可能）

## ビルド・テストコマンド

```bash
# 依存インストール
python -m venv .venv && .venv/bin/python -m pip install -r requirements.txt

# テスト（カバレッジ付き）
.venv/bin/python -m pytest -q --cov=app --cov-report=term-missing

# 開発サーバ起動
.venv/bin/python -m uvicorn app.main:app --reload
```

## 命名規則

- **ファイル名**: snake_case（`workflow.py`）
- **関数名 / 変数名**: snake_case
- **クラス名**: PascalCase（`WorkflowService`）
- **定数**: UPPER_SNAKE_CASE

## コーディング規約

- ビジネスルールは `app/workflow.py` に集約する。HTTP 層（`main.py`）にルールを書かない
- ドメインルール違反は `WorkflowError` を送出し、API 層で HTTP 409 に変換する
- 状態遷移メソッドは必ず監査ログ（`_log`）を残す（ADR-0002）
- 時刻取得は注入された `clock` を使い、`datetime.now()` を直接呼ばない（テスト容易性）
- インデント: スペース4

## J-SIX プロセス上の約束

- **テストファースト**: 新しい業務ルールは `tests/test_workflow.py` に REQ-NNN タグ付きで
  先に書いてから実装する（Phase 4 / TDD）
- **ADR**: ライブラリ選定・アーキテクチャ・統制に関わる判断は `docs/adr/` に記録する
- **トレーサビリティ**: 要件（REQ-NNN）⇔ テスト ⇔ コードの対応を `docs/traceability.md`
  に維持する
- **品質ゲート**: ドメインロジックのカバレッジ 95% 以上を維持する

## 禁止事項

- 申請者が自身の承認者になる経路を作らない（REQ-007）
- 終了状態（APPROVED/REJECTED/WITHDRAWN）への遷移を追加しない（REQ-009）
