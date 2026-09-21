# バッチ処理フロー

**工程成果物**: バッチ ② ／ **由来**: **コードから逆生成**
**逆生成元**: `app/batch.py`, `app/billing.py`
**対象**: 月次請求書発行 ／ **版**: 1.1 ／ **日付**: 2026-09-21

## BATCH-001 月次請求データ作成

```mermaid
flowchart TD
    START([起動: year_month, actor]) --> J1
    J1["JOB1 確定チェック<br/>_ensure_not_confirmed"] --> J1D{確定済みあり?}
    J1D -->|あり| ERR["BillingError<br/>中止"]
    J1D -->|なし| J2["JOB2 取引先ループ<br/>取引先コードの昇順"]
    J2 --> J3["JOB3 対象期間の決定<br/>period_of(year_month, closing_day)"]
    J3 --> J4["JOB4 売上抽出<br/>period_from ≤ sales_date ≤ period_to"]
    J4 --> J4D{売上あり?}
    J4D -->|なし| SKIP["請求を作らない<br/>REQ-008"]
    J4D -->|あり| J5["JOB5 明細作成<br/>計上日・record_id 順に採番"]
    J5 --> J6["JOB6 税率別集計<br/>summarize_tax"]
    J6 --> J7["JOB7 請求番号の決定<br/>既存があれば再利用"]
    J7 --> J8["JOB8 請求の登録"]
    SKIP --> NEXT{次の取引先}
    J8 --> NEXT
    NEXT -->|あり| J2
    NEXT -->|なし| J9["JOB9 振込先未登録の警告記録<br/>未登録の請求ごとに1件"]
    J9 --> J10["JOB10 監査ログ記録<br/>CLOSE / 作成件数"]
    J10 --> END([作成された請求の一覧を返す])
```

### ジョブステップと件数の目安

| ジョブ | 処理内容 | 入力件数 | 出力件数 |
|---|---|---|---|
| JOB1 | 確定済みの有無を判定 | 対象年月の請求 | 0 or 中止 |
| JOB2-J8 | 取引先ごとの請求作成 | 取引先数 | 売上のある取引先数 |
| JOB6 | 税率別集計 | 明細数 | 税率区分数（最大2） |
| JOB9 | 振込先未登録の警告記録（REQ-013） | 作成した請求 | 振込先が未登録の請求の件数（0 以上） |
| JOB10 | 監査ログ記録（REQ-010） | — | 1（監査ログの末尾） |

## BATCH-002 会計連携ファイル出力

```mermaid
flowchart TD
    START([起動: year_month]) --> K1["JOB1 対象年月の請求を取得<br/>請求番号の昇順"]
    K1 --> K2["JOB2 ヘッダ行を出力"]
    K2 --> K3{請求ごとに走査}
    K3 --> K4{status == CONFIRMED?}
    K4 -->|DRAFT| K5["スキップ（continue）<br/>**打ち切らない**"]
    K4 -->|CONFIRMED| K6["H 行を出力"]
    K6 --> K7["税率区分ごとに D 行を出力<br/>税率の昇順"]
    K5 --> K8{次の請求}
    K7 --> K8
    K8 -->|あり| K3
    K8 -->|なし| END([CSV 文字列を返す])
```

### JOB2 の「打ち切らない」

未確定の請求に出会ったときに走査を打ち切ると、請求番号順で後ろにある確定済み請求が
丸ごと欠ける。mutation testing がこの経路の未検証を検出しており、回帰テストで固定している
（`test_req_009_draft_invoice_does_not_stop_later_confirmed_ones`）。
