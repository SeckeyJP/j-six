"""Property-based tests（PROP-001〜006）。

要求 Spec の「3.3 受入条件と Property」で定義した性質を、Hypothesis で
入力空間全体に対して検証する。例ベースのテスト（test_workflow.py）を
置き換えるものではなく、併用する。例ベースは仕様の具体例を固定し、
PBT は入力空間を探す。役割が違う。

ケーススタディ #2 の経緯: mutation testing で生き残ったミュータントのうち、
以下は本テストが殺すことを狙って追加した。
  - `amount <= 0` → `amount <= 1`（境界値。amount=1 のテストが無かった）→ PROP-002
  - `_log(req, Action.REMAND, actor, note)` → `_log(req, Action.REMAND, note)`
    （監査ログの操作者が note で上書きされる）→ PROP-005
  - `_log(req, Action.REMAND, actor, )`（差し戻しの note が記録されない）→ PROP-005
"""

import pytest
from fastapi.testclient import TestClient
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from app import main
from app.models import Status
from app.workflow import WorkflowError, WorkflowService, required_approval_levels

# 承認者IDに使う文字列。空白のみや空文字は業務上ありえないため除外する
ACTOR = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=8)
AMOUNT = st.integers(min_value=1, max_value=10_000_000)


def _approvers_for(amount: int, applicant: str) -> list:
    """金額に必要な段数ぶんの、申請者と重複しない承認者を作る。"""
    n = required_approval_levels(amount)
    return [f"approver{i}_{applicant}" for i in range(n)]


@given(a=AMOUNT, b=AMOUNT)
def test_prop_001_levels_are_monotonic(a, b):
    """PROP-001 / REQ-001: 金額が大きいほど必要承認段数は減らない。"""
    lo, hi = sorted((a, b))
    assert required_approval_levels(lo) <= required_approval_levels(hi)


@given(amount=AMOUNT)
def test_prop_001_levels_are_within_defined_range(amount):
    """PROP-001 / REQ-001: 承認段数は 1〜3 段のいずれか。"""
    assert required_approval_levels(amount) in (1, 2, 3)


@given(applicant=ACTOR, amount=AMOUNT, title=st.text(min_size=1, max_size=20))
def test_prop_002_any_valid_request_is_created_as_draft(applicant, amount, title):
    """PROP-002 / REQ-001: 金額 1 以上・妥当な承認者なら起票は必ず成功し DRAFT になる。

    mutation testing で `amount <= 0` を `amount <= 1` に変えたミュータントが
    生き残った。amount=1 を試すテストが無かったため。この性質はその境界を含む。
    """
    assume(title.strip())
    service = WorkflowService()
    req = service.create_request(
        applicant, amount, title, _approvers_for(amount, applicant)
    )

    assert req.status is Status.DRAFT
    assert req.amount == amount
    assert len(req.approvers) == required_approval_levels(amount)


@given(applicant=ACTOR, amount=AMOUNT)
def test_prop_003_applicant_is_never_an_approver(applicant, amount):
    """PROP-003 / REQ-007: 起票が成功したなら、承認者リストに申請者は含まれない。"""
    service = WorkflowService()
    approvers = _approvers_for(amount, applicant)
    req = service.create_request(applicant, amount, "申請", approvers)
    assert applicant not in req.approvers

    # 申請者を混ぜた場合は必ず拒否される
    tainted = list(approvers)
    tainted[0] = applicant
    try:
        service.create_request(applicant, amount, "申請", tainted)
    except WorkflowError:
        pass
    else:
        raise AssertionError("申請者を承認者に含む起票が通ってしまった")


@given(applicant=ACTOR, amount=AMOUNT)
@settings(max_examples=50)
def test_prop_004_audit_log_counts_every_transition(applicant, amount):
    """PROP-004 / REQ-010: 監査ログの件数は成功した状態遷移の回数と一致する。"""
    service = WorkflowService()
    approvers = _approvers_for(amount, applicant)

    req = service.create_request(applicant, amount, "申請", approvers)
    transitions = 1  # CREATE

    service.submit(req.id, applicant)
    transitions += 1

    for approver in approvers:
        service.approve(req.id, approver)
        transitions += 1

    assert len(req.audit_log) == transitions
    assert req.status is Status.APPROVED


