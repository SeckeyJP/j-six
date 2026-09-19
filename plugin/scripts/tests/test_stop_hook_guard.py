"""Stop hook として呼ばれたときの、同じ失敗の繰り返しブロック防止。

ゲートが工程上まだ満たせない状態（例: Spec に REQ を追加した直後で、テストは次の工程で
書く）だと、Stop のたびに同じ失敗でブロックし続け、セッションが終わらなかった
（spec-create のヘッドレス実行で15回ブロック）。同じ失敗が続いたら停止を許可し、
ゲートは未達のまま残す。判定を緩めるのではなく、Hook でのループを止めるだけである。
"""
import io
import json

import pytest

import jsix_run_checks as runner


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def failing_project(tmp_path, fixtures, monkeypatch):
    """カバレッジ閾値を満たさず必ず失敗するプロジェクト。"""
    import shutil

    shutil.copy(fixtures / "coverage-cobertura.xml", tmp_path / "coverage.xml")
    _write(tmp_path / ".jsix-checks.json", {"gates": {"g2": {"coverage": {"file": "coverage.xml", "min": 100}}}})
    monkeypatch.setattr(runner, "stop_state_dir", lambda: tmp_path / "state")
    return tmp_path


def _stop(monkeypatch, project, active, session="s1", extra=()):
    payload = {"session_id": session, "stop_hook_active": active, "hook_event_name": "Stop"}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    return runner.main(["--dir", str(project), "--stop-hook", *extra])


def test_first_failure_blocks(failing_project, monkeypatch):
    assert _stop(monkeypatch, failing_project, active=False) == runner.EXIT_BLOCK


def test_identical_failures_are_released_after_limit(failing_project, monkeypatch, capsys):
    """既定では同じ失敗で3回まで止め、4回目の停止は許可する。"""
    codes = [_stop(monkeypatch, failing_project, active=i > 0) for i in range(4)]
    assert codes == [runner.EXIT_BLOCK] * 3 + [runner.EXIT_OK]
    out = capsys.readouterr().out
    assert "同じ失敗" in out and "未達" in out


def test_progress_resets_the_count(failing_project, monkeypatch):
    """失敗内容が変われば数え直す（作業が進んでいる間は止め続ける）。"""
    for i in range(3):
        assert _stop(monkeypatch, failing_project, active=i > 0) == runner.EXIT_BLOCK
    _write(failing_project / ".jsix-checks.json",
           {"gates": {"g2": {"coverage": {"file": "coverage.xml", "min": 99}}}})
    assert _stop(monkeypatch, failing_project, active=True) == runner.EXIT_BLOCK


def test_new_stop_sequence_resets_the_count(failing_project, monkeypatch):
    """stop_hook_active が false（新しい停止の試み）なら数え直す。"""
    for i in range(3):
        _stop(monkeypatch, failing_project, active=i > 0)
    assert _stop(monkeypatch, failing_project, active=False) == runner.EXIT_BLOCK


def test_limit_is_configurable(failing_project, monkeypatch):
    _write(failing_project / ".jsix-checks.json", {
        "gates": {"g2": {"coverage": {"file": "coverage.xml", "min": 100}}},
        "stop_hook": {"max_identical_blocks": 1},
    })
    assert _stop(monkeypatch, failing_project, active=False) == runner.EXIT_BLOCK
    assert _stop(monkeypatch, failing_project, active=True) == runner.EXIT_OK


def test_sessions_are_counted_separately(failing_project, monkeypatch):
    for i in range(3):
        _stop(monkeypatch, failing_project, active=i > 0, session="a")
    assert _stop(monkeypatch, failing_project, active=True, session="b") == runner.EXIT_BLOCK


def test_without_stop_hook_flag_always_blocks(failing_project):
    """CI や手動実行では従来どおり必ず止める（外側ループは解除しない）。"""
    for _ in range(5):
        assert runner.main(["--dir", str(failing_project)]) == runner.EXIT_BLOCK


def test_broken_stdin_still_blocks(failing_project, monkeypatch):
    """Hook 入力が読めなくてもゲートの判定は変えない。"""
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    for _ in range(5):
        assert runner.main(["--dir", str(failing_project), "--stop-hook"]) == runner.EXIT_BLOCK
