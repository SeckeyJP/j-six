"""ランナーのテスト: ゲート順序・打ち切り・G3 の2段構成・no-op・後方互換。"""
import json
import shutil
import subprocess

import pytest

import jsix_run_checks as runner


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def project(tmp_path, fixtures):
    """成果物が揃った最小プロジェクト。"""
    (tmp_path / "reports").mkdir()
    shutil.copy(fixtures / "junit-pass.xml", tmp_path / "reports" / "junit.xml")
    shutil.copy(fixtures / "coverage-cobertura.xml", tmp_path / "coverage.xml")
    shutil.copy(fixtures / "sast.sarif", tmp_path / "reports" / "sast.sarif")
    shutil.copy(fixtures / "mutation-elements.json", tmp_path / "reports" / "mutation.json")

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "spec.md").write_text("REQ-001 と REQ-002 と PROP-001", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text(
        "def test_req_001():  # REQ-001 PROP-001\n    assert True\n\n"
        "def test_req_002():  # REQ-002\n    assert True\n",
        encoding="utf-8",
    )
    return tmp_path


def test_no_config_is_noop(tmp_path):
    """設定が無いプロジェクトでは何もせず 0（既存の安全な既定を維持）。"""
    assert runner.main(["--dir", str(tmp_path)]) == runner.EXIT_OK


def test_legacy_config_still_works(project, capsys):
    """v2.0 のフラット形式がそのまま動き、移行案内を出す。"""
    _write(project / ".jsix-checks.json", {
        "traceability": {"requirements": "docs/spec.md", "tests": "tests", "pattern": r"REQ-\d+"},
        "coverage": {"file": "coverage.xml", "min": 80},
    })
    assert runner.main(["--dir", str(project)]) == runner.EXIT_OK
    out = capsys.readouterr().out
    assert "traceability" in out and "coverage" in out
    assert "v2.0 の形式です" in out


def test_legacy_config_fails_the_same_way(project):
    """旧形式でも閾値未達なら v2.0 と同じく 2 で止まる。"""
    _write(project / ".jsix-checks.json", {"coverage": {"file": "coverage.xml", "min": 95}})
    assert runner.main(["--dir", str(project)]) == runner.EXIT_BLOCK


def test_gates_run_in_order(project):
    _write(project / ".jsix-checks.json", {
        "gates": {
            "g1": {"sast": {"sarif": "reports/sast.sarif", "max_severity": "note"}},
            "g2": {"coverage": {"file": "coverage.xml", "min": 80}},
        }
    })
    cfg = runner.config.load(project)
    ok, results = runner.run_gates(cfg, runner.Context(project, run_commands=False))
    assert list(results) == ["g1", "g2"]
    assert not ok


def test_later_gate_not_run_when_earlier_fails(project):
    """G1 が落ちたら G2 以降は実行しない（壊れたコードを後段に見せない）。"""
    _write(project / ".jsix-checks.json", {
        "gates": {
            "g1": {"sast": {"sarif": "reports/sast.sarif", "max_severity": "error"}},
            "g2": {"coverage": {"file": "coverage.xml", "min": 10}},
            "g3": {"agent": "scope-judge"},
        }
    })
    cfg = runner.config.load(project)
    ok, results = runner.run_gates(cfg, runner.Context(project, run_commands=False))
    assert not ok
    assert results["g1"]["status"] == "failed"
    assert results["g2"]["status"] == "not-run"
    assert results["g3"]["status"] == "not-run"
    assert results["g2"]["checks"] == {}


def test_all_pass(project, fixtures):
    shutil.copy(fixtures / "sast-clean.sarif", project / "reports" / "sast.sarif")
    _write(project / ".jsix-checks.json", {
        "gates": {
            "g1": {"sast": {"sarif": "reports/sast.sarif", "max_severity": "warning"}},
            "g2": {
                "tests": {"junit": "reports/junit.xml"},
                "coverage": {"file": "coverage.xml", "min": 80},
                "mutation": {"report": "reports/mutation.json"},
                "traceability": {"requirements": "docs/spec.md", "tests": "tests"},
            },
        }
    })
    assert runner.main(["--dir", str(project)]) == runner.EXIT_OK


@pytest.mark.parametrize("adapter,name", [
    (runner._sarif_check, "sast"), (runner._sarif_check, "secrets"),
    (runner._sarif_check, "deps"), (runner._tests_check, "tests"),
    (runner._tests_check, "holdout"),
])
def test_command_only_runs_once(project, adapter, name):
    cmd = "python3 -c 'from pathlib import Path; p=Path(\"count\"); p.write_text(p.read_text()+\"x\" if p.exists() else \"x\")'"
    result = adapter(name, {"cmd": cmd}, runner.Context(project, run_commands=True))
    assert result.ok
    assert (project / "count").read_text() == "x"


def test_coverage_command_refreshes_report_once(project):
    report = project / "coverage.xml"
    report.write_text("<coverage line-rate=\"0\"/>", encoding="utf-8")
    cmd = "python3 -c 'from pathlib import Path; Path(\"coverage.xml\").write_text(\"<coverage line-rate=\\\"0.8\\\"/>\")'"
    cfg = {"file": "coverage.xml", "min": 70, "cmd": cmd}
    assert runner._coverage_check("coverage", cfg, runner.Context(project, True)).ok
    report.write_text("<coverage line-rate=\"0\"/>", encoding="utf-8")
    assert not runner._coverage_check("coverage", cfg, runner.Context(project, False)).ok
    assert report.read_text() == '<coverage line-rate="0"/>'


def test_failed_coverage_command_cannot_use_stale_report(project):
    cfg = {"file": "coverage.xml", "min": 10, "cmd": "exit 1"}
    result = runner._coverage_check("coverage", cfg, runner.Context(project, True))
    assert not result.ok and "コマンドが失敗" in result.summary


def test_traceability_checks_both_req_and_prop(project):
    """PROP をテストに書き忘れていたら落ちる。"""
    (project / "tests" / "test_a.py").write_text(
        "def test_req_001():  # REQ-001\n    assert True\n\ndef test_req_002():  # REQ-002\n    assert True\n",
        encoding="utf-8",
    )
    _write(project / ".jsix-checks.json", {
        "gates": {"g2": {"traceability": {"requirements": "docs/spec.md", "tests": "tests"}}}
    })
    assert runner.main(["--dir", str(project)]) == runner.EXIT_BLOCK


class TestG3TwoPhase:
    """G3 は command 型 Hook から LLM を呼べないため、判定ファイルを介した2段構成にする。"""

    def _config(self, project, **g3):
        cfg = {"agent": "scope-judge", "verdict": "reports/judge.json"}
        cfg.update(g3)
        _write(project / ".jsix-checks.json", {
            "gates": {"g2": {"coverage": {"file": "coverage.xml", "min": 10}}, "g3": cfg}
        })

    def test_missing_verdict_blocks_with_instructions(self, project):
        self._config(project)
        cfg = runner.config.load(project)
        ok, results = runner.run_gates(cfg, runner.Context(project, run_commands=False))
        assert not ok
        summary = results["g3"]["checks"]["judge"]["summary"]
        assert "G3 未実施" in summary and "scope-judge" in summary

    def test_pass_verdict(self, project):
        self._config(project)
        self._git_commit_all(project)
        (project / "docs" / "spec.md").write_text("REQ-001 と REQ-002 と PROP-001\n", encoding="utf-8")
        cfg = runner.config.load(project)
        _, results = runner.run_gates(cfg, runner.Context(project, run_commands=False))
        target = results["g3"]["checks"]["judge"]["metrics"]["target"]
        _write(project / "reports" / "judge.json", {"verdict": "PASS", "reasons": [], "target": target})
        assert runner.main(["--dir", str(project)]) == runner.EXIT_OK

    def test_pass_verdict_without_git_is_not_trusted(self, project):
        self._config(project)
        _write(project / "reports" / "judge.json", {"verdict": "PASS", "reasons": []})
        cfg = runner.config.load(project)
        ok, results = runner.run_gates(cfg, runner.Context(project, run_commands=False))
        assert not ok
        assert "差分指紋が無い" in results["g3"]["checks"]["judge"]["summary"]

    @staticmethod
    def _git_commit_all(project):
        env_args = ["-c", "user.name=t", "-c", "user.email=t@example.com"]
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        subprocess.run(["git", "add", "-A"], cwd=project, check=True)
        subprocess.run(["git", *env_args, "commit", "-q", "-m", "init"], cwd=project, check=True)

    def test_no_changes_skips_g3(self, project):
        """変更の無いセッション（レビューだけ等）では判定対象が無いので G3 を求めない。

        判定ファイルが無いと毎回 scope-judge の起動を要求し、読み取りだけの作業でも
        Stop がブロックされていた（Skill のヘッドレス実行で発覚）。
        """
        self._config(project)
        self._git_commit_all(project)
        cfg = runner.config.load(project)
        ok, results = runner.run_gates(cfg, runner.Context(project, run_commands=False))
        assert ok
        judge = results["g3"]["checks"]["judge"]
        assert judge["skipped"] is True
        assert "変更なし" in judge["summary"]

    @staticmethod
    def _git(project, *args):
        env_args = ["-c", "user.name=t", "-c", "user.email=t@example.com"]
        return subprocess.run(["git", *env_args, *args], cwd=project, check=True,
                              capture_output=True, text=True).stdout.strip()

    def _feature_branch_with_commit(self, project):
        """main から切ったブランチで、変更をコミット済みにする（tdd-cycle の手順どおり）。"""
        self._config(project)
        self._git_commit_all(project)
        self._git(project, "branch", "-M", "main")
        self._git(project, "checkout", "-q", "-b", "task")
        (project / "app.py").write_text("x = 1\n", encoding="utf-8")
        self._git(project, "add", "-A")
        self._git(project, "commit", "-q", "-m", "green")

    def test_committed_changes_still_require_g3(self, project):
        """フェーズごとにコミットしても、ブランチの差分があれば G3 を求める。

        未コミットの差分だけを見ていたため、コミット後の Stop では「変更なし」になり
        G3 が素通りしていた（tdd-cycle のヘッドレス実行で発覚）。
        """
        self._feature_branch_with_commit(project)
        cfg = runner.config.load(project)
        ok, results = runner.run_gates(cfg, runner.Context(project, run_commands=False))
        assert not ok
        assert "G3 未実施" in results["g3"]["checks"]["judge"]["summary"]

    def test_judge_must_match_current_diff(self, project):
        """前のタスクや、判定後に変わったコードに対する PASS では通さない。"""
        self._feature_branch_with_commit(project)
        _write(project / "reports" / "judge.json",
               {"verdict": "PASS", "reasons": [], "target": "stale"})
        cfg = runner.config.load(project)
        ok, results = runner.run_gates(cfg, runner.Context(project, run_commands=False))
        assert not ok
        assert "古い" in results["g3"]["checks"]["judge"]["summary"]

    def test_judge_matching_target_passes(self, project):
        self._feature_branch_with_commit(project)
        cfg = runner.config.load(project)
        ctx = runner.Context(project, run_commands=False)
        _, results = runner.run_gates(cfg, ctx)
        target = results["g3"]["checks"]["judge"]["metrics"]["target"]
        assert target and target in results["g3"]["checks"]["judge"]["summary"]
        _write(project / "reports" / "judge.json",
               {"verdict": "PASS", "reasons": [], "target": target})
        ok, _ = runner.run_gates(cfg, runner.Context(project, run_commands=False))
        assert ok

    def test_fingerprint_paths_limit_what_invalidates_judge(self, project):
        """g3.fingerprint_paths を指定すると、それ以外の変更では判定が古くならない（ROADMAP C8）。

        ドキュメントだけの変更でも scope-judge の再実行が必要になり、コストがかかっていた。
        """
        self._feature_branch_with_commit(project)
        cfg_path = project / ".jsix-checks.json"
        doc = json.loads(cfg_path.read_text(encoding="utf-8"))
        doc["gates"]["g3"]["fingerprint_paths"] = ["app.py"]
        cfg_path.write_text(json.dumps(doc), encoding="utf-8")
        self._git(project, "commit", "-qam", "limit")

        def target():
            cfg = runner.config.load(project)
            _, res = runner.run_gates(cfg, runner.Context(project, run_commands=False))
            return res["g3"]["checks"]["judge"]["metrics"]["target"]

        before = target()
        (project / "docs" / "note.md").write_text("メモ\n", encoding="utf-8")
        assert target() == before
        (project / "app.py").write_text("x = 2\n", encoding="utf-8")
        assert target() != before

    def test_changes_still_require_g3(self, project):
        """変更があれば従来どおり G3 未実施で止める。"""
        self._config(project)
        self._git_commit_all(project)
        (project / "app.py").write_text("x = 1\n", encoding="utf-8")
        cfg = runner.config.load(project)
        ok, results = runner.run_gates(cfg, runner.Context(project, run_commands=False))
        assert not ok
        assert "G3 未実施" in results["g3"]["checks"]["judge"]["summary"]

    def test_reject_first_attempt_allows_auto_fix(self, project):
        self._config(project, max_auto_fix=1)
        _write(project / "reports" / "judge.json", {
            "verdict": "REJECT", "attempt": 1,
            "reasons": [{"category": "scope", "detail": "タスク外の設定ファイルを変更している"}],
        })
        cfg = runner.config.load(project)
        _, results = runner.run_gates(cfg, runner.Context(project, run_commands=False))
        judge = results["g3"]["checks"]["judge"]
        assert judge["metrics"]["escalate_to_human"] is False
        assert "再判定" in judge["summary"]

    def test_reject_second_attempt_escalates_to_human(self, project):
        """却下2回目で人間へ。"""
        self._config(project, max_auto_fix=1)
        _write(project / "reports" / "judge.json", {
            "verdict": "REJECT", "attempt": 2,
            "reasons": [{"category": "requirement", "detail": "REQ-003 が未実装"}],
        })
        cfg = runner.config.load(project)
        _, results = runner.run_gates(cfg, runner.Context(project, run_commands=False))
        judge = results["g3"]["checks"]["judge"]
        assert judge["metrics"]["escalate_to_human"] is True
        assert "人間の判断" in judge["summary"]

    def test_invalid_verdict(self, project):
        self._config(project)
        _write(project / "reports" / "judge.json", {"verdict": "MAYBE"})
        assert runner.main(["--dir", str(project)]) == runner.EXIT_BLOCK


class TestReportDriven:
    """既定はレポート駆動。Stop hook が毎ターン重いコマンドを走らせない。"""

    def test_cmd_not_executed_by_default(self, project):
        marker = project / "ran.txt"
        _write(project / ".jsix-checks.json", {
            "gates": {"g1": {"build": {"cmd": f"touch {marker}"}}}
        })
        assert runner.main(["--dir", str(project)]) == runner.EXIT_OK
        assert not marker.exists()

    def test_cmd_executed_with_flag(self, project):
        marker = project / "ran.txt"
        _write(project / ".jsix-checks.json", {
            "gates": {"g1": {"build": {"cmd": f"touch {marker}"}}}
        })
        assert runner.main(["--dir", str(project), "--run-commands"]) == runner.EXIT_OK
        assert marker.exists()

    def test_failing_cmd_blocks(self, project):
        _write(project / ".jsix-checks.json", {
            "gates": {"g1": {"lint": {"cmd": "exit 3"}}}
        })
        assert runner.main(["--dir", str(project), "--run-commands"]) == runner.EXIT_BLOCK

    def test_report_is_still_checked_without_running_cmd(self, project):
        """cmd を実行しなくても、既にある成果物は判定する。"""
        _write(project / ".jsix-checks.json", {
            "gates": {"g1": {"sast": {"cmd": "exit 1", "sarif": "reports/sast.sarif", "max_severity": "error"}}}
        })
        assert runner.main(["--dir", str(project)]) == runner.EXIT_BLOCK


def test_json_output(project, tmp_path):
    _write(project / ".jsix-checks.json", {
        "gates": {"g2": {"coverage": {"file": "coverage.xml", "min": 80}}}
    })
    out = tmp_path / "out" / "result.json"
    runner.main(["--dir", str(project), "--json", str(out)])
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["ok"] is True
    assert doc["gates"]["g2"]["checks"]["coverage"]["metrics"]["line_pct"] == 80.0


def test_broken_config_blocks(project):
    (project / ".jsix-checks.json").write_text("{ nope", encoding="utf-8")
    assert runner.main(["--dir", str(project)]) == runner.EXIT_BLOCK


def test_check_exception_becomes_failure(project, monkeypatch):
    """チェック自体が例外を投げてもランナーは落ちず、不合格として理由を残す。"""
    _write(project / ".jsix-checks.json", {
        "gates": {"g2": {"coverage": {"file": "coverage.xml", "min": 80}}}
    })
    monkeypatch.setitem(runner.CHECKS, "coverage",
                        lambda *a: (_ for _ in ()).throw(RuntimeError("boom")))
    cfg = runner.config.load(project)
    ok, results = runner.run_gates(cfg, runner.Context(project, run_commands=False))
    assert not ok
    assert "RuntimeError: boom" in results["g2"]["checks"]["coverage"]["summary"]


def test_scope_uses_git_changed_files(tmp_path, fixtures):
    """G1 スコープ検査は git の変更ファイルを見る。"""
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=str(tmp_path), check=True)
    (tmp_path / "infra").mkdir()
    (tmp_path / "infra" / "deploy.tf").write_text("resource {}", encoding="utf-8")
    _write(tmp_path / ".jsix-checks.json", {
        "gates": {"g1": {"scope": {"allow": ["app/**"]}}}
    })
    assert runner.main(["--dir", str(tmp_path)]) == runner.EXIT_BLOCK


