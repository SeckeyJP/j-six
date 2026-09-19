"""templates/ のテンプレートを Plugin の各 Skill に同梱コピーする。

マーケットプレイスからインストールされた Plugin は、Plugin ディレクトリだけが
コピーされる。Skill がリポジトリルートの `templates/` を参照していると、利用者の
環境ではファイルが存在せず Skill が失敗する（spec-create は起動直後に止まる）。

そこでテンプレートを Skill ディレクトリに同梱し、Skill からは
`${CLAUDE_SKILL_DIR}/templates/...` で参照する。**正はルートの templates/ のまま**で、
同梱分はこのスクリプトで生成する。直接編集しない。

同梱先から辿れなくなる相対リンク（examples/ の記入済み実例など）は、
GitHub 上の URL に書き換える。

使い方:
    python3 tools/sync_plugin_templates.py          # 同梱コピーを更新
    python3 tools/sync_plugin_templates.py --check  # ずれがあれば 1 で終了（CI 用）
"""
from __future__ import annotations

import argparse
import posixpath
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GITHUB_BLOB = "https://github.com/SeckeyJP/j-six/blob/main/"

#: (正のパス, 同梱先) — いずれもリポジトリルート相対。ディレクトリは配下を丸ごと写す
MAPPINGS = (
    ("templates/spec/requirement-spec.md", "plugin/skills/spec-create/templates/requirement-spec.md"),
    ("templates/spec/design-spec.md", "plugin/skills/spec-create/templates/design-spec.md"),
    ("templates/adr/template.md", "plugin/skills/tdd-cycle/templates/adr-template.md"),
    ("templates/deliverables", "plugin/skills/doc-reverse-gen/templates/deliverables"),
)

HEADER = (
    "<!-- 自動生成: tools/sync_plugin_templates.py が {src} から生成。"
    "直接編集せず、正のファイルを直して再生成すること -->\n"
)

LINK = re.compile(r"(\]\()([^)\s]+)(\))")


def _pairs() -> list:
    """(正のファイル, 同梱先ファイル) を全件列挙する。"""
    pairs = []
    for src_rel, dst_rel in MAPPINGS:
        src = ROOT / src_rel
        if src.is_dir():
            for f in sorted(src.rglob("*.md")):
                rel = f.relative_to(src)
                pairs.append((f, ROOT / dst_rel / rel))
        else:
            pairs.append((src, ROOT / dst_rel))
    return pairs


def _rewrite_links(text: str, src: Path, dst: Path, dest_of: dict) -> str:
    """相対リンクを同梱先から辿れる形に直す。

    リンク先も同梱されていれば同梱先どうしの相対パスに、同梱されていなければ
    GitHub の URL にする。http(s) / mailto / ページ内アンカーはそのまま。
    """

    def repl(m: re.Match) -> str:
        target = m.group(2)
        if re.match(r"^(https?:|mailto:|#)", target):
            return m.group(0)
        path, _, anchor = target.partition("#")
        resolved = (src.parent / path).resolve()
        try:
            repo_rel = resolved.relative_to(ROOT).as_posix()
        except ValueError:
            return m.group(0)  # リポジトリの外 → 触らない
        if resolved in dest_of:
            new = posixpath.relpath(dest_of[resolved].as_posix(), dst.parent.as_posix())
        else:
            new = GITHUB_BLOB + repo_rel
            if resolved.is_dir():
                new = new.replace("/blob/", "/tree/", 1)
        return f"{m.group(1)}{new}{'#' + anchor if anchor else ''}{m.group(3)}"

    return LINK.sub(repl, text)


def render() -> dict:
    """同梱先パス → 生成すべき内容。"""
    pairs = _pairs()
    dest_of = {src.resolve(): dst for src, dst in pairs}
    out = {}
    for src, dst in pairs:
        body = _rewrite_links(src.read_text(encoding="utf-8"), src.resolve(), dst, dest_of)
        out[dst] = HEADER.format(src=src.relative_to(ROOT).as_posix()) + body
    return out


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="書き込まず、ずれがあれば 1 で終了")
    args = parser.parse_args(argv)

    expected = render()
    managed_dirs = {ROOT / d for _, d in MAPPINGS if (ROOT / _).is_dir()}
    stale = [
        f for d in managed_dirs if d.exists() for f in d.rglob("*.md") if f not in expected
    ]

    drift = [p for p, body in expected.items()
             if not p.exists() or p.read_text(encoding="utf-8") != body]

    if args.check:
        for p in drift:
            print(f"ずれ: {p.relative_to(ROOT)}", file=sys.stderr)
        for p in stale:
            print(f"正に無いファイル: {p.relative_to(ROOT)}", file=sys.stderr)
        if drift or stale:
            print("Plugin 同梱のテンプレートが templates/ と一致しません。"
                  "`python3 tools/sync_plugin_templates.py` を実行してください", file=sys.stderr)
            return 1
        print(f"Plugin 同梱のテンプレート {len(expected)} 件は templates/ と一致")
        return 0

    for p in drift:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(expected[p], encoding="utf-8")
    for p in stale:
        p.unlink()
    print(f"更新 {len(drift)} 件 / 削除 {len(stale)} 件（同梱 {len(expected)} 件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
