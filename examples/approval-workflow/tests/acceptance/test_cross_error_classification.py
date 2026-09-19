"""UC-002〜UC-006（横断）: エラーの分類（hold-out 受入テスト）。

要求 Spec 3.4 #5 / ADR-0003。

- 対象不在（REQ-011 / PROP-008）: 存在しない申請への参照・状態遷移は 404。409 にしない
- 入力不正（REQ-012 / PROP-009）: 未定義の項目を含む入力は 422。状態も監査ログも変えない
- ルール違反（REQ-002〜REQ-009）: 引き続き 409
- 判定順序（ADR-0003）: 入力不正 422 → 不在 404 → ルール違反 409

HTTP API 経由でのみ検証する。
"""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

TRANSITIONS = ("submit", "approve", "reject", "remand", "withdraw")

# 状態遷移の入力項目として定義されているもの（Design Spec 4.2）
TRANSITION_KEYS = {"actor", "note"}
# 起票の入力項目として定義されているもの（Design Spec 4.2）
CREATE_KEYS = {"applicant", "amount", "title", "approvers"}

# hold-out は make mutation でも走るので例の数を絞る。
# client fixture は例をまたいで共有されるが、各例は自分で作った申請と
# 全体のスナップショットだけを比べるので、蓄積があっても判定は変わらない。
PBT = settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)


def _create(client, applicant="alice", amount=50000, approvers=("bob",)):
    res = client.post(
        "/requests",
        json={
            "applicant": applicant,
            "amount": amount,
            "title": "申請",
            "approvers": list(approvers),
        },
    )
    assert res.is_success, res.text
    return res.json()["id"]


def _pending(client):
    rid = _create(client)
    res = client.post(f"/requests/{rid}/submit", json={"actor": "alice"})
    assert res.is_success, res.text
    return rid


def _snapshot(client):
    """登録済みの全申請（状態と監査ログを含む）。"""
    res = client.get("/requests")
    assert res.is_success, res.text
    return sorted(res.json(), key=lambda r: r["id"])


def _get(client, rid):
    res = client.get(f"/requests/{rid}")
    assert res.is_success, res.text
    return res.json()


# 各状態遷移について「この状態・この操作者なら成功する」組み合わせ。
# 未定義キーの検査で、未定義キーが無ければ通る入力であることを保証するために使う。
def _ready_for(client, action):
    """action が成功しうる状態の申請 ID と、その操作を行える actor を返す。"""
    if action == "submit":
        return _create(client), "alice"
    if action == "withdraw":
        return _create(client), "alice"
    # approve / reject / remand は PENDING の申請に現在の承認者が行う
    return _pending(client), "bob"


# ---------------------------------------------------------------------------
# 対象不在（REQ-011 / PROP-008）
# ---------------------------------------------------------------------------


def test_req011_get_unknown_request_returns_404(client):
    """REQ-011 / PROP-008: 存在しない申請の参照は 404（対象不在）。"""
    _create(client)

    res = client.get("/requests/REQ-9999")
    assert res.status_code == 404


@pytest.mark.parametrize("action", TRANSITIONS)
def test_req011_transition_on_unknown_request_returns_404_not_409(client, action):
    """UC-002〜UC-006 / REQ-011 / PROP-008: 存在しない申請への状態遷移は 404 であり 409 ではない。

    登録済みの申請の状態と監査ログは変わらない。
    """
    _create(client)
    _pending(client)
    before = _snapshot(client)

    res = client.post(f"/requests/REQ-9999/{action}", json={"actor": "alice"})

    assert res.status_code == 404, (res.status_code, res.text)
    assert _snapshot(client) == before


def test_uc003_approve_never_created_id_is_not_found(client):
    """UC-003 / REQ-011 / PROP-008（受入条件の例）: 一度も起票されていない ID の承認は対象不在。"""
    rid = _pending(client)
    before = _get(client, rid)

    res = client.post(
        "/requests/never-created/approve", json={"actor": "bob", "note": "OK"}
    )

    assert res.status_code == 404, (res.status_code, res.text)
    assert _get(client, rid) == before


