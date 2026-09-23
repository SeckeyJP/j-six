"""設定の正規化と v2.0 後方互換のテスト。

`.jsix-checks.json` を v2.0 のフラット形式のまま使っているプロジェクトを壊さないこと。
"""
import json

import pytest

import jsix_config as config


def test_legacy_detected(fixtures):
    raw = json.loads((fixtures / "checks-legacy.json").read_text())
    assert config.is_legacy(raw)


def test_legacy_maps_to_g2(fixtures):
    raw = json.loads((fixtures / "checks-legacy.json").read_text())
    cfg = config.normalize(raw)
    assert cfg["_legacy"] is True
    assert set(cfg["gates"]) == {"g2"}
    assert set(cfg["gates"]["g2"]) == {"traceability", "coverage"}


def test_legacy_pattern_becomes_ids(fixtures):
    """v2.0 の pattern（単一文字列）は v2.1 の ids（リスト）へ移す。"""
    raw = json.loads((fixtures / "checks-legacy.json").read_text())
    cfg = config.normalize(raw)
    tr = cfg["gates"]["g2"]["traceability"]
    assert tr["ids"] == [r"REQ-\d+"]
    assert "pattern" not in tr


def test_legacy_does_not_invent_checks(fixtures):
    """旧形式に無いチェック（mutation / scope 等）を勝手に増やさない。"""
    raw = json.loads((fixtures / "checks-legacy.json").read_text())
    cfg = config.normalize(raw)
    assert "g1" not in cfg["gates"]
    assert "mutation" not in cfg["gates"]["g2"]


def test_legacy_without_pattern_pins_v20_default():
    """pattern 未指定の旧形式は v2.0 の既定（REQ-\\d+ のみ）に固定する。

    v2.1 の既定は REQ と PROP の両方だが、それを旧形式に適用すると、Spec に
    PROP-nnn を書いた既存利用者のゲートが突然落ちる。回帰を防ぐための固定。
    """
    cfg = config.normalize({"traceability": {"requirements": "a.md", "tests": "tests"}})
    assert cfg["gates"]["g2"]["traceability"]["ids"] == [r"REQ-\d+"]


def test_v21_without_ids_checks_both_req_and_prop():
    """新形式で ids 未指定なら REQ と PROP の両方を見る（v2.1 の既定）。"""
    import jsix_traceability_check as tr
    assert tr._patterns_from({}) == [r"REQ-\d+", r"PROP-\d+"]


def test_v21_format(fixtures):
    raw = json.loads((fixtures / "checks-v21.json").read_text())
    cfg = config.normalize(raw)
    assert cfg["_legacy"] is False
    assert set(cfg["gates"]) == {"g1", "g2", "g3", "g4"}


def test_unknown_gate_rejected():
    with pytest.raises(config.ConfigError, match="未知のゲート"):
        config.normalize({"gates": {"g9": {}}})


def test_non_object_rejected():
    with pytest.raises(config.ConfigError):
        config.normalize([1, 2, 3])


def test_iter_checks_is_ordered(fixtures):
    """G1 → G2 → G3 → G4、ゲート内も定義順に並ぶ。"""
    cfg = config.normalize(json.loads((fixtures / "checks-v21.json").read_text()))
    order = [(g, n) for g, n, _ in config.iter_checks(cfg)]
    assert order == [
        ("g1", "lint"), ("g1", "sast"), ("g1", "scope"),
        ("g2", "tests"), ("g2", "coverage"), ("g2", "traceability"),
        ("g3", "judge"),
        ("g4", "evidence"),
    ]


def test_g3_g4_configs_are_passed_whole(fixtures):
    """g3 / g4 はチェック名で入れ子にしないため、ゲート設定をそのまま渡す。"""
    cfg = config.normalize(json.loads((fixtures / "checks-v21.json").read_text()))
    checks = {(g, n): c for g, n, c in config.iter_checks(cfg)}
    assert checks[("g3", "judge")]["agent"] == "scope-judge"
    assert checks[("g3", "judge")]["max_auto_fix"] == 1
    assert checks[("g4", "evidence")]["out"] == "reports/evidence/"


def test_g3_nested_form_also_works():
    """明示的に judge で入れ子にした書き方も受け付ける。"""
    cfg = config.normalize({"gates": {"g3": {"judge": {"agent": "custom-judge"}}}})
    checks = {(g, n): c for g, n, c in config.iter_checks(cfg)}
    assert checks[("g3", "judge")] == {"agent": "custom-judge"}


def test_load_returns_none_when_absent(tmp_path):
    """未設定プロジェクトでは None（＝ Hook を no-op にする）。"""
    assert config.load(tmp_path) is None


def test_load_reports_bad_json(tmp_path):
    (tmp_path / config.CONFIG_NAME).write_text("{ not json", encoding="utf-8")
    with pytest.raises(config.ConfigError, match="解析に失敗"):
        config.load(tmp_path)


@pytest.mark.parametrize("gate", ["g1", "g2"])
def test_unknown_check_is_configuration_error(gate):
    with pytest.raises(config.ConfigError, match="未知のチェック"):
        config.normalize({"gates": {gate: {"typo_test": {}}}})
