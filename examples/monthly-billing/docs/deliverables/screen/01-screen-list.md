# 画面一覧

**工程成果物**: 画面 ① ／ **由来**: **コードから逆生成**
**逆生成元**: `app/main.py` のルート定義、`app/templates/`
**対象**: 月次請求書発行 ／ **版**: 1.0 ／ **日付**: 2026-09-18

| SCR-ID | 画面名 | 分類 | パス | テンプレート | UC | 役割 |
|---|---|---|---|---|---|---|
| SCR-001 | 請求一覧 | 一覧 | `GET /invoices` | `invoice_list.html` | UC-003 | 対象年月の請求を一覧表示し、明細へ遷移する |
| SCR-002 | 請求明細 | 詳細 | `GET /invoices/{invoice_no}` | `invoice_detail.html` | UC-003 | 明細行と税率別内訳を表示する |
| SCR-003 | 請求書プレビュー | 確認 | `GET /invoices/{invoice_no}/preview` | `invoice_preview.html` | UC-003, UC-006 | 請求書の内容を確認し、確定操作を行う |

## 画面以外のエンドポイント

画面と混同しないよう、同じルータにある非画面のエンドポイントも記載する。

| パス | 種別 | 対応 |
|---|---|---|
| `GET /invoices/{invoice_no}/report` | 帳票 | RPT-001（[帳票一覧](../report/01-report-list.md)） |
| `GET /invoices.csv` | 帳票 | RPT-002 |
| `GET /invoices.json` | 画面のデータ源 | SCR-001 |
| `GET /invoices/{invoice_no}.json` | 画面のデータ源 | SCR-002 |
| `POST /invoices/{invoice_no}/confirm` | 操作 | UC-006（[画面アクション明細](05-screen-actions.md)） |

## 実装上の注意（ルート宣言順）

FastAPI のパスパラメータは `.` にも一致するため、`/invoices/{invoice_no}` を
`/invoices/{invoice_no}.json` より先に宣言すると、`.json` のリクエストが
HTML 側に吸われて 404 になる。**JSON のルートを先に宣言している。**

この不具合は hold-out 受入テストが実際に検出した。回帰テストとして
`test_json_routes_are_declared_before_html_detail` が順序を固定している。

## 画面を持たない機能

| 機能 | 理由 |
|---|---|
| 売上取込（UC-001） | バッチ（EIF-002）。画面を持たない |
| 月次締め（UC-002） | バッチ（BATCH-001）。画面を持たない |
| 会計連携（UC-005） | バッチ（BATCH-002）。画面を持たない |
