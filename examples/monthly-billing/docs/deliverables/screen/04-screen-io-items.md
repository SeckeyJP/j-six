# 画面入出力項目一覧

**工程成果物**: 画面 ④ ／ **由来**: **コードから逆生成**
**逆生成元**: `app/templates/*.html` の変数、`app/reports.py` の `invoice_view`
**対象**: 月次請求書発行 ／ **版**: 1.1 ／ **日付**: 2026-09-21

> IN=入力、OUT=出力。画面が描画するデータは `invoice_view()` が返す辞書に集約されており、
> **JSON エンドポイント（`/invoices.json`）と同一のデータ源**である（Design Spec 3.1）。

---

## SCR-001 請求一覧

| # | 項目名 | IN/OUT | 部品 | 型 | 書式 | データ源 |
|---|---|---|---|---|---|---|
| 1 | 対象年月 | IN | クエリパラメータ | 文字列 | `YYYY-MM` | `year_month` |
| 2 | 件数 | OUT | テキスト | 整数 | — | `invoices\|length` |
| 3 | 請求番号 | OUT | リンク | 文字列 | `INV-YYYYMM-nnnn` | `inv.invoice_no` |
| 4 | 取引先コード | OUT | テキスト | 文字列 | — | `inv.customer_code` |
| 5 | 取引先名 | OUT | テキスト | 文字列 | — | `inv.customer_name` |
| 6 | 締め日 | OUT | テキスト | 日付 | `YYYY-MM-DD` | `inv.closing_date` |
| 7 | 支払期日 | OUT | テキスト | 日付 | `YYYY-MM-DD` | `inv.due_date` |
| 8 | 税抜合計 | OUT | テキスト（右寄せ） | 整数 | 3桁区切り | `inv.subtotal` |
| 9 | 消費税 | OUT | テキスト（右寄せ） | 整数 | 3桁区切り | `inv.tax_total` |
| 10 | 請求金額 | OUT | テキスト（右寄せ） | 整数 | 3桁区切り | `inv.total` |
| 11 | 状態 | OUT | テキスト（色分け） | 列挙 | `DRAFT` / `CONFIRMED` | `inv.status` |
| 12 | CSV 出力 | IN | リンク | — | — | RPT-002 へ |

---

## SCR-002 請求明細

### ヘッダ部

| # | 項目名 | IN/OUT | 型 | 書式 | データ源 |
|---|---|---|---|---|---|
| 1 | 請求番号 | OUT | 文字列 | — | `inv.invoice_no` |
| 2 | 取引先 | OUT | 文字列 | `名称（コード）` | `inv.customer_name`, `inv.customer_code` |
| 3 | 対象期間 | OUT | 日付×2 | `YYYY-MM-DD 〜 YYYY-MM-DD` | `inv.period_from`, `inv.period_to` |
| 4 | 締め日 | OUT | 日付 | `YYYY-MM-DD` | `inv.closing_date` |
| 5 | 支払期日 | OUT | 日付 | `YYYY-MM-DD` | `inv.due_date` |
| 6 | 状態 | OUT | 列挙 | 色分け | `inv.status` |
| 7 | 振込先 | OUT | 文字列 | `{金融機関}　{支店}　{種別} {口座番号}`。未登録は「未登録（請求書には「振込先未登録」と印字されます）」 | `inv.bank_account` |

### 明細部（繰返し）

| # | 項目名 | IN/OUT | 型 | 書式 | データ源 |
|---|---|---|---|---|---|
| 7 | # | OUT | 整数 | 右寄せ | `line.line_no` |
| 8 | 品目 | OUT | 文字列 | — | `line.item_name` |
| 9 | 数量 | OUT | 整数 | 右寄せ | `line.quantity` |
| 10 | 単価 | OUT | 整数 | 3桁区切り・右寄せ | `line.unit_price` |
| 11 | 金額 | OUT | 整数 | 3桁区切り・右寄せ | `line.amount` |
| 12 | 税率 | OUT | 整数 | `n%`。軽減は色分け＋`※` | `line.tax_rate`, `line.is_reduced` |

### 税率別内訳部（繰返し）

| # | 項目名 | IN/OUT | 型 | 書式 | データ源 |
|---|---|---|---|---|---|
| 13 | 税率 | OUT | 整数 | `n%`。軽減は `（軽減）`付き | `s.tax_rate`, `s.is_reduced` |
| 14 | 対価の額（税抜） | OUT | 整数 | 3桁区切り・右寄せ | `s.subtotal` |
| 15 | 消費税額 | OUT | 整数 | 3桁区切り・右寄せ | `s.tax_amount` |

### 合計部

| # | 項目名 | IN/OUT | 型 | データ源 |
|---|---|---|---|---|
| 16 | 税抜合計 | OUT | 整数 | `inv.subtotal` |
| 17 | 消費税 | OUT | 整数 | `inv.tax_total` |
| 18 | 請求金額 | OUT | 整数（強調） | `inv.total` |

---

## SCR-003 請求書プレビュー

| # | 項目名 | IN/OUT | 型 | データ源 | 備考 |
|---|---|---|---|---|---|
| 1 | 取引先名 | OUT | 文字列 | `inv.customer_name` | 「御中」を付す |
| 2 | 請求番号 | OUT | 文字列 | `inv.invoice_no` | — |
| 3 | ご請求金額 | OUT | 整数（強調） | `inv.total` | 3桁区切り・「（税込）」を付す |
| 4 | 税率別内訳 | OUT | 繰返し | `inv.tax_summaries` | SCR-002 と同じ構造 |
| 5 | 操作者 | IN | hidden | `keiri01`（既定） | 確定時に監査ログへ（REQ-010） |
| 6 | 確定ボタン | IN | ボタン | — | `status == DRAFT` のときのみ表示 |

## 共通の書式ルール

| 項目種別 | 書式 | 実装 |
|---|---|---|
| 金額 | 3桁区切り・右寄せ | `{{ "{:,}".format(...) }}` ＋ `class="num"` |
| 日付 | `YYYY-MM-DD` | `invoice_view` が ISO 文字列に変換 |
| 軽減税率 | 色分け（`class="reduced"`）＋ `※` | `is_reduced` フラグ |
| 状態 | 色分け（`class="status-{{ status }}"`） | DRAFT=茶、CONFIRMED=緑・太字 |
