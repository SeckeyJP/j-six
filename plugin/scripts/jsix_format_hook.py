#!/usr/bin/env python3
"""PreToolUse Hook: 決定論的な format / lint を実行する。

v2.0 では PreToolUse に prompt 型 Hook（LLM に規約違反を判定させる）を置いていたが、
これを command 型に置き換えた。理由は3つある。

  1. 規約準拠は lint / format が決定論的に判定できる。LLM に判定させると
     同じコードで結果がぶれる
  2. prompt 型 Hook は編集のたびに LLM 呼び出しが発生する
  3. G1 で lint が落ちてから直すより、書いた時点で直すほうが安い

prompt 型 Hook は助言用途（ADR の提案など、判定基準が言語化しにくいもの）に限定する。

`.jsix-checks.json` の `gates.g1.format.hook_cmd` または `gates.g1.lint.hook_cmd` に
コマンドが宣言されている場合のみ実行する。未宣言なら何もしない（安全な no-op）。
言語別のツール名は plugin に持たせず、プロジェクト側が宣言する。

設定例:
    "gates": {
      "g1": {
        "format": { "cmd": "make format", "hook_cmd": ".venv/bin/python -m ruff format {file}" },
        "lint":   { "cmd": "make lint",   "hook_cmd": ".venv/bin/python -m ruff check --fix {file}" }
      }
    }

`{file}` は編集対象のファイルパスに置換される。

Hook はファイルを整形するだけで、**ツールの終了コードでは編集をブロックしない**。
書式は自動で直せばよく、止める必要がない。止めるべき違反（未使用変数など）は
G1 の lint が Stop 時に検出する。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jsix_config as config  # noqa: E402

TARGET_TOOLS = {"Edit", "Write", "MultiEdit"}
HOOK_CHECKS = ("format", "lint")


def _hook_commands(base: Path) -> list:
    try:
        cfg = config.load(base)
    except config.ConfigError:
        return []
    if not cfg:
        return []
    g1 = cfg.get("gates", {}).get("g1") or {}
    return [g1[name]["hook_cmd"] for name in HOOK_CHECKS
            if isinstance(g1.get(name), dict) and g1[name].get("hook_cmd")]


def run_for_file(file_path: str, base: Path | None = None) -> list:
    """対象ファイルに対して宣言された hook_cmd を順に実行し、実行結果を返す。"""
    base = base or Path.cwd()
    results = []
    for template in _hook_commands(base):
        cmd = template.replace("{file}", file_path)
        proc = subprocess.run(cmd, shell=True, cwd=str(base), capture_output=True, text=True)
        results.append({"cmd": cmd, "exit_code": proc.returncode})
    return results


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0

    tool = payload.get("tool_name") or payload.get("toolName") or ""
    if tool not in TARGET_TOOLS:
        return 0

    params = payload.get("tool_input") or payload.get("toolInput") or {}
    if not isinstance(params, dict):
        return 0

    target = params.get("file_path") or params.get("path")
    if not target:
        return 0

    run_for_file(str(target))
    return 0  # 整形するだけ。編集はブロックしない


if __name__ == "__main__":
    raise SystemExit(main())
