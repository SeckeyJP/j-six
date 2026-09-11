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
        _write(project / "reports" / "judge.json", {"verdict": "PASS", "reasons": []})
        assert runner.main(["--dir", str(project)]) == runner.EXIT_OK

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
        assert runner.main(["--dir", str(project), "--gates", "g1,g2,g4"]) == runner.EXIT_OK

    def test_excluded_gate_is_recorded_not_silently_dropped(self, project):
        """除外したゲートは「未実行」として結果に残す。黙って消さない。"""
        self._config(project)
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
