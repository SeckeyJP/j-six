# 品質報告書（品質メトリクス）— 申請承認ワークフロー

**対象タスク**: TASK-AW-002 ／ **生成日**: 2026-09-19
**生成元**: 証跡パッケージ `reports/evidence/TASK-AW-002/`（`03_coverage_mutation.md`, `05_scope_and_integrity.md`）＋ `quality-metrics` Skill の集計（`docs/quality-metrics-2026-09-19.md`）
**生成方法**: `doc-reverse-gen` Skill 種別 `quality`。数値は出典の値をそのまま引用し、再計算・推定をしていない

> 本書は証跡パッケージを整形したビューであり、直接編集しない。

---

## 1. 証跡（決定論的な検証結果）

### 1.1 カバレッジ

> 出典: `reports/evidence/TASK-AW-002/03_coverage_mutation.md`

| タスク | 判定 | ライン網羅率 | 閾値 | 形式 | 対象ファイル数 |
|---|---|---|---|---|---|
| TASK-AW-002 | ✅ 合格（coverage: 99.0% ≥ 閾値 95.0%） | 99.04% | 95.0 | cobertura | 4 |

| ファイル | 網羅率 | 到達行 / 全行 |
|---|---|---|
| `models.py` | 97.7% | 43 / 44 |
| `workflow.py` | 99.0% | 96 / 97 |
| `main.py` | 100.0% | 68 / 68 |

### 1.2 mutation score

> 出典: `reports/evidence/TASK-AW-002/03_coverage_mutation.md`

| タスク | 判定 | score | 閾値 | 殺したミュータント | 生存したミュータント | 判定対象外 | 対象範囲 |
|---|---|---|---|---|---|---|---|
| TASK-AW-002 | ✅ 合格（mutation: 全体 score 92.4% ≥ 閾値 90.0%） | 92.42% | 90.0 | 183 | 15 | None | all |

### 1.3 スコープ検査

> 出典: `reports/evidence/TASK-AW-002/05_scope_and_integrity.md`

| タスク | 判定 | 変更ファイル数 | 違反 |
|---|---|---|---|
| TASK-AW-002 | ✅ 合格（scope: 変更 27ファイルはすべて許可範囲内） | 27 | 0 |

- allow: `app/**`, `tests/**`, `docs/**`, `reports/**`, `coverage.xml`, `Makefile`, `requirements*.txt`, `.jsix-checks.json`, `README.md`, `CLAUDE.md`, `pyproject.toml`, `scripts/**`
- deny: `tests/acceptance/**`

### 1.4 テスト改変検出

> 出典: `reports/evidence/TASK-AW-002/05_scope_and_integrity.md`

**判定**: ✅ 合格 — test_tamper: 基準点 jsix/red-TASK-AW-002 以降にテストの弱体化なし（2ファイルに差分あり。弱体化なし）

| 指標 | 基準点 | 現在 | 増減 |
|---|---|---|---|
| アサーション数 | 191 | 191 | +0 |
| テスト関数数 | 96 | 96 | +0 |
| 無効化マーカー数 | 0 | 0 | +0 |

実装から hold-out への参照: 0 件

| ファイル | 基準点 (assert/test/skip) | 現在 | 内容変更 |
|---|---|---|---|
| `tests/test_properties.py` | 26/12/0 | 26/12/0 | あり |
| `tests/test_workflow.py` | 31/33/0 | 31/33/0 | あり |

### 1.5 プロセスの健全性（quality-metrics の集計）

> 出典: `docs/quality-metrics-2026-09-19.md`（`quality-metrics` Skill、集計日 2026-09-19）。同レポートは
> 証跡パッケージ・`reports/mutation.json`・`coverage.xml` などを読んで集計したもので、以下の値は同レポートからの引用

| メトリクス | 後（TASK-AW-002） | 前（`05fe639`） | 同レポートの出典 |
|---|---|---|---|
| mutation score（全体） | 92.42%（183 / 198） | 93.44%（171 / 183） | 証跡 `03`、`docs/case-study-02.md` |
| mutation score（`app/workflow.py`） | 148 / 160（92.5%） | 139 / 151（92.1%） | `reports/mutation.json`、`mutants/app/*.meta` |
| mutation score（`app/main.py`） | 35 / 38（92.1%） | 32 / 32（100%） | 同上 |
| G3 judge 却下率 | 0%（0 / 2） | — | `reports/evidence/judge.json` ほか |
| 人間レビュー指摘数 / PR | 未計測 | 未計測 | 両方の `07_approval.md` が未記入 |
| 分岐カバレッジ | 未計測 | — | `coverage.xml` の `branches-valid="0"` |