@given(applicant=ACTOR, amount=AMOUNT, note=st.text(min_size=1, max_size=20))
@settings(max_examples=50)
def test_prop_005_audit_log_records_the_actual_actor(applicant, amount, note):
    """PROP-005 / REQ-010: 監査ログ末尾の actor は操作を行った本人と一致する。

    mutation testing で `_log(req, Action.REMAND, actor, note)` を
    `_log(req, Action.REMAND, note)` に変えたミュータント（actor が note で
    上書きされる）が生き残った。差し戻しの監査ログの操作者を検証していなかったため。
    """
    service = WorkflowService()
    approvers = _approvers_for(amount, applicant)

    req = service.create_request(applicant, amount, "申請", approvers)
    assert req.audit_log[-1].actor == applicant

    service.submit(req.id, applicant)
    assert req.audit_log[-1].actor == applicant

    first_approver = approvers[0]
    service.remand(req.id, first_approver, note)
    assert req.audit_log[-1].actor == first_approver
    assert req.audit_log[-1].note == note

    service.submit(req.id, applicant)
    assert req.audit_log[-1].actor == applicant

    service.reject(req.id, approvers[0], note)
    assert req.audit_log[-1].actor == approvers[0]
    assert req.audit_log[-1].note == note


@given(applicant=ACTOR, amount=AMOUNT)
@settings(max_examples=50)
def test_prop_006_in_order_approval_always_completes(applicant, amount):
    """PROP-006 / REQ-003, REQ-008: 順序どおりに全段承認すると必ず APPROVED になる。"""
    service = WorkflowService()
    approvers = _approvers_for(amount, applicant)

    req = service.create_request(applicant, amount, "申請", approvers)
    service.submit(req.id, applicant)

    for i, approver in enumerate(approvers):
        assert req.next_approver == approver
        service.approve(req.id, approver)
        expected = Status.APPROVED if i == len(approvers) - 1 else Status.PENDING
        assert req.status is expected


@given(applicant=ACTOR, amount=AMOUNT)
@settings(max_examples=50)
def test_prop_006_out_of_order_approval_never_advances(applicant, amount):
    """PROP-006 / REQ-008: 現在の承認者以外の承認は、状態も承認段も進めない。"""
    service = WorkflowService()
    approvers = _approvers_for(amount, applicant)
    assume(len(approvers) >= 2)

    req = service.create_request(applicant, amount, "申請", approvers)
    service.submit(req.id, applicant)

    before_step, before_log = req.current_step, len(req.audit_log)
    try:
        service.approve(req.id, approvers[-1])
    except WorkflowError:
        pass
    else:
        raise AssertionError("順序外の承認が通ってしまった")

    assert req.current_step == before_step
    assert len(req.audit_log) == before_log


# --- PROP-007〜009（要求 Spec 3.3 改訂。REQ-010〜012） ---------------------

TRANSITIONS = ["submit", "approve", "reject", "remand", "withdraw"]
NOTE = st.text(max_size=20)


def _fresh_draft(applicant: str, amount: int):
    service = WorkflowService()
    approvers = _approvers_for(amount, applicant)
    req = service.create_request(applicant, amount, "申請", approvers)
    return service, req, approvers


def _run_transition(service, req, transition, actor, note):
    kwargs = {} if note is None else {"note": note}
    method = getattr(service, transition)
    return method(req.id, actor, **kwargs)


@given(
    applicant=ACTOR,
    amount=AMOUNT,
    transition=st.sampled_from(TRANSITIONS),
    note=st.one_of(st.none(), NOTE),
)
@settings(max_examples=40)
def test_prop_007_transition_note_matches_sent_note(
    applicant, amount, transition, note
):
    """PROP-007 / REQ-010: 任意の状態遷移操作と任意のコメントについて、操作が成功したなら、
    監査ログ末尾のコメントは送ったコメントと一致する（省略したときは空文字）。
    """
    service, req, approvers = _fresh_draft(applicant, amount)

    if transition == "submit":
        actor = applicant
    else:
        service.submit(req.id, applicant)
        actor = applicant if transition == "withdraw" else approvers[0]

    _run_transition(service, req, transition, actor, note)

    expected_note = note if note is not None else ""
    assert req.audit_log[-1].note == expected_note


