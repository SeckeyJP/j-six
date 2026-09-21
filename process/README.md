# J-SIX プロセス定義（データ版）

`docs/J-SIX.md` の Phase・ゲート・成果物・役割・遷移を、機械で読めるデータとして記述したもの。
J-SIX Plugin と J-SIX Hub の双方が参照する前提で置いている
（[ADR-0003](../docs/control-plane/adr/0003-dependency-direction-and-process-as-data.md)）。

| ファイル | 内容 |
|---|---|
| [`jsix-process.yaml`](jsix-process.yaml) | プロセス定義本体 |
| [`jsix-process.schema.json`](jsix-process.schema.json) | JSON Schema（draft 2020-12） |
| [`plugin-integration.md`](plugin-integration.md) | Plugin から参照する場合の設計メモ（未実装） |

## 原則

- **正は `docs/J-SIX.md`**。食い違う場合は J-SIX.md を正とし、yaml を直す。yaml の都合で J-SIX.md を書き換えない
- 各要素に **`source`**（J-SIX.md の該当箇所）と **`origin`**（出どころ）を持たせる
  - `jsix`：J-SIX.md が定義しているもの
  - `hub-concept`：J-SIX Hub の構想（[concept.md](../docs/control-plane/concept.md)）で追加したもの。J-SIX 単体では使わない
- 特定のモデル・ツールの名前（Skill 名など）は書かない（決定事項 D7）。自律度の名称は J-SIX.md の「CC 支援」「CC 主導」等を「AI 支援」「AI 主導」等に置き換えている

## 構成

| キー | 内容 |
|---|---|
| `autonomy_levels` | 自律度 L0〜L4 |
| `roles` | 役割（人間 / AI / システム）。人間の役割は J-SIX.md 第8章 |
| `artifacts` | 成果物 |
| `check_kinds` | ゲートを構成するチェックの種類（決定論的 / LLM 判定 / 人間承認 / 証跡生成）と、証跡パッケージの区分（証跡 / 参考所見 / 承認）の対応 |
| `gates` | ゲート。層（`layers`）とチェック（`checks`）を持つ。P4 の `task_quality_gate` は G1→G4 の順序固定（`ordered: true`） |
| `phases` | Phase。`gate`・入出力の成果物・自律度・実行形態（`continuous` / `sequential` / `per_task`） |
| `transitions` | Phase 間の遷移と条件 |
| `state_machines` | Phase とタスクの状態（`hub-concept`） |
| `escalation_conditions` | エスカレーション条件（J-SIX.md Phase 4） |
| `deviations` | 逸脱の種類と回収手順（決定事項 D6。エスカレーション以外は `hub-concept`） |

## 検証

```bash
python3 -m pip install pyyaml jsonschema pytest
python3 -m pytest tools/tests -q          # 検証スクリプト自体のテスト
python3 tools/validate_process.py         # スキーマ + 参照整合性
```

`tools/validate_process.py` は、スキーマでは表せない次の規則を検査する。
ID の重複、存在しない Phase・ゲート・成果物・役割・状態・逸脱への参照、ゲートと Phase の相互参照、
人間承認に承認者があること・承認者が人間であること、**タスク単位のゲートに人間承認を置かないこと**（人間承認は Phase 境界に限定する）、
状態機械のすべての状態に初期状態から到達できること、`origin: jsix` の要素が J-SIX.md を出典にしていること。

CI（`.github/workflows/process-definition.yml`）で同じ検証を実行する。

## 版と参照のしかた

J-SIX Hub などの外部からは、**タグまたはコミット SHA を指定して**取り込む。コピーして独自に改変しない。
yaml を変更したらタグを打ち、参照側で取り込む版を明示的に上げる。

## J-SIX.md との照合結果（2026-09-22、J-SIX.md v2.1）

yaml は J-SIX.md に従って書いた。J-SIX.md は変更していない。

### 叩き台（J-SIX Hub の検討時の状態モデル案）と J-SIX.md の違い

yaml は J-SIX.md の側に合わせた。

| # | 叩き台 | J-SIX.md | yaml の扱い |
|---|---|---|---|
| 1 | P0 の後に「承認」ゲートがある | P0 にゲートはない。CLAUDE.md は月次ループで継続的に改訂する | `gate: null`、`mode: continuous` |
| 2 | ゲートは「決定論的チェック＋人間承認」の組 | P4 のゲートは G1〜G4 で、G3 は LLM 判定、G4 は証跡生成。P4 に人間承認はない | チェックの種類を4つ（決定論的 / LLM 判定 / 人間承認 / 証跡生成）にした |
| 3 | P5 のゲート名「品質判定」 | 「品質基準達成判定」 | J-SIX.md の名称 |

### J-SIX.md に明記がなく、yaml で解釈したもの

| # | 箇所 | 内容 | yaml の扱い |
|---|---|---|---|
| 4 | P4 → P5 の遷移 | P5 に進む条件が書かれていない | 全タスクの完了（`all_tasks_done`）と仮定した |
| 5 | 各ゲートの承認者 | 第8章は「品質の門番」が P1〜P6 のゲートで承認するとし、Phase 1・6 は顧客との合意とする。ゲートごとの承認者は明記されていない | 顧客承認＝顧客・顧客折衝者、設計レビュー＝品質の門番・アーキテクト、タスク承認＝品質の門番、品質基準達成判定＝品質の門番・サンプリング検証者・探索的テスター、納品物レビュー＝顧客・顧客折衝者・品質の門番 |
| 6 | P5 のゲートの中身 | 結合・E2E テストは Phase 5 のフローにあるが、ゲートの判定に含むかは明記されていない | 決定論的チェックとしてゲートに含めた |

### J-SIX.md 内の不整合の候補

| # | 箇所 | 内容 |
|---|---|---|
| 7 | 2.3 自律度 L4 と Phase 4「G3 は固定装備ではない」 | L4 の条件は「G1〜G4 全層通過」だが、G3 は却下率を見て外すことがある。G3 を外したプロジェクトで L4 の条件をどう読むかが書かれていない（yaml では G3 を `optional: true` とした） |
| 8 | Phase 4 の G1 と Plugin の設定 | J-SIX.md の G1 は「型」を含むが、Plugin の `.jsix-checks.json` に型検査のキーはない（[plugin-integration.md](plugin-integration.md)） |
| 9 | Phase 4「工程上いま満たせない失敗」 | 同じ失敗が3回続いたら Stop を許可し、ゲートは未達のまま残す。これは逸脱の一種だが、エスカレーション条件にも逸脱の一覧にも入っていない（yaml ではモデル化していない） |

### Hub の構想で追加したもの（`origin: hub-concept`）

Phase とタスクの状態機械、逸脱の種類（エスカレーション以外）、Interface Contract（成果物・契約所有者・G1 のチェック）。
J-SIX 単体の動作には影響しない。J-SIX.md に取り込むかは未決である。
