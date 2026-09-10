"""green-agent 用 PreToolUse Hook のテスト。"""
import jsix_guard_tests as guard


def _payload(tool, path):
    return {"tool_name": tool, "tool_input": {"file_path": path}}


class TestWriteGuard:
    def test_blocks_edit_in_tests(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        d = guard.decide(_payload("Edit", "tests/test_workflow.py"))
        assert d["decision"] == "block"
        assert "テスト改変検出" in d["reason"]

    def test_blocks_write_and_notebook_edit(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert guard.decide(_payload("Write", "tests/new_test.py"))
        assert guard.decide({"tool_name": "NotebookEdit", "tool_input": {"notebook_path": "tests/nb.ipynb"}})

    def test_allows_implementation(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert guard.decide(_payload("Edit", "app/workflow.py")) is None

    def test_does_not_block_lookalike_directory(self, tmp_path, monkeypatch):
        """`tests` で始まるだけの別ディレクトリを巻き込まない。"""
        monkeypatch.chdir(tmp_path)
        assert guard.decide(_payload("Edit", "testsuite_helpers/util.py")) is None


class TestHoldoutReadGuard:
    def test_blocks_reading_holdout(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        d = guard.decide(_payload("Read", "tests/acceptance/test_uc001.py"))
        assert d["decision"] == "block"
        assert "hold-out" in d["reason"]

    def test_allows_reading_normal_tests(self, tmp_path, monkeypatch):
        """RED が書いた通常のテストは読める（それを通す実装を書くため）。"""
        monkeypatch.chdir(tmp_path)
        assert guard.decide(_payload("Read", "tests/test_workflow.py")) is None

    def test_allows_reading_spec(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert guard.decide(_payload("Read", "docs/requirement-spec.md")) is None


class TestAbsolutePaths:
    def test_absolute_path_under_cwd_is_blocked(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "tests").mkdir()
        target = tmp_path / "tests" / "test_a.py"
        target.write_text("x", encoding="utf-8")
        assert guard.decide(_payload("Edit", str(target)))


class TestConfigurable:
    def test_custom_dirs(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("JSIX_TESTS_DIRS", "spec:t")
        assert guard.decide(_payload("Edit", "spec/a_spec.rb"))
        assert guard.decide(_payload("Edit", "t/b_test.go"))
        assert guard.decide(_payload("Edit", "tests/c.py")) is None


class TestFailOpen:
    """Hook の誤作動で作業を止めない。判断できない入力は通す。"""

    def test_no_path(self):
        assert guard.decide({"tool_name": "Bash", "tool_input": {"command": "ls"}}) is None

    def test_unknown_tool(self):
        assert guard.decide(_payload("Grep", "tests/test_a.py")) is None

    def test_malformed_input(self):
        assert guard.decide({"tool_name": "Edit", "tool_input": "oops"}) is None
        assert guard.decide({}) is None
