#!/usr/bin/env python3
"""git を叩くための最小限のヘルパ（言語非依存）。

スコープ検査とテスト改変検出が使う。git が無い / リポジトリでない場合は
例外ではなく None / 空リストを返し、呼び出し側がスキップ扱いにできるようにする。
"""
from __future__ import annotations

import posixpath
import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def _run(args: list, cwd: Path | None = None) -> str:
    try:
        proc = subprocess.run(
            ["git"] + args,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:  # git 自体が無い
        raise GitError("git コマンドが見つかりません") from exc
    if proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} が失敗: {proc.stderr.strip()}")
    return proc.stdout


def is_repo(cwd: Path | None = None) -> bool:
    try:
        return _run(["rev-parse", "--is-inside-work-tree"], cwd).strip() == "true"
    except GitError:
        return False


def head_sha(cwd: Path | None = None) -> str | None:
    try:
        return _run(["rev-parse", "HEAD"], cwd).strip()
    except GitError:
        return None


def ref_exists(ref: str, cwd: Path | None = None) -> bool:
    try:
        _run(["rev-parse", "--verify", "--quiet", ref + "^{commit}"], cwd)
        return True
    except GitError:
        return False


def changed_files(base: str | None = None, cwd: Path | None = None, include_untracked: bool = True) -> list:
    """変更されたファイルのパス（**リポジトリルート相対**）を返す。

    base 指定時は `base..HEAD` ＋ 作業ツリーの未コミット変更。
    base 未指定時は作業ツリーの未コミット変更のみ（＝Stop hook 時点で CC が触ったもの）。

    git のサブコマンドは出力パスの基準が揃っていない（`ls-files` はカレント相対、
    `diff` はリポジトリルート相対。さらに `diff.relative` 設定で変わる）。
    基準を確実に揃えるため、**必ずリポジトリルートで実行し** `--full-name` を付ける。
    """
    root = repo_root(cwd)
    if root is None:
        raise GitError("git リポジトリではありません")

    paths: set = set()

    if base:
        for line in _run(["diff", "--name-only", "--no-renames", base, "HEAD"], root).splitlines():
            if line.strip():
                paths.add(line.strip())

    # 未コミットの変更（staged / unstaged）
    for args in (["diff", "--name-only", "--no-renames"],
                 ["diff", "--name-only", "--no-renames", "--cached"]):
        for line in _run(args, root).splitlines():
            if line.strip():
                paths.add(line.strip())

    if include_untracked:
        for line in _run(["ls-files", "--others", "--exclude-standard", "--full-name"], root).splitlines():
            if line.strip():
                paths.add(line.strip())

    return sorted(paths)


def changed_files_relative(base_dir: Path, ref: str | None = None) -> list:
    """変更ファイルを `base_dir` からの相対パスで返す。

    git が返すのはリポジトリルート相対のパスだが、`.jsix-checks.json` の
    allow / deny glob は設定ファイルのあるディレクトリ基準で書く。モノレポや
    リポジトリ内のサンプルプロジェクトでは両者が食い違うため、ここで揃える。

    `base_dir` の外にあるファイルは**除外する**。そのプロジェクトのスコープ設定が
    管轄するのは自ディレクトリ配下だけであり、リポジトリ内の別プロジェクトの変更を
    このゲートで判定するのは誤りだからである。
    """
    root = repo_root(base_dir)
    if root is None:
        return []
    changed = changed_files(ref, cwd=base_dir)
    base_abs = Path(base_dir).resolve()

    out = []
    for rel in changed:
        absolute = (root / rel).resolve()
        try:
            out.append(absolute.relative_to(base_abs).as_posix())
        except ValueError:
            continue  # base_dir の外 → このプロジェクトの管轄外
    return sorted(out)


def diff_text(base: str, paths: list | None = None, cwd: Path | None = None) -> str:
    """base から作業ツリーまでの unified diff を返す（指定パス配下のみ）。"""
    args = ["diff", "--unified=0", base, "--"]
    args += paths or []
    return _run(args, cwd)


def latest_tag(pattern: str, cwd: Path | None = None) -> str | None:
    """HEAD から到達可能な、pattern に一致する最新のタグ名を返す。"""
    try:
        out = _run(["describe", "--tags", "--abbrev=0", "--match", pattern], cwd).strip()
    except GitError:
        return None
    return out or None


