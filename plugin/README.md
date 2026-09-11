# J-SIX Plugin for Claude Code

**J-SIX (Japanese SI Transformation)** の日本品質レイヤーを Claude Code Plugin として提供します。

## 概要

J-SIX プロセスの Phase 0-6 を Claude Code のネイティブ機能（Skills / Agents / Hooks）で実装した Plugin です。

v2.1 の中心は **レビュー前の4層品質ゲート**です。人間レビューに出す前に、性質の異なる
4つの監督面を**順に**通します。後段は前段を通過した場合のみ実行します。

| 層 | 名称 | 内容 | 判定主体 |
|---|---|---|---|
| **G1** | 決定論的検証 | build / 型 / lint・format / SAST / secret scan / 依存脆弱性 / スコープ検査 | script（終了コード） |
| **G2** | テスト品質検証 | 全テスト通過 / カバレッジ / mutation score / テスト改変検出 / hold-out 受入テスト / トレーサビリティ | script（終了コード） |
| **G3** | 意図・スコープ判定 | 正確性・要件未充足・スコープ逸脱**のみ**を fresh context の judge が報告 | LLM（scope-judge） |
| **G4** | 証跡パッケージ生成 | G1〜G3 の結果を人間レビュー用・顧客納品用に構造化 | script ＋ LLM（要約のみ） |

**なぜテスト通過だけでは足りないか**: 監督面がテストスイート単独だと、エージェントは
それを検証手段ではなく最適化対象として扱います（reward hacking）。詳細と出典は
[docs/J-SIX.md 第2章 2.3](../docs/J-SIX.md) を参照してください。

## 設計原則: ツールを呼ばず、契約を決める

**Plugin は言語別ツールを直接呼びません。** `.jsix-checks.json` が「コマンド」と
「成果物のパス・形式」を宣言し、Plugin は**標準フォーマットのパースと閾値判定のみ**を行います。

| チェック | 入力フォーマット（言語横断） | 生成ツールの例（利用者が選ぶ） |
|---|---|---|
| テスト結果 | JUnit XML | pytest / jest / gradle / go test（変換） |
| カバレッジ | Cobertura XML / LCOV | coverage.py / istanbul / jacoco |
| SAST・secret・依存脆弱性 | SARIF | semgrep / bandit / gitleaks / trivy / CodeQL |
| mutation | mutation-testing-elements JSON（Stryker 系 / PIT 系）。未対応ツールは `{"score": <number>}` の最小契約 | stryker / pitest / mutmut（アダプタ） |
| テスト改変・スコープ | git（言語非依存） | — |
| トレーサビリティ | 正規表現（REQ- / PROP- ID）＋ JUnit のテスト名 | — |

これにより、Plugin 側に特定言語のツール名やコマンドを持ち込まずに済みます。

## 構成

### Skills（7件）

| Skill | Phase | 概要 |
|---|---|---|
| `j-six:spec-create` | P1-P2 | 要求Spec / Design Spec の対話的策定 |
| `j-six:design-review` | P2 | 設計レビュー（Spec・ADR・コード整合性検証） |
| `j-six:tdd-cycle` | P4 | Hold-out → Red → Green → Refactor → G1〜G4 の管理 |
| `j-six:evidence-pack` | P4 | 証跡パッケージへの要約付加（**v2.1 で新規**） |
| `j-six:doc-reverse-gen` | P6 | 設計書逆生成（基本/詳細/IF/DB/品質） |
| `j-six:quality-metrics` | P5 | プロセス健全性の集計（mutation score / judge 却下率 等） |
| `j-six:traceability` | P1-P6 | 要件→テスト→コード→設計書の追跡マトリクス |

### Agents（7件）

| Agent | Phase | 概要 |
|---|---|---|
| `holdout-test-writer` | P4 | hold-out 受入テスト作成（**v2.1 で新規**。実装コードを読まない） |
| `red-agent` | P4 | TDD Red Phase（テスト作成 + PROP から PBT + RED タグ付与） |
| `green-agent` | P4 | TDD Green Phase（最小実装のみ。テストに触れない） |
| `refactor-agent` | P4 | TDD Refactor Phase（品質改善のみ） |
| `scope-judge` | P4 | G3 の判定（**v2.1 で新規**。3分類のみ、スタイル指摘は禁止） |
| `qa-reviewer` | P5 | 証跡パックの要約と探索的テスト観点の提示 |
| `doc-generator` | P6 | 設計書一式の自動生成 |

### Hooks

