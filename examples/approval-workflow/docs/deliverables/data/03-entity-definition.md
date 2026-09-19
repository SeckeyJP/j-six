# エンティティ定義

**工程成果物**: データモデル ③ ／ **由来**: **コードから逆生成**
**逆生成元**: `app/models.py` の型注釈（`ApprovalRequest`, `AuditEntry`）、`app/workflow.py`（`WorkflowService.create_request` の検証、各状態遷移メソッド、`_log`）、`app/main.py`（`CreateRequestBody`, `ActorBody`）
**対象**: 申請承認ワークフロー（approval-workflow） ／ **版**: 1.0 ／ **日付**: 2026-09-19

制約違反はすべて起票（`create_request`）の時点で検出し、`WorkflowError`（API では 409）として
起票全体を拒否する。検証の順序はコードの順（下表の「検証順」）で、最初に違反したものの
メッセージが返る。型の不一致・必須項目の欠落は、ドメイン層に届く前に API 層で 422 になる。

## ApprovalRequest（申請）

| # | 属性 | 型 | PK | 必須 | 説明 | 制約 |
|---|---|---|---|---|---|---|
| 1 | `id` | `str` | ○ | ○ | 申請ID | システムが採番する（`REQ-` ＋ `_seq` の4桁ゼロ埋め）。`_seq` は起票が成功したときだけ1増える。削除が無いため再利用されない |
| 2 | `applicant` | `str` | | ○ | 申請者ID | 承認者に含めてはならない（検証順 3。違反時「申請者は自身の承認者になれません」。REQ-007） |
| 3 | `amount` | `int` | | ○ | 申請金額（円） | 1以上（検証順 1。違反時「金額は1以上で指定してください」） |
| 4 | `title` | `str` | | ○ | 申請タイトル | 前後の空白を除いて空でないこと（検証順 2。違反時「タイトルは必須です」）。値は空白を除かずにそのまま保持する |
| 5 | `approvers` | `list[str]` | | ○ | 承認者IDの順序付きリスト | 重複不可（検証順 4。違反時「承認者が重複しています」）。人数が必要承認段数と一致すること（検証順 5。違反時「金額 {amount:,} 円には {needed} 名の承認者が必要です（指定: {n} 名）」。REQ-001）。入力のリストの複製を保持する |
| 6 | `status` | `Status` | | ○ | 状態 | 初期値 `DRAFT`。変更は状態遷移メソッドだけ（[CRUD図](04-crud-matrix.md)） |
| 7 | `current_step` | `int` | | ○ | 次に承認すべき approvers のインデックス | 初期値 0。提出・差し戻しで 0、承認で +1。範囲は 0〜`len(approvers)` |
| 8 | `audit_log` | `list[AuditEntry]` | | ○ | 監査ログ | 初期値は空リストだが、起票時に `CREATE` を1件追記してから登録するため、登録済みの申請では常に1件以上。追記のみ |

**導出属性**

| 属性 | 算出式 | 根拠 |
|---|---|---|
| `next_approver`（次の承認者） | `status` が PENDING かつ `current_step < len(approvers)` のとき `approvers[current_step]`、それ以外は `None` | `ApprovalRequest.next_approver`。承認・却下・差し戻しを行えるのはこの人だけ（REQ-008） |
| 必要承認段数 | `required_approval_levels(amount)`: 100,000 未満 → 1、1,000,000 未満 → 2、それ以上 → 3 | REQ-001、PROP-001（金額に対して単調非減少） |
| 終了状態か | `status.is_terminal`: APPROVED / REJECTED / WITHDRAWN のとき真 | REQ-009、ADR-0001 |

**状態ごとの `current_step` の意味**

| 状態 | `current_step` | 備考 |
|---|---|---|
| DRAFT | 0 | 起票直後・差し戻し後とも 0 |
| PENDING | 承認済みの段数（0〜`len(approvers)-1`） | |
| APPROVED | `len(approvers)` | 最終段の承認で `current_step` が人数に達したとき APPROVED にする |
| REJECTED | 却下した承認者のインデックス（＝それまでの承認済み段数） | 却下では変えない |
| WITHDRAWN | 取下げ時点の値のまま | DRAFT からなら 0、PENDING からならそれまでの承認済み段数 |

> **申請には「必要承認段数」の属性が存在しない。** 段数は金額から毎回導出でき、起票時に承認者の
> 人数と一致させているため、別に持つと金額・承認者との食い違いが起こりうる（[ER図](01-er-diagram.md)）。

---

## AuditEntry（監査ログのエントリ）

`@dataclass(frozen=True)`。生成後は属性を書き換えられない（ADR-0002）。

| # | 属性 | 型 | PK | 必須 | 説明 | 制約 |
|---|---|---|---|---|---|---|
| 1 | `action` | `Action` | | ○ | 操作種別 | `Action` の6値のいずれか |
| 2 | `actor` | `str` | | ○ | 操作者ID | 起票では申請者、状態遷移では API で受けた `actor`（PROP-005） |
| 3 | `at` | `datetime` | | ○ | 操作時刻 | `WorkflowService` に注入された `clock` の戻り値。既定は `datetime.now`（タイムゾーン情報なし。[要確認]） |
| 4 | `note` | `str` | | | コメント | 既定値は空文字。起票（`CREATE`）では常に空文字。状態遷移では API で受けた `note` をそのまま記録し、省略時は空文字（REQ-010、PROP-007） |

> **監査ログのエントリには ID も、申請の内容（金額・タイトル）のスナップショットも無い。**
> 並び順はリスト内の位置で表し、申請の内容は起票後に変わらないため記録していない。
> 申請の内容を変更する経路を追加する場合は、変更前後の値を記録するかを別途決める必要がある
> （[要確認]。[システム化業務一覧](../behavior/01-system-function-list.md) の再編集の項）。