def test_failed_command_shows_its_stderr(project, capsys):
    """コマンド失敗時は理由（stderr）まで出力する。

    「失敗した」とだけ出て理由が分からないと、CI のログを見ても何を直せばよいか
    判断できない。stderr は findings の "text" に入るため、render が拾う必要がある。
    """
    _write(project / ".jsix-checks.json", {
        "gates": {"g1": {"lint": {"cmd": "echo 'E501 line too long' >&2; exit 1"}}}
    })
    assert runner.main(["--dir", str(project), "--run-commands"]) == runner.EXIT_BLOCK
    err = capsys.readouterr().err
    assert "コマンドが失敗しました" in err
    assert "E501 line too long" in err


class TestGateSelection:
    """--gates で実行するゲートを絞る。

    外側ループ（CI）で G3（LLM judge）を外し、G1/G2/G4 だけを必須にする用途。
    CI で LLM の API キーを扱わずに済ませるため。
    """

    def _config(self, project):
        _write(project / ".jsix-checks.json", {
            "gates": {
                "g1": {"scope": {"allow": ["**"]}},
                "g2": {"coverage": {"file": "coverage.xml", "min": 10}},
                "g3": {"agent": "scope-judge", "verdict": "reports/judge.json"},
            }
        })

    def test_g3_blocks_without_selection(self, project):
        """既定では設定にあるゲートをすべて実行するため、G3 未実施で止まる。"""
        self._config(project)
        assert runner.main(["--dir", str(project)]) == runner.EXIT_BLOCK

    def test_excluding_g3_passes(self, project):
        self._config(project)
        TestG3TwoPhase._git_commit_all(project)
        assert runner.main(["--dir", str(project), "--gates", "g1,g2,g4"]) == runner.EXIT_OK

    def test_excluded_gate_is_recorded_not_silently_dropped(self, project):
        """除外したゲートは「未実行」として結果に残す。黙って消さない。"""
        self._config(project)
        TestG3TwoPhase._git_commit_all(project)
        cfg = runner.config.load(project)
        ok, results = runner.run_gates(cfg, runner.Context(project, False), only={"g1", "g2"})
        assert ok
        assert results["g3"]["status"] == "excluded"
        assert "--gates" in results["g3"]["reason"]

    def test_unknown_gate_is_rejected(self, project):
        self._config(project)
        assert runner.main(["--dir", str(project), "--gates", "g1,g9"]) == runner.EXIT_BLOCK

    def test_selection_does_not_skip_failures(self, project):
        """選択しても、対象ゲートの失敗はそのままブロックする。"""
        _write(project / ".jsix-checks.json", {
            "gates": {"g2": {"coverage": {"file": "coverage.xml", "min": 99.9}}}
        })
        assert runner.main(["--dir", str(project), "--gates", "g1,g2,g4"]) == runner.EXIT_BLOCK


