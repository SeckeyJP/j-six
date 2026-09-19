---
name: quality-metrics
description: J-SIX Phase 5 の品質メトリクス集計。mutation score、G3 judge の却下率、ゲート失敗理由の分布、人間レビュー指摘数を集計し、プロセス自体の健全性を評価する。
allowed-tools: Read, Bash, Glob, Grep
---

# 品質メトリクス集計スキル

J-SIX プロセスの Phase 5（品質検証）で、品質状態と**プロセス自体の健全性**を集計する。

> **v2.1 での役割変更**: 個々のタスクの合否判定は Phase 4 の G1〜G3 に移った。
> このスキルはタスクを横断して**傾向**を見る。「今回のコードが良いか」ではなく
> 「ゲートが機能しているか」「どこで詰まっているか」を判断するための集計である。

## Ⅰ. プロセスの健全性メトリクス（v2.1 で追加）

証跡パッケージ（`reports/evidence/*/evidence.json`）を横断して集計する。

### 1. mutation score

テストスイート自体の有効性。カバレッジが「テストが実行した行」を測るのに対し、
mutation score は「テストが誤りを検出できるか」を測る。

```bash
python3 - <<'EOF'
import json, glob
for path in sorted(glob.glob("reports/evidence/*/evidence.json")):
    doc = json.load(open(path))
    m = ((doc["gates"].get("g2") or {}).get("checks") or {}).get("mutation") or {}
    score = (m.get("metrics") or {}).get("score")
    if score is not None:
        print(f"{doc['task_id']}: {score}%")
EOF
```

**閾値について**: J-SIX は mutation score の既定閾値を定めていない。根拠のない数値を
基準にしないためである。**自プロジェクトで数タスク計測してから**下限を決めること。
生存ミュータントが多い箇所は、テストが薄い箇所を正確に指している。

### 2. G3 judge の却下率と却下理由の分布

**judge を継続するか外すかの判断材料**になる。

| 観測 | 解釈 | 取るべき行動 |
|---|---|---|
| 却下率が高く、理由が `scope` に偏る | タスク定義の許可ファイル範囲が曖昧 | Phase 3 のタスク分解を見直す |
| 却下率が高く、理由が `requirement` に偏る | 受入条件が実装に伝わっていない | Spec の受入条件の粒度を見直す |
| 却下率がほぼ 0 になった | モデルの能力向上で judge が不要になった可能性 | G3 を外すことを検討する |
| 妥当な変更まで却下されている | judge が硬直的になっている | G3 を外すことを検討する |

> **G3 は固定装備ではない**。Spotify は Honk の初期に LLM judge で大きな効果を得たが、
> モデルの改善に伴い judge を撤去している（判定が硬直的で妥当な変更まで止めたため）。
> J-SIX でもこのメトリクスを見て外す判断を行う。G1・G2・G4 は決定論的でコストが低いため
> この判断の対象外。

### 3. ゲート失敗理由の分布

**Phase 0 の月次ループ（CLAUDE.md をコードとして扱う運用）の入力**になる。

| 頻出する失敗 | 還元先 |
|---|---|
| G1 lint / format | PostToolUse Hook（書いた時点で直す） |
| G1 scope | Phase 3 のタスク分解（許可範囲の定義） |
| G2 test_tamper | エスカレーション運用の見直し |
| G2 traceability | Spec の ID 付与ルール、red-agent への指示 |
| G3 scope | タスク定義の粒度 |

### 4. 人間レビュー指摘数 / PR

ゲートが機能しているかの**外形指標**。ゲートを強化した後に人間レビューの指摘が
減っていなければ、ゲートが本質的な問題を捕まえていない。
`reports/evidence/*/07_approval.md` の「指摘事項」欄から集計する。

---

## Ⅱ. 個別タスクの計測項目

以下は Phase 4 の G1 / G2 が自動判定済み。Phase 5 で再実行せず、
**証跡パッケージの値を読む**こと。

### 参考: 各項目の計測手段

### 1. テストカバレッジ

プロジェクトのテストフレームワークを検出し、カバレッジを計測する。

