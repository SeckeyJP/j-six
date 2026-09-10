#!/usr/bin/env python3
"""J-SIX G2: mutation score の算出と閾値判定。

読める形式:
  1. mutation-testing-elements JSON（Stryker 系 / PIT の変換出力などの業界共通形式）
     https://github.com/stryker-mutator/mutation-testing-elements
  2. 最小契約 JSON: `{"score": <number>}`
     未対応ツール（mutmut, mutatest 等）はプロジェクト側でアダプタを書き、
     この形にして渡す。アダプタは言語依存なので **plugin ではなく利用者側**に置く。

mutation score の定義（mutation-testing-elements に準拠）:
    score = killed / (killed + survived) * 100
  timeout は killed 扱い、no coverage は survived 扱い、
  runtime error / compile error / ignored は分母から除外する。

判定: `min_score` 未満なら不合格。**未指定なら計測のみ**（合格扱い）。
      閾値の既定値は置かない。根拠のない数値を仕様に固定しないため。

`scope: "changed"` を指定すると、変更ファイルに含まれるファイルだけで score を再計算する。

使い方:
    python jsix_mutation_gate.py --file reports/mutation.json [--min-score 70]

終了コード: 0=合格 or 計測のみ / 1=閾値未満 / 2=入力エラー
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jsix_result import Result, failed, missing_artifact, passed  # noqa: E402

#: 分子に数える status（殺せた）
KILLED = {"Killed", "Timeout"}
#: 分母に数えるが分子に数えない status（生き残った）
SURVIVED = {"Survived", "NoCoverage"}
#: 分母から除外する status
IGNORED = {"CompileError", "RuntimeError", "Ignored", "Pending"}


class MutationParseError(ValueError):
    pass


def _score(killed: int, survived: int) -> float | None:
    denom = killed + survived
    if denom == 0:
        return None
    return killed / denom * 100


def parse_mutation_report(path: Path) -> dict:
    """mutation-testing-elements JSON または最小契約 JSON を読む。"""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MutationParseError(f"JSON の解析に失敗: {exc}") from exc

    if not isinstance(doc, dict):
        raise MutationParseError("トップレベルがオブジェクトではありません")

    if "files" in doc and isinstance(doc["files"], dict):
        return _parse_elements(doc)

    if "score" in doc:
        try:
            score = float(doc["score"])
        except (TypeError, ValueError) as exc:
            raise MutationParseError("score が数値ではありません") from exc
        return {
            "format": "minimal",
            "score": score,
            "killed": doc.get("killed"),
            "survived": doc.get("survived"),
            "per_file": {},
            "survivors": [],
        }

    raise MutationParseError(
        "mutation-testing-elements JSON（files キー）でも最小契約 JSON（score キー）でもありません"
    )


def _parse_elements(doc: dict) -> dict:
    """mutation-testing-elements schema の JSON を集計する。"""
    per_file: dict = {}
    survivors: list = []
    total_killed = total_survived = total_ignored = 0

    for filename, entry in doc["files"].items():
        killed = survived = ignored = 0
        for mutant in entry.get("mutants") or []:
            status = mutant.get("status")
            if status in KILLED:
                killed += 1
            elif status in SURVIVED:
                survived += 1
                survivors.append({
                    "file": filename,
                    "line": (mutant.get("location") or {}).get("start", {}).get("line"),
                    "mutator": mutant.get("mutatorName"),
                    "status": status,
                    "replacement": (mutant.get("replacement") or "")[:80],
                })
            elif status in IGNORED:
                ignored += 1
            else:
                # 未知の status は分母に入れず、無視した数として記録する
                ignored += 1

        per_file[filename] = {"killed": killed, "survived": survived, "ignored": ignored}
        total_killed += killed
        total_survived += survived
        total_ignored += ignored

    return {
        "format": "mutation-testing-elements",
        "score": _score(total_killed, total_survived),
        "killed": total_killed,
        "survived": total_survived,
        "ignored": total_ignored,
        "per_file": per_file,
        "survivors": survivors,
        "schema_version": doc.get("schemaVersion"),
        "thresholds": doc.get("thresholds"),
    }


def _matches_changed(report_path: str, changed: list) -> bool:
    """レポート内のファイルパスが変更ファイル一覧に該当するか。

    レポート側は絶対パスや別基準の相対パスのことがあるため、末尾一致で判定する。
    """
    norm = report_path.replace("\\", "/").lstrip("./")
    for c in changed:
        cn = c.replace("\\", "/")
        if norm == cn or norm.endswith("/" + cn) or cn.endswith("/" + norm):
            return True
    return False


def scoped_score(data: dict, changed: list) -> dict:
    """変更ファイルに限定して score を再計算する。"""
    killed = survived = 0
    files = []
    for filename, agg in data["per_file"].items():
        if _matches_changed(filename, changed):
            killed += agg["killed"]
            survived += agg["survived"]
            files.append(filename)
    return {"score": _score(killed, survived), "killed": killed, "survived": survived, "files": files}


def check(cfg: dict, base_dir: Path | None = None, changed_files: list | None = None) -> Result:
    base = base_dir or Path.cwd()
    target = cfg.get("report") or cfg.get("file")
    if not target:
        return failed("mutation: 設定に report（mutation レポートのパス）がありません")

    path = base / target
    if not path.is_file():
        return missing_artifact("mutation", target, cfg, "mutation testing を実行してください")

    try:
        data = parse_mutation_report(path)
    except MutationParseError as exc:
        return failed(f"mutation: {target} — {exc}")

    scope = cfg.get("scope", "all")
    score = data["score"]
    metrics = {
        "format": data["format"],
        "score": None if score is None else round(score, 2),
        "killed": data.get("killed"),
        "survived": data.get("survived"),
        "ignored": data.get("ignored"),
        "scope": scope,
    }
    label = "全体"

    if scope == "changed":
        if data["format"] == "minimal":
            return failed(
                "mutation: scope=changed は最小契約 JSON では使えません"
                "（ファイル別の内訳が無いため）。mutation-testing-elements 形式にするか scope を外してください"
            )
        if changed_files is None:
            return failed("mutation: scope=changed だが変更ファイル一覧を取得できませんでした（git リポジトリか確認）")
        scoped = scoped_score(data, changed_files)
        metrics.update({
            "scoped_score": None if scoped["score"] is None else round(scoped["score"], 2),
            "scoped_killed": scoped["killed"],
            "scoped_survived": scoped["survived"],
            "scoped_files": scoped["files"],
        })
        score = scoped["score"]
        label = f"変更 {len(scoped['files'])}ファイル"

    survivors = data.get("survivors") or []
    if scope == "changed" and survivors:
        survivors = [s for s in survivors if _matches_changed(s["file"], changed_files or [])]

    if score is None:
        return passed(f"mutation: {label} に判定対象のミュータントがありません（計測のみ）", metrics)

    min_score = cfg.get("min_score")
    if min_score is None:
        return passed(
            f"mutation: {label} score {score:.1f}%（閾値未設定のため計測のみ）",
            metrics,
            survivors[:20],
        )

    min_score = float(min_score)
    metrics["min_score"] = min_score
    if score + 1e-9 < min_score:
        return failed(
            f"mutation: {label} score {score:.1f}% < 閾値 {min_score:.1f}%（生存 {data.get('survived')}件）",
            metrics,
            survivors[:20],
        )
    return passed(f"mutation: {label} score {score:.1f}% ≥ 閾値 {min_score:.1f}%", metrics, survivors[:20])


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="mutation score の閾値判定")
    parser.add_argument("--file", required=True, help="mutation-testing-elements JSON または {\"score\": N}")
    parser.add_argument("--min-score", type=float, default=None, help="最低 mutation score（％）。省略時は計測のみ")
    args = parser.parse_args(argv)

    cfg = {"report": args.file}
    if args.min_score is not None:
        cfg["min_score"] = args.min_score

    result = check(cfg)
    print(("✅ " if result.ok else "❌ ") + result.summary)
    for s in result.findings[:10]:
        print(f"  - 生存: {s.get('file')}:{s.get('line')} {s.get('mutator')} {s.get('replacement', '')}")
    if not result.ok and "見つかりません" in result.summary:
        return 2
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
