# エンティティ定義

**工程成果物**: データモデル ③ ／ **由来**: **コードから逆生成**
**逆生成元**: `app/models.py` の型注釈
**対象**: 月次請求書発行 ／ **版**: 1.1 ／ **日付**: 2026-09-21

## Customer（取引先）

| # | 属性 | 型 | PK | 必須 | 説明 | 制約 |
|---|---|---|---|---|---|---|
| 1 | customer_code | str | ○ | ○ | 取引先コード | — |
| 2 | name | str | | ○ | 取引先名 | 請求書の交付先名称に使う（REQ-006） |
| 3 | closing_day | int | | ○ | 締め日 | **20 または 31（月末）のみ**。他は `BillingError`（REQ-001） |
| 4 | payment_terms | PaymentTerms | | ○ | 支払サイト | 列挙型以外は `BillingError`（REQ-002） |
| 5 | bank_account | BankAccount / None | | | 振込先口座 | **任意**。未登録でも締めは止めない（REQ-013） |

## BankAccount（振込先口座）

**不変オブジェクト**（`frozen=True`）。請求は締め時点の口座を保存するため（REQ-012）、
可変にすると同じインスタンスを共有した時点でスナップショットが崩れる。

| # | 属性 | 型 | PK | 必須 | 説明 | 制約 |
|---|---|---|---|---|---|---|
| 1 | bank_name | str | | ○ | 金融機関名 | — |
| 2 | branch_name | str | | ○ | 支店名 | — |
| 3 | account_type | str | | ○ | 預金種別 | **普通 または 当座のみ**。他は `BillingError`（REQ-011） |
| 4 | account_number | str | | ○ | 口座番号 | 文字列。先頭の 0 を保つため整数にしない |
| 5 | account_holder | str | | ○ | 口座名義 | — |

## SalesRecord（売上）

| # | 属性 | 型 | PK | 必須 | 説明 | 制約 |
|---|---|---|---|---|---|---|
| 1 | record_id | str | ○ | ○ | 販売管理システムの採番 | 重複は取込時に無視（冪等） |
| 2 | customer_code | str | | ○ | 取引先コード（FK） | 未登録は `BillingError` |
| 3 | sales_date | date | | ○ | 計上日 | 請求対象期間の判定に使う |
| 4 | item_name | str | | ○ | 品目 | 請求書の取引内容に使う |
| 5 | quantity | int | | ○ | 数量 | — |
| 6 | unit_price | int | | ○ | 単価（円） | 整数。小数は扱わない |
| 7 | tax_rate | TaxRate | | ○ | 税率区分 | 8 / 10 以外は `BillingError`（REQ-004） |

**導出属性**: `amount` = `quantity` × `unit_price`（税抜金額）

## Invoice（請求）

| # | 属性 | 型 | PK | 必須 | 説明 | 制約 |
|---|---|---|---|---|---|---|
| 1 | invoice_no | str | ○ | ○ | 請求番号 | `INV-YYYYMM-nnnn`。**再締めでも変わらない** |
| 2 | customer_code | str | | ○ | 取引先コード（FK） | — |
| 3 | customer_name | str | | ○ | 取引先名 | 締め時点のスナップショット |
| 4 | year_month | str | | ○ | 対象年月 | `YYYY-MM` |
| 5 | period_from | date | | ○ | 対象期間 開始 | 前回締め日の翌日（REQ-001） |
| 6 | period_to | date | | ○ | 対象期間 終了 | 締め日と一致 |
| 7 | closing_date | date | | ○ | 締め日 | REQ-001 |
| 8 | due_date | date | | ○ | 支払期日 | **常に closing_date 以降**（PROP-004） |
| 9 | status | InvoiceStatus | | ○ | 状態 | 既定 DRAFT |
| 10 | lines | InvoiceLine[] | | ○ | 明細 | 1件以上（REQ-008） |
| 11 | tax_summaries | TaxSummary[] | | ○ | 税率別内訳 | 税率の昇順 |
| 12 | bank_account | BankAccount / None | | | 締め時点の振込先 | **締め後にマスタを変更しても変わらない**（REQ-012 / PROP-007）。未登録は None（REQ-013） |

**導出属性**

| 属性 | 算出式 | 根拠 |
|---|---|---|
| subtotal | Σ lines[].amount | PROP-001 |
| tax_total | Σ tax_summaries[].tax_amount | PROP-003 |
| total | subtotal + tax_total | PROP-003 |

## InvoiceLine（請求明細）

| # | 属性 | 型 | PK | 必須 | 説明 |
|---|---|---|---|---|---|
| 1 | line_no | int | ○ | ○ | 請求内の連番（1 始まり） |
| 2 | item_name | str | | ○ | 品目 |
| 3 | quantity | int | | ○ | 数量 |
| 4 | unit_price | int | | ○ | 単価（円） |
| 5 | amount | int | | ○ | 税抜金額 |
| 6 | tax_rate | TaxRate | | ○ | 税率区分 |

> **消費税額の属性は存在しない。** 端数処理は請求単位・税率ごとに1回であり（ADR-0001）、
> 明細ごとの税額を保持すると合計したくなる。構造として書けなくしている。

## TaxSummary（税率別内訳）

| # | 属性 | 型 | PK | 必須 | 説明 | 算出式 |
|---|---|---|---|---|---|---|
| 1 | tax_rate | TaxRate | ○ | ○ | 税率区分 | — |
| 2 | subtotal | int | | ○ | 税率ごとの対価の額 | Σ（同一税率の明細の amount） |
| 3 | tax_amount | int | | ○ | 消費税額 | `floor(subtotal × 税率 / 100)` |

## AuditEntry（監査記録）

| # | 属性 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| 1 | action | str | ○ | `CLOSE` / `CONFIRM` |
| 2 | actor | str | ○ | 操作者 ID |
| 3 | at | datetime | ○ | 実行日時（注入された clock から取得） |
| 4 | year_month | str | ○ | 対象年月 |
| 5 | created_count | int | | 作成件数（CLOSE のみ） |
| 6 | invoice_no | str | | 請求番号（CONFIRM のみ） |

> 明細の内容を保持する属性は持たない（Design Spec 6.2）。
