# 申請承認ワークフロー — J-SIX サンプルアプリ

J-SIX プロセスを小さな実題材で一周した**動くサンプル**です。1つの題材を3つの用途で共有します。

- **ケーススタディ（A1）**: J-SIX を一周した実測結果 → [`docs/case-study-01.md`](../../docs/case-study-01.md)
- **テンプレート実例（B）**: 記入済みの CLAUDE.md / Spec / ADR（本ディレクトリ）
- **Plugin デモ（C2）**: J-SIX Plugin の各 Skill をこのリポジトリに適用する手順（下記）

## 構成

```
approval-workflow/
├── CLAUDE.md                 # 記入済み CLAUDE.md 実例（base + api-service）
├── app/
│   ├── models.py             # ドメインモデル
│   ├── workflow.py           # ステートマシン（ビジネスルールの集約点）
│   └── main.py               # FastAPI 層
├── tests/
│   ├── test_workflow.py      # ドメイン単体テスト（REQ-NNN タグ付き）
│   └── test_api.py           # API 結線テスト
├── docs/
│   ├── requirement-spec.md   # 記入済み 要求 Spec 実例
│   ├── design-spec.md        # 記入済み Design Spec 実例
│   ├── traceability.md       # 要件⇔テスト⇔コード 対応表
│   └── adr/
│       ├── 0001-state-machine.md
│       └── 0002-audit-log.md
└── requirements.txt
```

## セットアップと実行

```bash
cd examples/approval-workflow
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

# テスト（カバレッジ付き）
.venv/bin/python -m pytest -q --cov=app --cov-report=term-missing

# API サーバ起動 → http://127.0.0.1:8000/docs で Swagger UI
.venv/bin/python -m uvicorn app.main:app --reload
```

## 計測結果（2026-06-14 時点）

| 指標 | 実測値 |
|---|---|
| アプリ実装 LOC | 354 行（app/） |
| テスト LOC | 290 行（tests/） |
| テスト件数 | 37 件 |
| ステートメントカバレッジ | 99% |
| 要件トレーサビリティ | 10/10 要件にテスト存在 |

## API クイック例

```bash
# 50,000円の申請を起票（1段承認）
curl -X POST localhost:8000/requests -H 'Content-Type: application/json' \
  -d '{"applicant":"alice","amount":50000,"title":"備品購入","approvers":["bob"]}'

# 提出 → 承認
curl -X POST localhost:8000/requests/REQ-0001/submit  -d '{"actor":"alice"}' -H 'Content-Type: application/json'
curl -X POST localhost:8000/requests/REQ-0001/approve -d '{"actor":"bob"}'   -H 'Content-Type: application/json'
```

## J-SIX Plugin デモ（C2）— 各 Skill の適用ポイント

このサンプルは J-SIX Plugin（`plugin/`）の各 Skill / Agent を実際に適用した成果物です。

| Phase | Plugin 機能 | このサンプルでの対応物 |
|---|---|---|
| P1-P2 | `j-six:spec-create` | `docs/requirement-spec.md`, `docs/design-spec.md` |
| P2 | `j-six:design-review` | ADR-0001/0002 と Spec の整合確認 |
| P4 | `j-six:tdd-cycle` / red・green・refactor-agent | `tests/` を先に書き `app/` を実装（REQ タグでトレース） |
| P5 | `j-six:quality-metrics` | カバレッジ 99% / 品質ゲート 95% を充足 |
| P6 | `j-six:doc-reverse-gen` / doc-generator | `app/` から IF 設計書（`/docs` Swagger）を生成可能 |
| P1-P6 | `j-six:traceability` | `docs/traceability.md` |
