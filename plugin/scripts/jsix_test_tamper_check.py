#!/usr/bin/env python3
"""J-SIX G2: テスト改変検出。

TDD の RED 完了時に打つタグ（既定 `jsix/red-<task-id>`）を基準点として、それ以降に
**テストを弱める変更**が入っていないかを検査する。

検出するのは「弱体化」であって「差分そのもの」ではない。REFACTOR 工程では
テストコードの命名整理・重複排除を行うことが正当なため、単なる差分はブロックしない
（証跡には記録する）。判定は差分行ではなく **基準点と現在の総数の比較** で行う。
これにより、テストを別ファイルへ移動しただけの変更を誤検知しない。

| 検出パターン | 判定 |
|---|---|
| アサーション総数の減少 | ブロック |
| テスト関数総数の減少 | ブロック |
| 無効化マーカー（skip / xfail / Ignore 等）の増加 | ブロック |
| 実装コードから hold-out テストへの参照 | ブロック |
| 上記以外の tests/ の差分 | 警告（証跡に記録） |

設定:
    "test_tamper": {
      "baseline_ref": "jsix/red-TASK-001",   # 省略時: $JSIX_TASK_ID → 最新の jsix/red-* タグ
      "paths": ["tests/**"],                 # 検査対象（既定 tests/）
      "holdout_dir": "tests/acceptance",     # 実装からの参照を禁止するディレクトリ
      "source_paths": ["app/**", "src/**"]   # hold-out 参照を検査する実装側の範囲
    }

使い方:
    python jsix_test_tamper_check.py --baseline-ref jsix/red-TASK-001

終了コード: 0=合格 / 1=弱体化を検出 / 2=入力エラー
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jsix_gitutil as git  # noqa: E402
from jsix_result import Result, failed, passed, skipped  # noqa: E402
from jsix_scope_check import glob_to_regex  # noqa: E402

TEST_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".kt", ".go", ".rb", ".cs", ".rs", ".php", ".scala", ".swift"}

#: アサーション（言語横断。過不足はあるが「総数の増減」を見るので相対比較として機能する）
ASSERT_RE = re.compile(
    r"(?:\bassert\b|\bassert_\w+|\bassertThat\b|\bassert[A-Z]\w*"
    r"|\bexpect\s*\(|\bshould\b|\bEXPECT_\w+|\bASSERT_\w+"
    r"|\brequire\.\w+|\bt\.Error\w*\(|\bt\.Fatal\w*\(|\bXCTAssert\w*)"
)

#: テスト関数の宣言
TEST_FUNC_RE = re.compile(
    r"(?:^\s*(?:async\s+)?def\s+test\w*\s*\("                    # Python
    r"|^\s*(?:it|test|specify)\s*(?:\.\w+)?\s*\(\s*['\"`]"       # JS/TS
    r"|@Test\b"                                                  # Java/Kotlin
    r"|^\s*func\s+Test\w*\s*\("                                  # Go
    r"|^\s*(?:it|specify)\s+['\"]"                               # Ruby RSpec
    r"|#\[test\]"                                                # Rust
    r"|^\s*\[Fact\]|^\s*\[Theory\]"                              # C# xUnit
    r")",
    re.MULTILINE,
)

#: テストを無効化するマーカー
SKIP_RE = re.compile(
    r"(?:@pytest\.mark\.(?:skip|skipif|xfail)"
    r"|@unittest\.skip\w*"
    r"|\bpytest\.skip\s*\("
    r"|\b(?:it|test|describe|context)\.(?:skip|todo)\s*\("
    r"|\bx(?:it|test|describe)\s*\("
    r"|@(?:Ignore|Disabled)\b"
    r"|\bt\.Skip\s*\("
    r"|#\[ignore\]"
    r"|\[Skip\s*=\s*['\"]"
    r"|\bskip\s*:\s*true\b"
    r")"
)


def _is_test_file(path: str) -> bool:
    return Path(path).suffix in TEST_SUFFIXES


def _match_paths(path: str, patterns: list) -> bool:
    return any(glob_to_regex(p).match(path.replace("\\", "/")) for p in patterns)


#: 総数の比較に使うキー（digest は含めない）
COUNT_KEYS = ("asserts", "tests", "skips")


def scan_text(text: str) -> dict:
    """1ファイル分のテキストからアサーション数・テスト関数数・skip 数を数える。

    digest は「弱体化はしていないが内容は変わった」変更（REFACTOR での命名整理など）を
    証跡に残すために持つ。判定には使わない。
    """
    return {
        "asserts": len(ASSERT_RE.findall(text)),
        "tests": len(TEST_FUNC_RE.findall(text)),
        "skips": len(SKIP_RE.findall(text)),
        "digest": hashlib.sha256(text.encode("utf-8")).hexdigest()[:12],
    }


def _aggregate(files: dict) -> dict:
    total = {k: 0 for k in COUNT_KEYS}
    for counts in files.values():
        for k in COUNT_KEYS:
            total[k] += counts[k]
    return total


def project_prefix(base: Path, root: Path) -> str:
    """リポジトリルートから見たプロジェクトディレクトリの相対パス（末尾 / なし）。

    `paths` の glob は `.jsix-checks.json` のあるディレクトリ基準で書くが、git が
    返すのはリポジトリルート基準。リポジトリ内のサブディレクトリにあるプロジェクト
    （モノレポ、examples/ 配下のサンプル）で両者が食い違うため、ここで変換する。
    """
    try:
        rel = Path(base).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return ""
    return "" if rel == "." else rel


def _scan_baseline(ref: str, patterns: list, base: Path, root: Path) -> dict:
    """基準点 ref 時点のテストファイルを走査する（キーはプロジェクト基準の相対パス）。"""
    prefix = project_prefix(base, root)
    scope = [prefix] if prefix else None

    files: dict = {}
    for repo_path in git.ls_tree(ref, scope, cwd=root):
        rel = repo_path[len(prefix) + 1:] if prefix else repo_path
        if not _is_test_file(rel) or not _match_paths(rel, patterns):
            continue
        text = git.show_file(ref, repo_path, cwd=root)
        if text is not None:
            files[rel] = scan_text(text)
    return files


def _scan_worktree(patterns: list, base: Path) -> dict:
    """作業ツリーのテストファイルを走査する（キーはプロジェクト基準の相対パス）。"""
    files: dict = {}
    for path in Path(base).rglob("*"):
        if not path.is_file() or path.suffix not in TEST_SUFFIXES:
            continue
        rel = path.relative_to(base).as_posix()
        if not _match_paths(rel, patterns):
            continue
        files[rel] = scan_text(path.read_text(encoding="utf-8", errors="ignore"))
    return files


def resolve_baseline(cfg: dict, base: Path) -> str | None:
    """基準点となる git ref を決める。

    優先順: 設定の baseline_ref → $JSIX_TASK_ID から組み立て → 最新の jsix/red-* タグ
    """
    ref = cfg.get("baseline_ref")
    if ref:
        return ref
    task_id = os.environ.get("JSIX_TASK_ID")
    if task_id:
        return f"jsix/red-{task_id}"
    return git.latest_tag("jsix/red-*", cwd=base)


def check_holdout_reference(cfg: dict, base: Path) -> list:
    """実装コードが hold-out テストを参照していないか検査する。"""
    holdout = cfg.get("holdout_dir", "tests/acceptance")
    source_patterns = cfg.get("source_paths") or ["app/**", "src/**", "lib/**", "internal/**", "pkg/**"]

    # import 等で使われる形（tests/acceptance, tests.acceptance）の両方を見る
    needles = [holdout, holdout.replace("/", "."), Path(holdout).name]
    violations: list = []

    for path in Path(base).rglob("*"):
        if not path.is_file() or path.suffix not in TEST_SUFFIXES:
            continue
        rel = path.relative_to(base).as_posix()
        if not _match_paths(rel, source_patterns):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), 1):
            # 「参照」とみなすのは import / require / open 等の実際の取り込みのみ
            if not re.search(r"\b(?:import|from|require|include|open|load|Path)\b", line):
                continue
            if any(n in line for n in needles if n and n != "acceptance"):
                violations.append({"file": rel, "line": lineno, "text": line.strip()[:120]})
                break
            if re.search(r"\btests[./]acceptance\b", line):
                violations.append({"file": rel, "line": lineno, "text": line.strip()[:120]})
                break
    return violations


def check(cfg: dict, base_dir: Path | None = None) -> Result:
    base = base_dir or Path.cwd()
    if not git.is_repo(base):
        return failed("test_tamper: git リポジトリではないため検査できません")

    root = git.repo_root(base) or base
    patterns = cfg.get("paths") or ["tests/**"]

    findings: list = []
    metrics: dict = {}

    # 1) 実装からの hold-out 参照（基準点が無くても検査できる）
    holdout_violations = check_holdout_reference(cfg, base)
    metrics["holdout_references"] = len(holdout_violations)
    for v in holdout_violations:
        findings.append({"kind": "holdout-reference", **v})

    # 2) 基準点との比較
    ref = resolve_baseline(cfg, base)
    if not ref:
        metrics["baseline_ref"] = None
        if holdout_violations:
            return failed(
                f"test_tamper: 実装から hold-out テストへの参照 {len(holdout_violations)}件",
                metrics, findings,
            )
        return skipped(
            "test_tamper: 基準点（jsix/red-* タグ）が無いため差分検査をスキップ"
            "（RED 完了時に `git tag jsix/red-<task-id>` を打ってください）"
        )

    metrics["baseline_ref"] = ref
    if not git.ref_exists(ref, base):
        return failed(f"test_tamper: 基準点 {ref} が存在しません（RED 完了時にタグを打ってください）")

    try:
        before_files = _scan_baseline(ref, patterns, base, root)
    except git.GitError as exc:
        return failed(f"test_tamper: 基準点の読み取りに失敗: {exc}")
    after_files = _scan_worktree(patterns, base)

    before = _aggregate(before_files)
    after = _aggregate(after_files)
    metrics.update({
        "baseline": before,
        "current": after,
        "delta": {k: after[k] - before[k] for k in before},
    })

    blocking: list = list(findings)

    if after["asserts"] < before["asserts"]:
        blocking.append({
            "kind": "assert-removed",
            "detail": f"アサーション {before['asserts']} → {after['asserts']}（{before['asserts'] - after['asserts']} 件減少）",
        })
    if after["tests"] < before["tests"]:
        blocking.append({
            "kind": "test-removed",
            "detail": f"テスト関数 {before['tests']} → {after['tests']}（{before['tests'] - after['tests']} 件減少）",
        })
    if after["skips"] > before["skips"]:
        blocking.append({
            "kind": "skip-added",
            "detail": f"無効化マーカー {before['skips']} → {after['skips']}（{after['skips'] - before['skips']} 件増加）",
        })

    # ファイル別の内訳（証跡用。ブロック判定には使わない）
    empty = {k: 0 for k in COUNT_KEYS}
    empty["digest"] = None
    changed_detail = []
    for path in sorted(set(before_files) | set(after_files)):
        b = before_files.get(path, empty)
        a = after_files.get(path, empty)
        if b != a:
            changed_detail.append({
                "file": path,
                "before": {k: b[k] for k in COUNT_KEYS},
                "after": {k: a[k] for k in COUNT_KEYS},
                "content_changed": b.get("digest") != a.get("digest"),
            })
    metrics["changed_test_files"] = len(changed_detail)

    if blocking:
        kinds = ", ".join(sorted({f["kind"] for f in blocking}))
        return failed(
            f"test_tamper: テストを弱める変更を検出（{kinds}）。基準点 {ref}",
            metrics,
            blocking + changed_detail[:10],
        )

    note = f"（{len(changed_detail)}ファイルに差分あり。弱体化なし）" if changed_detail else ""
    return passed(f"test_tamper: 基準点 {ref} 以降にテストの弱体化なし{note}", metrics, changed_detail[:10])


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="テスト改変（弱体化）の検出")
    parser.add_argument("--baseline-ref", default=None, help="基準点の git ref（既定: $JSIX_TASK_ID → 最新の jsix/red-* タグ）")
    parser.add_argument("--paths", action="append", default=None, help="検査対象の glob（既定 tests/**）")
    parser.add_argument("--holdout-dir", default="tests/acceptance", help="実装からの参照を禁止するディレクトリ")
    args = parser.parse_args(argv)

    cfg = {"holdout_dir": args.holdout_dir}
    if args.baseline_ref:
        cfg["baseline_ref"] = args.baseline_ref
    if args.paths:
        cfg["paths"] = args.paths

    result = check(cfg)
    mark = "⏭ " if result.skipped else ("✅ " if result.ok else "❌ ")
    print(mark + result.summary)
    for f in result.findings[:20]:
        print(f"  - {f.get('kind', 'detail')}: {f.get('detail') or f.get('file')}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
