"""PostToolUse の決定論的 format/lint Hook のテスト。"""
import json

import jsix_format_hook as hook


def test_noop_without_config(tmp_path):
    """設定が無いプロジェクトでは何もしない。"""
    assert hook.run_for_file("app/x.py", tmp_path) == []


def test_noop_without_hook_cmd(tmp_path):
    """cmd はあっても hook_cmd が無ければ実行しない（Stop 時の判定用と区別する）。"""
    (tmp_path / ".jsix-checks.json").write_text(
        json.dumps({"gates": {"g1": {"format": {"cmd": "make format"}}}}), encoding="utf-8")
    assert hook.run_for_file("app/x.py", tmp_path) == []


def test_runs_declared_commands_with_file_substitution(tmp_path):
    (tmp_path / ".jsix-checks.json").write_text(
        json.dumps({"gates": {"g1": {
            "format": {"hook_cmd": "echo formatted {file} > out.txt", "hook_files": ["*.py"]},
            "lint": {"hook_cmd": "echo linted {file} >> out.txt", "hook_files": ["*.py"]},
        }}}), encoding="utf-8")
    results = hook.run_for_file("app/x.py", tmp_path)
    assert [r["exit_code"] for r in results] == [0, 0]
    assert (tmp_path / "out.txt").read_text() == "formatted app/x.py\nlinted app/x.py\n"


def test_legacy_config_is_noop(tmp_path):
    """v2.0 のフラット形式には g1 が無いので何もしない。"""
    (tmp_path / ".jsix-checks.json").write_text(
        json.dumps({"coverage": {"file": "coverage.xml", "min": 95}}), encoding="utf-8")
    assert hook.run_for_file("app/x.py", tmp_path) == []


def test_broken_config_is_noop(tmp_path):
    """設定が壊れていても Hook で作業を止めない。"""
    (tmp_path / ".jsix-checks.json").write_text("{ broken", encoding="utf-8")
    assert hook.run_for_file("app/x.py", tmp_path) == []


class TestPayloadHandling:
    def test_ignores_non_edit_tools(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".jsix-checks.json").write_text(
            json.dumps({"gates": {"g1": {"format": {"hook_cmd": "touch ran.txt", "hook_files": ["*.py"]}}}}), encoding="utf-8")
        import io
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "ls"}})))
        assert hook.main() == 0
        assert not (tmp_path / "ran.txt").exists()

    def test_runs_on_edit(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".jsix-checks.json").write_text(
            json.dumps({"gates": {"g1": {"format": {"hook_cmd": "touch ran.txt", "hook_files": ["*.py"]}}}}), encoding="utf-8")
        import io
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
            {"tool_name": "Edit", "tool_input": {"file_path": "app/x.py"}})))
        assert hook.main() == 0
        assert (tmp_path / "ran.txt").exists()

    def test_malformed_stdin_is_noop(self, monkeypatch):
        import io
        monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
        assert hook.main() == 0


class TestTargetFiles:
    """整形するファイルはプロジェクトが hook_files で宣言する。

    拡張子を見ずに ruff format を実行していたため、reports/evidence/judge.json を
    Python として整形し（末尾カンマ）、JSON を壊していた（Skill のヘッドレス実行で発覚）。
    """

    def _config(self, tmp_path, **fmt):
        cfg = {"hook_cmd": "echo {file} >> out.txt"}
        cfg.update(fmt)
        (tmp_path / ".jsix-checks.json").write_text(
            json.dumps({"gates": {"g1": {"format": cfg}}}), encoding="utf-8")

    def test_skips_files_outside_hook_files(self, tmp_path):
        self._config(tmp_path, hook_files=["*.py"])
        assert hook.run_for_file("reports/evidence/judge.json", tmp_path) == []
        assert hook.run_for_file(str(tmp_path / "docs" / "spec.md"), tmp_path) == []
        assert not (tmp_path / "out.txt").exists()

    def test_runs_on_matching_files(self, tmp_path):
        self._config(tmp_path, hook_files=["*.py"])
        assert len(hook.run_for_file(str(tmp_path / "app" / "x.py"), tmp_path)) == 1

    def test_directory_patterns_match_relative_path(self, tmp_path):
        self._config(tmp_path, hook_files=["app/*.py"])
        assert len(hook.run_for_file(str(tmp_path / "app" / "x.py"), tmp_path)) == 1
        assert hook.run_for_file(str(tmp_path / "tests" / "t.py"), tmp_path) == []

    def test_without_hook_files_is_noop(self, tmp_path):
        """対象が宣言されていなければ何もしない（どの言語のファイルか plugin は知らない）。"""
        self._config(tmp_path)
        assert hook.run_for_file("app/x.py", tmp_path) == []


def test_registered_as_post_tool_use():
    """整形は編集の後に行う。

    PreToolUse で編集前のファイルを整形すると、直後の Edit の置換対象が一致しなくなったり、
    Write が「読んだ後に変更された」で失敗したりする。
    """
    from pathlib import Path

    hooks = json.loads((Path(hook.__file__).resolve().parent.parent / "hooks" / "hooks.json")
                       .read_text(encoding="utf-8"))["hooks"]
    commands = lambda event: [h.get("command", "") for e in hooks.get(event, []) for h in e["hooks"]]  # noqa: E731
    assert any("jsix_format_hook.py" in c for c in commands("PostToolUse"))
    assert not any("jsix_format_hook.py" in c for c in commands("PreToolUse"))
