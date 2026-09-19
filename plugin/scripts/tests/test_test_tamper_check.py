"""G2: テスト改変検出のテスト。

ハンドオフ §5 の完了条件「テストを意図的に弱めた変更が G2 で確実にブロックされる」
に対応する。実際の git リポジトリを作って検証する。
"""
import subprocess

import pytest

import jsix_test_tamper_check as tamper

BASELINE_TESTS = '''\
import pytest

from app.workflow import approve


def test_req_001_single_step():
    assert approve("a") == "APPROVED"
    assert approve("b") != "DRAFT"


def test_req_008_order_enforced():
    with pytest.raises(ValueError):
        approve(None)
    assert True
'''


def _git(repo, *args):
    subprocess.run(["git"] + list(args), cwd=str(repo), check=True,
                   capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    """RED 完了時点（jsix/red-TASK-001 タグ付き）のリポジトリを作る。"""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")

    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_workflow.py").write_text(BASELINE_TESTS, encoding="utf-8")
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "workflow.py").write_text("def approve(x):\n    return 'APPROVED'\n", encoding="utf-8")

    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "red")
    _git(tmp_path, "tag", "jsix/red-TASK-001")
    return tmp_path


def _cfg(**over):
    cfg = {"baseline_ref": "jsix/red-TASK-001", "paths": ["tests/**"], "source_paths": ["app/**"]}
    cfg.update(over)
    return cfg


def test_unchanged_passes(repo):
    r = tamper.check(_cfg(), repo)
    assert r.ok, r.summary


def test_assert_removal_blocks(repo):
    """assert を削るとブロックされる。"""
    path = repo / "tests" / "test_workflow.py"
    path.write_text(BASELINE_TESTS.replace('    assert approve("b") != "DRAFT"\n', ""), encoding="utf-8")
    r = tamper.check(_cfg(), repo)
    assert not r.ok
    assert any(f["kind"] == "assert-removed" for f in r.findings)


def test_skip_marker_blocks(repo):
    """@pytest.mark.skip を足すとブロックされる。"""
    path = repo / "tests" / "test_workflow.py"
    path.write_text(
        BASELINE_TESTS.replace("def test_req_008_order_enforced():",
                              "@pytest.mark.skip\ndef test_req_008_order_enforced():"),
        encoding="utf-8",
    )
    r = tamper.check(_cfg(), repo)
    assert not r.ok
    assert any(f["kind"] == "skip-added" for f in r.findings)


def test_xfail_marker_blocks(repo):
    path = repo / "tests" / "test_workflow.py"
    path.write_text(
        BASELINE_TESTS.replace("def test_req_001_single_step():",
                              "@pytest.mark.xfail\ndef test_req_001_single_step():"),
        encoding="utf-8",
    )
    assert not tamper.check(_cfg(), repo).ok


def test_test_deletion_blocks(repo):
    """テスト関数ごと消してもブロックされる。"""
    path = repo / "tests" / "test_workflow.py"
    path.write_text(BASELINE_TESTS.split("def test_req_008")[0], encoding="utf-8")
    r = tamper.check(_cfg(), repo)
    assert not r.ok
    assert any(f["kind"] == "test-removed" for f in r.findings)


def test_whole_test_file_deletion_blocks(repo):
    (repo / "tests" / "test_workflow.py").unlink()
    assert not tamper.check(_cfg(), repo).ok


def test_implementation_referencing_holdout_blocks(repo):
    """実装が hold-out テストを参照したらブロックされる。"""
    (repo / "tests" / "acceptance").mkdir()
    (repo / "tests" / "acceptance" / "test_uc001.py").write_text("def test_uc001():\n    assert True\n", encoding="utf-8")
    (repo / "app" / "workflow.py").write_text(
        "from tests.acceptance.test_uc001 import test_uc001\n\ndef approve(x):\n    return 'APPROVED'\n",
        encoding="utf-8",
    )
    r = tamper.check(_cfg(holdout_dir="tests/acceptance"), repo)
    assert not r.ok
    assert any(f["kind"] == "holdout-reference" for f in r.findings)


class TestRefactorIsNotBlocked:
    """REFACTOR 工程のテスト整理は止めない（弱体化パターンのみブロックする方針）。"""

    def test_rename_passes(self, repo):
        path = repo / "tests" / "test_workflow.py"
        path.write_text(BASELINE_TESTS.replace("test_req_001_single_step", "test_req_001_approves_single_step"),
                        encoding="utf-8")
        r = tamper.check(_cfg(), repo)
        assert r.ok, r.summary
        assert r.metrics["changed_test_files"] == 1

    def test_moving_tests_between_files_passes(self, repo):
        """別ファイルへ移しただけの変更を誤検知しない（総数で比較しているため）。"""
        src = repo / "tests" / "test_workflow.py"
        head, tail = src.read_text(encoding="utf-8").split("def test_req_008")
        src.write_text(head, encoding="utf-8")
        (repo / "tests" / "test_order.py").write_text(
            "import pytest\n\nfrom app.workflow import approve\n\n\ndef test_req_008" + tail,
            encoding="utf-8",
        )
        r = tamper.check(_cfg(), repo)
        assert r.ok, r.summary

    def test_adding_tests_passes(self, repo):
        path = repo / "tests" / "test_workflow.py"
        path.write_text(BASELINE_TESTS + '\n\ndef test_new_case():\n    assert approve("c") == "APPROVED"\n',
                        encoding="utf-8")
        assert tamper.check(_cfg(), repo).ok