```bash
# フレームワーク別コマンド例（自動検出して実行）
# Jest:     npx jest --coverage
# pytest:   pytest --cov --cov-report=term
# Go:       go test -coverprofile=coverage.out ./...
```

報告項目:
- 行カバレッジ（Line Coverage）
- 分岐カバレッジ（Branch Coverage）
- カバレッジが低いファイル上位5件

### 2. コード品質

利用可能なリンターを検出して実行する:
- ESLint / Biome（JavaScript/TypeScript）
- Ruff / Flake8（Python）
- golangci-lint（Go）

報告項目:
- エラー数 / 警告数
- カテゴリ別集計（セキュリティ、パフォーマンス、スタイル等）

### 3. Spec ⇔ コード整合性

`docs/specs/` の受入条件と、テストコードを照合する:
- 受入条件に対応するテストが存在するか
- テストされていない受入条件の一覧

### 4. ADR カバレッジ

コード内の主要な技術判断（フレームワーク選択、DB選択、認証方式等）に ADR が存在するか確認する。

### 5. セキュリティチェック（基本）

- ハードコードされた秘密情報の検出（API キー、パスワード等のパターン）
- 既知の脆弱なパッケージの検出（`npm audit` / `pip audit` 等）

## 品質ゲートの基準

基準は `.jsix-checks.json` が持つ（このスキルではなく設定ファイル）。

| 指標 | 設定キー | 既定 |
|---|---|---|
| テストカバレッジ（行） | `gates.g2.coverage.min` | 未設定なら計測のみ |
| mutation score | `gates.g2.mutation.min_score` | **未設定（実測してから決める）** |
| SARIF の severity | `gates.g1.sast.max_severity` | 未設定なら集計のみ |
| テストのスキップ数 | `gates.g2.tests.max_skipped` | 未設定なら制限なし |
| REQ / PROP のテスト網羅率 | `gates.g2.traceability` | 100%（未トレースがあれば不合格） |

## 出力フォーマット

```markdown
## 品質メトリクスレポート

**プロジェクト**: [名前]
**集計期間**: [開始] 〜 [終了]
**対象タスク数**: N（reports/evidence/ の証跡パッケージ）

### プロセスの健全性

| メトリクス | 値 | 前回 | 判断 |
|---|---|---|---|
| mutation score（中央値） | XX% | XX% | [テストスイートの有効性] |
| G3 judge 却下率 | XX%（N/M） | XX% | [judge を継続するか] |
| G3 却下理由の内訳 | correctness N / requirement N / scope N | — | [どこを直すか] |
| 人間レビュー指摘数 / PR | X.X 件 | X.X 件 | [ゲートが機能しているか] |

### ゲート失敗理由の分布

| ゲート | チェック | 失敗回数 | 還元先 |
|---|---|---|---|
| G1 | lint | N | PostToolUse Hook 化を検討 |

### 個別タスクの指標（証跡から引用）

| タスク | カバレッジ | mutation | hold-out | G3 |
|---|---|---|---|---|
| TASK-001 | 99% | 60% | 10/10 | PASS |

### 次のアクション

- [ ] [ゲート失敗の傾向から導いた CLAUDE.md / Hook / Skill への還元]
- [ ] [mutation score の下限をいくつに設定するか]
```

**数値はすべて証跡パッケージから引用すること。** 推定値を書かない。
実測していない指標は「未計測」と明記する。

## 決定論的バックエンド

品質ゲートの判定は、LLM の推定ではなく決定論的スクリプトで行う。個別の判定は
Phase 4 の G1〜G4 が実行済みなので、Phase 5 では通常このスクリプトを直接呼ばない。

```bash
# 全ゲートをまとめて実行（証跡パッケージも生成される）
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/jsix_run_checks.py" --json reports/gate.json

# 個別に確認する場合
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/jsix_coverage_gate.py" --file coverage.xml --min 95
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/jsix_mutation_gate.py" --file reports/mutation.json
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/jsix_sarif_gate.py" --file reports/sast.sarif --max-severity error
```

実例は `examples/approval-workflow/`（`make gate` / `make gate-ci`）。
