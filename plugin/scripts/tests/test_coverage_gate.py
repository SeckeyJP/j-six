"""G2: カバレッジ判定のテスト（Cobertura / LCOV）。"""
import pytest

import jsix_coverage_gate as cov


def test_cobertura(fixtures):
    data = cov.parse_coverage(fixtures / "coverage-cobertura.xml")
    assert data["format"] == "cobertura"
    assert data["line_rate"] == pytest.approx(0.8)
    assert data["per_file"]["app/main.py"] == {"covered": 1, "total": 3, "missing": [2, 3]}


def test_lcov(fixtures):
    """LCOV は DA レコードから数える（LF/LH の集計行は信用しない）。"""
    data = cov.parse_coverage(fixtures / "coverage-lcov.info")
    assert data["format"] == "lcov"
    assert data["line_rate"] == pytest.approx(4 / 5)
    assert data["per_file"]["src/workflow.ts"] == {"covered": 2, "total": 3, "missing": [3]}


def test_read_line_rate_backward_compat(fixtures):
    """v2.0 から公開している関数のシグネチャを維持する。"""
    assert cov.read_line_rate(fixtures / "coverage-cobertura.xml") == pytest.approx(0.8)


def test_threshold_pass_and_fail(fixtures):
    assert cov.check({"file": "coverage-cobertura.xml", "min": 80}, fixtures).ok
    r = cov.check({"file": "coverage-cobertura.xml", "min": 95}, fixtures)
    assert not r.ok and "不足" in r.summary


def test_no_threshold_measures_only(fixtures):
    """min 未指定は計測のみ（合格扱い）。"""
    r = cov.check({"file": "coverage-lcov.info"}, fixtures)
    assert r.ok and "計測のみ" in r.summary


def test_lowest_files_reported(fixtures):
    r = cov.check({"file": "coverage-cobertura.xml", "min": 80}, fixtures)
    assert r.findings[0]["file"] == "app/main.py"


def test_missing_file(fixtures):
    assert not cov.check({"file": "nope.xml"}, fixtures).ok


def test_optional_missing_is_skipped(fixtures):
    r = cov.check({"file": "nope.xml", "min": 95, "optional": True}, fixtures)
    assert r.ok and r.skipped


def test_missing_is_failure_by_default(fixtures):
    r = cov.check({"file": "nope.xml", "min": 95}, fixtures)
    assert not r.ok and not r.skipped


def test_missing_lines_are_reported_cobertura(fixtures):
    """網羅率の低いファイルに、未到達の行番号を添える（ROADMAP C11）。"""
    r = cov.check({"file": "coverage-cobertura.xml", "min": 80}, fixtures)
    main = next(f for f in r.findings if f["file"] == "app/main.py")
    assert main["missing"] == [2, 3]


def test_missing_lines_are_reported_lcov(fixtures):
    r = cov.check({"file": "coverage-lcov.info"}, fixtures)
    wf = next(f for f in r.findings if f["file"] == "src/workflow.ts")
    assert wf["missing"] == [3]
