"""G1: SARIF 集計と閾値判定のテスト。"""
import jsix_sarif_gate as sarif


def test_level_falls_back_to_rule_default(fixtures):
    """result.level が無い場合は rule.defaultConfiguration.level を使う。"""
    data = sarif.parse_sarif(fixtures / "sast.sarif")
    assert data["counts"]["error"] == 1   # B105
    assert data["counts"]["note"] == 1    # B404
    assert data["counts"]["warning"] == 0


def test_suppressed_results_excluded(fixtures):
    data = sarif.parse_sarif(fixtures / "sast.sarif")
    assert data["suppressed"] == 1


def test_tool_name_and_version_recorded(fixtures):
    """証跡の再現情報としてツール名と版を残す。"""
    data = sarif.parse_sarif(fixtures / "sast.sarif")
    assert data["tools"] == [{"name": "bandit", "version": "1.8.6"}]


def test_threshold_error_blocks(fixtures):
    r = sarif.check({"sarif": "sast.sarif", "max_severity": "error"}, fixtures)
    assert not r.ok and r.metrics["error"] == 1


def test_threshold_note_blocks_more(fixtures):
    r = sarif.check({"sarif": "sast.sarif", "max_severity": "note"}, fixtures)
    assert not r.ok
    assert len(r.findings) == 2


def test_clean_report_passes(fixtures):
    r = sarif.check({"sarif": "sast-clean.sarif", "max_severity": "note"}, fixtures)
    assert r.ok


def test_no_threshold_counts_only(fixtures):
    r = sarif.check({"sarif": "sast.sarif"}, fixtures)
    assert r.ok and "集計のみ" in r.summary


def test_invalid_severity(fixtures):
    r = sarif.check({"sarif": "sast.sarif", "max_severity": "critical"}, fixtures)
    assert not r.ok and "max_severity が不正" in r.summary


def test_not_sarif(fixtures):
    r = sarif.check({"sarif": "mutation-minimal.json"}, fixtures)
    assert not r.ok and "SARIF ではありません" in r.summary