@PBT
@given(
    unknown_id=st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_",
        min_size=1,
        max_size=12,
    ),
    operation=st.sampled_from(("get",) + TRANSITIONS),
    actor=st.sampled_from(("alice", "bob", "carol")),
    note=st.one_of(st.none(), st.text(max_size=20)),
)
def test_prop008_any_operation_on_unregistered_id_is_not_found(
    client, unknown_id, operation, actor, note
):
    """PROP-008 / REQ-011: 未登録の任意の ID への任意の操作は必ず 404。

    登録済みの申請の状態と監査ログは変わらない。
    """
    if not _snapshot(client):
        _create(client)
        _pending(client)
    before = _snapshot(client)
    if unknown_id in {r["id"] for r in before}:
        return  # 登録済みの ID は対象外

    if operation == "get":
        res = client.get(f"/requests/{unknown_id}")
    else:
        body = {"actor": actor}
        if note is not None:
            body["note"] = note
        res = client.post(f"/requests/{unknown_id}/{operation}", json=body)

    assert res.status_code == 404, (operation, unknown_id, res.status_code, res.text)
    assert _snapshot(client) == before


# ---------------------------------------------------------------------------
# 入力不正（REQ-012 / PROP-009）
# ---------------------------------------------------------------------------


def test_uc003_approve_with_typo_nte_returns_422_and_changes_nothing(client):
    """UC-003 / REQ-012 / PROP-009（受入条件の例）: `note` の打ち間違い `nte` は 422。

    申請の状態も監査ログも変わらない。
    """
    rid = _pending(client)
    before = _get(client, rid)

    res = client.post(
        f"/requests/{rid}/approve", json={"actor": "bob", "nte": "確認しました"}
    )

    assert res.status_code == 422, (res.status_code, res.text)
    after = _get(client, rid)
    assert after == before
    assert after["status"] == "PENDING"
    assert [e["action"] for e in after["audit_log"]] == ["CREATE", "SUBMIT"]


@pytest.mark.parametrize("action", TRANSITIONS)
def test_req012_transition_with_undefined_key_returns_422(client, action):
    """UC-002〜UC-006 / REQ-012 / PROP-009: 状態遷移の入力に未定義の項目があれば 422。

    未定義の項目が無ければ成功する入力（正しい状態・正しい操作者）で試す。
    申請の状態も監査ログも変わらない。
    """
    rid, actor = _ready_for(client, action)
    before = _snapshot(client)

    res = client.post(
        f"/requests/{rid}/{action}",
        json={"actor": actor, "note": "", "comment": "未定義の項目"},
    )

    assert res.status_code == 422, (action, res.status_code, res.text)
    assert _snapshot(client) == before


def test_uc001_create_with_undefined_key_returns_422(client):
    """UC-001 / REQ-012 / PROP-009: 起票の入力に未定義の項目があれば 422。申請は作られない。"""
    _create(client)
    before = _snapshot(client)

    res = client.post(
        "/requests",
        json={
            "applicant": "alice",
            "amount": 50000,
            "title": "備品購入",
            "approvers": ["bob"],
            "note": "起票には note は定義されていない",
        },
    )

    assert res.status_code == 422, (res.status_code, res.text)
    assert _snapshot(client) == before


_EXTRA_KEY = st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=10)
_EXTRA_VALUE = st.one_of(st.none(), st.booleans(), st.integers(), st.text(max_size=10))


@PBT
@given(
    action=st.sampled_from(TRANSITIONS),
    extra=st.dictionaries(
        _EXTRA_KEY.filter(lambda k: k not in TRANSITION_KEYS),
        _EXTRA_VALUE,
        min_size=1,
        max_size=3,
    ),
    note=st.one_of(st.none(), st.text(max_size=20)),
)
def test_prop009_transition_with_any_undefined_key_is_invalid_input(
    client, action, extra, note
):
    """PROP-009 / REQ-012: 任意の状態遷移で、未定義の項目を 1 つ以上含む入力は必ず 422。

    対象の申請の状態も監査ログも変わらない。
    """
    rid, actor = _ready_for(client, action)
    before = _get(client, rid)

    body = {"actor": actor, **extra}
    if note is not None:
        body["note"] = note
    res = client.post(f"/requests/{rid}/{action}", json=body)

    assert res.status_code == 422, (action, body, res.status_code, res.text)
    assert _get(client, rid) == before


