# エンティティ一覧

**工程成果物**: データモデル ② ／ **由来**: **コードから逆生成**
**逆生成元**: `app/models.py`
**対象**: 月次請求書発行 ／ **版**: 1.1 ／ **日付**: 2026-09-21

| # | エンティティ | 論理名 | 役割 | 主キー | 永続化 |
|---|---|---|---|---|---|
| 1 | `Customer` | 取引先 | 締め日と支払サイトを持つ | customer_code | インメモリ |
| 2 | `SalesRecord` | 売上 | 販売管理システムから取り込んだ売上明細 | record_id | インメモリ |
| 3 | `Invoice` | 請求 | 取引先 × 対象期間で1件 | invoice_no | インメモリ |
| 4 | `InvoiceLine` | 請求明細 | 請求に属する明細行 | invoice_no + line_no | Invoice に内包 |
| 5 | `TaxSummary` | 税率別内訳 | 税率区分ごとの対価の額と消費税額 | invoice_no + tax_rate | Invoice に内包 |
| 6 | `AuditEntry` | 監査記録 | 締め・確定の証跡 | （連番） | インメモリ |
| 7 | `BankAccount` | 振込先口座 | 取引先の振込先。請求には締め時点の内容を複製して持つ（REQ-012） | （なし。値オブジェクト） | Customer / Invoice に内包 |

## 区分（列挙型）

| # | 列挙型 | 論理名 | 値 |
|---|---|---|---|
| 1 | `TaxRate` | 税率区分 | `REDUCED`(8) 軽減税率 ／ `STANDARD`(10) 標準税率 |
| 2 | `InvoiceStatus` | 請求状態 | `DRAFT` 未確定 ／ `CONFIRMED` 確定済み |
| 3 | `PaymentTerms` | 支払サイト | `NEXT_MONTH_END` 翌月末 ／ `MONTH_AFTER_NEXT_END` 翌々月末 |

## 永続化について

本サンプルはインメモリ実装であり、DB テーブルは存在しない（Design Spec 1.3）。
`BillingService` が Repository の役割を兼ねており、永続化実装に差し替える場合は
この層を置き換える。エンティティの構造は変わらない。

**DDL を逆生成する場合**: `Customer` / `SalesRecord` / `Invoice` はテーブル、
`InvoiceLine` / `TaxSummary` は子テーブル（invoice_no を FK に持つ）になる。
