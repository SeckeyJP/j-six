"""process/jsix-process.yaml を検証する。

JSON Schema（process/jsix-process.schema.json）で構造を検査したうえで、スキーマでは表せない
参照整合性（存在しない Phase・ゲート・役割・成果物・状態を指していないか）と、
J-SIX の設計原則から来る規則（人間承認は Phase 境界だけ、など）を検査する。

使い方:
    python3 tools/validate_process.py                 # 既定のファイルを検証
    python3 tools/validate_process.py path/to/x.yaml  # 任意のファイルを検証
終了コード: 0 = 問題なし / 1 = エラーあり

依存: PyYAML, jsonschema
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROCESS = ROOT / "process" / "jsix-process.yaml"
DEFAULT_SCHEMA = ROOT / "process" / "jsix-process.schema.json"

#: Phase 間の遷移で、ゲート以外に使える条件
SPECIAL_CONDITIONS = {"all_tasks_done"}


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_schema(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate(data: dict, schema: dict) -> list[str]:
    """エラーメッセージの一覧を返す。空なら問題なし。"""
    validator = jsonschema.Draft202012Validator(schema)
    # JSON Schema はキーを文字列として扱う。YAML 1.1 の `on:` は True になり、ここで検出される
    schema_errors = [
        f"schema: {'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}"
        for e in sorted(validator.iter_errors(data), key=lambda e: list(map(str, e.absolute_path)))
    ]
    if schema_errors:
        # 構造が壊れていると参照の検査は誤った指摘を量産するため、ここで止める
        return schema_errors
    return _check_references(data)


def _ids(items: list[dict]) -> set[str]:
    return {x["id"] for x in items}


def _duplicates(label: str, items: list[dict]) -> list[str]:
    counts = Counter(x["id"] for x in items)
    return [f"{label}: ID が重複している: '{i}'" for i, n in counts.items() if n > 1]


def _check_references(data: dict) -> list[str]:
    errors: list[str] = []
    for key in ("roles", "artifacts", "check_kinds", "gates", "phases", "autonomy_levels",
                "state_machines", "escalation_conditions", "deviations"):
        errors += _duplicates(key, data[key])

    errors += _check_phases_and_gates(data)
    errors += _check_gate_checks(data)
    errors += _check_transitions(data)
    errors += _check_state_machines(data)
    errors += _check_deviations(data)
    errors += _check_origins(data)
    return errors


def _check_phases_and_gates(data: dict) -> list[str]:
    errors: list[str] = []
    gates = {g["id"]: g for g in data["gates"]}
    artifacts = _ids(data["artifacts"])
    levels = _ids(data["autonomy_levels"])
    used_gates: set[str] = set()

    for p in data["phases"]:
        gate_id = p["gate"]
        if gate_id is not None:
            used_gates.add(gate_id)
            if gate_id not in gates:
                errors.append(f"{p['id']}: gate '{gate_id}' が gates にない")
        for a in p.get("inputs", []) + p["outputs"]:
            if a not in artifacts:
                errors.append(f"{p['id']}: 成果物 '{a}' が artifacts にない")
        for lv in p["autonomy"]:
            if lv not in levels:
                errors.append(f"{p['id']}: 自律度 '{lv}' が autonomy_levels にない")

    phases = {p["id"]: p for p in data["phases"]}
    for g in data["gates"]:
        owner = phases.get(g["phase"])
        if owner is None or owner["gate"] != g["id"]:
            errors.append(f"{g['id']}: phase '{g['phase']}' のゲートではない")
        if g["id"] not in used_gates:
            errors.append(f"{g['id']}: どの Phase からも参照されていない")
        if g["scope"] == "task" and (owner is None or owner["mode"] != "per_task"):
            errors.append(f"{g['id']}: タスク単位のゲートが per_task の Phase にない")
    return errors


def _check_gate_checks(data: dict) -> list[str]:
    errors: list[str] = []
    kinds = _ids(data["check_kinds"])
    roles = {r["id"]: r for r in data["roles"]}
    for g in data["gates"]:
        for layer in g["layers"]:
            for c in layer["checks"]:
                where = f"{g['id']}/{layer['id']}/{c['id']}"
                if c["kind"] not in kinds:
                    errors.append(f"{where}: kind '{c['kind']}' が check_kinds にない")
                if c["kind"] == "human_approval":
                    if g["scope"] == "task":
                        # 人間承認は Phase 境界に限定する（concept.md §3）
                        errors.append(f"{g['id']}: タスク単位のゲートに人間承認がある（{where}）")
                    if "approver_roles" not in c:
                        errors.append(f"{where}: 人間承認に approver_roles がない")
                for r in c.get("approver_roles", []):
                    if r not in roles:
                        errors.append(f"{where}: 役割 '{r}' が roles にない")
                    elif roles[r]["kind"] != "human":
                        errors.append(f"{where}: 承認者 '{r}' が人間の役割ではない")
    return errors


def _check_transitions(data: dict) -> list[str]:
    errors: list[str] = []
    phases = {p["id"]: p for p in data["phases"]}
    for t in data["transitions"]:
        where = f"遷移 {t['from']}→{t['to']}"
        for end in (t["from"], t["to"]):
            if end not in phases:
                errors.append(f"{where}: Phase '{end}' が phases にない")
        src = phases.get(t["from"])
        cond = t["condition"]
        if src is not None and cond not in SPECIAL_CONDITIONS and cond != src["gate"]:
            errors.append(f"{where}: 条件 '{cond}' は {t['from']} のゲートではない")
    return errors


def _check_state_machines(data: dict) -> list[str]:
    errors: list[str] = []
    deviations = _ids(data["deviations"])
    for sm in data["state_machines"]:
        states = _ids(sm["states"])
        errors += _duplicates(f"{sm['id']}.states", sm["states"])
        if sm["initial"] not in states:
            errors.append(f"{sm['id']}: 初期状態 '{sm['initial']}' が states にない")
        for t in sm["transitions"]:
            for end in (t["from"], t["to"]):
                if end not in states:
                    errors.append(f"{sm['id']}: 状態 '{end}' が states にない")
            dev = t.get("via_deviation")
            if dev is not None and dev not in deviations:
                errors.append(f"{sm['id']}: 逸脱 '{dev}' が deviations にない")
        reachable = _reachable(sm["initial"], sm["transitions"])
        for s in sorted(states - reachable):
            errors.append(f"{sm['id']}: 状態 '{s}' に到達できない")
    return errors


def _reachable(initial: str, transitions: list[dict]) -> set[str]:
    seen = {initial}
    frontier = [initial]
    while frontier:
        cur = frontier.pop()
        for t in transitions:
            if t["from"] == cur and t["to"] not in seen:
                seen.add(t["to"])
                frontier.append(t["to"])
    return seen


def _check_deviations(data: dict) -> list[str]:
    errors: list[str] = []
    roles = _ids(data["roles"])
    for d in data["deviations"]:
        for r in d.get("approver_roles", []):
            if r not in roles:
                errors.append(f"{d['id']}: 役割 '{r}' が roles にない")
    return errors


def _check_origins(data: dict) -> list[str]:
    """origin: jsix の要素は J-SIX.md を出典にしているか。照合の手がかりを失わないため。"""
    errors: list[str] = []
    items: list[dict] = []
    for key in ("roles", "artifacts", "gates", "phases", "state_machines",
                "escalation_conditions", "deviations"):
        items += data[key]
    for g in data["gates"]:
        for layer in g["layers"]:
            items += [c for c in layer["checks"] if "origin" in c]
    for x in items:
        if x.get("origin") == "jsix" and "J-SIX.md" not in x.get("source", ""):
            errors.append(f"{x['id']}: origin が jsix なのに source が J-SIX.md を指していない")
    return errors


def main(argv: list[str]) -> int:
    path = Path(argv[0]) if argv else DEFAULT_PROCESS
    errors = validate(load_yaml(path), load_schema(DEFAULT_SCHEMA))
    for e in errors:
        print(e, file=sys.stderr)
    if errors:
        print(f"NG: {path} にエラーが {len(errors)} 件ある", file=sys.stderr)
        return 1
    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
