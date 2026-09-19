# 外部インタフェース項目説明

**工程成果物**: 外部インタフェース ③ ／ **由来**: **コードから逆生成**
**逆生成元**: `app/main.py`（`CreateRequestBody`, `ActorBody`, `RequestView`, `AuditEntryView`, `RequestView.of`）、`app/workflow.py`（`create_request` の検証とメッセージ）、`app/models.py`（`ApprovalRequest.next_approver`）、FastAPI が生成する OpenAPI（`app.openapi()`）
**対象**: 申請承認ワークフロー（approval-workflow） ／ **版**: 1.0 ／ **日付**: 2026-09-19

すべての IF で、リクエスト・レスポンスとも JSON（`application/json`、UTF-8）。

---

## `POST /requests` 起票の入力（受信）

**レイアウト**: JSON オブジェクト（`CreateRequestBody`）。**未定義の項目を含むと 422**（`extra="forbid"`。REQ-012）

| No | 項目名 | 型 | 必須 | 説明 | 検証 |
|---|---|---|---|---|---|
| 1 | `applicant` | string | ○ | 申請者ID | 欠落・型不一致は 422。承認者に含まれると 409「申請者は自身の承認者になれません」（REQ-007） |
| 2 | `amount` | integer | ○ | 申請金額（円） | 欠落・型不一致は 422。1未満は 409「金額は1以上で指定してください」 |
| 3 | `title` | string | ○ | 申請タイトル | 欠落・型不一致は 422。前後の空白を除いて空なら 409「タイトルは必須です」 |
| 4 | `approvers` | array of string | ○ | 承認者IDの順序付きリスト。先頭から順に承認する | 欠落・型不一致は 422。重複は 409「承認者が重複しています」。人数が金額から決まる段数と違えば 409「金額 {amount:,} 円には {needed} 名の承認者が必要です（指定: {n} 名）」（REQ-001） |

409 の検証は 金額 → タイトル → 自己承認 → 重複 → 人数 の順に行い、最初に違反したものを返す
（`WorkflowService.create_request`）。

**サンプル**（受入テスト `test_uc001_applicant_creates_draft_request` の入力）

```json
{"applicant": "alice", "amount": 50000, "title": "備品購入", "approvers": ["bob"]}
```

---

## 状態遷移 5本の入力（受信）

`POST /requests/{request_id}/submit` / `approve` / `reject` / `remand` / `withdraw` は同じ入力を取る。

**レイアウト**: パスパラメータ `request_id`（string）＋ JSON オブジェクト（`ActorBody`）。**未定義の項目を含むと 422**（`extra="forbid"`。REQ-012）

| No | 項目名 | 型 | 必須 | 説明 | 検証 |
|---|---|---|---|---|---|
| 1 | `request_id`（パス） | string | ○ | 対象の申請ID | 存在しなければ 404「申請が存在しません: {request_id}」（REQ-011） |
| 2 | `actor` | string | ○ | 操作者ID | 欠落・型不一致は 422。操作できる人でなければ 409（下表） |
| 3 | `note` | string | | コメント（既定値は空文字） | 型不一致は 422。内容の制約は無い。監査ログにそのまま記録する（REQ-010、PROP-007） |

**409 になる条件とメッセージ**（`app/workflow.py` から写した）

| IF | 条件 | `detail` |
|---|---|---|
| 5本共通 | 申請が終了状態（APPROVED / REJECTED / WITHDRAWN） | 「終了済みの申請は操作できません（状態: {status}）」（REQ-009） |
| `submit` | 状態が DRAFT でない | 「起票中の申請のみ提出できます」 |
| `submit` | `actor` が申請者でない | 「提出できるのは申請者のみです」（REQ-002） |
| `approve` / `reject` / `remand` | 状態が PENDING でない | 「承認待ちの申請のみ操作できます」 |
| `approve` | `actor` が現在の承認者でない | 「承認順序が不正です。現在の承認者は {next_approver} です」（REQ-008） |
| `reject` | `actor` が現在の承認者でない | 「却下できるのは現在の承認者 {next_approver} のみです」（REQ-008） |
| `remand` | `actor` が現在の承認者でない | 「差し戻しできるのは現在の承認者 {next_approver} のみです」（REQ-008） |
| `withdraw` | `actor` が申請者でない | 「取下げできるのは申請者のみです」（REQ-006） |

**サンプル**（受入テスト `test_uc002_uc003_notes_on_submit_and_approve_are_recorded` の入力）

```json
{"actor": "bob", "note": "内容確認済み"}
```

---

## 申請の出力（送信。全 IF の成功時）

起票・取得・状態遷移は申請1件を、一覧は申請の配列を返す。

**レイアウト**: JSON オブジェクト（`RequestView`）。監査ログは `AuditEntryView` の配列として内包する。

