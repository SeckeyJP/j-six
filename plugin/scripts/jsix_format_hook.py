#!/usr/bin/env python3
"""PostToolUse Hook: 編集したファイルに決定論的な format / lint をかける。

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
        "format": { "cmd": "make format", "hook_cmd": ".venv/bin/python -m ruff format {file}", "hook_files": ["*.py"] },
        "lint":   { "cmd": "make lint",   "hook_cmd": ".venv/bin/python -m ruff check --fix {file}", "hook_files": ["*.py"] }
      }
    }

`{file}` は編集対象のファイルパスに置換される。

**対象ファイルは `hook_files`（glob のリスト）で宣言する。**宣言が無ければ実行しない。
plugin はどの言語のファイルかを知らないためで、拡張子を見ずに実行していたときは
`.json` を Python として整形して壊していた（reports/evidence/judge.json）。
glob はファイル名、または設定ファイルのあるディレクトリからの相対パスと照合する。

**編集の後（PostToolUse）に実行する。**編集の前に整形すると、直後の Edit の置換対象が
一致しなくなったり、Write が「読んだ後に変更された」で失敗したりする。

Hook はファイルを整形するだけで、**ツールの終了コードでは編集をブロックしない**。
書式は自動で直せばよく、止める必要がない。止めるべき違反（未使用変数など）は
G1 の lint が Stop 時に検出する。
"""
from __future__ import annotations

import fnmatch
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jsix_config as config  # noqa: E402

TARGET_TOOLS = {"Edit", "Write", "MultiEdit"}
HOOK_CHECKS = ("format", "lint")


def _hook_commands(base: Path) -> list:
    """(hook_cmd, hook_files) の組を返す。hook_files が無いものは対象外。"""
    try:
        cfg = config.load(base)
    except config.ConfigError:
        return []
    if not cfg:
        return []
    g1 = cfg.get("gates", {}).get("g1") or {}
    out = []
    for name in HOOK_CHECKS:
        check = g1.get(name)
        if isinstance(check, dict) and check.get("hook_cmd") and check.get("hook_files"):
            out.append((check["hook_cmd"], list(check["hook_files"])))
    return out


def _matches(file_path: str, base: Path, patterns: list) -> bool:
    path = Path(file_path)
    if not path.is_absolute():
        path = base / path
    try:
        rel = path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return False  # プロジェクトの外のファイルは整形しない
    return any(fnmatch.fnmatch(path.name, p) if "/" not in p else fnmatch.fnmatch(rel, p)
               for p in patterns)


def run_for_file(file_path: str, base: Path | None = None) -> list:
    """対象ファイルに対して宣言された hook_cmd を順に実行し、実行結果を返す。"""
    base = base or Path.cwd()
    results = []
    for template, patterns in _hook_commands(base):
        if not _matches(file_path, base, patterns):
            continue
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
