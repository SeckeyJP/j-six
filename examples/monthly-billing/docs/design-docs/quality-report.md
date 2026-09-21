# 品質報告書 — 月次請求書発行

**納品物**: 品質報告書 ／ **対象**: 月次請求書発行（monthly-billing）
**版**: 1.0 ／ **作成日**: 2026-09-21 ／ **対象タスク**: TASK-MB-007
**由来**: 証跡パッケージからの変換（`doc-reverse-gen quality` 相当）

> **本書は Phase 4 の品質ゲートが出力した実行結果を整形したものである。**納品直前に人手で
> 書き起こしたものではないため、コードとの乖離が原理的に起こらない。
> 区分（**証跡** / **参考所見** / **承認**）を混ぜずに記載している。

## 1. 品質指標（証跡）

| 指標 | 実測値 | 閾値 | 判定 |
|---|---|---|---|
| テスト通過 | 111件／111件 | 全通過 | ✅ |
| hold-out 受入テスト | 23件／23件 | 全通過 | ✅ |
| ステートメントカバレッジ | 99.7% | 95.0% | ✅ |
| mutation score | 91.49% | 90.0% | ✅ |
| トレーサビリティ | 21/21 | 未トレース 0 | ✅ |
| 静的解析（SAST） | error 0 / warning 0 | error 以上なし | ✅ |

## 2. カバレッジ（証跡）

**判定**: ✅ 合格 — coverage: 99.7% ≥ 閾値 95.0%

| 項目 | 値 |
|---|---|
| ライン網羅率 | 99.72% |
| 閾値 | 95.0 |
| 形式 | cobertura |
| 対象ファイル数 | 8 |

### 網羅率の低いファイル

| ファイル | 網羅率 | 到達行 / 全行 | 未到達行 |
|---|---|---|---|
| `models.py` | 98.9% | 94 / 95 | 36 |
| `billing.py` | 100.0% | 125 / 125 | — |
| `main.py` | 100.0% | 61 / 61 | — |
| `importer.py` | 100.0% | 35 / 35 | — |
| `accounting.py` | 100.0% | 17 / 17 | — |

## 3. mutation score（証跡）

_カバレッジは「テストが実行した行」を測るが、mutation score は「テストが誤りを検出できるか」を測る。_

**判定**: ✅ 合格 — mutation: 全体 score 91.5% ≥ 閾値 90.0%

| 項目 | 値 |
|---|---|
| score | 91.49% |
| 閾値 | 90.0 |
| 殺したミュータント | 505 |
| 生存したミュータント | 47 |
| 判定対象外 | None |
| 対象範囲 | all |

### 生存したミュータント

_テストが通っているのに振る舞いが固定されていない箇所。探索的テストの出発点として質が高い。_

| ファイル | 行 | 変異 |
|---|---|---|
| — | — | app.accounting.x_build_accounting_csv__mutmut_19 |
| — | — | app.importer.x_import_sales__mutmut_9 |
| — | — | app.billing.xǁBillingServiceǁregister_customer__mutmut_2 |
| — | — | app.billing.xǁBillingServiceǁregister_customer__mutmut_5 |
| — | — | app.billing.xǁBillingServiceǁregister_customer__mutmut_7 |
| — | — | app.billing.xǁBillingServiceǁset_bank_account__mutmut_4 |
| — | — | app.billing.xǁBillingServiceǁadd_sale__mutmut_2 |
| — | — | app.billing.xǁBillingServiceǁadd_sale__mutmut_9 |
| — | — | app.billing.xǁBillingServiceǁclose_month__mutmut_16 |
| — | — | app.billing.xǁBillingServiceǁ_ensure_not_confirmed__mutmut_5 |
| — | — | app.billing.xǁBillingServiceǁ_build_invoice__mutmut_15 |
| — | — | app.billing.xǁBillingServiceǁconfirm__mutmut_4 |
| — | — | app.billing.xǁBillingServiceǁconfirm__mutmut_9 |
| — | — | app.billing.xǁBillingServiceǁconfirm__mutmut_10 |
| — | — | app.billing.xǁBillingServiceǁconfirm__mutmut_11 |
| — | — | app.billing.xǁBillingServiceǁconfirm__mutmut_16 |
| — | — | app.billing.xǁBillingServiceǁget_invoice__mutmut_2 |
| — | — | app.billing.xǁBillingServiceǁget_customer__mutmut_2 |
| — | — | app.batch.x_run_accounting_export__mutmut_2 |
| — | — | app.reports.x_invoice_view__mutmut_7 |

**生存ミュータントの扱い**: 生存47件は、エラーメッセージの文言・表示用ビューの変異が中心である。
これらは Design Spec が規定していない詳細であり、テストで固定すると文言の改善のたびにテストが
壊れる（脆いテスト）。**意図的に生かしている**。mutation score 100% は目的ではない。

本タスクでは、生存ミュータント `BankAccount(account_type=None)` が**本物のテストの穴**だった。
振込先の預金種別を検証するテストが無かったため、単体テストを1件追加して塞いだ。

## 4. スコープと整合性（証跡）

_変更ファイルがタスクの許可リストに収まっているか。許可リストはPhase 3 で人間が承認したもの。_

**判定**: ✅ 合格 — scope: 変更 23ファイルはすべて許可範囲内

| 項目 | 値 |
|---|---|
| 変更ファイル数 | 23 |
| 違反 | 0 |
| allow | `app/**`, `tests/**`, `docs/**`, `reports/**`, `coverage.xml`, `Makefile`, `requirements*.txt`, `.jsix-checks.json`, `README.md`, `CLAUDE.md`, `pyproject.toml`, `scripts/**` |
| deny | `tests/acceptance/**` |

_RED タグ以降にテストが弱められていないか。検出するのは差分そのものではなく弱体化（アサーション・テスト関数の減少、無効化マーカーの増加、hold-out 参照）。_

**判定**: ✅ 合格 — test_tamper: 基準点 jsix/red-TASK-MB-007 以降にテストの弱体化なし（1ファイルに差分あり。弱体化なし）

**基準点**: `jsix/red-TASK-MB-007`

| 指標 | 基準点 | 現在 | 増減 |
|---|---|---|---|
| アサーション数 | 230 | 235 | +5 |
| テスト関数数 | 133 | 134 | +1 |
| 無効化マーカー数 | 0 | 0 | +0 |

実装から hold-out への参照: 0 件
／ 差分のあったテストファイル: 1 件

### 差分のあったテストファイル（弱体化なし）

| ファイル | 基準点 (assert/test/skip) | 現在 | 内容変更 |
|---|---|---|---|
| `tests/test_billing.py` | 63/46/0 | 68/47/0 | あり |
---

## 検証条件（再現情報）

| 項目 | 値 |
|---|---|
| commit | `988c9713e12b` |
| 比較基準点 | `jsix/red-TASK-MB-007` |
| 実行日時 | 2026-09-21T01:25:03.114568+00:00 |
| 設定ファイル | `.jsix-checks.json`（sha256 `c58f8dd3f9273a92`） |
| 実行環境 | Python 3.9.6 ／ macOS-26.6.2-arm64-arm-64bit |
| ツール | Bandit 1.8.6 |

**出典**: 証跡パッケージ [`reports/evidence/TASK-MB-007/`](../../reports/evidence/TASK-MB-007/)。
本書の数値はすべて証跡からの引用であり、再計算していない。
