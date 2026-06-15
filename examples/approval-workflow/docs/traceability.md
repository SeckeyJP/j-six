# トレーサビリティマトリクス — 申請承認ワークフロー

> J-SIX `j-six:traceability` Skill の出力に相当する、要件 ⇔ テスト ⇔ コードの対応表。
> 計測日: 2026-06-14（37 tests / カバレッジ 99%）

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
| REQ-010 | 全状態遷移の監査記録 | `test_full_audit_trail`, `test_create_request_sets_draft_and_audit` | `WorkflowService._log`, `models.AuditEntry` |

**カバレッジ充足**: 全 10 要件にテストが存在し、未トレースの要件はゼロ。
API 結線は `test_api.py`（create/get/list/submit/approve/reject/remand/withdraw）で検証。
