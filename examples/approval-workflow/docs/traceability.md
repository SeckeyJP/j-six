# トレーサビリティマトリクス — 申請承認ワークフロー

> J-SIX `j-six:traceability` Skill の出力に相当する、要件 ⇔ テスト ⇔ コードの対応表。
> 計測日: 2026-06-14 / 更新: 2026-09-19（TASK-AW-002 反映。unit 81 + hold-out 72 = 153 tests / カバレッジ 99% / mutation 92.42%）

| 要件 | 内容 | テスト | 実装 | ADR |
|---|---|---|---|---|
| REQ-001 | 金額に応じた承認段数 | `test_required_levels_by_amount`, `test_create_request_rejects_wrong_approver_count` | `workflow.required_approval_levels`, `WorkflowService.create_request` | — |
| REQ-002 | 提出は申請者のみ | `test_submit_moves_draft_to_pending`, `test_only_applicant_can_submit`, `test_cannot_submit_twice` | `WorkflowService.submit` | ADR-0001, ADR-0003 |
| REQ-003 | 順序どおりの多段承認 | `test_two_step_approval_completes`, `test_single_step_approval_completes` | `WorkflowService.approve` | ADR-0001, ADR-0003 |
| REQ-004 | 却下 | `test_reject_terminates`, `test_only_current_approver_can_reject`, `test_reject_endpoint` | `WorkflowService.reject` | ADR-0003 |
| REQ-005 | 差し戻し | `test_remand_returns_to_draft_and_resets_step`, `test_remand_endpoint` | `WorkflowService.remand` | ADR-0001, ADR-0003 |
| REQ-006 | 取下げ | `test_withdraw_from_draft`, `test_withdraw_from_pending`, `test_only_applicant_can_withdraw`, `test_withdraw_endpoint` | `WorkflowService.withdraw` | ADR-0003 |
| REQ-007 | 自己承認の禁止 | `test_applicant_cannot_be_approver`, `test_duplicate_approvers_rejected` | `WorkflowService.create_request` | ADR-0003 |
| REQ-008 | 承認順序の強制 | `test_out_of_order_approval_rejected`, `test_cannot_approve_draft`, `test_out_of_order_returns_409` | `WorkflowService.approve` / `reject` / `remand` | ADR-0001, ADR-0003 |
| REQ-009 | 終了済みは操作不可 | `test_cannot_operate_on_terminal_request`, `test_operating_on_terminal_request_returns_409_not_404` | `WorkflowService._ensure_active` / `_ensure_pending` | ADR-0001, ADR-0003 |
| REQ-010 | 全状態遷移の監査記録（コメント含む） | `test_full_audit_trail`, `test_create_request_sets_draft_and_audit`, `test_{submit,approve,withdraw}_records_note`, `test_{submit,approve,reject,remand,withdraw}_note_defaults_to_empty_string`, `test_{submit,approve,withdraw}_note_reaches_audit_log`（API） | `WorkflowService._log`, 5 遷移メソッドの `note` 引数, `main.ActorBody.note`, `models.AuditEntry` | ADR-0002 |
| REQ-011 | 対象不在をルール違反と区別する | `test_get_unknown_request_raises`, `test_request_not_found_is_not_a_workflow_error`, `test_unknown_id_raises_request_not_found_for_every_operation`, `test_unknown_request_get_returns_404`, `test_unknown_request_transition_returns_404_not_409` | `workflow.RequestNotFound`, `WorkflowService.get`, `main._guard`（→ 404） | ADR-0003 |
| REQ-012 | 未定義の入力項目は拒否する | `test_transition_body_with_undefined_key_returns_422`, `test_create_body_with_undefined_key_returns_422`, `test_unknown_id_with_invalid_body_returns_422_not_404` | `main.CreateRequestBody` / `main.ActorBody`（`extra="forbid"` → 422） | ADR-0003 |

REQ-010 のうち reject / remand に非空のコメントを渡すケースは unit テスト（`test_workflow.py`）に
個別テストがなく、`test_prop_007_transition_note_matches_sent_note`（全 5 遷移 × 任意のコメント）と
hold-out の `test_cross_transition_notes.py` で検証している。

