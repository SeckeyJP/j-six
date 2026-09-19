# 画面アクション明細

**工程成果物**: 画面 ⑤ ／ **由来**: **コードから逆生成**
**逆生成元**: `app/main.py` のハンドラ、`app/templates/invoice_preview.html` のフォーム
**対象**: 月次請求書発行 ／ **版**: 1.1 ／ **日付**: 2026-09-19

> 画面遷移に伴って起動される処理の明細。

---

## ACT-001 請求一覧の表示

| 項目 | 内容 |
|---|---|
| 画面 | SCR-001 |
| 契機 | 画面表示 |
| 要求 | `GET /invoices?year_month=YYYY-MM` |
| 処理 | `service.list_invoices(year_month)` → 請求番号の昇順 |
| 結果 | 一覧を描画。0件なら「対象の請求がありません。」 |
| 状態変化 | なし |

---

## ACT-002 請求明細の表示

| 項目 | 内容 |
|---|---|
| 画面 | SCR-002 |
| 契機 | 請求番号リンクの押下 |
| 要求 | `GET /invoices/{invoice_no}` |
| 処理 | `service.get_invoice(invoice_no)` → `invoice_view()` |
| 結果 | 明細行・税率別内訳・合計を描画 |
| 異常 | 請求が存在しない → **HTTP 404** |
| 状態変化 | なし |

---

## ACT-003 請求書プレビューの表示

| 項目 | 内容 |
|---|---|
| 画面 | SCR-003 |
| 契機 | 「請求書プレビュー →」の押下 |
| 要求 | `GET /invoices/{invoice_no}/preview` |
| 処理 | 同上 |
| 結果 | 税率別内訳と請求金額を描画。DRAFT なら確定ボタンを表示 |
| 異常 | 請求が存在しない → **HTTP 404** |
| 状態変化 | なし |

---

## ACT-004 請求の確定

| 項目 | 内容 |
|---|---|
| 画面 | SCR-003 |
| 契機 | 「この請求を確定する」の押下 |
| 要求 | `POST /invoices/{invoice_no}/confirm` |
| 入力 | `actor`（操作者）。**form（x-www-form-urlencoded）/ JSON のどちらでも受け取る**。省略時は `keiri01`。multipart/form-data は受け付けない |
| 事前条件 | 請求が存在し、`status == DRAFT` であること |
| 処理 | `service.confirm(invoice_no, actor)` → status を CONFIRMED に更新し、監査ログに CONFIRM を記録 |
| 結果 | **HTTP 303** で SCR-002（請求明細）へリダイレクト |
| 異常 | 請求が存在しない → HTTP 404 ／ 既に確定済み → **HTTP 409** ／ multipart/form-data → **HTTP 415**（確定しない） |
| 状態変化 | DRAFT → CONFIRMED（**不可逆**。REQ-007） |

### 入力形式を両方受け取る理由

画面は form post、プログラムからの呼び出しは JSON を送る。片方だけを受け付けると、
もう片方は**黙って既定値になり**、監査ログ（REQ-010）に誤った操作者が記録される。

> この不具合は G3 の scope-judge が検出した。当初は `Form(...)` のみを受けており、
> hold-out が送っていた JSON の actor は無視されていた。hold-out が既定値と同じ
> 値を送っていたため偶然テストが通っていた。

### form を標準ライブラリで読む理由

form の解析に python-multipart を使っていたが、CI の依存脆弱性スキャン（G1 deps）が
HIGH 3件を検出した。修正版は Python 3.10 以上が必要で、本サンプルの前提（3.9+）と両立しない。
画面のフォームは x-www-form-urlencoded なので標準ライブラリ（`urllib.parse`）で読めるため、
依存ごと外した（ADR-0004）。受け付けない multipart は**既定値で黙って確定させず** 415 で拒否する。

### 303 リダイレクトにする理由

POST 後にブラウザをリロードしても二重送信にならないようにするため（PRG パターン）。
仮に二重送信されても HTTP 409 で拒否される（REQ-007）。

---

## ACT-005 帳票の出力

| 項目 | 内容 |
|---|---|
| 画面 | SCR-001（CSV）／ SCR-003（請求書） |
| 契機 | リンクの押下 |
| 要求 | `GET /invoices.csv?year_month=...` ／ `GET /invoices/{invoice_no}/report` |
| 結果 | RPT-002（`text/csv`）／ RPT-001（`text/html`） |
| 状態変化 | なし |

詳細は[帳票一覧](../report/01-report-list.md)を参照。