def test_judge_message_uses_relative_path(project):
    """G3 の案内に実行環境の絶対パスを出さない。"""
    _write(project / ".jsix-checks.json", {
        "gates": {"g3": {"agent": "scope-judge", "verdict": "reports/evidence/judge.json"}}
    })
    cfg = runner.config.load(project)
    _, results = runner.run_gates(cfg, runner.Context(project, False))
    summary = results["g3"]["checks"]["judge"]["summary"]
    assert "reports/evidence/judge.json" in summary
    assert str(project) not in summary


class TestScopeBaseline:
    """スコープの deny（hold-out を実装側が触らない）は、RED タグ以降の変更で判定する。

    hold-out テストは同じタスクの前半で正当にコミットされる。ブランチ全体の差分で
    見ると、その追加まで違反になってしまう。
    """

    @staticmethod
    def _git(project, *args):
        env_args = ["-c", "user.name=t", "-c", "user.email=t@example.com"]
        subprocess.run(["git", *env_args, *args], cwd=project, check=True, capture_output=True)

    def _task(self, project):
        _write(project / ".jsix-checks.json", {"gates": {"g1": {"scope": {
            "allow": ["app/**", "tests/**", "docs/**", "reports/**", "coverage.xml", ".jsix-checks.json"],
            "deny": ["tests/acceptance/**"],
        }}}})
        self._git(project, "init", "-q")
        self._git(project, "add", "-A")
        self._git(project, "commit", "-q", "-m", "init")
        self._git(project, "branch", "-M", "main")
        self._git(project, "checkout", "-q", "-b", "task")
        (project / "tests" / "acceptance").mkdir()
        (project / "tests" / "acceptance" / "test_uc.py").write_text("def test_uc(): pass\n", encoding="utf-8")
        self._git(project, "add", "-A")
        self._git(project, "commit", "-q", "-m", "hold-out")
        self._git(project, "tag", "jsix/red-T1")

    def _scope(self, project):
        cfg = runner.config.load(project)
        ok, results = runner.run_gates(cfg, runner.Context(project, run_commands=False))
        return ok, results["g1"]["checks"]["scope"]["summary"]

    def test_holdout_added_before_red_is_allowed(self, project):
        self._task(project)
        (project / "app").mkdir()
        (project / "app" / "x.py").write_text("x = 1\n", encoding="utf-8")
        self._git(project, "add", "-A")
        self._git(project, "commit", "-q", "-m", "green")
        ok, summary = self._scope(project)
        assert ok, summary

    def test_committed_holdout_edit_after_red_is_denied(self, project):
        """RED 以降に hold-out を変えたら、コミット済みでも検出する。"""
        self._task(project)
        (project / "tests" / "acceptance" / "test_uc.py").write_text("def test_uc(): assert True\n", encoding="utf-8")
        self._git(project, "add", "-A")
        self._git(project, "commit", "-q", "-m", "tamper")
        ok, summary = self._scope(project)
        assert not ok
        assert "tests/acceptance/test_uc.py" in summary


