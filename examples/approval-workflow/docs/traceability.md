# トレーサビリティマトリクス — 申請承認ワークフロー

> J-SIX `j-six:traceability` Skill の出力に相当する、要件 ⇔ テスト ⇔ コードの対応表。
> 計測日: 2026-06-14 / 更新: 2026-09-10（45 tests + hold-out 10 / カバレッジ 99% / mutation 93.4%）

| 要件 | 内容 | テスト | 実装 |
|---|---|---|---|
| REQ-001 | 金額に応じた承認段数 | `test_required_levels_by_amount`, `test_create_request_rejects_wrong_approver_count` | `workflow.required_approval_levels`, `WorkflowService.create_request` |
| REQ-002 | 提出は申請者のみ | `test_submit_moves_draft_to_pending`, `test_only_applicant_can_submit`, `test_cannot_submit_twice` | `WorkflowService.submit` |
| REQ-003 | 順序どおりの多段承認 | `test_two_step_approval_completes`, `test_single_step_approval_completes` | `WorkflowService.approve` |
| REQ-004 | 却下 | `test_reject_terminates`, `test_only_current_approver_can_reject`, `test_reject_endpoint` | `WorkflowService.reject` |
| REQ-005 | 差し戻し | `test_remand_returns_to_draft_and_resets_step`, `test_remand_endpoint` | `WorkflowService.remand` |
| REQ-006 | 取下げ | `test_withdraw_from_draft`, `test_withdraw_from_pending`, `test_only_applicant_can_withdraw`, `test_withdraw_endpoint` | `WorkflowService.withdraw` |
| REQ-007 | 自己承認の禁止 | `test_applicant_cannot_be_approver`, `test_duplicate_approvers_rejected` | `WorkflowService.create_request` |
| REQ-008 | 承認順序の強制 | `test_out_of_order_approval_rejected`, `test_cannot_approve_draft`, `test_out_of_order_returns_409` | `WorkflowService.approve` / `reject` / `remand` |
| REQ-009 | 終了済みは操作不可 | `test_cannot_operate_on_terminal_request` | `WorkflowService._ensure_active` / `_ensure_pending` |
| REQ-010 | 全状態遷移の監査記録 | `test_full_audit_trail`, `test_create_request_sets_draft_and_audit`（submit / approve / withdraw のコメント記録は**未トレース**。要求 Spec 1.1 で追加、Phase 4 で作成） | `WorkflowService._log`, `models.AuditEntry` |
| REQ-011 | 対象不在をルール違反と区別する | **未トレース**（要求 Spec 1.1 で追加。Phase 4 で作成） | — |
| REQ-012 | 未定義の入力項目は拒否する | **未トレース**（要求 Spec 1.1 で追加。Phase 4 で作成） | — |

## Property（PROP）⇔ テスト

要求 Spec 3.3 で定義した性質。`tests/test_properties.py` で property-based testing（Hypothesis）
として検証する。ケーススタディ #2 の生存ミュータント分析から PROP-002 / PROP-005 を追加した。

| 性質 | 内容 | テスト | 対応要件 |
|---|---|---|---|
| PROP-001 | 承認段数は金額の単調非減少関数 | `test_prop_001_levels_are_monotonic`, `test_prop_001_levels_are_within_defined_range` | REQ-001 |
| PROP-002 | 金額 ≥ 1 なら起票は必ず成功し DRAFT になる | `test_prop_002_any_valid_request_is_created_as_draft` | REQ-001 |
| PROP-003 | 起票成功なら承認者に申請者は含まれない | `test_prop_003_applicant_is_never_an_approver` | REQ-007 |
| PROP-004 | 監査ログ件数 = 成功した状態遷移の回数 | `test_prop_004_audit_log_counts_every_transition` | REQ-010 |
| PROP-005 | 監査ログ末尾の actor は操作者本人 | `test_prop_005_audit_log_records_the_actual_actor` | REQ-010 |
| PROP-006 | 順序どおりの全段承認は必ず APPROVED になる | `test_prop_006_in_order_approval_always_completes`, `test_prop_006_out_of_order_approval_never_advances` | REQ-003, REQ-008 |
| PROP-007 | 状態遷移で送ったコメントが監査ログ末尾に残る | **未トレース**（Phase 4 で作成） | REQ-010 |
| PROP-008 | 未登録の ID への参照・操作は必ず「対象不在」 | **未トレース**（Phase 4 で作成） | REQ-011 |
| PROP-009 | 未定義の項目を含む入力は必ず「入力不正」で、状態も監査ログも変わらない | **未トレース**（Phase 4 で作成） | REQ-012 |

## hold-out 受入テスト ⇔ ユースケース

実装を書くエージェントが読めない受入テスト（`tests/acceptance/`）。

| ユースケース | テストファイル | 件数 |
|---|---|---|
| UC-001 | `test_uc001_create.py` | 2 |
| UC-002, UC-003 | `test_uc002_uc003_approve.py` | 3 |
| UC-004, UC-005 | `test_uc004_uc005_reject_remand.py` | 2 |
| UC-006 | `test_uc006_withdraw.py` | 3 |

## 充足状況

**トレーサビリティ**: 全 21 件（REQ 12 + PROP 9）のうち 16 件にテストが存在する。
要求 Spec 1.1（2026-09-19）で追加した REQ-011 / REQ-012 / PROP-007〜PROP-009 の 5 件は未トレースで、
Phase 4 でテストを先に書いて解消する。それまで `make gate` の G2（トレーサビリティ）は不合格になる。
API 結線は `test_api.py`（create/get/list/submit/approve/reject/remand/withdraw）で検証。