**生存ミュータント（`app/main.py` の3件）**（同レポート 3.2 の `mutmut show` の結果）

| ミュータント | 変異内容 |
|---|---|
| `app.main.x__guard__mutmut_2` | `detail=str(exc)` → `detail=None` |
| `app.main.x__guard__mutmut_4` | `detail=str(exc)` → 引数を削除 |
| `app.main.x__guard__mutmut_6` | `detail=str(exc)` → `detail=str(None)` |

**未到達行**（同レポート 3.1）: `models.py:72`（`next_approver` の範囲外ガード）、`workflow.py:133`
（`remand` を現在の承認者以外が呼んだときの送出。hold-out では検証されているが、hold-out はカバレッジの計測に入らない）。

### 1.6 実施されなかったチェック

> 出典: `reports/evidence/TASK-AW-002/00_summary.md` のゲート結果一覧

| ゲート | チェック | 判定 | 内容 |
|---|---|---|---|
| G1 | `build` / `lint` / `format` | ⏭ 未実施 | レポート駆動モードのため未実行（CI では --run-commands で実行） |
| G1 | `secrets` | ⏭ 未実施 | reports/secrets.sarif が無いためスキップ（optional 指定。CI で生成される想定） |
| G1 | `deps` | ⏭ 未実施 | reports/deps.sarif が無いためスキップ（optional 指定。CI で生成される想定） |

---

## 2. 参考所見（AI による所見）

> ⚠ **AI による参考所見。単独で品質判定の根拠にしない。** 決定論的な検証結果（証跡）ではない。
> 数値は必ず 1 章（証跡）を参照すること。

以下は `docs/quality-metrics-2026-09-19.md` の判断部分（ツールの出力ではなく、同レポートの判断と
明記されているもの）の要約である。

- 全体 score の低下（−1.02pt。同レポートの計算値）は、新しく生き残った `app/main.py` の3件だけが原因で、
  いずれも 404 の `detail` の文言の変異。404 の `detail` は Spec・ADR のどれにも定義されていないため、
  「エラーメッセージ文言」（等価に近い変異）と同じ種類と判断している（同レポート 3.2）
- 同レポートは次のアクションとして、ゲート失敗の履歴を残すこと、`07_approval.md` の記入、404 の `detail` を
  仕様にするかの決定、`remand` の非承認者経路を可視テストで押さえるかの決定、G1 build / lint / format を
  実行した状態での証跡作成などを挙げている（同レポート 6）

証跡パッケージの要約節（`00_summary.md`「変更概要・リスク箇所・計画からの逸脱」）は**未記入**であり、
本書には転記していない。

---

## 3. 承認

**未承認。** `07_approval.md` の確認項目・承認欄はすべて未記入である。詳細は[レビュー記録](review-record.md)を参照。

---

## 検証条件

> 出典: `reports/evidence/TASK-AW-002/env.json`

| 項目 | 値 |
|---|---|
| 対象 commit | `f3ccb671a321c6d96b446ff9d3679a35ae4a92d5` |
| 基準点（RED タグ） | `jsix/red-TASK-AW-002` |
| 証跡の生成日時 | 2026-09-19T05:03:09.803547+00:00 |
| ゲート設定 | `.jsix-checks.json`（SHA-256 `c58f8dd3f9273a9286f3af53256164470c1ce4e3951a8ac1ba03621e4240517d`） |
| 実行環境 | Python 3.9.6 / macOS-26.6.2-arm64-arm-64bit |
| ツール（`env.json` に記録されたもの） | Bandit 1.8.6 |
| ツール（`env.json` 以外） | mutmut 3.7.0（`docs/quality-metrics-2026-09-19.md` 3.2 の記載。`env.json` には記録されていない） |

**証跡生成後の変更**: なし。証跡は本書の生成時点の HEAD `f3ccb67` に対して生成された。本書を含む
`docs/deliverables/`・`docs/design-docs/` は未コミットの作業ツリーとして、スコープ検査（変更 27ファイル）の対象に含まれている。