def test_missing_baseline_tag_is_reported(repo):
    r = tamper.check(_cfg(baseline_ref="jsix/red-NOPE"), repo)
    assert not r.ok and "存在しません" in r.summary


def test_no_baseline_skips_diff_but_still_checks_holdout(repo):
    """タグが無い場合、差分検査はスキップするが hold-out 参照は見る。"""
    _git(repo, "tag", "-d", "jsix/red-TASK-001")
    r = tamper.check({"paths": ["tests/**"], "source_paths": ["app/**"]}, repo)
    assert r.ok and r.skipped


def test_baseline_resolved_from_env(repo, monkeypatch):
    monkeypatch.setenv("JSIX_TASK_ID", "TASK-001")
    assert tamper.resolve_baseline({}, repo) == "jsix/red-TASK-001"


def test_baseline_resolved_from_latest_tag(repo, monkeypatch):
    monkeypatch.delenv("JSIX_TASK_ID", raising=False)
    assert tamper.resolve_baseline({}, repo) == "jsix/red-TASK-001"


class TestScanHeuristics:
    """言語横断の検出パターン。"""

    @pytest.mark.parametrize("text,expected", [
        ("assert x == 1", 1),
        ("expect(x).toBe(1)", 1),
        ("assertEquals(a, b)", 1),
        ("EXPECT_EQ(a, b)", 1),
        ("t.Error(\"boom\")", 1),
    ])
    def test_assert_detection(self, text, expected):
        assert tamper.scan_text(text)["asserts"] == expected

    @pytest.mark.parametrize("text", [
        "@pytest.mark.skip",
        "@unittest.skipIf(True)",
        "it.skip('x', () => {})",
        "xit('x', () => {})",
        "@Ignore",
        "@Disabled",
        "t.Skip()",
        "#[ignore]",
    ])
    def test_skip_detection(self, text):
        assert tamper.scan_text(text)["skips"] >= 1

    @pytest.mark.parametrize("text", [
        "def test_foo():",
        "it('does a thing', () => {})",
        "@Test",
        "func TestFoo(t *testing.T) {",
        "#[test]",
    ])
    def test_test_function_detection(self, text):
        assert tamper.scan_text(text)["tests"] >= 1


class TestRedTagPerProject:
    """1つのリポジトリに複数プロジェクトがある場合、RED タグは自プロジェクトのものを使う。

    タグはリポジトリ共有のため、最新の jsix/red-* を無条件に使うと、別プロジェクトの
    タスクのタグを比較元に拾っていた（monthly-billing が approval-workflow の
    jsix/red-TASK-AW-002 で検査された）。
    """

    @staticmethod
    def _git(repo, *args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                       cwd=str(repo), check=True, capture_output=True)

    def _monorepo(self, tmp_path):
        for proj in ("a", "b"):
            (tmp_path / proj / "tests").mkdir(parents=True)
            (tmp_path / proj / "tests" / "test_x.py").write_text("def test_x(): pass\n", encoding="utf-8")
        self._git(tmp_path, "init", "-q")
        self._git(tmp_path, "add", "-A")
        self._git(tmp_path, "commit", "-q", "-m", "init")
        for proj, task in (("a", "TA"), ("b", "TB")):
            (tmp_path / proj / "tests" / "test_y.py").write_text("def test_y(): pass\n", encoding="utf-8")
            self._git(tmp_path, "add", "-A")
            self._git(tmp_path, "commit", "-q", "-m", f"red {task}")
            self._git(tmp_path, "tag", f"jsix/red-{task}")
        return tmp_path

    def test_uses_own_projects_tag(self, tmp_path, monkeypatch):
        monkeypatch.delenv("JSIX_TASK_ID", raising=False)
        repo = self._monorepo(tmp_path)
        assert tamper.resolve_baseline({}, repo / "a") == "jsix/red-TA"
        assert tamper.resolve_baseline({}, repo / "b") == "jsix/red-TB"

    def test_no_tag_for_untouched_project(self, tmp_path, monkeypatch):
        monkeypatch.delenv("JSIX_TASK_ID", raising=False)
        repo = self._monorepo(tmp_path)
        (repo / "c").mkdir()
        assert tamper.resolve_baseline({}, repo / "c") is None

    def test_evidence_task_id_uses_own_projects_tag(self, tmp_path, monkeypatch):
        import jsix_evidence_pack as pack

        monkeypatch.delenv("JSIX_TASK_ID", raising=False)
        repo = self._monorepo(tmp_path)
        assert pack.resolve_task_id(repo / "a") == "TA"