| イベント | 型 | 対象 | 内容 |
|---|---|---|---|
| PreToolUse | **command** | Edit/Write/MultiEdit | 決定論的な format / lint（v2.0 の prompt 型を置換） |
| PostToolUse | prompt | Bash | テスト実行結果の自動確認 |
| Stop | **command** | 全体 | 品質ゲート G1→G4（`.jsix-checks.json` 同梱時のみ動く） |
| Stop | prompt | 全体 | 「G3 未実施」を検出したら scope-judge を起動する |
| Stop | prompt | 全体 | ADR 記録すべき技術判断の検出 |
| StopFailure | prompt | 全体 | エラー終了時のリトライ/エスカレーション判断 |
| PermissionDenied | prompt | 全体 | 権限拒否時の代替アプローチ提案 |

**prompt 型を command 型に置き換えた理由**（PreToolUse）:
規約準拠は lint / format が決定論的に判定できます。LLM に判定させると同じコードで
結果がぶれ、編集のたびに LLM 呼び出しが発生します。prompt 型は**助言用途**
（ADR の提案など、判定基準が言語化しにくいもの）に限定しています。

`green-agent` には subagent スコープの Hook が付いており、`tests/` への書き込みと
`tests/acceptance/`（hold-out）の読み取りが機械的に拒否されます。

## 決定論的チェック（command 型 Hook / CI）

`plugin/scripts/` に LLM を介さないチェックスクリプトを同梱しています。

| スクリプト | ゲート | 役割 | 終了コード |
|---|---|---|---|
| `jsix_run_checks.py` | 全体 | gates を G1→G4 の順に実行する基盤。前段失敗で後段を打ち切る | 0=合格/未設定 / 2=未達 |
| `jsix_scope_check.py` | G1 | `git diff` の変更ファイルを allow/deny glob と照合 | 0/1 |
| `jsix_sarif_gate.py` | G1 | SARIF の severity 集計と閾値判定 | 0/1 |
| `jsix_junit_check.py` | G2 | JUnit XML の失敗・エラー・スキップ数の判定 | 0/1 |
| `jsix_coverage_gate.py` | G2 | Cobertura XML / LCOV のライン網羅率を閾値判定 | 0/1 |
| `jsix_mutation_gate.py` | G2 | mutation score の算出と閾値判定（`scope: changed` で変更範囲に限定） | 0/1 |
| `jsix_test_tamper_check.py` | G2 | RED タグ以降のテスト**弱体化**を検出 | 0/1 |
| `jsix_traceability_check.py` | G2 | REQ / PROP ⇔ テストの対応を検証 | 0/1 |
| `jsix_evidence_pack.py` | G4 | 証跡パッケージの生成 | 0 |
| `jsix_format_hook.py` | — | PreToolUse の決定論的 format / lint | 0 |
| `jsix_guard_tests.py` | — | green-agent の監督面保護（PreToolUse） | 0 |
| `jsix_config.py` / `jsix_result.py` / `jsix_gitutil.py` | — | 設定の正規化・共通インタフェース・git ヘルパ | — |

スクリプト自体の単体テストは `plugin/scripts/tests/` にあります。

```bash
python3 -m pytest plugin/scripts/tests -q
```

### オプトイン方式

Stop Hook（command）は、プロジェクト直下に `.jsix-checks.json` が存在する場合のみ
チェックを実行します。無いプロジェクトでは何もしません（安全な no-op）。

### レポート駆動（既定）

既定では、宣言された成果物（JUnit XML / カバレッジ / SARIF / mutation JSON）を
**読んで判定するだけ**で、`cmd` に書かれたコマンドは実行しません。

Stop hook が毎ターン build や test を走らせて数分待たされると、Hook 自体が無効化される
運用に傾くためです。CI では `--run-commands` を付けて実行します。

```bash
# 内側ループ（ローカル）: 既存の成果物を読んで判定する
python3 plugin/scripts/jsix_run_checks.py

# 外側ループ（CI）: コマンドを実行して成果物を作ってから判定する
python3 plugin/scripts/jsix_run_checks.py --run-commands --json reports/gate.json
```

### 内側ループと外側ループの二重化

| | 内側ループ（Hook） | 外側ループ（CI） |
|---|---|---|
| 目的 | 早く気づく | 確実に止める |
| 実行タイミング | ターン終了時 | PR / push |
| コマンド実行 | しない（成果物を読む） | する（`--run-commands`） |
| G3（LLM judge） | 実行する | 必須にしない |

**Hook は最終防衛線になりません。** Stop hook は8回連続ブロックすると Claude Code が
上書きしてターンを終了します。またローカル設定に依存し、オプトインです。したがって
「Hook が解除されても CI ゲートで止まる」構成を標準とします。両者は**同じ判定スクリプトと
同じ設定ファイル**を使います。

CI の例: [`.github/workflows/jsix-gate.yml`](../.github/workflows/jsix-gate.yml)
（対象は `examples/approval-workflow/` だが、GitHub Actions はサブディレクトリの
`.github/workflows/` を読まないため、ワークフロー自体はリポジトリ直下に置く）

## `.jsix-checks.json`

### v2.1 の形式

