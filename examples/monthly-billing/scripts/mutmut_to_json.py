#!/usr/bin/env python3
"""mutmut の結果を J-SIX の最小契約 JSON に変換する（プロジェクト側のアダプタ）。

**なぜ plugin ではなくここに置くか**

J-SIX Plugin は言語別ツールを直接呼ばない。標準フォーマット（mutation-testing-elements
JSON）をパースして閾値判定するだけである。mutmut はこの形式を出力しないため、変換が要る。
その変換は mutmut という特定ツールに依存する処理なので、**利用者側（このサンプル）**に置く。
他の言語・ツールを使うプロジェクトは、それぞれのアダプタを自分の側に書けばよい。

出力する最小契約:
    {"score": <number>, "killed": <int>, "survived": <int>, "tool": "mutmut", ...}

使い方:
    python3 scripts/mutmut_to_json.py --out reports/mutation.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

#: mutmut results の出力行（例: "    app.workflow.xǁFooǁbar__mutmut_1: survived"）
RESULT_LINE = re.compile(r"^\s*(?P<name>\S+):\s*(?P<status>\w[\w ]*)\s*$")

#: 分子に数える（殺せた）/ 分母に数えるが分子に数えない（生き残った）/ 分母から除外
KILLED = {"killed", "timeout"}
SURVIVED = {"survived", "no tests"}
IGNORED = {"skipped", "suspicious", "not checked", "check was successful"}


#: 生成されたミュータント関数の識別子（例: xǁWorkflowServiceǁsubmit__mutmut_3）
MUTANT_NAME = re.compile(r"\b([A-Za-z_][\w\u0080-\uffff]*__mutmut_\d+)\b")


def count_total_mutants(mutants_dir: Path) -> int:
    """生成されたミュータントの総数を数える。

    `mutmut results` は**殺せなかったミュータントしか出力しない**ため、
    分母（総数）は生成物から数える必要がある。
    """
    total = 0
    for path in sorted(Path(mutants_dir).rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        total += len(set(MUTANT_NAME.findall(text)))
    return total


def parse_results(text: str) -> dict:
    """`mutmut results` の出力から、殺せなかったミュータントを分類する。"""
    counts = {"survived": 0, "ignored": 0}
    survivors = []
    other = []
    for line in text.splitlines():
        m = RESULT_LINE.match(line)
        if not m:
            continue
        status = m.group("status").strip().lower()
        name = m.group("name")
        if status in SURVIVED:
            counts["survived"] += 1
            survivors.append(name)
        elif status in KILLED:
            # 通常は出力されないが、出たら分子に数える
            counts.setdefault("killed_listed", 0)
            counts["killed_listed"] += 1
        else:
            counts["ignored"] += 1
            other.append(f"{name}: {status}")
    counts["survivors"] = survivors
    counts["other"] = other
    return counts


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="mutmut → J-SIX 最小契約 JSON")
    parser.add_argument("--out", default="reports/mutation.json")
    parser.add_argument("--python", default=".venv-mut/bin/python",
                        help="mutmut を動かす Python（mutmut 3.x は Python 3.10+ が必要）")
    parser.add_argument("--mutants-dir", default="mutants/app",
                        help="mutmut が生成したミュータントのディレクトリ（総数を数えるために使う）")
    args = parser.parse_args(argv)

    proc = subprocess.run([args.python, "-m", "mutmut", "results"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"ERROR: mutmut results が失敗しました\n{proc.stderr}", file=sys.stderr)
        return 2

    counts = parse_results(proc.stdout)
    total = count_total_mutants(args.mutants_dir)
    if total == 0:
        print(f"ERROR: {args.mutants_dir} にミュータントが見つかりません（mutmut run を先に実行してください）",
              file=sys.stderr)
        return 2

    killed = total - counts["survived"] - counts["ignored"]
    denominator = killed + counts["survived"]
    if denominator <= 0:
        print("ERROR: 判定対象のミュータントが0件です", file=sys.stderr)
        return 2

    version = subprocess.run([args.python, "-m", "mutmut", "--version"],
                             capture_output=True, text=True).stdout.strip()

    doc = {
        "score": round(killed / denominator * 100, 2),
        "killed": killed,
        "survived": counts["survived"],
        "ignored": counts["ignored"],
        "total": total,
        "tool": "mutmut",
        "tool_version": version,
        "survivors": counts["survivors"],
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"mutation score: {doc['score']}%（killed {doc['killed']} / survived {doc['survived']}）→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
