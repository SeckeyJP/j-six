"""Existing Plugin functions against an isolated local Git fixture."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "plugin/scripts"))
import jsix_scope_check as scope
import jsix_guard_tests as guard
import jsix_config as config


def main():
    original = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="jsix-scope-") as tmp:
        root = Path(tmp)
        def git(*args):
            return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
        git("init", "-q")
        (root / "src").mkdir()
        (root / "tests/acceptance").mkdir(parents=True)
        (root / "src/add.py").write_text("value = 1\n")
        (root / "tests/acceptance/test_add.py").write_text("assert True\n")
        git("add", "src", "tests")
        git("-c", "user.name=Local fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
        cfg = dict(allow=["src/**", "tests/**"], deny=["tests/acceptance/**"], base="HEAD")
        (root / "src/add.py").write_text("value = 2\n")
        assert scope.check(cfg, root).ok
        (root / "tests/acceptance/test_add.py").write_text("assert False\n")
        blocked = scope.check(cfg, root)
        assert not blocked.ok and blocked.findings[0]["file"] == "tests/acceptance/test_add.py"
        unset = scope.check({}, root)
        assert unset.ok and unset.skipped
        try:
            config.normalize({"gates": {"g1": {"unknown_check": {}}}})
        except config.ConfigError:
            unknown_rejected = True
        else:
            unknown_rejected = False
        assert unknown_rejected
        os.chdir(root)
        try:
            assert guard.decide({"tool_name": "Read", "tool_input": {"file_path": "tests/acceptance/test_add.py"}})["decision"] == "block"
            assert guard.decide({"tool_name": "Edit", "tool_input": {"file_path": "tests/acceptance/test_add.py"}})["decision"] == "block"
            # Diagnostic only; no real bypass command or hold-out content read.
            assert guard.decide({"tool_name": "Bash", "tool_input": {"command": "synthetic-placeholder"}}) is None
            assert guard.decide({"tool_name": "Grep", "tool_input": {"path": "tests/acceptance"}}) is None
        finally:
            os.chdir(original)
        return dict(kind="local_plugin_function_and_git_observation", scope_allowed=True,
                    holdout_change_blocked=True, unset_scope="skipped", unknown_check_rejected=True,
                    hook_Read_Edit="block", hook_Bash_Grep="no_decision",
                    limitation="Hook decision function tested; not live Claude subagent activation or OS isolation. Git fixture is synthetic and discarded.")


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