```json
{
  "gates": {
    "g1": {
      "build":  { "cmd": "make build" },
      "lint":   { "cmd": "make lint", "hook_cmd": ".venv/bin/python -m ruff check --fix {file}" },
      "format": { "cmd": "make format", "hook_cmd": ".venv/bin/python -m ruff format {file}" },
      "sast":   { "cmd": "make sast", "sarif": "reports/sast.sarif", "max_severity": "error" },
      "secrets":{ "sarif": "reports/secrets.sarif", "max_severity": "warning", "optional": true },
      "scope":  { "allow": ["src/approval/**", "tests/**"], "deny": ["tests/acceptance/**"] }
    },
    "g2": {
      "tests":        { "cmd": "make test", "junit": "reports/junit.xml", "max_skipped": 0 },
      "holdout":      { "cmd": "make test-acceptance", "junit": "reports/junit-acceptance.xml" },
      "coverage":     { "file": "reports/coverage.xml", "min": 90 },
      "mutation":     { "report": "reports/mutation.json", "min_score": 70, "scope": "changed" },
      "test_tamper":  { "baseline_ref": "jsix/red-TASK-001", "paths": ["tests/**"] },
      "traceability": { "requirements": "docs/requirement-spec.md", "tests": "tests",
                        "ids": ["REQ-\\d+", "PROP-\\d+"], "junit": "reports/junit.xml" }
    },
    "g3": { "agent": "scope-judge", "verdict": "reports/evidence/judge.json", "max_auto_fix": 1 },
    "g4": { "out": "reports/evidence/", "formats": ["md", "json"] }
  }
}
```

### 主なオプション

| キー | 意味 |
|---|---|
| `cmd` | `--run-commands` 指定時（CI）に実行するコマンド |
| `hook_cmd` | PreToolUse Hook で実行するコマンド。`{file}` が編集対象に置換される |
| `optional` | 成果物が無い場合にスキップする（CI でのみ生成する SARIF 等）。**既定は不合格** |
| `max_skipped` | 許容するテストのスキップ数。`0` にするとスキップ追加を検出できる |
| `min` / `min_score` / `max_severity` | 閾値。**未指定なら計測・集計のみ**（判定しない） |
| `scope: "changed"` | mutation を変更ファイルに限定して再計算する |
| `max_auto_fix` | G3 の却下を自動修正する回数。超えたら人間へエスカレーション（既定 1） |

**mutation score の閾値に既定値はありません。** 根拠のない数値を仕様に固定しないためです。
自プロジェクトで数タスク計測してから下限を決めてください。

### v2.0 の形式（後方互換）

v2.0 のフラット形式もそのまま動きます。G2 相当へマップされ、判定結果は v2.0 と同じです。

```json
{
  "traceability": { "requirements": "docs/requirement-spec.md", "tests": "tests" },
  "coverage": { "file": "coverage.xml", "min": 95 }
}
```

実行時に移行を促す案内が1行出ますが、**ブロックはしません**。

動作する実例は [`examples/approval-workflow/`](../examples/approval-workflow/)（`make gate` / `make gate-ci`）。

## 使い方

### インストール

```bash
claude plugin add ./plugin
```

### Skills の実行例

```bash
/j-six:spec-create          # Spec 策定
/j-six:tdd-cycle            # TDD サイクル + 品質ゲート
/j-six:evidence-pack        # 証跡パッケージに要約を付加
/j-six:doc-reverse-gen all  # 設計書逆生成（全種別）
/j-six:doc-reverse-gen quality  # 証跡から品質・テスト系の納品物を生成
/j-six:quality-metrics      # プロセス健全性の集計
/j-six:traceability         # トレーサビリティマトリクス生成
```

### 個別スクリプトの実行

```bash
python3 plugin/scripts/jsix_traceability_check.py --requirements <spec> --tests <dir>
python3 plugin/scripts/jsix_coverage_gate.py --file coverage.xml --min 95
python3 plugin/scripts/jsix_sarif_gate.py --file reports/sast.sarif --max-severity error
python3 plugin/scripts/jsix_mutation_gate.py --file reports/mutation.json
python3 plugin/scripts/jsix_test_tamper_check.py --baseline-ref jsix/red-TASK-001
```

## 前提条件

- Claude Code がインストールされていること
- プロジェクトに CLAUDE.md が設定されていること（テンプレート: `templates/claude-md/`）
- Python 3.9 以上（スクリプトの実行に使用。対象プロジェクトの言語とは無関係）
- J-SIX プロセスの Phase に沿って運用すること

## テンプレート

Plugin と併用するテンプレートはリポジトリルートの `templates/` を参照:
- `templates/claude-md/` — CLAUDE.md テンプレート
- `templates/spec/` — Spec テンプレート（受入条件・PROP・品質ゲート設定の欄を含む）
- `templates/adr/` — ADR テンプレート

## ライセンス

CC BY 4.0