class TestGateHistory:
    """ゲート失敗の履歴を残す（ROADMAP C9）。

    証跡と gate.json は最後の1回で上書きされるため、途中の失敗が残らず、
    Phase 0 の月次ループ（失敗理由を CLAUDE.md / Hook に還元）の入力にならなかった。
    """

    def _cfg(self, project, min_cov):
        _write(project / ".jsix-checks.json",
               {"gates": {"g2": {"coverage": {"file": "coverage.xml", "min": min_cov}}}})

    def _history(self, project):
        path = project / "reports" / "gate-history.jsonl"
        if not path.exists():
            return []
        return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]

    def test_failures_are_recorded(self, project):
        self._cfg(project, 100)
        runner.main(["--dir", str(project)])
        runner.main(["--dir", str(project)])
        hist = self._history(project)
        assert [h["ok"] for h in hist] == [False, False]
        assert hist[0]["failed"] == ["g2.coverage"]
        assert "at" in hist[0]

    def test_passes_are_recorded_only_on_recovery(self, project):
        self._cfg(project, 10)
        runner.main(["--dir", str(project)])
        runner.main(["--dir", str(project)])
        assert self._history(project) == []
        self._cfg(project, 100)
        runner.main(["--dir", str(project)])
        self._cfg(project, 10)
        runner.main(["--dir", str(project)])
        runner.main(["--dir", str(project)])
        assert [h["ok"] for h in self._history(project)] == [False, True]

    def test_history_path_is_configurable(self, project):
        _write(project / ".jsix-checks.json", {
            "gates": {"g2": {"coverage": {"file": "coverage.xml", "min": 100}}},
            "history": "logs/gates.jsonl",
        })
        runner.main(["--dir", str(project)])
        assert (project / "logs" / "gates.jsonl").is_file()


