"""Git パスと比較不能の境界ケース。"""
import subprocess

import pytest

import jsix_gitutil as git
import jsix_run_checks as runner


def _git(root, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com",
                           *args], cwd=root, check=True, capture_output=True).stdout


def test_special_paths_are_not_git_quoted_or_split(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "commit", "--allow-empty", "-qm", "base")
    names = ["src/日本語.py", "src/space name.py", 'src/quote"name.py', "src/line\nbreak.py"]
    (tmp_path / "src").mkdir()
    for name in names:
        (tmp_path / name).write_text("v1\n", encoding="utf-8")
    assert git.changed_files_relative(tmp_path) == sorted(names)
    before = git.diff_fingerprint("HEAD", tmp_path)
    (tmp_path / names[0]).write_text("v2\n", encoding="utf-8")
    assert git.diff_fingerprint("HEAD", tmp_path) != before
    _git(tmp_path, "add", "-A")
    assert git.changed_files_relative(tmp_path) == sorted(names)


def test_invalid_ref_with_protected_edit_fails_closed(tmp_path):
    _git(tmp_path, "init", "-q")
    (tmp_path / "protected").mkdir()
    (tmp_path / "protected" / "case.py").write_text("safe\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "base")
    (tmp_path / "protected" / "case.py").write_text("changed\n", encoding="utf-8")
    cfg = {"gates": {"g1": {"scope": {"base": "no-such-ref", "deny": ["protected/**"]}},
                     "g3": {"agent": "scope-judge"}}}
    ok, results = runner.run_gates(cfg, runner.Context(tmp_path, False))
    assert not ok
    assert results["g1"]["status"] == "failed"
    assert "変更比較に失敗" in results["g1"]["checks"]["scope"]["summary"]
    assert results["g3"]["status"] == "not-run"


def test_non_repo_does_not_mean_no_changes(tmp_path):
    with pytest.raises(git.GitError):
        git.changed_files_relative(tmp_path)
    ok, results = runner.run_gates({"gates": {"g1": {"scope": {"deny": ["**"]}}}},
                                   runner.Context(tmp_path, False))
    assert not ok
    assert "検証できません" in results["g1"]["checks"]["scope"]["summary"]


def test_untracked_file_boundaries_change_fingerprint(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "commit", "--allow-empty", "-qm", "base")
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b.txty", encoding="utf-8")
    before = git.diff_fingerprint("HEAD", tmp_path)
    (tmp_path / "a.txt").write_text("xb.txt", encoding="utf-8")
    (tmp_path / "b.txt").write_text("y", encoding="utf-8")
    assert git.diff_fingerprint("HEAD", tmp_path) != before
