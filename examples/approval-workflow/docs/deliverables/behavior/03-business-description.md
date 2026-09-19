# システム化業務説明

**工程成果物**: システム振舞い ③ ／ **由来**: **hold-out 受入テストから逆生成**
**逆生成元**: `tests/acceptance/`（7ファイル・72件〔parametrize 展開後〕・全て通過。2026-09-19 に `pytest tests/acceptance` で確認）
**対象**: 申請承認ワークフロー（approval-workflow） ／ **版**: 1.0 ／ **日付**: 2026-09-19

> システム利用作業と機能の内容を、事前条件・事後条件・基本シナリオで記述したもの。

## この成果物が逆生成できる理由

IPA ガイドが想定する「システム化業務説明」の構成要素は、**受入テストの構造そのもの**である。

| 工程成果物の欄 | 受入テストの対応物 |
|---|---|
| 事前条件 | fixture（`client`: 申請ストアを空にして API クライアントを返す）と、各テストの準備関数（`_create` / `_pending` / `_submitted` / `_prepare`）が作る状態 |
| 基本シナリオ | テスト本体の操作列 |
| 事後条件 | アサーション |
| 入力データ / 出力データ | リクエストと検証対象のレスポンス |

したがって本書の記述は**通っているテストが根拠**であり、実装との乖離が起こらない。
テストが落ちれば本書も誤りになるため、G2 が本書の正しさを保証している。

対象は `tests/acceptance/`（hold-out 受入テスト）に限る。実装を書く工程が読めない
テストであり、実装に引きずられていないため。

### 本書を読む前提

- 受入テストは HTTP API 経由でのみ検証する（`tests/acceptance/conftest.py`）。例外として
  `test_cross_request_not_found_domain.py` だけはドメイン層の公開された例外を検証する（本書末尾の横断 3）。
- **成功の判定は 2xx で行っている。** 成功時のステータスコード（201 / 200 など）は Design Spec が
  規定していないため、受入テストは固定していない（`conftest.py` の docstring）。本書でも
  「成功（2xx）」と書く。
- テストの登場人物は、申請者 `alice`、承認者 `bob`・`carol`（2段承認では `bob` → `carol` の順）。
- 失敗時のステータスは 409（ルール違反）/ 404（対象不在）/ 422（入力不正）で、受入テストが固定している。

---

## UC-001 申請を起票する

| 項目 | 内容 |
|---|---|
| 概要 | 申請者が金額・タイトル・承認者を指定して、DRAFT の申請を作成する |
| アクター | 申請者 |
| 事前条件 | 申請が1件も無い（`client` fixture がストアを空にする） |
| 事後条件 | 状態 DRAFT の申請が作られ、申請者・金額・承認者が入力どおりで、監査ログが `CREATE` の1件だけであること。作った申請を ID で取得できること |
| 入力データ | `applicant`=`alice`, `amount`=`50000`, `title`=`備品購入`, `approvers`=`["bob"]` |
| 出力データ | 申請（`id`, `status`=`DRAFT`, `applicant`=`alice`, `amount`=`50000`, `approvers`=`["bob"]`, `audit_log` の action 列 = `["CREATE"]`） |
| 根拠テスト | `test_uc001_applicant_creates_draft_request` |

**基本シナリオ**

1. 申請者が `POST /requests` に、金額 50,000 円・承認者1名（`bob`）で起票する
2. システムは成功（2xx）を返し、状態 DRAFT の申請を返す。監査ログには `CREATE` が1件残る
3. 申請者が返された `id` で `GET /requests/{id}` を呼ぶと、同じ申請が取得できる

**代替シナリオ**

| 状況 | 動作 | 根拠テスト |
|---|---|---|
| 申請者自身を承認者に含めた（`approvers`=`["alice"]`） | 409（REQ-007） | `test_uc001_rejects_self_approval` |
| 金額 300,000 円に承認者1名（段数不一致） | 409（422 ではない）。申請は作られない（一覧が空） | `test_uc001_create_rule_violation_is_still_409` |
| 入力に未定義の項目 `note` を含めた | 422。申請は作られない（一覧が変わらない） | `test_uc001_create_with_undefined_key_returns_422` |
| 入力に未定義の項目を1〜3個含めた（任意の項目名・値。25例） | 必ず 422。申請は作られない（PROP-009） | `test_prop009_create_with_any_undefined_key_is_invalid_input` |

---

## UC-002 申請を提出する