def latest_tag_touching(prefix: str, base_dir: Path) -> str | None:
    """base_dir 配下を変更したコミットに付いた、prefix で始まる最新のタグ名を返す。

    タグはリポジトリ共有のため、1つのリポジトリに複数プロジェクトがあると、
    最新の jsix/red-* が別プロジェクトのタスクのものになりうる。自プロジェクトの
    ディレクトリを変更したコミットを新しい順にたどり、最初に見つかったタグを使う。
    """
    root = repo_root(base_dir)
    if root is None:
        return None
    try:
        rel = Path(base_dir).resolve().relative_to(root.resolve()).as_posix() or "."
        out = _run(["log", "--decorate=short", "--format=%D", "HEAD", "--", rel], root)
    except (GitError, ValueError):
        return None
    for line in out.splitlines():
        for ref in (r.strip() for r in line.split(",")):
            if ref.startswith("tag: ") and ref[5:].startswith(prefix):
                return ref[5:]
    return None


def ls_tree(ref: str, paths: list | None = None, cwd: Path | None = None) -> list:
    """指定 ref に存在するファイルのパス一覧を返す。"""
    args = ["ls-tree", "-r", "--name-only", ref, "--"] + (paths or [])
    return [ln.strip() for ln in _run(args, cwd).splitlines() if ln.strip()]


def show_file(ref: str, path: str, cwd: Path | None = None) -> str | None:
    """指定 ref 時点のファイル内容を返す。存在しなければ None。"""
    try:
        return _run(["show", f"{ref}:{path}"], cwd)
    except GitError:
        return None


def default_base(cwd: Path | None = None) -> str | None:
    """タスクの起点とみなすコミット（既定ブランチとの分岐点）を返す。

    tdd-cycle はフェーズごとにコミットするため、未コミットの差分だけを見ると
    Stop の時点で「変更なし」になり、スコープ検査も G3 も空振りする。ブランチで
    作業している前提で、既定ブランチとの merge-base を起点にする。
    既定ブランチが見つからなければ None（呼び出し側は未コミットの差分だけを見る）。
    """
    candidates = []
    try:
        head = _run(["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"], cwd).strip()
        if head:
            candidates.append(head)
    except GitError:
        pass
    candidates += ["origin/main", "main", "origin/master", "master"]
    for ref in candidates:
        if ref_exists(ref, cwd):
            try:
                return _run(["merge-base", "HEAD", ref], cwd).strip() or None
            except GitError:
                continue
    return None


def diff_fingerprint(base: str | None, base_dir: Path, exclude: list | None = None) -> str | None:
    """base から作業ツリーまでの差分（base_dir 配下、未追跡ファイルを含む）の指紋。

    G3 の判定がどの差分に対するものかを照合するために使う。判定後にコードが
    変わった場合や、別タスクの判定が残っている場合に指紋が一致しなくなる。

    exclude（base_dir 相対）には判定ファイルと証跡の出力先を渡す。これらはゲート自身が
    書くため、含めると判定を書いた瞬間に指紋が変わってしまう。
    """
    import hashlib

    root = repo_root(base_dir)
    if root is None:
        return None
    rel = Path(base_dir).resolve().relative_to(root.resolve()).as_posix() or "."
    pathspec = [rel] + [
        f":(exclude){posixpath.normpath(posixpath.join(rel, e))}" for e in (exclude or [])
    ]
    h = hashlib.sha256()
    try:
        h.update(_run(["diff", "--binary", base or "HEAD", "--"] + pathspec, root).encode("utf-8"))
        untracked = _run(["ls-files", "--others", "--exclude-standard", "--full-name", "--"] + pathspec, root)
    except GitError:
        return None
    for path in sorted(ln.strip() for ln in untracked.splitlines() if ln.strip()):
        h.update(path.encode("utf-8"))
        try:
            h.update((root / path).read_bytes())
        except OSError:
            continue
    return h.hexdigest()[:16]


def repo_root(cwd: Path | None = None) -> Path | None:
    try:
        return Path(_run(["rev-parse", "--show-toplevel"], cwd).strip())
    except GitError:
        return None
