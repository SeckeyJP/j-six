"""G1: スコープ検査のテスト。"""
import jsix_scope_check as scope


class TestGlobSemantics:
    """`**` がディレクトリ境界を越え、`*` は越えないこと（fnmatch と違う点）。"""

    def test_doublestar_crosses_directories(self):
        assert scope.matches_any("src/a/b/c.py", ["src/**"])

    def test_star_does_not_cross_directories(self):
        assert scope.matches_any("src/a.py", ["src/*.py"])
        assert not scope.matches_any("src/a/b.py", ["src/*.py"])

    def test_leading_doublestar_matches_root_level(self):
        assert scope.matches_any("c.py", ["**/c.py"])
        assert scope.matches_any("a/b/c.py", ["**/c.py"])

    def test_trailing_slash_means_everything_under(self):
        assert scope.matches_any("migrations/001.sql", ["migrations/"])

    def test_question_mark(self):
        assert scope.matches_any("a1.py", ["a?.py"])
        assert not scope.matches_any("a/1.py", ["a?.py"])


def test_allow_only():
    r = scope.check({"allow": ["app/**", "tests/**"]}, changed=["app/x.py", "tests/y.py"])
    assert r.ok


def test_file_outside_allow_blocks():
    r = scope.check({"allow": ["app/**"]}, changed=["app/x.py", "infra/deploy.tf"])
    assert not r.ok
    assert r.findings == [{"file": "infra/deploy.tf", "reason": "not-in-allow", "pattern": None}]


def test_deny_wins_over_allow():
    """deny は allow より優先する（tests/** は許すが tests/acceptance/** は禁じる等）。"""
    r = scope.check(
        {"allow": ["tests/**"], "deny": ["tests/acceptance/**"]},
        changed=["tests/test_a.py", "tests/acceptance/test_uc001.py"],
    )
    assert not r.ok
    assert r.findings[0]["file"] == "tests/acceptance/test_uc001.py"
    assert r.findings[0]["reason"] == "deny"


def test_deny_only_without_allow():
    """allow 未整備でも deny だけで使える。"""
    r = scope.check({"deny": ["migrations/**"]}, changed=["app/x.py"])
    assert r.ok


def test_no_patterns_skips():
    r = scope.check({}, changed=["app/x.py"])
    assert r.ok and r.skipped


def test_metrics_recorded():
    r = scope.check({"allow": ["app/**"]}, changed=["app/a.py", "app/b.py"])
    assert r.metrics["changed_files"] == 2
    assert r.metrics["violations"] == 0


class TestPathBase:
    """glob は設定ファイルのあるディレクトリ基準。git はリポジトリルート基準なので揃える必要がある。"""

    def test_paths_are_relative_to_project_dir(self, tmp_path):
        """リポジトリ内のサブディレクトリにあるプロジェクトでも allow が効く。"""
        import subprocess

        import jsix_gitutil as git

        subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
        project = tmp_path / "examples" / "demo"
        (project / "app").mkdir(parents=True)
        (project / "app" / "x.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "other.py").write_text("y = 1\n", encoding="utf-8")

        rel = git.changed_files_relative(project)
        # プロジェクト配下だけがプロジェクト基準の相対パスで返る
        assert rel == ["app/x.py"]
        assert scope.check({"allow": ["app/**"]}, project, rel).ok

    def test_files_outside_project_are_not_judged(self, tmp_path):
        """リポジトリ内の別プロジェクトの変更は、このゲートの管轄外。"""
        import subprocess

        import jsix_gitutil as git

        subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
        project = tmp_path / "examples" / "demo"
        project.mkdir(parents=True)
        (project / "keep.py").write_text("k = 1\n", encoding="utf-8")
        (tmp_path / "plugin").mkdir()
        (tmp_path / "plugin" / "tool.py").write_text("t = 1\n", encoding="utf-8")

        assert git.changed_files_relative(project) == ["keep.py"]