| 項目 | 内容 |
|---|---|
| 概要 | 申請者が DRAFT の申請を提出し、承認待ち（PENDING）にする |
| アクター | 申請者 |
| 事前条件 | `alice` が金額 50,000 円・承認者 `["bob"]` で起票した DRAFT の申請がある |
| 事後条件 | 状態が PENDING になり、次の承認者（`next_approver`）が `bob` になること |
| 入力データ | `actor`=`alice` |
| 出力データ | 申請（`status`=`PENDING`, `next_approver`=`bob`） |
| 根拠テスト | `test_uc002_applicant_submits_draft` |

**基本シナリオ**

1. 申請者 `alice` が `POST /requests/{id}/submit` を呼ぶ
2. システムは成功（2xx）を返し、状態 PENDING・次の承認者 `bob` の申請を返す

**代替シナリオ**

| 状況 | 動作 | 根拠テスト |
|---|---|---|
| 申請者以外（`bob`）が提出した | 409（REQ-002）。状態・監査ログは変わらない | `test_rule_violation_on_existing_request_is_still_409[submit-bob]` |
| 取下げ済み（WITHDRAWN）の申請を提出した | 409（REQ-009）。状態・監査ログは変わらない | `test_rule_violation_on_terminal_request_is_still_409[submit]` |
| コメント `至急お願いします` を付けて提出した | 監査ログ末尾が (`SUBMIT`, `alice`, `至急お願いします`) | `test_uc002_uc003_notes_on_submit_and_approve_are_recorded` |

存在しない申請への提出・コメントの記録は、横断 1・2 を参照。

---

## UC-003 申請を承認する

| 項目 | 内容 |
|---|---|
| 概要 | 承認者が、承認者リストの順序どおりに承認する。全段の承認で APPROVED になる |
| アクター | 承認者 |
| 事前条件 | (a) 金額 50,000 円・承認者 `["bob"]` の申請を `alice` が提出済み ／ (b) 金額 300,000 円・承認者 `["bob", "carol"]` の申請を `alice` が提出済み |
| 事後条件 | (a) `bob` の承認で APPROVED ／ (b) `bob` の承認後は PENDING・次の承認者 `carol`、`carol` の承認で APPROVED。監査ログの action 列が `["CREATE", "SUBMIT", "APPROVE", "APPROVE"]` |
| 入力データ | `actor`（`bob` / `carol`）、任意で `note` |
| 出力データ | 申請（`status`, `next_approver`, `audit_log`） |
| 根拠テスト | `test_uc003_single_step_approval_completes`, `test_uc003_two_step_approval_requires_both_in_order`, `test_uc002_uc003_notes_on_submit_and_approve_are_recorded` |

**基本シナリオ（2段承認）**

1. 申請者 `alice` が金額 300,000 円・承認者 `["bob", "carol"]` で起票し、提出する
2. 1人目の承認者 `bob` が `POST /requests/{id}/approve` を呼ぶ
3. システムは成功（2xx）を返す。状態は PENDING のまま、次の承認者は `carol`
4. 2人目の承認者 `carol` が承認する
5. システムは成功（2xx）を返し、状態は APPROVED。監査ログは `CREATE` → `SUBMIT` → `APPROVE` → `APPROVE`

**コメントの記録（同じ2段承認の例）**

| 操作 | 送ったコメント | 監査ログに残った (action, actor, note) |
|---|---|---|
| 起票 | — | (`CREATE`, `alice`, ``) |
| 提出 | `至急お願いします` | (`SUBMIT`, `alice`, `至急お願いします`) |
| 1段目の承認 | `内容確認済み` | (`APPROVE`, `bob`, `内容確認済み`) |
| 2段目の承認 | 省略 | (`APPROVE`, `carol`, ``) |

取得し直しても（`GET /requests/{id}`）同じ4件がこの順で残っている（`test_uc002_uc003_notes_on_submit_and_approve_are_recorded`）。

**代替シナリオ**

| 状況 | 動作 | 根拠テスト |
|---|---|---|
| 2段承認で2人目（`carol`）が先に承認した | 409（REQ-008） | `test_uc003_two_step_approval_requires_both_in_order` |
| 現在の承認者でない `carol` が承認した（承認者 `["bob"]`） | 409（REQ-008）。状態・監査ログは変わらない | `test_rule_violation_on_existing_request_is_still_409[approve-carol]` |
| 一度も起票されていない ID `never-created` を承認した | 404（対象不在）。登録済みの申請は変わらない | `test_uc003_approve_never_created_id_is_not_found` |
| 承認の入力で `note` を `nte` と打ち間違えた | 422。状態は PENDING のまま、監査ログは `["CREATE", "SUBMIT"]` のまま | `test_uc003_approve_with_typo_nte_returns_422_and_changes_nothing` |
| 取下げ済みの申請を承認した | 409（REQ-009） | `test_rule_violation_on_terminal_request_is_still_409[approve]` |
| 却下済みの申請を承認した | 409（REQ-009） | `test_uc004_approver_rejects_and_it_is_terminal` |

