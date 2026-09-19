# ER図

**工程成果物**: データモデル ① ／ **由来**: **コードから逆生成**
**逆生成元**: `app/models.py`
**対象**: 月次請求書発行 ／ **版**: 1.0 ／ **日付**: 2026-09-18

```mermaid
erDiagram
    Customer ||--o{ SalesRecord : "売上が発生する"
    Customer ||--o{ Invoice : "請求する"
    Invoice  ||--|{ InvoiceLine : "明細を持つ"
    Invoice  ||--|{ TaxSummary : "税率別内訳を持つ"

    Customer {
        string customer_code PK "取引先コード"
        string name "取引先名"
        int closing_day "締め日（20 or 31=月末）"
        enum payment_terms "支払サイト"
    }
    SalesRecord {
        string record_id PK "販売管理システムの採番"
        string customer_code FK
        date sales_date "計上日"
        string item_name "品目"
        int quantity "数量"
        int unit_price "単価（円）"
        enum tax_rate "税率区分（8 or 10）"
    }
    Invoice {
        string invoice_no PK "INV-YYYYMM-nnnn"
        string customer_code FK
        string customer_name "締め時点の取引先名"
        string year_month "対象年月"
        date period_from "対象期間 開始"
        date period_to "対象期間 終了"
        date closing_date "締め日"
        date due_date "支払期日"
        enum status "DRAFT / CONFIRMED"
    }
    InvoiceLine {
        int line_no PK "請求内の連番"
        string item_name
        int quantity
        int unit_price
        int amount "税抜金額 = 数量 × 単価"
        enum tax_rate
    }
    TaxSummary {
        enum tax_rate PK "税率区分"
        int subtotal "税率ごとの対価の額"
        int tax_amount "消費税額（税率ごとに1回丸め）"
    }
```

## 構造上の重要点

### InvoiceLine が消費税額を持たない

端数処理は**請求単位・税率ごとに1回**である（ADR-0001 / REQ-005）。明細に税額を持たせると、
それを合計する実装を書きたくなる。制度上認められない計算方法を**構造として書けなくする**ため、
意図的に属性を置いていない。

### TaxSummary を独立させた理由

REQ-004 / REQ-006 が税率ごとの区分記載を求めており、端数処理の単位もこの粒度と一致する。
「端数処理が起きる場所」をエンティティとして明示している。

### Invoice が customer_name を持つ理由

締め時点の取引先名を保持する（スナップショット）。取引先名が変更されても、発行済みの
請求書の記載は変わらない。
