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
├── Makefile                  # 品質ゲート用ターゲット（build/lint/format/sast/test/gate）
├── .jsix-checks.json         # 品質ゲートの宣言（コマンドと成果物のパス・閾値）
├── .github/workflows/
│   └── jsix-gate.yml         # 外側ループ（CI）の例
├── tests/
│   ├── test_workflow.py      # ドメイン単体テスト（REQ-NNN タグ付き）
│   ├── test_api.py           # API 結線テスト
│   └── acceptance/           # hold-out 受入テスト（GREEN 実装者は読めない）
│       ├── test_uc001_create.py
│       ├── test_uc002_uc003_approve.py
│       ├── test_uc004_uc005_reject_remand.py
│       └── test_uc006_withdraw.py
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
make setup                    # venv 作成 + 依存インストール（本体 + 開発用）

make test                     # 単体・結合テスト（JUnit XML + カバレッジを生成）
make test-acceptance          # hold-out 受入テスト
make gate                     # 品質ゲート G1→G4（既存の成果物を読んで判定）
make gate-ci                  # 品質ゲート（コマンドも実行してから判定）

# API サーバ起動 → http://127.0.0.1:8000/docs で Swagger UI
.venv/bin/python -m uvicorn app.main:app --reload
```

## 品質ゲート（v2.1）

`make gate` を実行すると、`.jsix-checks.json` に宣言したゲートが G1→G4 の順に走ります。

```
  ⏭ [G1] build / lint / format: レポート駆動モードのため未実行（CI では --run-commands）
  ✅ [G1] sast: error 以上の指摘なし（error 0 / warning 0 / note 0）
  ⏭ [G1] secrets / deps: SARIF が無いためスキップ（optional 指定。CI で生成される想定）
  ✅ [G1] scope: 変更ファイルはすべて許可範囲内
  ✅ [G2] tests: 全 37件 通過
  ✅ [G2] holdout: 全 10件 通過
  ✅ [G2] coverage: 99.0% ≥ 閾値 95.0%
  ⏭ [G2] test_tamper: 基準点（jsix/red-* タグ）が無いため差分検査をスキップ
  ✅ [G2] traceability: 全10件トレース済
  ✅ [G3] judge: PASS
  ✅ [G4] evidence: 証跡パッケージを生成しました → reports/evidence/<タスクID>/
```

**G3 は2段構成**です。command 型 Hook から LLM サブエージェントは呼べないため、
ランナーは「G3 未実施」で止まります。`scope-judge` を起動して判定を
`reports/evidence/judge.json` に書き出し、ゲートを再実行してください。

**内側ループと外側ループ**: `make gate` はローカルの内側ループ（成果物を読むだけ）、
`.github/workflows/jsix-gate.yml` が外側ループ（コマンドを実行してから判定）です。
両者は同じ判定スクリプトと同じ設定ファイルを使います。

### テストを弱める変更がブロックされることの確認

```bash
# assert を1つ削除する / @pytest.mark.skip を足す / app から tests/acceptance を参照する
make gate        # → exit 2 でブロックされる
git checkout tests/ app/
```

## 計測結果（2026-06-14 計測 / 2026-09-10 再計測）

| 指標 | 実測値 |
|---|---|
| アプリ実装 LOC | 368 行（app/） |
| テスト LOC | 299 行（tests/） |
| テスト件数 | 37 件 |
| ステートメントカバレッジ | 99% |
| 要件トレーサビリティ | 10/10 要件にテスト存在 |

> 行数は v2.1 の format ゲート導入に伴う整形で変化している（app 354→368 / tests 290→299）。
> テスト件数・カバレッジ・トレーサビリティは変化なし。

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
| P4 | `j-six:tdd-cycle` / holdout-test-writer・red・green・refactor-agent | `tests/acceptance/` に hold-out を書き、`tests/` を先に書いて `app/` を実装（REQ タグでトレース） |
| P4 | `scope-judge`（G3） | diff・タスク定義・Spec から意図とスコープを判定 → `reports/evidence/judge.json` |
| P4 | `j-six:evidence-pack`（G4） | `reports/evidence/<タスクID>/` に証跡パッケージを生成 |
| P5 | `j-six:quality-metrics` | カバレッジ 99% / 品質ゲート 95% を充足 |
| P6 | `j-six:doc-reverse-gen` / doc-generator | `app/` から IF 設計書（`/docs` Swagger）を生成可能 |
| P1-P6 | `j-six:traceability` | `docs/traceability.md` |