---

## UC-004 申請を却下する

| 項目 | 内容 |
|---|---|
| 概要 | 現在の承認者が承認待ちの申請を却下する。却下は終了状態 |
| アクター | 承認者 |
| 事前条件 | 金額 50,000 円・承認者 `["bob"]` の申請を `alice` が提出済み |
| 事後条件 | 状態が REJECTED になること。以降の承認（`bob`）・取下げ（`alice`）が 409 になること |
| 入力データ | `actor`=`bob`, `note`=`予算超過` |
| 出力データ | 申請（`status`=`REJECTED`） |
| 根拠テスト | `test_uc004_approver_rejects_and_it_is_terminal` |

**基本シナリオ**

1. 承認者 `bob` が理由 `予算超過` を付けて `POST /requests/{id}/reject` を呼ぶ
2. システムは成功（2xx）を返し、状態 REJECTED の申請を返す
3. その後の `bob` による承認、`alice` による取下げは、いずれも 409 になる（REQ-009）

**代替シナリオ**

| 状況 | 動作 | 根拠テスト |
|---|---|---|
| 現在の承認者でない `carol` が却下した | 409（REQ-008）。状態・監査ログは変わらない | `test_rule_violation_on_existing_request_is_still_409[reject-carol]` |
| 取下げ済みの申請を却下した | 409（REQ-009）。状態・監査ログは変わらない | `test_rule_violation_on_terminal_request_is_still_409[reject]` |
| 却下のコメントを付けた / 省略した | 監査ログ末尾が (`REJECT`, `bob`, 送ったコメント) / (`REJECT`, `bob`, ``) | `test_req010_every_transition_records_its_note[reject]`, `test_req010_omitted_note_is_recorded_as_empty[reject]` |

---

## UC-005 申請を差し戻す

| 項目 | 内容 |
|---|---|
| 概要 | 現在の承認者が承認待ちの申請を DRAFT に差し戻す。再提出すると最初の承認者からやり直す |
| アクター | 承認者 |
| 事前条件 | 金額 300,000 円・承認者 `["bob", "carol"]` の申請を `alice` が提出し、`bob` が承認済み（現在の承認者は `carol`） |
| 事後条件 | 差し戻しで状態が DRAFT になること。申請者が再提出すると、次の承認者が最初の `bob` に戻ること |
| 入力データ | `actor`=`carol`, `note`=`見積添付漏れ` |
| 出力データ | 申請（`status`=`DRAFT`）、再提出後の申請（`next_approver`=`bob`） |
| 根拠テスト | `test_uc005_remand_returns_to_draft_and_restarts` |

**基本シナリオ**

1. 2人目の承認者 `carol` が理由 `見積添付漏れ` を付けて `POST /requests/{id}/remand` を呼ぶ
2. システムは成功（2xx）を返し、状態 DRAFT の申請を返す
3. 申請者 `alice` が再提出する
4. システムは成功（2xx）を返し、次の承認者は `bob`（1段目からやり直し。REQ-005）

**代替シナリオ**

| 状況 | 動作 | 根拠テスト |
|---|---|---|
| 現在の承認者でない `carol` が差し戻した（承認者 `["bob"]`） | 409（REQ-008）。状態・監査ログは変わらない | `test_rule_violation_on_existing_request_is_still_409[remand-carol]` |
| 取下げ済みの申請を差し戻した | 409（REQ-009）。状態・監査ログは変わらない | `test_rule_violation_on_terminal_request_is_still_409[remand]` |
| 差し戻しのコメントを付けた / 省略した | 監査ログ末尾が (`REMAND`, `bob`, 送ったコメント) / (`REMAND`, `bob`, ``) | `test_req010_every_transition_records_its_note[remand]`, `test_req010_omitted_note_is_recorded_as_empty[remand]` |

---

## UC-006 申請を取下げる

