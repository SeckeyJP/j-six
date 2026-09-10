#!/usr/bin/env python3
"""J-SIX G1: スコープ検査（変更ファイル ⊆ タスクの許可リスト）。

Phase 3 でタスクごとに承認された「変更してよいファイル範囲」を、実際の変更
ファイル一覧と照合する。言語非依存（git と glob だけを使う）。

設定:
    "scope": {
      "allow": ["src/approval/**", "tests/**"],   # このどれかに一致しないファイルは違反
      "deny":  ["tests/acceptance/**", "migrations/**"],  # 一致したら allow より優先して違反
      "base":  "main"        # 省略時は未コミットの変更のみを対象にする
    }

allow を省略した場合は deny のみを検査する（許可リストが未整備な段階でも使えるように）。

glob は `**` を含むパターンを扱う。`fnmatch` は `**` を `*` と同じに扱い
ディレクトリ境界を越えないため、pathlib の `PurePath.match` ではなく
自前で正規表現へ変換している。

使い方:
    python jsix_scope_check.py --allow 'src/**' --allow 'tests/**' --deny 'migrations/**'

終了コード: 0=合格 / 1=スコープ逸脱あり / 2=入力エラー
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jsix_gitutil as git  # noqa: E402
from jsix_result import Result, failed, passed, skipped  # noqa: E402


def glob_to_regex(pattern: str) -> re.Pattern:
    """glob パターンを正規表現へ変換する。

    `**` は「0個以上のパスセグメント」、`*` は「/ を含まない任意の文字列」、
    `?` は「/ 以外の1文字」。末尾が `/` または `**` で終わる場合は配下すべてに一致する。
    """
    pattern = pattern.strip().replace("\\", "/")
    if pattern.endswith("/"):
        pattern += "**"

    out = ["^"]
    i = 0
    n = len(pattern)
    while i < n:
        c = pattern[i]
        if c == "*":
            if pattern[i:i + 3] == "**/":
                out.append("(?:.*/)?")
                i += 3
                continue
            if pattern[i:i + 2] == "**":
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
            i += 1
            continue
        if c == "?":
            out.append("[^/]")
            i += 1
            continue
        out.append(re.escape(c))
        i += 1
    out.append("$")
    return re.compile("".join(out))


def matches_any(path: str, patterns: list) -> str | None:
    """一致した最初のパターンを返す。一致しなければ None。"""
    norm = path.replace("\\", "/")
    for pat in patterns:
        if glob_to_regex(pat).match(norm):
            return pat
    return None


def check(cfg: dict, base_dir: Path | None = None, changed: list | None = None) -> Result:
    base = base_dir or Path.cwd()
    allow = cfg.get("allow") or []
    deny = cfg.get("deny") or []

    if not allow and not deny:
        return skipped("scope: allow / deny のどちらも未設定のため検査をスキップ")

    if changed is None:
        if not git.is_repo(base):
            return failed("scope: git リポジトリではないため変更ファイルを取得できません")
        try:
            changed = git.changed_files_relative(base, cfg.get("base"))
        except git.GitError as exc:
            return failed(f"scope: git の実行に失敗: {exc}")

    violations: list = []
    for path in changed:
        hit_deny = matches_any(path, deny)
        if hit_deny:
            violations.append({"file": path, "reason": "deny", "pattern": hit_deny})
            continue
        if allow and not matches_any(path, allow):
            violations.append({"file": path, "reason": "not-in-allow", "pattern": None})

    metrics = {
        "changed_files": len(changed),
        "violations": len(violations),
        "allow": allow,
        "deny": deny,
    }

    if violations:
        names = ", ".join(v["file"] for v in violations[:5])
        more = f" ほか{len(violations) - 5}件" if len(violations) > 5 else ""
        return failed(
            f"scope: 許可範囲外の変更 {len(violations)}件 → {names}{more}",
            metrics,
            violations,
        )
    return passed(f"scope: 変更 {len(changed)}ファイルはすべて許可範囲内", metrics)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="変更ファイルのスコープ検査")
    parser.add_argument("--allow", action="append", default=[], help="許可する glob（複数指定可）")
    parser.add_argument("--deny", action="append", default=[], help="禁止する glob（複数指定可）")
    parser.add_argument("--base", default=None, help="比較元の git ref（省略時は未コミット変更のみ）")
    args = parser.parse_args(argv)

    cfg = {"allow": args.allow, "deny": args.deny}
    if args.base:
        cfg["base"] = args.base

    result = check(cfg)
    print(("✅ " if result.ok else "❌ ") + result.summary)
    for v in result.findings[:20]:
        print(f"  - {v['file']}（{v['reason']}{': ' + v['pattern'] if v['pattern'] else ''}）")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
