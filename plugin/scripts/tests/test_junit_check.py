"""G2: JUnit XML 判定のテスト。"""
import jsix_junit_check as junit


def test_counts_from_testsuites(fixtures):
    data = junit.parse_junit(fixtures / "junit-pass.xml")
    assert data["tests"] == 3
    assert data["failures"] == 0 and data["errors"] == 0 and data["skipped"] == 0
    assert "tests.test_workflow.test_req_001_levels" in data["test_names"]


def test_counts_from_bare_testsuite(fixtures):
    """<testsuites> でラップされていない <testsuite> 単体も読める。"""
    data = junit.parse_junit(fixtures / "junit-skipped.xml")
    assert data["tests"] == 2
    assert data["skipped"] == 1


def test_failure_and_error_block(fixtures):
    r = junit.check({"junit": "junit-fail.xml"}, fixtures)
    assert not r.ok
    assert r.metrics["failures"] == 1 and r.metrics["errors"] == 1
    assert len(r.findings) == 2


def test_pass(fixtures):
    r = junit.check({"junit": "junit-pass.xml"}, fixtures)
    assert r.ok
    assert r.metrics["tests"] == 3


def test_skip_is_allowed_by_default(fixtures):
    assert junit.check({"junit": "junit-skipped.xml"}, fixtures).ok


def test_max_skipped_blocks_added_skips(fixtures):
    """テストを skip で黙らせる操作を検出できる。"""
    r = junit.check({"junit": "junit-skipped.xml", "max_skipped": 0}, fixtures)
    assert not r.ok
    assert "スキップ" in r.summary
    assert r.findings[0]["kind"] == "skipped"


def test_min_tests_blocks_shrinking_suite(fixtures):
    r = junit.check({"junit": "junit-pass.xml", "min_tests": 10}, fixtures)
    assert not r.ok


def test_missing_file(fixtures):
    r = junit.check({"junit": "nope.xml"}, fixtures)
    assert not r.ok and "見つかりません" in r.summary


def test_missing_config(fixtures):
    r = junit.check({}, fixtures)
    assert not r.ok and "junit" in r.summary


def test_label_distinguishes_holdout(fixtures):
    """通常テストと hold-out 受入テストを同じロジックで判定しつつ、出力で区別できる。"""
    r = junit.check({"junit": "junit-pass.xml"}, fixtures, label="holdout")
    assert r.summary.startswith("holdout:")
    assert junit.check({"junit": "junit-pass.xml"}, fixtures).summary.startswith("tests:")


def test_non_junit_root_is_rejected(tmp_path):
    (tmp_path / "wrong.xml").write_text("<report/>", encoding="utf-8")
    assert not junit.check({"junit": "wrong.xml"}, tmp_path).ok


def test_suite_error_without_testcase_is_rejected(tmp_path):
    (tmp_path / "suite.xml").write_text(
        '<testsuite tests="0" errors="1"><error message="setup failed"/></testsuite>', encoding="utf-8")
    assert not junit.check({"junit": "suite.xml"}, tmp_path).ok


def test_count_mismatch_is_rejected_but_empty_suite_is_valid(tmp_path):
    path = tmp_path / "suite.xml"
    path.write_text('<testsuite tests="2"><testcase name="one"/></testsuite>', encoding="utf-8")
    assert not junit.check({"junit": "suite.xml"}, tmp_path).ok
    path.write_text('<testsuite tests="0"/>', encoding="utf-8")
    assert junit.check({"junit": "suite.xml"}, tmp_path).ok