| 項目 | 内容 |
|---|---|
| 概要 | 申請者が DRAFT または PENDING の申請を取下げる。取下げは終了状態 |
| アクター | 申請者 |
| 事前条件 | 金額 50,000 円・承認者 `["bob"]` で `alice` が起票した申請（DRAFT）、またはそれを提出した申請（PENDING） |
| 事後条件 | 状態が WITHDRAWN になること。付けたコメントが監査ログに残ること |
| 入力データ | `actor`=`alice`、任意で `note` |
| 出力データ | 申請（`status`=`WITHDRAWN`） |
| 根拠テスト | `test_uc006_applicant_withdraws_from_draft`, `test_uc006_applicant_withdraws_from_pending`, `test_uc006_withdraw_note_is_recorded_from_draft`, `test_uc006_withdraw_note_is_recorded_from_pending` |

**基本シナリオ**

1. 申請者 `alice` が `POST /requests/{id}/withdraw` を呼ぶ（DRAFT・PENDING のどちらでも）
2. システムは成功（2xx）を返し、状態 WITHDRAWN の申請を返す

**コメントの記録**

| 取下げ元 | 送ったコメント | 監査ログ |
|---|---|---|
| DRAFT | `購入不要になった` | (`CREATE`, `alice`, ``) → (`WITHDRAW`, `alice`, `購入不要になった`) の2件 |
| PENDING | `金額を誤った` | 末尾が (`WITHDRAW`, `alice`, `金額を誤った`) |

**代替シナリオ**

| 状況 | 動作 | 根拠テスト |
|---|---|---|
| 申請者以外（`bob`）が取下げた（DRAFT） | 409（REQ-006） | `test_uc006_others_cannot_withdraw` |
| 申請者以外（`bob`）が取下げた（PENDING） | 409（REQ-006）。状態・監査ログは変わらない | `test_rule_violation_on_existing_request_is_still_409[withdraw-bob]` |
| 取下げ済みの申請を再び取下げた | 409（REQ-009）。状態・監査ログは変わらない | `test_rule_violation_on_terminal_request_is_still_409[withdraw]` |
| 却下済みの申請を取下げた | 409（REQ-009） | `test_uc004_approver_rejects_and_it_is_terminal` |

---

## 横断 1. 状態遷移コメントの記録（UC-002〜UC-006）

根拠: `test_cross_transition_notes.py`（13件）。対応: REQ-010 / PROP-007。

| 項目 | 内容 |
|---|---|
| 事前条件 | 金額 50,000 円・承認者 `["bob"]` の申請。提出・取下げ（DRAFT から）は DRAFT のまま、承認・却下・差し戻し・取下げ（PENDING から）は `alice` が提出済み |
| 事後条件 | 操作の応答と、取得し直した申請の両方で、監査ログ末尾が (その操作の action, 操作者, 送ったコメント) であること。コメントを省略したときは空文字 |

| 操作 | 操作者 | 監査ログ末尾の action | 根拠テスト |
|---|---|---|---|
| 提出 | `alice` | `SUBMIT` | `test_req010_every_transition_records_its_note[submit]` ほか |
| 承認 | `bob` | `APPROVE` | `test_req010_every_transition_records_its_note[approve]` ほか |
| 却下 | `bob` | `REJECT` | `test_req010_every_transition_records_its_note[reject]` ほか |
| 差し戻し | `bob` | `REMAND` | `test_req010_every_transition_records_its_note[remand]` ほか |
| 取下げ（DRAFT から） | `alice` | `WITHDRAW` | `test_req010_every_transition_records_its_note[withdraw]` ほか |
| 取下げ（PENDING から） | `alice` | `WITHDRAW` | `test_req010_every_transition_records_its_note[withdraw_pending]` ほか |

- コメントを付けた場合（`"<操作> のコメント"`）: `test_req010_every_transition_records_its_note`（6件）
- コメントを省略した場合（空文字で記録。操作は成功）: `test_req010_omitted_note_is_recorded_as_empty`（6件）
- 上の6操作 × 任意のコメント（省略を含む、40文字以内。30例）で、末尾のコメントが送ったもの
  （省略時は空文字）と一致し、action・actor も一致する: `test_prop007_last_audit_note_equals_sent_note`（PROP-007）

---

## 横断 2. エラーの分類（UC-001〜UC-006）

根拠: `test_cross_error_classification.py`（39件）。対応: REQ-011 / REQ-012 / PROP-008 / PROP-009 / ADR-0003。

どの異常でも、登録済みの申請の状態と監査ログは変わらない（各テストが操作前後の一覧・申請を比較している）。

