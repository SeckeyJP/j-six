#!/usr/bin/env python3
"""J-SIX 品質ゲートのランナー（コマンド型 Hook / CI の共通エントリポイント）。

カレントディレクトリに `.jsix-checks.json` が存在する場合のみ、そこに定義された
ゲートを **G1 → G2 → G3 → G4 の順に** 実行する。設定ファイルが無いプロジェクトでは
**何もせず exit 0**（安全な no-op）。

## 順序固定と打ち切り

後段は前段が全通過した場合のみ実行する。G1 が落ちているコードを G3 の LLM judge に
見せても意味のある判定は返らないため、前段失敗時点で打ち切る。

## レポート駆動（既定）

既定では、宣言された成果物（JUnit XML / Cobertura・LCOV / SARIF / mutation JSON）を
**読んで判定するだけ**で、`cmd` に書かれたコマンドは実行しない。Stop hook が毎ターン
ビルドやテストを走らせて数分待たされると、Hook 自体が無効化される運用に傾くためである。
`--run-commands` を付けた場合（CI での利用を想定）のみ `cmd` を順に実行する。

## G3（LLM judge）の扱い

command 型 Hook から LLM サブエージェントは呼べない。そこで G1/G2 通過後、
`g3.verdict`（既定 `reports/evidence/<task-id>/judge.json`）が無ければ
「G3 未実施」として exit 2 で止め、Stop の prompt 型 Hook / Skill が scope-judge を
呼んで判定を書き込む。次回実行時に runner がそれを読んで G3 を判定する。

## 後方互換

v2.0 のフラット形式（`{"traceability": ..., "coverage": ...}`）もそのまま動く。
`jsix_config` が G2 相当へマップし、判定結果は v2.0 と同じになる。

終了コード: 0=全ゲート合格 or 未設定 / 2=いずれか失敗（Stop Hook をブロック）
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jsix_config as config  # noqa: E402
import jsix_coverage_gate as coverage_gate  # noqa: E402
import jsix_gitutil as git  # noqa: E402
import jsix_junit_check as junit_check  # noqa: E402
import jsix_mutation_gate as mutation_gate  # noqa: E402
import jsix_sarif_gate as sarif_gate  # noqa: E402
import jsix_scope_check as scope_check  # noqa: E402
import jsix_test_tamper_check as tamper_check  # noqa: E402
import jsix_traceability_check as traceability_check  # noqa: E402
from jsix_result import Result, failed, passed, skipped  # noqa: E402

CONFIG_NAME = config.CONFIG_NAME
EXIT_OK = 0
EXIT_BLOCK = 2


class Context:
    """1回の実行で共有する情報。"""

    def __init__(self, base: Path, run_commands: bool):
        self.base = base
        self.run_commands = run_commands
        self._changed = None

    @property
    def changed_files(self) -> list | None:
        """変更ファイル（設定ファイルのあるディレクトリからの相対パス）。"""
        if self._changed is None:
            if not git.is_repo(self.base):
                self._changed = []
            else:
                try:
                    self._changed = git.changed_files_relative(self.base)
                except git.GitError:
                    self._changed = []
        return self._changed


# --------------------------------------------------------------------------
# 各チェックのアダプタ
# --------------------------------------------------------------------------

def _run_cmd(name: str, cfg: dict, ctx: Context) -> Result | None:
    """`cmd` を実行する（--run-commands 指定時のみ）。失敗したら Result を返す。"""
    cmd = cfg.get("cmd")
    if not cmd or not ctx.run_commands:
        return None
    proc = subprocess.run(cmd, shell=True, cwd=str(ctx.base), capture_output=True, text=True)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-10:]
        return failed(
            f"{name}: コマンドが失敗しました（exit {proc.returncode}）: {cmd}",
            {"exit_code": proc.returncode, "cmd": cmd},
            [{"kind": "stderr", "text": line} for line in tail],
        )
    return None


def _command_only(name: str, cfg: dict, ctx: Context) -> Result:
    """成果物を持たず、コマンドの終了コードだけで判定するチェック（build / lint 等）。"""
    fail = _run_cmd(name, cfg, ctx)
    if fail:
        return fail
    if not cfg.get("cmd"):
        return skipped(f"{name}: cmd が未設定のためスキップ")
    if not ctx.run_commands:
        return skipped(f"{name}: レポート駆動モードのため未実行（CI では --run-commands で実行）")
    return passed(f"{name}: 成功", {"cmd": cfg["cmd"]})


def _sarif_check(name: str, cfg: dict, ctx: Context) -> Result:
    fail = _run_cmd(name, cfg, ctx)
    if fail:
        return fail
    if not (cfg.get("sarif") or cfg.get("file")):
        return _command_only(name, cfg, ctx)
    return sarif_gate.check(cfg, ctx.base, label=name)


def _tests_check(name: str, cfg: dict, ctx: Context) -> Result:
    fail = _run_cmd(name, cfg, ctx)
    if fail:
        return fail
    if not (cfg.get("junit") or cfg.get("file")):
        return _command_only(name, cfg, ctx)
    return junit_check.check(cfg, ctx.base)


def _mutation_check(name: str, cfg: dict, ctx: Context) -> Result:
    fail = _run_cmd(name, cfg, ctx)
    if fail:
        return fail
    return mutation_gate.check(cfg, ctx.base, ctx.changed_files)


def _judge_check(name: str, cfg: dict, ctx: Context) -> Result:
    """G3: scope-judge の判定ファイルを読む。

    判定ファイルが無い場合は「G3 未実施」として不合格にする。Stop の prompt 型 Hook
    または tdd-cycle / evidence-pack Skill が scope-judge を呼び、結果を書き込む。
    """
    verdict_path = ctx.base / cfg.get("verdict", "reports/evidence/judge.json")
    agent = cfg.get("agent", "scope-judge")

    if not verdict_path.is_file():
        return failed(
            f"judge: G3 未実施。`{agent}` サブエージェントに diff・タスク定義・該当 Spec を渡して判定させ、"
            f"結果を {verdict_path} に書き出してください"
            ' 形式: {"verdict": "PASS"|"REJECT", "reasons": [{"category": "correctness"|"requirement"|"scope", "detail": "..."}], "attempt": 1}',
            {"verdict_path": str(verdict_path), "agent": agent},
        )

    try:
        doc = json.loads(verdict_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return failed(f"judge: {verdict_path} の解析に失敗: {exc}")

    verdict = str(doc.get("verdict", "")).upper()
    reasons = doc.get("reasons") or []
    attempt = int(doc.get("attempt", 1))
    max_auto_fix = int(cfg.get("max_auto_fix", 1))

    metrics = {
        "verdict": verdict,
        "attempt": attempt,
        "max_auto_fix": max_auto_fix,
        "reason_categories": sorted({str(r.get("category", "unknown")) for r in reasons}),
    }

    if verdict == "PASS":
        return passed("judge: PASS（正確性・要件・スコープに問題なし）", metrics)

    if verdict != "REJECT":
        return failed(f"judge: verdict が不正です（{verdict!r}）。PASS または REJECT を指定してください", metrics)

    escalate = attempt > max_auto_fix
    note = (
        f" — 自動修正の上限（{max_auto_fix}回）を超えました。**人間の判断を仰いでください**"
        if escalate else f" — 修正して再判定してください（{attempt}/{max_auto_fix}回目）"
    )
    metrics["escalate_to_human"] = escalate
    return failed(f"judge: REJECT（{attempt}回目）{note}", metrics, reasons)


def _evidence_check(name: str, cfg: dict, ctx: Context) -> Result:
    """G4: 証跡パッケージ生成。Step 4 で実装する。"""
    return skipped("evidence: 証跡パッケージ生成は未実装（Step 4）")


CHECKS = {
    "build": _command_only,
    "typecheck": _command_only,
    "lint": _command_only,
    "format": _command_only,
    "sast": _sarif_check,
    "secrets": _sarif_check,
    "deps": _sarif_check,
    "scope": lambda name, cfg, ctx: scope_check.check(cfg, ctx.base, ctx.changed_files),
    "tests": _tests_check,
    "holdout": _tests_check,
    "coverage": lambda name, cfg, ctx: coverage_gate.check(cfg, ctx.base),
    "mutation": _mutation_check,
    "test_tamper": lambda name, cfg, ctx: tamper_check.check(cfg, ctx.base),
    "traceability": lambda name, cfg, ctx: traceability_check.check(cfg, ctx.base),
    "judge": _judge_check,
    "evidence": _evidence_check,
}


def run_gates(cfg: dict, ctx: Context) -> tuple:
    """ゲートを順に実行する。前段のゲートが失敗したら後段は実行しない。

    戻り値: (全体の合否, ゲート別の結果)
    """
    results: dict = {}
    aborted_after = None

    for gate in config.GATE_ORDER:
        gate_cfg = cfg.get("gates", {}).get(gate)
        if not gate_cfg:
            continue

        if aborted_after:
            results[gate] = {"status": "not-run", "reason": f"{aborted_after} が未通過のため未実行", "checks": {}}
            continue

        gate_results: dict = {}
        gate_ok = True
        for g, name, check_cfg in config.iter_checks({"gates": {gate: gate_cfg}}):
            handler = CHECKS.get(name)
            if handler is None:
                gate_results[name] = skipped(f"{name}: 未知のチェックのためスキップ").to_dict()
                continue
            try:
                result = handler(name, check_cfg, ctx)
            except Exception as exc:  # チェック自体の異常は不合格にして理由を残す
                result = failed(f"{name}: チェックの実行中に例外が発生: {exc.__class__.__name__}: {exc}")
            gate_results[name] = result.to_dict()
            if not result.ok:
                gate_ok = False

        results[gate] = {
            "status": "passed" if gate_ok else "failed",
            "checks": gate_results,
        }
        if not gate_ok:
            aborted_after = gate.upper()

    return aborted_after is None, results


def render(results: dict, legacy: bool) -> tuple:
    """結果を人間向けの行に整形する。戻り値: (出力行, 失敗の有無)"""
    lines: list = []
    has_failure = False

    for gate, info in results.items():
        label = gate.upper()
        if info["status"] == "not-run":
            lines.append(f"⏭ {label}: {info['reason']}")
            continue
        for name, res in info["checks"].items():
            if res["skipped"]:
                lines.append(f"  ⏭ [{label}] {res['summary']}")
            elif res["ok"]:
                lines.append(f"  ✅ [{label}] {res['summary']}")
            else:
                has_failure = True
                lines.append(f"  ❌ [{label}] {res['summary']}")
                for f in res["findings"][:5]:
                    detail = f.get("detail") or f.get("file") or f.get("test") or f.get("id") or f.get("message") or ""
                    if detail:
                        lines.append(f"       - {detail}")

    if legacy:
        lines.append(
            f"ℹ {CONFIG_NAME} は v2.0 の形式です。gates 形式への移行を推奨します"
            "（現状のまま動作します。移行例は plugin/README.md 参照）"
        )
    return lines, has_failure


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="J-SIX 品質ゲートのランナー")
    parser.add_argument("--run-commands", action="store_true",
                        help="設定の cmd を実際に実行する（CI 用。既定はレポート駆動）")
    parser.add_argument("--json", dest="json_out", default=None,
                        help="結果を JSON で書き出すパス")
    parser.add_argument("--dir", default=None, help="対象ディレクトリ（既定: カレント）")
    args = parser.parse_args(argv)

    base = Path(args.dir) if args.dir else Path.cwd()

    try:
        cfg = config.load(base)
    except config.ConfigError as exc:
        print(f"J-SIX checks: {exc}", file=sys.stderr)
        return EXIT_BLOCK

    if cfg is None:
        return EXIT_OK  # 未設定プロジェクトでは no-op

    ctx = Context(base, args.run_commands)
    ok, results = run_gates(cfg, ctx)
    lines, has_failure = render(results, cfg.get("_legacy", False))

    stream = sys.stderr if has_failure else sys.stdout
    for line in lines:
        print(line, file=stream)

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"ok": ok, "gates": results}, ensure_ascii=False, indent=2), encoding="utf-8")

    if not ok:
        print("J-SIX 品質ゲート未達。修正してください。", file=sys.stderr)
        return EXIT_BLOCK
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