## Property（PROP）⇔ テスト

要求 Spec 3.3 で定義した性質。`tests/test_properties.py` で property-based testing（Hypothesis）
として検証する。ケーススタディ #2 の生存ミュータント分析から PROP-002 / PROP-005 を追加した。
PROP-007〜PROP-009 は要求 Spec 1.1 で追加し、TASK-AW-002 でテストを作成した。

| 性質 | 内容 | テスト | 対応要件 |
|---|---|---|---|
| PROP-001 | 承認段数は金額の単調非減少関数 | `test_prop_001_levels_are_monotonic`, `test_prop_001_levels_are_within_defined_range` | REQ-001 |
| PROP-002 | 金額 ≥ 1 なら起票は必ず成功し DRAFT になる | `test_prop_002_any_valid_request_is_created_as_draft` | REQ-001 |
| PROP-003 | 起票成功なら承認者に申請者は含まれない | `test_prop_003_applicant_is_never_an_approver` | REQ-007 |
| PROP-004 | 監査ログ件数 = 成功した状態遷移の回数 | `test_prop_004_audit_log_counts_every_transition` | REQ-010 |
| PROP-005 | 監査ログ末尾の actor は操作者本人 | `test_prop_005_audit_log_records_the_actual_actor` | REQ-010 |
| PROP-006 | 順序どおりの全段承認は必ず APPROVED になる | `test_prop_006_in_order_approval_always_completes`, `test_prop_006_out_of_order_approval_never_advances` | REQ-003, REQ-008 |
| PROP-007 | 状態遷移で送ったコメントが監査ログ末尾に残る | `test_prop_007_transition_note_matches_sent_note` | REQ-010 |
| PROP-008 | 未登録の ID への参照・操作は必ず「対象不在」 | `test_prop_008_unknown_id_always_raises_request_not_found` | REQ-011 |
| PROP-009 | 未定義の項目を含む入力は必ず「入力不正」で、状態も監査ログも変わらない | `test_prop_009_transition_body_with_undefined_key_returns_422`, `test_prop_009_create_body_with_undefined_key_returns_422` | REQ-012 |

## hold-out 受入テスト ⇔ ユースケース

実装を書くエージェントが読めない受入テスト（`tests/acceptance/`）。件数は parametrize 展開後。

| ユースケース | テストファイル | 対応要件 / 性質 | 件数 |
|---|---|---|---|
| UC-001 | `test_uc001_create.py` | REQ-001, REQ-007, REQ-010 | 2 |
| UC-002, UC-003 | `test_uc002_uc003_approve.py` | REQ-001〜003, REQ-008, REQ-010 / PROP-007 | 4 |
| UC-004, UC-005 | `test_uc004_uc005_reject_remand.py` | REQ-004, REQ-005 | 2 |
| UC-006 | `test_uc006_withdraw.py` | REQ-006, REQ-009, REQ-010 / PROP-007 | 5 |
| UC-002〜UC-006（横断） | `test_cross_transition_notes.py` | REQ-010 / PROP-007 | 13 |
| UC-001〜UC-006（横断） | `test_cross_error_classification.py` | REQ-011, REQ-012 / PROP-008, PROP-009 / ADR-0003 | 39 |
| UC-002〜UC-006（横断） | `test_cross_request_not_found_domain.py` | REQ-011 / PROP-008 / ADR-0003 | 7 |

## 充足状況

**トレーサビリティ**: 全 21 件（REQ 12 + PROP 9）にテストが存在する（`jsix_traceability_check.py`:
REQ 12/12・PROP 9/9 トレース済）。要求 Spec 1.1 で追加した REQ-011 / REQ-012 / PROP-007〜PROP-009 は
TASK-AW-002 で解消し、G2（トレーサビリティ）は合格。
全テストに対応する実装が存在し、153 件すべて合格する。技術判断は ADR-0001〜0003 に記録済みで、
REQ-001（段数ルール）以外の要件はいずれかの ADR から参照されている。
API 結線は `test_api.py`（create/get/list/submit/approve/reject/remand/withdraw と 404/409/422 の分類）で検証。
