# トレーサビリティマトリクス — 月次請求書発行

> J-SIX `j-six:traceability` Skill の出力に相当する、要件 ⇔ テスト ⇔ コードの対応表。
> 計測日: 2026-09-21（テスト 111件 + hold-out 23件 / カバレッジ 99.7% / mutation 91.49%）

## 業務ルール（REQ）⇔ テスト ⇔ 実装

| 要件 | 内容 | テスト | 実装 |
|---|---|---|---|
| REQ-001 | 締め日で請求対象期間が決まる | `TestClosingPeriod`, `TestYearBoundary` | `billing.closing_date_of`, `billing.period_of` |
| REQ-002 | 支払期日 = 締め日 + 支払サイト | `TestDueDate` | `billing.due_date_of` |
| REQ-003 | 取引先ごとに1請求へ集約 | `TestAggregation`, `TestInvoiceLines` | `BillingService.close_month`, `_build_invoice` |
| REQ-004 | 税率区分ごとに対価の額を区分 | `TestTaxSummary` | `billing.summarize_tax`, `models.TaxSummary` |
| REQ-005 | 端数処理は請求単位・税率ごとに1回 | `TestTaxCalculation`, `test_prop_002_*` | `billing.calc_tax` |
| REQ-006 | 適格請求書の記載事項を出力 | `TestReports`, `test_uc004_report_has_qualified_invoice_items` | `templates/report_invoice.html`, `reports.ISSUER_*` |
| REQ-007 | 確定済みの請求は変更不可 | `TestConfirmation`, `TestInvoiceNumbering`, `test_prop_006_*` | `BillingService.confirm`, `_ensure_not_confirmed` |
| REQ-008 | 対象売上が無ければ請求を作らない | `TestAggregation` | `BillingService._build_invoice` |
| REQ-009 | 会計連携は税率ごとの内訳行を持つ | `tests/test_accounting.py` | `accounting.build_accounting_csv` |
| REQ-010 | 締め処理を監査記録 | `TestAudit` | `BillingService._log`, `models.AuditEntry` |
| REQ-011 | 振込先口座は取引先ごとに登録する | `test_req011_*`, `test_uc004_report_shows_bank_account` | `BillingService.set_bank_account`, `models.BankAccount` |
| REQ-012 | 振込先は締め時点の内容を請求に保存する | `test_req012_*`, `test_prop_007_*`, `test_uc002_bank_account_is_snapshot_at_closing` | `BillingService._build_invoice`, `models.Invoice.bank_account` |
| REQ-013 | 振込先が未登録でも締めは止めない | `test_req013_*`, `test_prop_008_*`, `test_uc002_close_succeeds_when_bank_account_is_missing` | `BillingService.close_month`, `templates/report_invoice.html` |

## Property（PROP）⇔ テスト

要求 Spec 3.3 で定義した性質。`tests/test_properties.py` で Hypothesis により検証する。

| 性質 | 内容 | テスト |
|---|---|---|
| PROP-001 | 請求の税抜合計 = 明細の税抜金額の総和 | `test_prop_001_subtotal_equals_sum_of_lines` |
| PROP-002 | 端数処理は税率ごとに1回。明細ごとに丸めた合計とは一致しないことがある | `test_prop_002_tax_is_rounded_once_per_rate`, `test_prop_002_detects_per_line_rounding`, `test_prop_002_calc_tax_is_floor` |
| PROP-003 | 税率ごとの対価の額の総和 = 請求の税抜合計 | `test_prop_003_rate_subtotals_sum_to_invoice_subtotal` |
| PROP-004 | 支払期日 ≥ 締め日 / 対象期間は締め日で終わる | `test_prop_004_due_date_is_not_before_closing_date`, `test_prop_004_period_is_contiguous_and_ends_on_closing_date` |
| PROP-005 | 請求は取引先ごとに高々1件。再締めしても番号が変わらない | `test_prop_005_at_most_one_invoice_per_customer`, `test_prop_005_reclose_keeps_invoice_number` |
| PROP-006 | 確定済みの請求は金額が変化しない | `test_prop_006_confirmed_invoice_amount_never_changes` |
| PROP-007 | 保存された振込先は締め後のマスタ変更で変化しない | `test_prop_007_bank_account_is_frozen_at_closing` |
| PROP-008 | 振込先の登録有無は請求の件数と金額に影響しない | `test_prop_008_bank_account_does_not_change_invoice_amounts` |

## hold-out 受入テスト ⇔ ユースケース

実装を書く工程からは読めない受入テスト（`tests/acceptance/`）。

| ユースケース | テストファイル | 件数 |
|---|---|---|
| UC-001, UC-002 | `test_uc001_uc002_close.py` | 6 |
| UC-003 | `test_uc003_screens.py` | 4 |
| UC-004 | `test_uc004_report.py` | 4 |
| UC-005, UC-006 | `test_uc005_uc006_confirm_export.py` | 5 |
| UC-002, UC-004 | `test_uc002_uc004_bank_account.py`（振込先口座） | 4 |

## 工程成果物 ⇔ 実装

IPA「機能要件の合意形成ガイド」の工程成果物と、その逆生成元。

| 領域 | 工程成果物 | 逆生成元 |
|---|---|---|
| システム振舞い | システム化業務一覧 / 業務フロー / 業務説明 | Spec の UC 一覧、`tests/acceptance/` |
| 画面 | 画面一覧 / 遷移 / レイアウト / 入出力項目 / アクション明細 | `app/main.py` のルート、`app/templates/*.html` |
| データモデル | ER図 / エンティティ一覧 / 定義 / CRUD図 | `app/models.py` |
| 外部インタフェース | 関連図 / 一覧 / 項目説明 / 処理説明 | `app/importer.py`（EIF-002）、`app/accounting.py`（EIF-001） |
| バッチ | バッチ処理一覧 / フロー / 定義 | `app/batch.py` |
| 帳票 | 帳票一覧 / 概要 / レイアウト / 項目説明 / 編集定義 | `app/templates/report_invoice.html`、`app/reports.py` |

## 充足状況

**トレーサビリティ**: 全21件（REQ 13 + PROP 8）にテストが存在し、未トレースはゼロ。
`make gate` の G2 で機械的に検証している。