def test_history_keeps_failure_detail(tmp_path):
    """失敗したコマンドの出力（末尾）を履歴に残す。

    要約（「コマンドが失敗しました」）だけでは、断続的な失敗の原因を後から調べられなかった
    （Hypothesis の DeadlineExceeded による不安定なテストの調査で発覚）。
    """
    results = {"g2": {"status": "failed", "checks": {"tests": {
        "ok": False, "skipped": False, "summary": "tests: コマンドが失敗しました（exit 2）: make test",
        "findings": [{"text": "x" * 5000 + "DeadlineExceeded: Test took 250ms"}]}}}}
    runner._record_history(tmp_path, {}, results, False, "ci")
    rec = json.loads((tmp_path / "reports" / "gate-history.jsonl").read_text(encoding="utf-8"))
    detail = rec["details"]["g2.tests"]
    assert detail.endswith("DeadlineExceeded: Test took 250ms")
    assert len(detail) <= 1000


def test_unknown_check_cannot_pass_even_without_normalization(tmp_path):
    cfg = {"gates": {"g2": {"typo_test": {}}, "g3": {"agent": "scope-judge"}}}
    ok, results = runner.run_gates(cfg, runner.Context(tmp_path, run_commands=False))
    assert not ok
    assert results["g2"]["status"] == "failed"
    assert results["g2"]["checks"]["typo_test"]["skipped"] is False
    assert results["g3"]["status"] == "not-run"


def test_unknown_check_cli_blocks(tmp_path):
    _write(tmp_path / ".jsix-checks.json", {"gates": {"g2": {"typo_test": {}}}})
    assert runner.main(["--dir", str(tmp_path)]) == runner.EXIT_BLOCK


def test_empty_configuration_is_not_evidence_of_required_checks(tmp_path):
    # 既存 no-op の成功は「実行すべき必須検査を満たした」という意味ではない。
    ok, results = runner.run_gates({"gates": {}}, runner.Context(tmp_path, run_commands=False))
    assert ok
    assert results == {}
