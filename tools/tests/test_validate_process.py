"""tools/validate_process.py のテスト。

実データ（process/jsix-process.yaml）が通ることと、スキーマでは表せない参照整合性の
規則ごとに、壊したデータがその規則のエラーで落ちることを確かめる。
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import validate_process as vp  # noqa: E402


@pytest.fixture(scope="module")
def base() -> dict:
    return vp.load_yaml(vp.DEFAULT_PROCESS)


@pytest.fixture
def data(base: dict) -> dict:
    return copy.deepcopy(base)


def find(items: list[dict], item_id: str) -> dict:
    return next(x for x in items if x["id"] == item_id)


def errors_of(data: dict) -> list[str]:
    return vp.validate(data, vp.load_schema(vp.DEFAULT_SCHEMA))


def assert_error(data: dict, fragment: str) -> None:
    errors = errors_of(data)
    assert any(fragment in e for e in errors), f"{fragment!r} を含むエラーがない: {errors}"


# --- 実データ ---------------------------------------------------------------

def test_real_process_definition_is_valid(data):
    assert errors_of(data) == []


def test_cli_returns_zero_for_real_file():
    assert vp.main([]) == 0


def test_cli_returns_one_for_invalid_file(tmp_path, base):
    broken = copy.deepcopy(base)
    del broken["phases"]
    path = tmp_path / "broken.yaml"
    path.write_text(vp.yaml.safe_dump(broken, allow_unicode=True), encoding="utf-8")
    assert vp.main([str(path)]) == 1


# --- スキーマ ---------------------------------------------------------------

def test_schema_rejects_missing_required_field(data):
    del find(data["phases"], "P1")["gate"]
    assert_error(data, "schema:")


def test_schema_rejects_unknown_origin(data):
    find(data["roles"], "architect")["origin"] = "somewhere"
    assert_error(data, "schema:")


def test_yaml_boolean_key_is_rejected(tmp_path):
    # YAML 1.1 では `on:` が真偽値のキーになる。遷移の条件に使うと気づかず壊れるため検出する
    text = vp.DEFAULT_PROCESS.read_text(encoding="utf-8")
    assert text.count(", condition: customer_approval}") == 1
    path = tmp_path / "on.yaml"
    path.write_text(text.replace(", condition: customer_approval}", ", on: customer_approval}"), encoding="utf-8")
    data = vp.load_yaml(path)
    assert True in data["transitions"][0]
    assert_error(data, "schema: transitions/0")


# --- 参照整合性 -------------------------------------------------------------

def test_duplicate_ids_are_rejected(data):
    data["roles"].append(copy.deepcopy(find(data["roles"], "architect")))
    assert_error(data, "roles: ID が重複")


def test_phase_gate_must_exist(data):
    find(data["phases"], "P1")["gate"] = "no_such_gate"
    assert_error(data, "P1: gate 'no_such_gate' が gates にない")


def test_gate_phase_must_point_back(data):
    find(data["gates"], "design_review")["phase"] = "P1"
    assert_error(data, "design_review: phase 'P1' のゲートではない")


def test_every_gate_is_used_by_a_phase(data):
    find(data["phases"], "P5")["gate"] = None
    assert_error(data, "quality_acceptance: どの Phase からも参照されていない")


def test_phase_artifacts_must_exist(data):
    find(data["phases"], "P2")["outputs"].append("no_such_artifact")
    assert_error(data, "P2: 成果物 'no_such_artifact' が artifacts にない")


def test_phase_autonomy_must_exist(data):
    find(data["phases"], "P2")["autonomy"] = ["L9"]
    assert_error(data, "P2: 自律度 'L9' が autonomy_levels にない")


def test_check_kind_must_exist(data):
    gate = find(data["gates"], "task_quality_gate")
    gate["layers"][0]["checks"][0]["kind"] = "no_such_kind"
    assert_error(data, "task_quality_gate/G1/build: kind 'no_such_kind' が check_kinds にない")


def test_human_approval_requires_approver_roles(data):
    check = find(data["gates"], "customer_approval")["layers"][0]["checks"][0]
    del check["approver_roles"]
    assert_error(data, "customer_approval/agreement/agreement_maturity: 人間承認に approver_roles がない")


def test_approver_roles_must_exist(data):
    check = find(data["gates"], "customer_approval")["layers"][0]["checks"][0]
    check["approver_roles"] = ["nobody"]
    assert_error(data, "customer_approval/agreement/agreement_maturity: 役割 'nobody' が roles にない")


def test_approver_roles_must_be_human(data):
    check = find(data["gates"], "customer_approval")["layers"][0]["checks"][0]
    check["approver_roles"] = ["ai_agent"]
    assert_error(data, "customer_approval/agreement/agreement_maturity: 承認者 'ai_agent' が人間の役割ではない")


def test_deviation_approver_roles_must_exist(data):
    find(data["deviations"], "gate_exception")["approver_roles"] = ["nobody"]
    assert_error(data, "gate_exception: 役割 'nobody' が roles にない")


def test_task_scope_gate_has_no_human_approval(data):
    # 人間承認は Phase 境界に限定する（concept.md §3）
    gate = find(data["gates"], "task_quality_gate")
    gate["layers"][0]["checks"].append(
        {"id": "manual", "name": "手動承認", "kind": "human_approval", "approver_roles": ["gatekeeper"]}
    )
    assert_error(data, "task_quality_gate: タスク単位のゲートに人間承認がある")


def test_task_scope_gate_must_belong_to_per_task_phase(data):
    find(data["phases"], "P4")["mode"] = "sequential"
    assert_error(data, "task_quality_gate: タスク単位のゲートが per_task の Phase にない")


def test_transition_phases_must_exist(data):
    data["transitions"].append({"from": "P6", "to": "P9", "condition": "deliverable_review"})
    assert_error(data, "遷移 P6→P9: Phase 'P9' が phases にない")


def test_transition_condition_must_be_gate_of_from_phase(data):
    find_t = next(t for t in data["transitions"] if t["from"] == "P1")
    find_t["condition"] = "design_review"
    assert_error(data, "遷移 P1→P2: 条件 'design_review' は P1 のゲートではない")


def test_state_machine_references_must_exist(data):
    sm = find(data["state_machines"], "task")
    sm["transitions"].append({"from": "done", "to": "nowhere"})
    assert_error(data, "task: 状態 'nowhere' が states にない")


def test_state_machine_initial_must_exist(data):
    find(data["state_machines"], "phase")["initial"] = "nowhere"
    assert_error(data, "phase: 初期状態 'nowhere' が states にない")


def test_state_machine_deviation_must_exist(data):
    sm = find(data["state_machines"], "task")
    sm["transitions"].append({"from": "failed", "to": "done", "via_deviation": "no_such"})
    assert_error(data, "task: 逸脱 'no_such' が deviations にない")


def test_every_state_is_reachable(data):
    sm = find(data["state_machines"], "task")
    sm["states"].append({"id": "orphan", "name": "孤立"})
    assert_error(data, "task: 状態 'orphan' に到達できない")


def test_jsix_origin_must_cite_jsix_md(data):
    # origin: jsix なら出典は J-SIX.md。照合の手がかりを失わないため
    find(data["artifacts"], "code")["source"] = "concept.md §4"
    assert_error(data, "code: origin が jsix なのに source が J-SIX.md を指していない")