@PBT
@given(
    extra=st.dictionaries(
        _EXTRA_KEY.filter(lambda k: k not in CREATE_KEYS),
        _EXTRA_VALUE,
        min_size=1,
        max_size=3,
    ),
)
def test_prop009_create_with_any_undefined_key_is_invalid_input(client, extra):
    """PROP-009 / REQ-012: 起票で未定義の項目を 1 つ以上含む入力は必ず 422。申請は作られない。"""
    before = _snapshot(client)

    body = {
        "applicant": "alice",
        "amount": 50000,
        "title": "申請",
        "approvers": ["bob"],
        **extra,
    }
    res = client.post("/requests", json=body)

    assert res.status_code == 422, (body, res.status_code, res.text)
    assert _snapshot(client) == before


# ---------------------------------------------------------------------------
# ルール違反は 409 のまま（区別の確認）
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("action", "actor"),
    [
        ("submit", "bob"),  # REQ-002: 申請者以外は提出できない
        ("approve", "carol"),  # REQ-008: 現在の承認者以外は承認できない
        ("reject", "carol"),  # REQ-008
        ("remand", "carol"),  # REQ-008
        ("withdraw", "bob"),  # REQ-006: 申請者以外は取下げできない
    ],
)
def test_rule_violation_on_existing_request_is_still_409(client, action, actor):
    """UC-002〜UC-006 / REQ-002, REQ-006, REQ-008 / REQ-011: 存在する申請へのルール違反は 409。

    404 / 422 とは区別される。状態と監査ログは変わらない。
    """
    rid = _create(client) if action == "submit" else _pending(client)
    before = _snapshot(client)

    res = client.post(f"/requests/{rid}/{action}", json={"actor": actor})

    assert res.status_code == 409, (action, res.status_code, res.text)
    assert _snapshot(client) == before


@pytest.mark.parametrize("action", TRANSITIONS)
def test_rule_violation_on_terminal_request_is_still_409(client, action):
    """UC-002〜UC-006 / REQ-009: 終了済みの申請への状態遷移は 409（404 ではない）。"""
    rid = _create(client)
    res = client.post(f"/requests/{rid}/withdraw", json={"actor": "alice"})
    assert res.is_success, res.text
    before = _snapshot(client)

    actor = "alice" if action in ("submit", "withdraw") else "bob"
    res = client.post(f"/requests/{rid}/{action}", json={"actor": actor})

    assert res.status_code == 409, (action, res.status_code, res.text)
    assert _snapshot(client) == before


def test_uc001_create_rule_violation_is_still_409(client):
    """UC-001 / REQ-001 / REQ-012: 定義済みの項目だけで段数が合わない起票は 409（422 ではない）。"""
    res = client.post(
        "/requests",
        json={
            "applicant": "alice",
            "amount": 300000,
            "title": "申請",
            "approvers": ["bob"],
        },
    )
    assert res.status_code == 409, (res.status_code, res.text)
    assert _snapshot(client) == []


# ---------------------------------------------------------------------------
# 判定順序（ADR-0003）: 入力不正 422 → 不在 404 → ルール違反 409
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("action", TRANSITIONS)
@pytest.mark.parametrize(
    "body",
    [
        {"actor": "alice", "nte": "打ち間違い"},  # 未定義キー
        {"note": "actor が無い"},  # 必須項目の欠落
    ],
    ids=["undefined-key", "missing-actor"],
)
def test_adr0003_invalid_body_on_unknown_id_returns_422(client, action, body):
    """REQ-011, REQ-012 / ADR-0003: 存在しない ID に不正なボディを送ると 422（404 より先）。"""
    _pending(client)
    before = _snapshot(client)

    res = client.post(f"/requests/REQ-9999/{action}", json=body)

    assert res.status_code == 422, (action, res.status_code, res.text)
    assert _snapshot(client) == before


def test_adr0003_unknown_id_takes_precedence_over_rule_violation(client):
    """REQ-011 / ADR-0003: 形の正しい入力で、存在しない ID なら 404（ルール違反の判定より先）。

    どの actor で操作しても、対象が無ければルール違反ではなく対象不在になる。
    """
    _pending(client)
    for actor in ("alice", "bob", "carol", "nobody"):
        for action in TRANSITIONS:
            res = client.post(f"/requests/REQ-9999/{action}", json={"actor": actor})
            assert res.status_code == 404, (actor, action, res.status_code)
