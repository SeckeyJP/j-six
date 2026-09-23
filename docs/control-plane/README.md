# J-SIX Hub（構想）

**Author**: H.Sekita | **状態**: 構想段階（本ディレクトリの内容はすべて仮説であり、実装・実証されたものではない）

J-SIX Hub は、J-SIX を大規模・複数チーム・複数ベンダーの案件に適用するための構想である。旧称は J-SIX Control Plane。
J-SIX 本体は、個人〜小規模チームが Claude Code Plugin として使う前提で設計されている。大規模案件では次の問題が起きると考えている。

- 開発者ごとに環境（CC・Plugin・CLAUDE.md・テンプレートの版数）がばらつく
- Skill の実行タイミングや Phase の順序が個人の判断に委ねられている
- 承認・レビュー・ゲート判定・証跡が各自の PC とリポジトリに散在し、横断的に見えない

## 一文定義

> J-SIX の工程と AI エージェントの実行を管理し、対象・版・証拠に基づくプロセス適合性の判断と、複数チーム・複数ベンダーにまたがる逸脱回収を支援する開発基盤の構想。

## 3層構成

```
[J-SIX Hub：Control Plane]
  工程状態・ゲート・承認・証跡・Interface Contract・メトリクス
        │ タスク投入（Spec・CLAUDE.md・契約を添えて）
        ▼
[Execution Plane]
  タスクごとにコンテナ生成 → CC + J-SIX Plugin → TDD → 品質ゲート → PR → 破棄
        │
        ▼
[Git：正本]
  Spec / ADR / コード / テスト / 逆生成設計書
```

構想の詳細（課題、状態モデルとスイムレーン図、関連研究とポジショニング、仮説と評価計画、課題と制約）は [concept.md](concept.md) にまとめている。

## 決定事項と ADR

| # | 決定 | 記録 |
|---|---|---|
| D1 | 正本は Git。Hub は Git から再構築できる読み取りモデルだけを持つ | [ADR-0001](adr/0001-git-as-source-of-truth.md) |
| D2 | 差別化軸はプロセス適合性の統制（アクセス統制ではない） | [ADR-0002](adr/0002-process-conformance-as-differentiator.md) |
| D3 | J-SIX は Hub に依存しない。依存は Hub → J-SIX の一方向 | [ADR-0003](adr/0003-dependency-direction-and-process-as-data.md) |
| D4 | プロセス定義をデータ化して J-SIX に置く（`process/jsix-process.yaml`） | [ADR-0003](adr/0003-dependency-direction-and-process-as-data.md) |
| D5 | サンプル環境は実行記録を再生するリプレイ型 | [ADR-0004](adr/0004-replay-sample-environment.md) |
| D6 | 逸脱の扱い（Phase 逆戻り、ゲート例外承認、エスカレーション、ローカル退避、Interface Contract 違反）を状態モデルに明示する | [concept.md §4.3](concept.md#43-逸脱と回収)、[`process/jsix-process.yaml`](../../process/jsix-process.yaml) の `deviations` |
| D7 | 実装は CC ネイティブのまま。マルチモデル・オーケストレータは作らない。モデル非依存性はプロセス定義の記述レベルで主張する | 本表のみ（スコープの決定のため ADR は作らない） |
| D8 | 中央実行を基本とし、ローカル CC への退避路を残す。ローカルの成果物は必ずゲートを再通過する | [ADR-0005](adr/0005-central-execution-with-local-fallback.md) |
| D9 | Hub 自体を J-SIX で開発し、その記録をケーススタディにする | 本表のみ。開発は [j-six-hub](https://github.com/SeckeyJP/j-six-hub) リポジトリで行う |

## 実行基盤の試作前に満たす条件（著者提案）

- [ADR-0006](adr/0006-trust-boundaries-and-policy.md)：主体別の権限、必須検査、方針変更と緊急失効
- [ADR-0007](adr/0007-execution-recovery.md)：実行要求の先行記録、結果不明時の照合と取消し
- [構想 §5.2](concept.md#52-interface-contract)：共通運営主体、証拠の開示範囲、利用者登録の責任

D2 は独自の認証基盤を作らないという位置付けであり、既存の認証・権限・Git 保護への依存はある。
これらの ADR は未実装の設計案であり、既存のリプレイが強制する機能ではない。

## 関係するリポジトリ

| リポジトリ | 置くもの |
|---|---|
| `SeckeyJP/j-six`（本リポジトリ） | 構想文書・ADR（本ディレクトリ）、プロセス定義 [`process/`](../../process/) |
| `SeckeyJP/j-six-hub` | リプレイ型サンプル Web アプリ（https://seckeyjp.github.io/j-six-hub/ ）、リプレイ用イベントデータ（MIT） |
