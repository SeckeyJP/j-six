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
「G3 未実施」として exit 2 で止める。stderr の案内を受けた Claude（または Skill）が
scope-judge を呼んで判定を書き込み、次回実行時に runner がそれを読んで G3 を判定する。
変更ファイルが無いセッションでは G3 を求めない。

## 後方互換

v2.0 のフラット形式（`{"traceability": ..., "coverage": ...}`）もそのまま動く。
`jsix_config` が G2 相当へマップし、判定結果は v2.0 と同じになる。

終了コード: 0=全ゲート合格 or 未設定 / 2=いずれか失敗（Stop Hook をブロック）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jsix_config as config  # noqa: E402
import jsix_coverage_gate as coverage_gate  # noqa: E402
import jsix_evidence_pack as evidence_pack  # noqa: E402
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

#: ゲート失敗の履歴（`history` で変更可）。Phase 0 の月次ループの入力
DEFAULT_HISTORY = "reports/gate-history.jsonl"

#: Stop hook で同じ失敗によるブロックを何回まで続けるか（`stop_hook.max_identical_blocks`）
DEFAULT_MAX_IDENTICAL_BLOCKS = 3


class Context:
    """1回の実行で共有する情報。"""

    def __init__(self, base: Path, run_commands: bool):
        self.base = base
        self.run_commands = run_commands
        self._changed = None
        #: 変更ファイルの比較元。設定の scope.base、無ければ既定ブランチとの分岐点
        self.scope_base: str | None = None
        self._base_ref: str | None = None
        self._base_resolved = False
        #: 設定のゲート定義（G3 が G4 の出力先を知るために使う）
        self.config_gates: dict = {}
        #: ゲート履歴の出力先（G3 の差分の指紋から除外する）
        self.history_path: str | None = None
        #: G4 は G1〜G3 の結果を入力に取るため、実行中の結果を参照できるようにする
        self.results: dict = {}
        self.config_path: Path | None = None

    @property
    def base_ref(self) -> str | None:
        """タスクの起点。コミット済みの変更も検査対象に含めるために使う。"""
        if not self._base_resolved:
            self._base_resolved = True
            if git.is_repo(self.base):
                self._base_ref = self.scope_base or git.default_base(self.base)
        return self._base_ref

    @property
    def changed_files(self) -> list | None:
        """変更ファイル（設定ファイルのあるディレクトリからの相対パス）。

        タスクの起点（base_ref）からの差分＋未コミットの変更。フェーズごとにコミット
        しても、スコープ検査と G3 が空振りしないようにするため。
        """
        if self._changed is None:
            if not git.is_repo(self.base):
                self._changed = []
            else:
                try:
                    self._changed = git.changed_files_relative(self.base, self.base_ref)
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
    return junit_check.check(cfg, ctx.base, label=name)


def _mutation_check(name: str, cfg: dict, ctx: Context) -> Result:
    fail = _run_cmd(name, cfg, ctx)
    if fail:
        return fail
    return mutation_gate.check(cfg, ctx.base, ctx.changed_files)


def _scope_check(cfg: dict, ctx: Context) -> Result:
    """G1 スコープ検査。比較元は RED タグ（実装フェーズの変更だけを見る）。

    deny（例: hold-out を実装側が触らない）は実装フェーズの規則である。hold-out テストは
    同じタスクの前半で正当にコミットされるため、ブランチ全体の差分で見ると誤検出になる。
    優先順: 設定の scope.base → RED タグ（$JSIX_TASK_ID → 最新の jsix/red-*）→ 未コミットの変更のみ。
    """
    if not git.is_repo(ctx.base):
        return scope_check.check(cfg, ctx.base, [])
    ref = cfg.get("base") or tamper_check.resolve_baseline({}, ctx.base)
    try:
        changed = git.changed_files_relative(ctx.base, ref)
    except git.GitError:
        changed = []
    result = scope_check.check(cfg, ctx.base, changed)
    result.metrics["compared_from"] = ref or "未コミットの変更のみ"
    return result