UNKNOWN_ID = st.text(
    alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-", min_size=1, max_size=12
)
REFERENCE_OR_TRANSITION = ["get", *TRANSITIONS]


@given(
    applicant=ACTOR,
    amount=AMOUNT,
    unknown_id=UNKNOWN_ID,
    operation=st.sampled_from(REFERENCE_OR_TRANSITION),
)
@settings(max_examples=40)
def test_prop_008_unknown_id_always_raises_request_not_found(
    applicant, amount, unknown_id, operation
):
    """PROP-008 / REQ-011: 任意の未登録 ID と任意の操作（参照・5 遷移）について、
    結果は必ず RequestNotFound（対象不在）であり、登録済み申請の状態と監査ログは
    変わらない。
    """
    from app.workflow import RequestNotFound

    service = WorkflowService()
    approvers = _approvers_for(amount, applicant)
    req = service.create_request(applicant, amount, "申請", approvers)
    assume(unknown_id != req.id)

    before_status = req.status
    before_log_len = len(req.audit_log)

    with pytest.raises(RequestNotFound):
        if operation == "get":
            service.get(unknown_id)
        elif operation == "withdraw":
            service.withdraw(unknown_id, applicant)
        elif operation == "submit":
            service.submit(unknown_id, applicant)
        else:
            getattr(service, operation)(unknown_id, approvers[0])

    assert req.status == before_status
    assert len(req.audit_log) == before_log_len


EXTRA_KEY = st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=10)
EXTRA_VALUE = st.one_of(st.text(max_size=10), st.integers(), st.booleans())


@given(
    endpoint=st.sampled_from(TRANSITIONS),
    extra_key=EXTRA_KEY,
    extra_value=EXTRA_VALUE,
)
@settings(max_examples=20)
def test_prop_009_transition_body_with_undefined_key_returns_422(
    endpoint, extra_key, extra_value
):
    """PROP-009 / REQ-012: 任意の状態遷移操作と、定義されていない項目を1つ以上含む
    任意の入力について、結果は必ず入力不正（422）であり、対象の申請の状態と監査ログは
    変わらない。
    """
    assume(extra_key not in ("actor", "note"))
    main.service = WorkflowService()
    client = TestClient(main.app)

    create_res = client.post(
        "/requests",
        json={
            "applicant": "alice",
            "amount": 50_000,
            "title": "申請",
            "approvers": ["bob"],
        },
    )
    rid = create_res.json()["id"]
    client.post(f"/requests/{rid}/submit", json={"actor": "alice"})
    before = client.get(f"/requests/{rid}").json()

    body = {"actor": "bob", extra_key: extra_value}
    res = client.post(f"/requests/{rid}/{endpoint}", json=body)
    assert res.status_code == 422

    after = client.get(f"/requests/{rid}").json()
    assert after == before


@given(extra_key=EXTRA_KEY, extra_value=EXTRA_VALUE)
@settings(max_examples=20)
def test_prop_009_create_body_with_undefined_key_returns_422(extra_key, extra_value):
    """PROP-009 / REQ-012: 起票の入力に、定義されていない項目を1つ以上含めた場合、
    結果は必ず入力不正（422）であり、申請は作られない（監査ログも増えない）。
    """
    assume(extra_key not in ("applicant", "amount", "title", "approvers"))
    main.service = WorkflowService()
    client = TestClient(main.app)

    before_count = len(client.get("/requests").json())

    body = {
        "applicant": "alice",
        "amount": 50_000,
        "title": "申請",
        "approvers": ["bob"],
        extra_key: extra_value,
    }
    res = client.post("/requests", json=body)
    assert res.status_code == 422

    after_count = len(client.get("/requests").json())
    assert after_count == before_count
