# 帳票項目説明

**工程成果物**: 帳票 ④ ／ **由来**: **コードから逆生成**
**逆生成元**: `app/templates/report_invoice.html`, `app/reports.py`
**対象**: 月次請求書発行 ／ **版**: 1.1 ／ **日付**: 2026-09-21

---

## RPT-001 請求書

### ヘッダ部

| # | 項目名 | 型 | 書式 | 配置 | 参照先 | 記載事項 |
|---|---|---|---|---|---|---|
| 1 | 表題 | 固定 | 「請求書」 | 中央 | — | — |
| 2 | 交付先名称 | 文字列 | `{名称}　御中`（18px 太字） | 左上 | `Invoice.customer_name` | **(5)** |
| 3 | ご請求金額 | 整数 | 3桁区切り ＋「円（税込）」（20px 太字） | 左上 | `Invoice.total` | — |
| 4 | お支払期日 | 日付 | `YYYY-MM-DD` | 左上 | `Invoice.due_date` | — |
| 5 | 発行者名称 | 固定 | 太字 | 右上 | `reports.ISSUER_NAME` | **(1)** |
| 6 | 登録番号 | 固定 | `登録番号：T#############` | 右上 | `reports.ISSUER_REGISTRATION_NO` | **(1)** |
| 7 | 請求番号 | 文字列 | `INV-YYYYMM-nnnn` | 右上 | `Invoice.invoice_no` | — |
| 8 | 取引年月日 | 日付 | `YYYY-MM-DD` | 右上 | `Invoice.closing_date` | **(2)** |
| 9 | 対象期間 | 日付×2 | `YYYY-MM-DD 〜 YYYY-MM-DD` | 右上 | `Invoice.period_from/period_to` | — |

### 明細部（繰返し：明細数ぶん）

| # | 項目名 | 型 | 書式 | 配置 | 参照先 | 記載事項 |
|---|---|---|---|---|---|---|
| 10 | 行番号 | 整数 | 右寄せ | — | `InvoiceLine.line_no` | — |
| 11 | 品目 | 文字列 | 軽減税率対象は末尾に `※` | 左 | `InvoiceLine.item_name` | **(3)** |
| 12 | 数量 | 整数 | 右寄せ | 右 | `InvoiceLine.quantity` | — |
| 13 | 単価 | 整数 | 3桁区切り・右寄せ | 右 | `InvoiceLine.unit_price` | — |
| 14 | 金額 | 整数 | 3桁区切り・右寄せ | 右 | `InvoiceLine.amount` | — |
| 15 | 税率 | 整数 | `n%` | 左 | `InvoiceLine.tax_rate` | **(3)** |

> **明細部に消費税額の列は無い。** 端数処理は請求単位・税率ごとに1回であり（ADR-0001）、
> 明細ごとの税額は保持していない。

### 注記

| # | 項目名 | 内容 | 条件 |
|---|---|---|---|
| 16 | 軽減税率の注記 | 「※ は軽減税率（8%）対象品目です。」（橙字） | 常時表示 |

### 内訳部（繰返し：税率区分数ぶん）

| # | 項目名 | 型 | 書式 | 参照先 | 記載事項 |
|---|---|---|---|---|---|
| 17 | 区分 | 文字列 | `n%（軽減）対象` / `n% 対象` | `TaxSummary.tax_rate` | **(4)** |
| 18 | 対価の額（税抜） | 整数 | 3桁区切り・右寄せ | `TaxSummary.subtotal` | **(4)** |
| 19 | 消費税額 | 整数 | 3桁区切り・右寄せ | `TaxSummary.tax_amount` | **(4)** |
| 20 | 税込金額 | 整数 | 3桁区切り・右寄せ（**算出**） | `subtotal + tax_amount` | — |

### 合計行

| # | 項目名 | 型 | 書式 | 参照先 |
|---|---|---|---|---|
| 21 | 税抜合計 | 整数 | 3桁区切り・右寄せ | `Invoice.subtotal` |
| 22 | 消費税合計 | 整数 | 3桁区切り・右寄せ | `Invoice.tax_total` |
| 23 | 請求金額 | 整数 | 3桁区切り・右寄せ・太字 | `Invoice.total` |

### 振込先部（REQ-011）

| # | 項目名 | 型 | 書式 | 参照先 |
|---|---|---|---|---|
| 24 | 見出し | 固定 | 「お振込先」 | — |
| 25 | 金融機関 | 文字列 | `{金融機関名}　{支店名}` | `Invoice.bank_account.bank_name` / `.branch_name` |
| 26 | 種別・口座番号 | 文字列 | `{預金種別}　{口座番号}` | `Invoice.bank_account.account_type` / `.account_number` |
| 27 | 口座名義 | 文字列 | そのまま | `Invoice.bank_account.account_holder` |
| 28 | 振込手数料の注記 | 固定 | 「振込手数料は貴社にてご負担をお願いいたします。」（12px 灰字） | — |

**未登録の場合（REQ-013）**: 25〜28 を出さず、「振込先未登録です。経理までお問い合わせください。」を
軽減税率の注記と同じ書式（朱色）で表示する。請求書自体は出力する。

### 脚注

| # | 項目名 | 内容 |
|---|---|---|
| 29 | 端数処理の説明 | 「消費税額は税率ごとの対価の額の合計に対して1回のみ端数処理（切捨て）しています。」（12px 灰字） |

---

## RPT-002 請求一覧表

| No | 列名 | 型 | 書式 | 参照先 |
|---|---|---|---|---|
| 1 | invoice_no | 文字列 | `INV-YYYYMM-nnnn` | `Invoice.invoice_no` |
| 2 | customer_code | 文字列 | — | `Invoice.customer_code` |
| 3 | customer_name | 文字列 | — | `Invoice.customer_name` |
| 4 | closing_date | 文字列 | `YYYY-MM-DD` | `Invoice.closing_date` |
| 5 | due_date | 文字列 | `YYYY-MM-DD` | `Invoice.due_date` |
| 6 | subtotal | 整数 | 区切りなし | `Invoice.subtotal` |
| 7 | tax_total | 整数 | 区切りなし | `Invoice.tax_total` |
| 8 | total | 整数 | 区切りなし | `Invoice.total` |
| 9 | status | 文字列 | `DRAFT` / `CONFIRMED` | `Invoice.status` |

CSV は表計算ソフトでの検算に使うため、金額に3桁区切りを入れない（数値として扱えるように）。
