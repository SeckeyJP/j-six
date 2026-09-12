"""PreToolUse の決定論的 format/lint Hook のテスト。"""
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
            "format": {"hook_cmd": "echo formatted {file} > out.txt"},
            "lint": {"hook_cmd": "echo linted {file} >> out.txt"},
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
            json.dumps({"gates": {"g1": {"format": {"hook_cmd": "touch ran.txt"}}}}), encoding="utf-8")
        import io
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "ls"}})))
        assert hook.main() == 0
        assert not (tmp_path / "ran.txt").exists()

    def test_runs_on_edit(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".jsix-checks.json").write_text(
            json.dumps({"gates": {"g1": {"format": {"hook_cmd": "touch ran.txt"}}}}), encoding="utf-8")
        import io
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
            {"tool_name": "Edit", "tool_input": {"file_path": "app/x.py"}})))
        assert hook.main() == 0
        assert (tmp_path / "ran.txt").exists()

    def test_malformed_stdin_is_noop(self, monkeypatch):
        import io
        monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
        assert hook.main() == 0
