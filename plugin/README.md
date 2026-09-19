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
| `j-six:doc-reverse-gen` | P6 | 工程成果物（IPA 27点）の逆生成 → 組立定義による設計書の組立、品質系納品物 |
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
| PostToolUse | **command** | Edit/Write/MultiEdit | 編集したファイルに決定論的な format / lint（v2.0 の prompt 型を置換）。対象は `hook_files` で宣言したファイルのみ |
| Stop | **command** | 全体 | 品質ゲート G1→G4（`.jsix-checks.json` 同梱時のみ動く）。G1/G2 通過後に判定ファイルが無ければ「G3 未実施」で止め、scope-judge の起動を案内する。変更ファイルが無いセッションでは G3 を求めない。同じ失敗でのブロックが3回続いたら停止を許可する（判定は未達のまま。CI で止まる。`stop_hook.max_identical_blocks` で変更可） |
| Stop | prompt | 全体 | ADR を記録すべき技術判断をしたのに ADR を作成・提案していない場合だけ停止を止める |

**prompt 型を command 型に置き換えた理由**（format / lint Hook）:
規約準拠は lint / format が決定論的に判定できます。LLM に判定させると同じコードで
結果がぶれ、編集のたびに LLM 呼び出しが発生します。prompt 型は**助言用途**
（ADR の提案など、判定基準が言語化しにくいもの）に限定しています。

**prompt 型 Hook は「停止してよいか」を判定する評価器として書く**:
prompt 型 Hook は、判定役のモデルが `{"ok": true|false, "reason": ...}` を返す仕組みです。
`ok: false` なら reason が Claude に返されて作業が続きます。「〜の場合は…してください。
該当しなければ何も出力しない」という**指示文の形で書くと、「何も出力しない」という選択肢が
無いため毎回ブロックされ、セッションが止まらなくなります**。J-SIX v2.1 までの Hook は
この形で書かれており、Skill をヘッドレスで実行した際に発覚しました。現在の Hook は
「`ok: false` にする条件」を明示し、それ以外（迷う場合と `stop_hook_active` が true の場合を
含む）は `ok: true` とする形に揃えています。同じ理由で、判定すべき条件の無い prompt 型
Hook（PostToolUse のテスト結果確認、StopFailure、PermissionDenied）は削除しました。

`green-agent` には subagent スコープの Hook が付いており、`tests/` への書き込みと
`tests/acceptance/`（hold-out）の読み取りが機械的に拒否されます。

## 評価ケース

`plugin/evals/` に `claude plugin eval` の評価ケースを置いている。Plugin を実際に読み込ませて
Skill を動かし、結果を採点する（Plugin を変更したときの受入試験。CI では実行しない）。
実行方法と費用は [`evals/README.md`](evals/README.md) を参照。

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
| `jsix_format_hook.py` | — | PostToolUse の決定論的 format / lint（`hook_files` に一致するファイルのみ） | 0 |
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
# --gates で G3（LLM judge）を外す（CI で LLM の API キーを扱わずに済ませる）
python3 plugin/scripts/jsix_run_checks.py --run-commands --gates g1,g2,g4 --json reports/gate.json
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
      "lint":   { "cmd": "make lint", "hook_cmd": ".venv/bin/python -m ruff check --fix {file}", "hook_files": ["*.py"] },
      "format": { "cmd": "make format", "hook_cmd": ".venv/bin/python -m ruff format {file}", "hook_files": ["*.py"] },
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
| `hook_cmd` | 編集後（PostToolUse）に実行するコマンド。`{file}` が編集対象に置換される |
| `hook_files` | `hook_cmd` をかけるファイルの glob（例 `["*.py"]`）。**無ければ実行しない**。ファイル名、`/` を含む場合は設定ファイルからの相対パスと照合する。拡張子を見ずに実行すると `.json` などを壊す |
| `optional` | 成果物が無い場合にスキップする（CI でのみ生成する SARIF 等）。**既定は不合格** |
| `max_skipped` | 許容するテストのスキップ数。`0` にするとスキップ追加を検出できる |
| `min` / `min_score` / `max_severity` | 閾値。**未指定なら計測・集計のみ**（判定しない） |
| `scope: "changed"` | mutation を変更ファイルに限定して再計算する |
| `max_auto_fix` | G3 の却下を自動修正する回数。超えたら人間へエスカレーション（既定 1） |
| `fingerprint_paths`（g3） | G3 の判定を紐づける差分の対象パス（例 `["app", "tests"]`）。指定するとそれ以外（ドキュメント等）の変更では判定が古くならない。**既定はプロジェクト全体**（安全側。ドキュメントの変更も判定対象になる） |
| `base`（g1.scope） | スコープ検査の比較元。既定は RED タグ（`$JSIX_TASK_ID` → 自プロジェクトの最新の `jsix/red-*`）、無ければ未コミットの変更のみ |
| `history`（トップレベル） | ゲート失敗の履歴の出力先（既定 `reports/gate-history.jsonl`）。失敗はすべて、成功は回復時だけ記録。quality-metrics が読む |
| `stop_hook.max_identical_blocks`（トップレベル） | Stop hook で同じ失敗によるブロックを何回まで続けるか（既定 3）。超えたら停止を許可する。判定は未達のまま残り、CI では止まる |

### CLI オプション

| オプション | 用途 |
|---|---|
| `--run-commands` | 設定の `cmd` を実際に実行する（CI 用。既定はレポート駆動） |
| `--gates g1,g2,g4` | 実行するゲートを絞る。**CI で G3 を外す**のに使う。除外したゲートは「未実行」として結果に残り、黙って消えない |
| `--json <path>` | 結果を JSON で書き出す（証跡パッケージ生成の入力になる） |
| `--dir <path>` | 対象ディレクトリ（既定: カレント） |

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
/j-six:doc-reverse-gen all  # 工程成果物の逆生成 → 設計書の組立 → 品質系納品物
/j-six:doc-reverse-gen screen  # 画面の工程成果物（6点）だけを逆生成
/j-six:doc-reverse-gen assemble kihon-sekkei  # 基本設計書に組み立てる
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