def _judge_check(name: str, cfg: dict, ctx: Context) -> Result:
    """G3: scope-judge の判定ファイルを読む。

    判定ファイルが無い場合は「G3 未実施」として不合格にする。この案内（stderr）を受けた
    Claude、または tdd-cycle / evidence-pack Skill が scope-judge を呼び、結果を書き込む。

    git 管理下で変更ファイルが1つも無い場合は、判定対象の差分が無いので G3 を求めない。
    レビューや調査だけのセッションで、毎回 scope-judge の起動を強いないためである。
    """
    if git.is_repo(ctx.base) and ctx.changed_files == []:
        return skipped("judge: 変更なし（判定対象の差分が無いため G3 は不要）")

    verdict_rel = cfg.get("verdict", "reports/evidence/judge.json")
    verdict_path = ctx.base / verdict_rel
    agent = cfg.get("agent", "scope-judge")
    # 判定がどの差分に対するものかを照合する。git 管理外では照合しない
    evidence_out = (ctx.config_gates.get("g4") or {}).get("out", "reports/evidence/")
    history = ctx.history_path or DEFAULT_HISTORY
    target = (git.diff_fingerprint(ctx.base_ref, ctx.base, exclude=[verdict_rel, evidence_out, history])
              if git.is_repo(ctx.base) else None)
    target_hint = f', "target": "{target}"' if target else ""
    base_hint = f"（比較元 {ctx.base_ref[:12]}）" if ctx.base_ref else ""

    instructions = (
        f"`{agent}` サブエージェントに diff{base_hint}・タスク定義・該当 Spec を渡して判定させ、"
        f"結果を {verdict_rel} に書き出してください"
        ' 形式: {"verdict": "PASS"|"REJECT", "reasons": [{"category": "correctness"|"requirement"|"scope", "detail": "..."}], "attempt": 1'
        + target_hint + "}"
    )
    meta = {"verdict_path": verdict_rel, "agent": agent, "target": target, "base_ref": ctx.base_ref}

    if not verdict_path.is_file():
        return failed(f"judge: G3 未実施。{instructions}", meta)

    try:
        doc = json.loads(verdict_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return failed(f"judge: {verdict_path} の解析に失敗: {exc}")

    if target and doc.get("target") != target:
        return failed(
            "judge: G3 の判定が古い（判定後に差分が変わった、または別タスクの判定が残っている）。"
            f"再判定してください。{instructions}",
            meta,
        )

    verdict = str(doc.get("verdict", "")).upper()
    reasons = doc.get("reasons") or []
    attempt = int(doc.get("attempt", 1))
    max_auto_fix = int(cfg.get("max_auto_fix", 1))

    metrics = {
        "verdict": verdict,
        "attempt": attempt,
        "max_auto_fix": max_auto_fix,
        "reason_categories": sorted({str(r.get("category", "unknown")) for r in reasons}),
        "target": target,
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
    """G4: 証跡パッケージ生成。

    ここに到達しているのは G1〜G3 がすべて通過した場合だけなので、
    証跡パッケージは「通過した状態の記録」になる。未通過時の記録が必要な場合は
    `--json` の出力から `jsix_evidence_pack.py` を直接実行する。
    """
    return evidence_pack.check(cfg, ctx.base, ctx.results, overall_ok=True,
                               config_path=ctx.config_path)


CHECKS = {
    "build": _command_only,
    "typecheck": _command_only,
    "lint": _command_only,
    "format": _command_only,
    "sast": _sarif_check,
    "secrets": _sarif_check,
    "deps": _sarif_check,
    "scope": lambda name, cfg, ctx: _scope_check(cfg, ctx),
    "tests": _tests_check,
    "holdout": _tests_check,
    "coverage": lambda name, cfg, ctx: coverage_gate.check(cfg, ctx.base),
    "mutation": _mutation_check,
    "test_tamper": lambda name, cfg, ctx: tamper_check.check(cfg, ctx.base),
    "traceability": lambda name, cfg, ctx: traceability_check.check(cfg, ctx.base),
    "judge": _judge_check,
    "evidence": _evidence_check,
}


def run_gates(cfg: dict, ctx: Context, only: set | None = None) -> tuple:
    """ゲートを順に実行する。前段のゲートが失敗したら後段は実行しない。

    `only` を渡すと、そこに含まれるゲートだけを実行する。外側ループ（CI）で
    G3（LLM judge）を外し、G1/G2/G4 だけを必須にする用途を想定している
    （CI で LLM の API キーを扱わずに済ませるため）。

    戻り値: (全体の合否, ゲート別の結果)
    """
    results: dict = {}
    aborted_after = None
    ctx.config_gates = cfg.get("gates", {})
    ctx.history_path = cfg.get("history")
    scope_cfg = cfg.get("gates", {}).get("g1", {}).get("scope") or {}
    if scope_cfg.get("base") and ctx.scope_base is None:
        ctx.scope_base = scope_cfg["base"]

    for gate in config.GATE_ORDER:
        gate_cfg = cfg.get("gates", {}).get(gate)
        if not gate_cfg:
            continue

        if only is not None and gate not in only:
            results[gate] = {"status": "excluded",
                             "reason": "--gates で対象外に指定されたため未実行",
                             "checks": {}}
            continue

        if aborted_after:
            results[gate] = {"status": "not-run", "reason": f"{aborted_after} が未通過のため未実行", "checks": {}}
            continue

        ctx.results = results  # 実行中のゲートより前の結果を G4 から読めるようにする
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
        ctx.results = results  # G4 が G1〜G3 の結果を参照できるようにする
        if not gate_ok:
            aborted_after = gate.upper()

    return aborted_after is None, results


def render(results: dict, legacy: bool) -> tuple:
    """結果を人間向けの行に整形する。戻り値: (出力行, 失敗の有無)"""
    lines: list = []
    has_failure = False

    for gate, info in results.items():
        label = gate.upper()
        if info["status"] in ("not-run", "excluded"):
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
                    # コマンド失敗時の stderr は "text" に入る。ここを拾い損ねると
                    # 「失敗した」とだけ出て理由が分からない出力になる。
                    detail = (f.get("detail") or f.get("file") or f.get("test")
                              or f.get("id") or f.get("message") or f.get("text") or "")
                    if detail:
                        lines.append(f"       - {detail}")

    if legacy:
        lines.append(
            f"ℹ {CONFIG_NAME} は v2.0 の形式です。gates 形式への移行を推奨します"
            "（現状のまま動作します。移行例は plugin/README.md 参照）"
        )
    return lines, has_failure


def _failed_checks(results: dict) -> list:
    out = []
    for gate, res in results.items():
        for name, chk in (res.get("checks") or {}).items():
            if not chk.get("ok", True) and not chk.get("skipped"):
                out.append(f"{gate}.{name}")
    return out


def _record_history(base: Path, cfg: dict, results: dict, ok: bool, mode: str) -> None:
    """ゲートの失敗を履歴に追記する。成功は、直前の記録が失敗だった場合（回復）だけ残す。

    証跡と gate.json は最後の1回で上書きされるため、途中の失敗が残らなかった。
    Stop のたびに走るので、成功を毎回記録すると履歴が埋まる。
    """
    path = base / cfg.get("history", DEFAULT_HISTORY)
    if ok:
        try:
            lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
            last_ok = json.loads(lines[-1]).get("ok", True) if lines else True
        except (OSError, ValueError):
            last_ok = True
        if last_ok:
            return
    record = {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ok": ok,
        "mode": mode,
        "failed": _failed_checks(results),
        "summaries": {k: v["summary"] for g in results.values()
                      for k, v in (g.get("checks") or {}).items()
                      if not v.get("ok", True) and not v.get("skipped")},
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass  # 履歴を残せなくてもゲートの判定は変えない


def stop_state_dir() -> Path:
    """Stop hook のブロック回数を覚えておく場所。プロジェクトを汚さないよう一時領域に置く。"""
    return Path(tempfile.gettempdir()) / "jsix-stop-hook"


def _read_hook_input() -> dict | None:
    """Stop hook の入力（stdin の JSON）を読む。読めなければ None。"""
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except (ValueError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _release_repeated_block(hook: dict | None, lines: list, cfg: dict) -> str | None:
    """同じ失敗でのブロックが上限を超えたら、停止を許可する理由を返す。

    ゲートが工程上まだ満たせない状態（Spec に REQ を追加した直後で、テストは次の工程で
    書く等）だと、Stop のたびに同じ失敗でブロックし続けセッションが終わらない。
    Claude Code 自身の上限（連続8回）に頼らず、失敗内容が変わらないブロックだけを数えて
    解除する。**判定は緩めない**: ゲートは未達のまま残り、CI（外側ループ）では止まる。
    """
    if not hook or not hook.get("session_id"):
        return None
    limit = int(cfg.get("stop_hook", {}).get("max_identical_blocks", DEFAULT_MAX_IDENTICAL_BLOCKS))
    fingerprint = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    session = hashlib.sha256(str(hook["session_id"]).encode("utf-8")).hexdigest()[:16]
    state_path = stop_state_dir() / f"{session}.json"

    count = 1
    if hook.get("stop_hook_active"):
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            state = {}
        if state.get("fingerprint") == fingerprint:
            count = int(state.get("count", 0)) + 1

    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"fingerprint": fingerprint, "count": count}), encoding="utf-8")
    except OSError:
        return None  # 状態を残せないなら従来どおり止める

    if count > limit:
        return (f"J-SIX: 同じ失敗で {limit} 回ブロックしたため、停止を許可します。"
                "品質ゲートは未達のままです（CI では止まります）。"
                "工程上いま満たせない失敗であれば、次の工程で解消してください")
    return None


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="J-SIX 品質ゲートのランナー")
    parser.add_argument("--run-commands", action="store_true",
                        help="設定の cmd を実際に実行する（CI 用。既定はレポート駆動）")
    parser.add_argument("--json", dest="json_out", default=None,
                        help="結果を JSON で書き出すパス")
    parser.add_argument("--dir", default=None, help="対象ディレクトリ（既定: カレント）")
    parser.add_argument("--stop-hook", action="store_true",
                        help="Stop hook として実行する（stdin の Hook 入力を読み、同じ失敗の繰り返しブロックを解除する）")
    parser.add_argument("--gates", default=None,
                        help="実行するゲートをカンマ区切りで指定（例: g1,g2,g4）。"
                             "省略時は設定にあるゲートをすべて実行する")
    args = parser.parse_args(argv)

    only = None
    if args.gates:
        only = {g.strip().lower() for g in args.gates.split(",") if g.strip()}
        unknown = only - set(config.GATE_ORDER)
        if unknown:
            print(f"J-SIX checks: 未知のゲート: {', '.join(sorted(unknown))}"
                  f"（有効: {', '.join(config.GATE_ORDER)}）", file=sys.stderr)
            return EXIT_BLOCK

    base = Path(args.dir) if args.dir else Path.cwd()

    try:
        cfg = config.load(base)
    except config.ConfigError as exc:
        print(f"J-SIX checks: {exc}", file=sys.stderr)
        return EXIT_BLOCK

    if cfg is None:
        return EXIT_OK  # 未設定プロジェクトでは no-op

    ctx = Context(base, args.run_commands)
    ctx.config_path = Path(cfg["_path"]) if cfg.get("_path") else None
    ok, results = run_gates(cfg, ctx, only)
    lines, has_failure = render(results, cfg.get("_legacy", False))
    mode = "stop-hook" if args.stop_hook else ("ci" if args.run_commands else "manual")
    _record_history(base, cfg, results, ok, mode)

    stream = sys.stderr if has_failure else sys.stdout
    for line in lines:
        print(line, file=stream)

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"ok": ok, "gates": results}, ensure_ascii=False, indent=2), encoding="utf-8")

    if not ok:
        if args.stop_hook:
            released = _release_repeated_block(_read_hook_input(), lines, cfg)
            if released:
                print(released)
                return EXIT_OK
        print("J-SIX 品質ゲート未達。修正してください。", file=sys.stderr)
        return EXIT_BLOCK
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