### 対象不在（404）

| 状況 | 動作 | 根拠テスト |
|---|---|---|
| 存在しない申請 `REQ-9999` を取得した | 404 | `test_req011_get_unknown_request_returns_404` |
| 存在しない申請 `REQ-9999` に状態遷移（5種）を行った | 404（409 ではない） | `test_req011_transition_on_unknown_request_returns_404_not_409`（5件） |
| 任意の未登録 ID（英数字・`-`・`_` の1〜12文字）に、参照または状態遷移（5種）を、任意の操作者・任意のコメントで行った（25例） | 必ず 404 | `test_prop008_any_operation_on_unregistered_id_is_not_found`（PROP-008） |

### 入力不正（422）

| 状況 | 動作 | 根拠テスト |
|---|---|---|
| 状態遷移（5種）の入力に未定義の項目 `comment` を含めた。未定義の項目が無ければ成功する状態・操作者で試す | 422 | `test_req012_transition_with_undefined_key_returns_422`（5件） |
| 状態遷移（5種）の入力に、未定義の項目を1〜3個含めた（任意の項目名・値。25例） | 必ず 422 | `test_prop009_transition_with_any_undefined_key_is_invalid_input`（PROP-009） |

起票の入力不正は UC-001 の代替シナリオ、承認の `nte` は UC-003 の代替シナリオを参照。

### ルール違反（409）

UC-002〜UC-006 の代替シナリオに記載（`test_rule_violation_on_existing_request_is_still_409` 5件、
`test_rule_violation_on_terminal_request_is_still_409` 5件、`test_uc001_create_rule_violation_is_still_409`）。
存在する申請へのルール違反は 404 / 422 にならず 409 のままであることを確認している。

### 判定の順序（ADR-0003）

| 状況 | 動作 | 根拠テスト |
|---|---|---|
| 存在しない申請 `REQ-9999` に、未定義の項目 `nte` を含む入力で状態遷移（5種）を行った | 422（404 より先） | `test_adr0003_invalid_body_on_unknown_id_returns_422[undefined-key-*]`（5件） |
| 存在しない申請 `REQ-9999` に、`actor` を欠いた入力で状態遷移（5種）を行った | 422（404 より先） | `test_adr0003_invalid_body_on_unknown_id_returns_422[missing-actor-*]`（5件） |
| 存在しない申請 `REQ-9999` に、形の正しい入力で、`alice` / `bob` / `carol` / `nobody` のいずれが状態遷移（5種）を行っても | 404（ルール違反の判定より先） | `test_adr0003_unknown_id_takes_precedence_over_rule_violation` |

---

## 横断 3. 対象不在の例外（ドメイン層の公開インタフェース）

根拠: `test_cross_request_not_found_domain.py`（7件）。対応: REQ-011 / PROP-008 / ADR-0003。

| 状況 | 動作 | 根拠テスト |
|---|---|---|
| 例外の型の関係 | `RequestNotFound` は `Exception` のサブクラスで、`WorkflowError` のサブクラスではない（逆も同じ） | `test_request_not_found_is_not_a_workflow_error` |
| 存在しない申請 `REQ-9999` を `WorkflowService.get` で取得した | `RequestNotFound`（`WorkflowError` ではない） | `test_get_unknown_request_raises_request_not_found` |
| 存在しない申請 `REQ-9999` に状態遷移（5種）のメソッドを呼んだ | `RequestNotFound`（`WorkflowError` ではない）。登録済みの申請（PENDING）の状態・監査ログは変わらない | `test_transition_on_unknown_request_raises_request_not_found`（5件） |

---

## 受入テストに無いため本書に書かなかったこと

本書は通っている受入テストだけを根拠にしているため、次の事項は書いていない。仕様としては
要求 Spec・Design Spec にあるが、hold-out 受入テストでは検証していない。

| 事項 | 仕様の所在 | 検証している可視テスト |
|---|---|---|
| 100万円以上の3段承認 | 要求 Spec REQ-001 | `test_required_levels_by_amount`（`tests/test_workflow.py`） |
| 金額が1未満・タイトルが空の起票の拒否 | Design Spec 4.3 | `test_create_request_rejects_zero_amount`, `test_create_request_rejects_empty_title` |
| 承認者の重複の拒否 | Design Spec 4.3 | `test_duplicate_approvers_rejected` |
| 申請の一覧（`GET /requests`）の並び順 | 規定なし | なし（`test_list_requests` は件数のみ） |