| No | 項目名 | 型 | null | 説明 |
|---|---|---|---|---|
| 1 | `id` | string | 不可 | 申請ID（`REQ-` ＋ 4桁の連番） |
| 2 | `applicant` | string | 不可 | 申請者ID |
| 3 | `amount` | integer | 不可 | 申請金額（円） |
| 4 | `title` | string | 不可 | 申請タイトル（入力のまま） |
| 5 | `approvers` | array of string | 不可 | 承認者IDの順序付きリスト |
| 6 | `status` | string | 不可 | `DRAFT` / `PENDING` / `APPROVED` / `REJECTED` / `WITHDRAWN` |
| 7 | `current_step` | integer | 不可 | 次に承認すべき `approvers` のインデックス（0始まり） |
| 8 | `next_approver` | string | **可** | 次の承認者。PENDING 以外では null |
| 9 | `audit_log` | array of object | 不可 | 監査ログ。古い順 |
| 9.1 | `audit_log[].action` | string | 不可 | `CREATE` / `SUBMIT` / `APPROVE` / `REJECT` / `REMAND` / `WITHDRAW` |
| 9.2 | `audit_log[].actor` | string | 不可 | 操作者ID |
| 9.3 | `audit_log[].at` | string | 不可 | 操作時刻。`datetime.isoformat()` の文字列（タイムゾーンのオフセット無し。[要確認]） |
| 9.4 | `audit_log[].note` | string | 不可 | コメント。省略時・起票時は空文字 |

**サンプル**（`alice` が起票し、コメント付きで提出した直後の応答。2026-09-19 に TestClient で実際に取得。`at` は取得時刻）

```json
{
  "id": "REQ-0001",
  "applicant": "alice",
  "amount": 50000,
  "title": "備品購入",
  "approvers": ["bob"],
  "status": "PENDING",
  "current_step": 0,
  "next_approver": "bob",
  "audit_log": [
    {"action": "CREATE", "actor": "alice", "at": "2026-09-19T13:47:55.447038", "note": ""},
    {"action": "SUBMIT", "actor": "alice", "at": "2026-09-19T13:47:55.448522", "note": "至急お願いします"}
  ]
}
```

---

## エラーの出力（送信）

| ステータス | 本文 | サンプル（2026-09-19 に TestClient で実際に取得） |
|---|---|---|
| 404 | `{"detail": <string>}` | `{"detail": "申請が存在しません: REQ-9999"}` |
| 409 | `{"detail": <string>}` | `{"detail": "承認順序が不正です。現在の承認者は bob です"}` |
| 422 | `{"detail": [<検証エラー>...]}`（FastAPI / Pydantic の既定形式） | `{"detail": [{"type": "extra_forbidden", "loc": ["body", "nte"], "msg": "Extra inputs are not permitted", "input": "x"}]}` |

404 / 409 の `detail` の文言は Spec・ADR・受入テストのいずれでも規定されていない
（`docs/quality-metrics-2026-09-19.md` 3.2: 404 の `detail` を変異させたミュータント3件が生存）。
クライアントは文言ではなくステータスで分岐すること。

## 項目間の整合

| 制約 | 内容 | 根拠 |
|---|---|---|
| 承認者の人数 | `len(approvers)` は `amount` から決まる段数（10万円未満 1 / 100万円未満 2 / それ以上 3）に等しい | REQ-001（起票時に検証。以後変わらない） |
| 申請者と承認者 | `applicant` は `approvers` に含まれない。`approvers` に重複は無い | REQ-007、PROP-003 |
| 次の承認者 | `status` が `PENDING` のとき `next_approver` = `approvers[current_step]`。それ以外は null | `ApprovalRequest.next_approver` |
| 承認完了 | `status` が `APPROVED` なら `current_step` = `len(approvers)` | `WorkflowService.approve` |
| 監査ログの先頭 | `audit_log[0]` は必ず (`CREATE`, `applicant`, `""`) | `WorkflowService.create_request` |
| 監査ログの件数 | `audit_log` の件数 = 1（起票）＋ 成功した状態遷移の回数 | PROP-004 |
| 並び順 | `audit_log` は操作の古い順。`GET /requests` の配列は起票の古い順（dict の挿入順） | `_log` の append、`list_all`（一覧の並び順は Spec で規定されていない） |

**読み違えやすい点**

- `current_step` は「承認済みの人数」とほぼ同じだが、**差し戻すと 0 に戻る**。差し戻し前に
  誰が承認していたかは `audit_log` にしか残らない
- DRAFT では `next_approver` が null になる。提出前の申請では、最初の承認者は `approvers[0]` で読む
- REJECTED では `current_step` は却下した承認者のインデックスのまま、WITHDRAWN では取下げ時点の値のまま残る
  （[エンティティ定義](../data/03-entity-definition.md) の「状態ごとの `current_step` の意味」）
