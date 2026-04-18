# J-SIX：Japanese SI Transformation

## — Claude Code で日本のSI開発を再定義する、AI ネイティブ開発プロセス —

**Version 1.0** | 2026-03-29 | Author: H.Sekita

---

## エグゼクティブサマリー

J-SIX（Japanese SI Transformation）は、Anthropic Claude Code（以下CC）の能力を最大限に活用することを前提に再設計した、日本のSI業界向けシステム開発プロセスである。

従来のV字モデルに CC を「貼り付ける」のではなく、CC の能力を前提にプロセス自体を再構築した。世界標準の Spec-Driven Development（SDD）の原則を採用しつつ、日本特有の品質基準・設計書文化・受発注構造に対応する「日本品質レイヤー」を独自に設計している。

### 4つの設計原則

| # | 原則 | 内容 |
|---|---|---|
| 1 | **CC ネイティブ** | 外部フレームワーク（BMAD等）に依存せず、CC のネイティブ機能のみで構築 |
| 2 | **3層ドキュメント** | Spec（Why）+ ADR（Why Not）+ 逆生成設計書（What/How）で従来設計書を超越 |
| 3 | **TDD が品質の中核** | テストファーストにより CC 自律実行の品質を担保 |
| 4 | **段階的移行** | 既存V字モデルから3ステージで移行。既存案件を止めない |

### 期待効果

※ 以下の数値は、各種事例報告と著者の分析に基づく **推定目標値** である。プロジェクト特性により異なる。

| 指標 | 従来V字モデル | J-SIX | 改善率 |
|---|---|---|---|
| 実装工数 | 100% | 30-40% | **60-70%削減**（※1） |
| 設計書⇔コード乖離 | 常態化 | 原理的にゼロ | **解消** |
| 設計判断の記録率 | 10-20%（暗黙知） | 80%以上（ADR） | **4倍以上**（※2） |
| テストカバレッジ | 60-70% | 85-95% | **15-25pt向上**（※3） |
| 手戻り率 | 15-25% | 5-10% | **半減以下**（※4） |

> ※1 個別事例では40-80%の生産性向上が報告されている[2][16]が、組織全体への適用時は控えめに見積
> ※2 ADR 運用定着時の目標値
> ※3 TDD 全面適用時の一般的目標水準
> ※4 プロトタイプ駆動と TDD による早期検証効果を想定した著者推定

---

## 第1章：なぜ従来プロセスを再設計するのか

### 1.1 V字モデルの前提崩壊

V字モデルは「実装コストが高く、変更が困難」な時代に最適化されたプロセスである。CC により以下の前提が崩壊した。

| 崩壊した前提 | CC がもたらす現実 |
|---|---|
| 実装コストが高い | CC は数分で数百行のコードを生成する |
| 人間が全行コードを書く | CC が大部分を生成し、人間はレビュー・判断に集中 |
| テスト作成が高コスト | テストコードを自動生成。TDD サイクルが CC 前提で回る |
| 変更が困難 | 変更コストが劇的に低下。リファクタリングも CC 任せ |

### 1.2 しかし変わらないもの

| 変わらない前提 | 理由 |
|---|---|
| 何を作るかの合意は人間が行う | ビジネス要件・ステークホルダー合意は AI で代替不可 |
| アーキテクチャ判断は人間が行う | 技術選定・非機能要件のトレードオフは文脈依存 |
| 品質の最終責任は人間にある | CC 生成コードには人間より多いロジックエラーを含む報告あり |
| トレーサビリティは必要 | 監査・保守において要件→実装→テストの追跡可能性は不可欠 |
| 顧客との合意プロセスは必要 | 日本のSIモデルでは受発注関係がある |

### 1.3 CC の現実的な能力水準（2026年3月時点）

| 指標 | 数値 | 出典 |
|---|---|---|
| 初回自律実行成功率 | 約33% | Anthropic RL Engineering チームの報告 [2][16][19] |
| AI生成PRのイシュー率 | 人間の約1.7倍 | CodeRabbit 調査（2025.12、470PR分析）[8] |
| セキュリティイシュー | 人間の最大2.74倍 | 同上 [8] |
| Sonnet 4.5 コード編集エラー率 | 0%（内部ベンチマーク） | Anthropic 公式発表（2026.02）[4] |

**含意**: CC は「速いが雑な新人開発者」に類似する特性を持つ。適切なガードレール（TDD + Hooks + レビュー）があれば実用水準だが、「任せっきり」は危険。

> **注**: 上記データは各出典の発表時点のものであり、モデルの世代更新（Opus 4.6 / 4.7 等）により能力水準は継続的に改善されている。最新のベンチマークは各出典元を参照のこと。

---

## 第2章：J-SIX プロセス全体像

### 2.1 7つの Phase

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 0: プロジェクト憲法策定（CLAUDE.md）     [自律度 L1]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1: 要求の合意（Spec 策定）              [自律度 L1-L2]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         ↓ 🚪 品質ゲート: 顧客承認
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 2: 技術設計（Design Spec + プロトタイプ） [自律度 L2]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         ↓ 🚪 品質ゲート: 設計レビュー
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 3: タスク分解                            [自律度 L2]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         ↓ 🚪 品質ゲート: タスク承認（自律実行圏への最後のゲート）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 4: TDD 実装  ★生産性の源泉             [自律度 L3-L4]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         ↓ 🚪 品質ゲート: 自動テスト通過 + CC 相互レビュー
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 5: 品質検証                              [自律度 L2-L3]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         ↓ 🚪 品質ゲート: 品質基準達成判定
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 6: ドキュメント生成（3層戦略）           [自律度 L3]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         ↓ 🚪 品質ゲート: 納品物レビュー
```

### 2.2 従来V字モデルとの本質的な違い

| 観点 | V字モデル（従来） | J-SIX |
|---|---|---|
| **Source of Truth** | 設計書（Excel/Word） | Spec + コード + テスト（三位一体） |
| **設計書の位置づけ** | 実装前に書く「設計図」 | 実装後にコードから逆生成する「納品物」 |
| **実装者** | 人間（SE/PG） | CC 自律実行（TDD サイクル） |
| **品質保証** | レビュー会議 + テスト | TDD + CC相互レビュー + 人間サンプリング |
| **テストの位置づけ** | 実装後に書く | **実装前に書く（TDD）** |
| **並列性** | 基本的に直列 | **Agent Teams + git worktree で大規模並列** |
| **変更耐性** | 低い（凍結管理） | **高い（TDD + 自動リグレッション）** |

### 2.3 自律度の5段階モデル

```
L0: 手動          人間が全て実行、CC は参考回答のみ
L1: CC 支援       人間が主導、CC が補助
L2: CC 主導       CC が実行案を作成、人間が毎回承認
L3: CC 自律       CC が自律実行、人間は結果を監督・異常時介入
L4: CC 完全自律   CC が自律実行、人間は介入しない（自動テストのみ）
```

**基本原則**: 判断（What/Why）は人間、実行（How）は CC。影響範囲が大きいほど人間の関与を増やす。

---

## 第3章：各 Phase の詳細

### Phase 0: プロジェクト憲法策定（CLAUDE.md）

**自律度**: L1（人間が主導、CC が支援）
**従来の対応物**: 開発標準、コーディング規約、プロジェクト計画書

CLAUDE.md はプロジェクトの全ルールを CC が理解・実行可能な形式で記述した「憲法」。CC の全出力がこの文書に制約される。Anthropic 社内の調査でも「CLAUDE.md の充実度と CC 出力品質は直接相関する」と報告されている [2][19]。

**CLAUDE.md に定義すべき内容**:

```
CLAUDE.md
├── プロジェクト概要
│   ├── システムの目的・業務概要
│   ├── アーキテクチャ方針
│   └── 技術スタック
├── 開発規約
│   ├── コーディング規約（命名規則、フォーマット）
│   ├── ディレクトリ構成ルール
│   ├── Git 運用ルール（ブランチ戦略、コミットメッセージ）
│   └── エラーハンドリング方針
├── 設計方針
│   ├── DB 設計ルール
│   ├── API 設計ルール
│   └── 画面設計ルール
├── 品質基準
│   ├── テストカバレッジ目標
│   ├── 静的解析ルール
│   └── パフォーマンス基準
├── ADR ルール
│   ├── ADR 必須の判断基準
│   └── ADR テンプレートの場所
└── 禁止事項・制約
    ├── 使用禁止ライブラリ
    ├── セキュリティ制約
    ├── 変更禁止ファイル一覧
    └── 本番環境に関する制約
```

---

### Phase 1: 要求の合意

**自律度**: L1-L2（人間が主導、CC がドラフト生成・曖昧性検出）
**従来の対応物**: 要件定義工程
**成果物**: 要求 Spec（3層戦略の第1層）

**フロー**:
1. ステークホルダーヒアリング（人間）
2. CC インタビューモード：曖昧性の発見・深掘り質問の自動生成
3. CC による並列リサーチ（Subagents で業務ドメイン・技術動向を調査）
4. 要求 Spec 作成（CC がドラフト生成 → 人間がレビュー）
5. 業務フロープロトタイプ生成（CC が即時生成 → 顧客確認）
6. 🚪 品質ゲート: 顧客承認

**CC 機能**: Plan Mode, ask_user_question, Subagents（並列リサーチ）

---

### Phase 2: 技術設計

**自律度**: L2（人間がアーキテクチャ判断、CC が具現化）
**従来の対応物**: 基本設計工程
**成果物**: Design Spec + 実動プロトタイプ + ADR（3層戦略の第1層・第2層）

**フロー**:
1. アーキテクチャ決定（人間が判断）→ ADR に記録
2. Design Spec 作成
   - DB 設計 → DDL → ER図 を一貫生成（CC）
   - API 設計 → OpenAPI Spec 自動生成（CC）
   - 画面設計 → 実動 HTML プロトタイプ生成（CC）
3. 技術選定の裏付け調査（CC Subagents が並列実行）→ ADR に記録
4. 🚪 品質ゲート: 設計レビュー（プロトタイプベースのレビュー）

**レビューの革新**: 「紙の設計書」ではなく「動くプロトタイプ」でレビュー。「設計書には書いてあるが動かない」問題を根絶。

**CC 機能**: Plan Mode, Subagents（並列調査）, CLAUDE.md（設計方針の永続化）

---

### Phase 3: タスク分解

**自律度**: L2（CC がタスク提案、人間が承認）
**従来の対応物**: 詳細設計工程 + WBS 作成
**成果物**: タスク一覧（受入条件付き）

**フロー**:
1. Design Spec → タスク自動分解（CC）
2. 各タスクに受入条件（テスト条件）を定義（CC）
3. 依存関係・並列実行可能性の分析（CC）
4. 🚪 品質ゲート: タスク承認（自律実行圏への最後のゲート）

**Phase 3 の完了 = CC 自律実行の開始**。ここまでの上流工程で「何を作るか」「どう作るか」「どう検証するか」が全て定義される。

**CC 機能**: Native Tasks システム

---

### Phase 4: TDD 実装 ★生産性の源泉

**自律度**: L3-L4（CC が自律実行、人間は監督・異常時介入）
**従来の対応物**: 実装 + 単体テスト

**J-SIX の最も革新的な Phase**。3つのメカニズムで品質を担保しつつ、CC の自律実行で最大の生産性を発揮する。

#### メカニズム①: TDD サイクル（サブエージェント分離）

```
🔴 RED:    テスト作成（CC サブエージェント A）
   ↓       テスト失敗を確認 → テストをコミット【チェックポイント】
🟢 GREEN:  最小実装（CC サブエージェント B）
   ↓       テスト通過を確認 → 実装をコミット【チェックポイント】
🔵 REFACTOR: リファクタリング（CC サブエージェント C）
   ↓       テスト通過を再確認 → コミット

※ サブエージェント分離 = コンテキスト汚染の防止 [14]
※ テストをコミットしてから実装にハンドオフ = テスト改変の防止 [1][16]
```

#### メカニズム②: Writer/Reviewer パターン

コードを生成した CC とは別の CC インスタンスがレビュー。自分が書いたコードへのバイアスを排除。

#### メカニズム③: 並列実行

```
タスク A ─── [TDD サイクル] → [Review] → ✅
タスク B ─── [TDD サイクル] → [Review] → ✅  ← git worktree で並列
タスク C ─── [TDD サイクル] → [Review] → ✅  ← Agent Teams で協調
タスク D ─── [待機: A に依存] → 開始 → ...
```

#### エスカレーション条件（CC → 人間）

以下の場合、CC は自律実行を中断し人間に判断を仰ぐ。

| 条件 | 理由 | 実装 |
|---|---|---|
| Spec に記載のない要件が必要 | 業務判断は人間の領域 | ask_user_question |
| セキュリティに関わる判断 | リスク判断は人間が行うべき | Hook で検出 |
| 外部 IF 仕様の変更が必要 | 他システムへの影響 | Hook で検出 |
| テスト3回連続失敗 | 根本的な設計問題の可能性 | Hook で監視 |
| アーキテクチャ変更が必要 | 影響範囲大 | CLAUDE.md で変更禁止ファイル定義 |

**CC 機能**: Subagents（TDD 分離）, Agent Teams（並列実行）, git worktree, Hooks, チェックポイント

---

### Phase 5: 品質検証

**自律度**: L2-L3（自動チェック + 人間サンプリング検証）
**従来の対応物**: 結合テスト + 総合テスト + 品質管理

**フロー**:
1. 自動品質チェック（Hooks で実行）
   - テストカバレッジ計測
   - 静的解析（セキュリティ・脆弱性・コード品質）
   - Spec ⇔ コード整合性検証
2. 人間による検証
   - CC コードレビュー結果のサンプリング検証
   - 設計判断・業務ロジックの妥当性確認
   - 探索的テスト（人間の直感によるテスト）
3. Spec からテストケースを自動生成し、E2E テスト実行
4. 🚪 品質ゲート: 品質基準達成判定

**品質基準は従来と同等を維持**: バグ密度、カバレッジ率等の定量基準は変えない。自動化により網羅性はむしろ向上。

---

### Phase 6: ドキュメント生成（3層戦略）

**自律度**: L3（CC が自動生成、人間がレビュー・承認）
**従来の対応物**: 各工程で作成していた設計書を一括生成

**J-SIX 最大のパラダイムシフト**: 設計書は「事前に書くもの」から「事後に生成するもの」へ。

#### 3層ドキュメント戦略

```
┌────────────────────────────────────────────────────────┐
│ 第1層：Spec（Phase 1-2 で作成済み）                     │
│   「なぜ作るか」「何を作るか」                          │
│   ・要求 Spec（業務背景・目的・スコープ・制約）         │
│   ・Design Spec（アーキテクチャ方針・技術選定理由）     │
├────────────────────────────────────────────────────────┤
│ 第2層：ADR（Phase 2-4 で随時記録済み）                  │
│   「なぜそう判断したか」「他の選択肢は何だったか」       │
│   ・設計判断とその理由                                  │
│   ・検討した代替案と却下理由                            │
│   ・前提条件・制約の根拠                                │
├────────────────────────────────────────────────────────┤
│ 第3層：逆生成設計書（Phase 6 で自動生成）               │
│   「何をどう実装したか」                                │
│   ・基本設計書・詳細設計書・IF設計書・DB設計書          │
│   ・テスト仕様書・テスト結果                            │
│   ・ADR の内容を「設計根拠」欄に自動統合                │
└────────────────────────────────────────────────────────┘
```

#### なぜ3層が従来の設計書より優れるか

| 情報カテゴリ | 従来V字モデル | J-SIX（3層戦略） |
|---|---|---|
| 構造情報（What/How） | ○（設計書に記載） | ◎（コードから正確に逆生成） |
| 業務背景（Why Business） | △（形骸化しがち） | ◎（Spec で記録） |
| 設計判断理由（Why Technical） | △（暗黙知に留まる） | ◎（ADR で記録） |
| 却下した代替案（Why Not） | ×（記録されない） | ◎（ADR で記録） |
| 設計書⇔コードの整合性 | △（乖離が頻発） | ◎（原理的に一致） |
| トレーサビリティ | ○（手動管理） | ◎（自動リンク） |

🚪 品質ゲート: 納品物レビュー（従来フォーマットでの出力も対応）

---

## 第4章：技術基盤（CC ネイティブ機能の活用）

### 4.1 アーキテクチャ

```
┌────────────────────────────────────────────────┐
│           日本品質レイヤー（独自設計）           │
│  品質ゲート / 設計書テンプレート / 品質メトリクス │
│  レビュー手順 / トレーサビリティ / 納品物定義    │
├────────────────────────────────────────────────┤
│           SDD プロセス（世界標準準拠）            │
│  Specify → Design → Tasks → Implement → Verify  │
├────────────────────────────────────────────────┤
│           CC ネイティブ機能（基盤）               │
│  CLAUDE.md │ Skills │ Subagents │ Agent Teams │  │
│  Hooks │ MCP │ Plugins │ Tasks │ git worktree │  │
└────────────────────────────────────────────────┘
```

### 4.2 CC 機能の Phase 別マッピング

| Phase | CLAUDE.md | Skills | Subagents | Agent Teams | Hooks | その他 |
|---|---|---|---|---|---|---|
| P0: 憲法策定 | ◎策定 | | | | | Plan Mode |
| P1: 要求合意 | ◎参照 | Spec テンプレート | 並列リサーチ | | | ask_user_question |
| P2: 技術設計 | ◎参照 | Design Spec | 並列調査 | | ADR チェック | Plan Mode |
| P3: タスク分解 | ◎参照 | | | | | Native Tasks |
| P4: TDD 実装 | ◎参照 | TDD Skill | Red/Green/Refactor | 並列実行 | 品質チェック | git worktree, チェックポイント |
| P5: 品質検証 | ◎参照 | 品質メトリクス | | | 品質ゲート判定 | |
| P6: ドキュメント | ◎参照 | 設計書逆生成 | | | | |

### 4.3 CC Plugin 構成

日本品質レイヤーを CC Plugin としてパッケージ化する。

```
j-six-plugin/
├── CLAUDE.md                    # 日本品質基準のベースライン
├── skills/
│   ├── spec-create/             # Spec 策定スキル（日本語テンプレート）
│   ├── design-review/           # 設計レビュースキル
│   ├── tdd-cycle/               # TDD サイクル管理スキル
│   ├── doc-reverse-gen/         # 設計書逆生成スキル
│   │   ├── basic-design/        #   基本設計書
│   │   ├── detail-design/       #   詳細設計書
│   │   ├── if-design/           #   IF設計書
│   │   └── db-design/           #   DB設計書
│   ├── quality-metrics/         # 品質メトリクス計測スキル
│   └── traceability/            # トレーサビリティ管理スキル
├── agents/
│   ├── red-agent/               # TDD Red Phase エージェント
│   ├── green-agent/             # TDD Green Phase エージェント
│   ├── refactor-agent/          # TDD Refactor Phase エージェント
│   ├── qa-reviewer/             # 品質レビューエージェント
│   └── doc-generator/           # ドキュメント生成エージェント
├── hooks/
│   ├── pre-commit-quality/      # コミット前品質チェック
│   ├── phase-gate-check/        # Phase Gate 自動判定
│   ├── adr-check/               # 設計判断検出 → ADR 提案
│   ├── escalation-monitor/      # エスカレーション条件監視
│   └── coverage-check/          # カバレッジ閾値チェック
└── templates/
    ├── claude-md/               # CLAUDE.md テンプレート
    ├── spec/                    # Spec テンプレート（日本語）
    ├── adr/                     # ADR テンプレート
    └── design-doc/              # 設計書テンプレート
```

---

## 第5章：段階的移行パス

### 5.1 3ステージ移行マップ

```
              Stage 0        Stage 1          Stage 2           Stage 3
              (現状)         (3ヶ月)          (3-6ヶ月)         (6ヶ月〜)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
プロセス       V字           V字+CC補助       SDD+V字互換       J-SIX
自律度         L0            L1-L2            L2-L3             L3-L4
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLAUDE.md      なし     ──→  基本版     ──→  拡充版     ──→   完全版
Spec           なし          なし       ──→  並行導入   ──→   唯一の上流成果物
ADR            なし          なし       ──→  運用開始   ──→   全判断を記録
TDD            なし          なし       ──→  新規のみ   ──→   全面適用
設計書         事前作成      事前+CC支援 ──→  二重作成   ──→   逆生成のみ
Hooks          なし          なし       ──→  基本セット ──→   完全セット
Agent Teams    なし          なし            なし       ──→   並列実行
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
工数削減       0%            20-30%           40-50%            60-70%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 5.2 Stage 1: CC 補助 V字モデル（3ヶ月）

**方針**: V字モデルのプロセスは変えない。各工程で CC を補助的に活用。

**導入するもの**: CLAUDE.md（基本版）、実装+UT での CC 活用（L2）、効果計測の仕組み

**完了基準**: 実装工数20%以上削減、CC生成コードのバグ密度が人間の2倍以内、チーム全員がCC を日常的に使用

### 5.3 Stage 2: CC 駆動ハイブリッド（3-6ヶ月）

**方針**: V字の骨格を維持しつつ、内部プロセスを CC 駆動に置換。

**導入するもの**: Spec テンプレート、ADR 運用、新規モジュールでの TDD、Hooks 基本セット、設計書の二重作成（従来+逆生成の品質比較）

**完了基準**: 工数40%以上削減、逆生成設計書が従来と同等品質、ADR が主要判断の80%以上を記録

### 5.4 Stage 3: J-SIX（6ヶ月〜）

**方針**: J-SIX プロセス（Phase 0-6）の全面適用。

**導入するもの**: Agent Teams、git worktree 運用、Writer/Reviewer パターン、設計書逆生成の全面移行、品質ダッシュボード

### 5.5 投資対効果（5人チームの場合）

※ 以下は仮定条件（CC Max 5x $100/月/人、人件費80万円/人月）に基づく **試算** であり、実際はプロジェクト特性により異なる。

| ステージ | CC 費用（月額） | 工数削減額（月額） | 月次 ROI |
|---|---|---|---|
| Stage 1 | 約7.5万円 | 約100万円（25%削減） | **+92.5万円** |
| Stage 2 | 約7.5万円 | 約180万円（45%削減） | **+172.5万円** |
| Stage 3 | 約7.5万円 | 約260万円（65%削減） | **+252.5万円** |

---

## 第6章：日本特有の課題への対応

### 6.1 設計書文化

**対策**: Phase 6 でコードから設計書を逆生成。フォーマットは従来互換（Excel/Word）。コードが Source of Truth のため乖離が原理的に発生しない。

### 6.2 受発注・多重下請け構造

**対策**: CLAUDE.md により全参加者のルールを統一。Plugin として共有することで、下請け各社でも同一品質を確保。

### 6.3 品質保証部門（QA）

**対策**: QA の役割を「テスト戦略策定 + サンプリング検証 + 探索的テスト」に再定義。テスト実行の自動化によりQAは本質的な品質活動に集中。

### 6.4 IPA/共通フレーム・PMBOK

**対策**: J-SIX の Phase は共通フレームのアクティビティにマッピング可能。Phase 6 の設計書により監査証跡も従来互換で提供。

### 6.5 顧客が事前設計書を求める場合

**段階的対策**:
1. **短期**: Design Spec + プロトタイプを「基本設計書相当」として提出
2. **中期**: Spec + プロトタイプ + ADR を設計書の代替として合意
3. **長期**: 業界全体で「Spec + コード + テスト + ADR = 設計書」の認識を普及

---

## 第7章：リスクと対策

| リスク | 影響度 | 対策 |
|---|---|---|
| CC 生成コードの品質ばらつき | 高 | TDD + Hooks + Writer/Reviewer で多層防御 |
| 開発者のスキル低下 | 中 | 「AI開発オーケストレーター」への役割転換。レビュー能力を重視した育成 |
| セキュリティ（コード外部送信） | 高 | Enterprise プラン + VPC。機密情報マスキングルール |
| CC 依存によるベンダーロック | 中 | CLAUDE.md/Spec/ADR はベンダー非依存の Markdown。プロセスの原則は他ツールにも適用可能 |
| 顧客・監査への説明責任 | 高 | 3層戦略による従来以上のトレーサビリティ。品質メトリクスの継続的提示 |
| CC サービス障害 | 中 | 従来方式へのフォールバック手順を整備。Spec + タスク一覧があれば人間でも実装可能 |

---

## 第8章：人間の役割の再定義

### J-SIX における人間の不可替な役割

| 役割 | 内容 | Phase |
|---|---|---|
| **ビジネス翻訳者** | ステークホルダーの要求を Spec に翻訳 | P1 |
| **アーキテクト** | 技術的判断・トレードオフの決定 | P2 |
| **品質の門番** | Phase Gate での承認・判定 | P1-P6 |
| **CLAUDE.md 設計者** | プロジェクト憲法の策定・継続的改善 | P0（継続） |
| **サンプリング検証者** | CC 出力の妥当性をサンプリングで確認 | P4-P6 |
| **顧客折衝者** | 顧客との合意形成 | P1, P6 |
| **探索的テスター** | 人間の直感による創造的テスト | P5 |

### SE/PG の進化

```
【従来】  SE: 設計書を書く人  →  PG: コードを書く人

【J-SIX】SE/PG 統合 → 「AI 開発オーケストレーター」
  ・Spec を書き、CC に指示を出す
  ・CC の出力をレビューし、判断する
  ・CLAUDE.md を育てる
  ・品質メトリクスを監視する
  ・エスカレーション時に判断する
```

---

## 付録

### A. ドキュメント構成（本プロジェクトの全成果物）

| # | ドキュメント | 内容 | 状態 |
|---|---|---|---|
| 本書 | J-SIX プロセス完成版 | 全体像の統合ドキュメント | ✅ |
| 補足 | [Phase 4 TDD ワークスルー](walkthrough-phase4-tdd.md) | TDD サイクルの具体的コマンド・プロンプト例 | ✅ |
| 補足 | [レガシーコード適用ガイド](guide-legacy-code.md) | 既存コードベースへの段階的適用戦略 | ✅ |
| 01 | プロセス俯瞰図（初版） | V字+CC貼り付け版（参考） | ✅ |
| 01a | J-SIX プロセス提案 | Phase 0-6 の初期提案 | ✅ |
| 02 | 論点1: SDD vs 独自設計 | CC ネイティブ+日本品質レイヤーの設計根拠 | ✅ |
| 03 | 論点2: 設計書逆生成 | 3層戦略の設計根拠 | ✅ |
| 04 | 論点3: 自律実行範囲 | 5段階モデルの設計根拠 | ✅ |
| 05 | 論点4: 段階的移行 | 3ステージ移行パスの設計根拠 | ✅ |

### B. 今後の展開予定

| # | テーマ | 形態 | 状態 |
|---|---|---|---|
| 1 | J-SIX 概論（本書の要約版） | Qiita/Zenn 記事 | 予定 |
| 2 | CLAUDE.md 設計・運用ガイド | GitHub MD + 記事 | ✅ テンプレート完成 |
| 3 | 3層ドキュメント戦略の実践 | 記事 | 予定 |
| 4 | TDD × CC サブエージェント実践 | 記事 | 予定 |
| 5 | 設計書逆生成 Skill の実装 | GitHub（Skill コード） | ✅ 完成 |
| 6 | j-six Plugin | GitHub（Plugin） | ✅ 完成 |
| 7 | 導入事例・ROI レポート | 記事 | 予定 |

### C. 用語集

| 用語 | 定義 |
|---|---|
| CC | Claude Code（Anthropic のエージェント型コーディングツール） |
| J-SIX | Japanese SI Transformation。本ドキュメントで提案する CC フル活用・AI ネイティブ開発プロセス |
| SDD | Spec-Driven Development（仕様駆動開発） |
| ADR | Architecture Decision Records（アーキテクチャ判断記録） |
| TDD | Test-Driven Development（テスト駆動開発） |
| Phase Gate | 工程完了時の品質判定・承認ポイント |
| CLAUDE.md | CC のプロジェクト設定ファイル（プロジェクト憲法） |
| Spec | 仕様書（要求 Spec / Design Spec） |
| L0-L4 | CC の自律度レベル（0=手動、4=完全自律） |
| 逆生成 | 実装済みコードから設計書を自動生成すること |
| 3層戦略 | Spec + ADR + 逆生成設計書 による文書体系 |

### D. 参考文献

#### Anthropic 公式

- [1] Anthropic. "Best Practices for Claude Code". https://code.claude.com/docs/en/best-practices
- [2] Anthropic. "How Anthropic teams use Claude Code" (2025.07). https://claude.com/blog/how-anthropic-teams-use-claude-code
- [3] Anthropic. "How AI is Transforming Work at Anthropic" (2025). https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic
- [4] Anthropic. "Introducing Claude Sonnet 4.5" (2026.02). https://www.anthropic.com/news/claude-sonnet-4-5
- [5] Anthropic. "Enabling Claude Code to work more autonomously". https://www.anthropic.com/news/enabling-claude-code-to-work-more-autonomously
- [6] Anthropic. "Create custom subagents - Claude Code Docs". https://code.claude.com/docs/en/sub-agents
- [7] Anthropic. "How Claude Code works - Claude Code Docs". https://code.claude.com/docs/en/how-claude-code-works

#### AI コード品質研究

- [8] CodeRabbit. "State of AI vs Human Code Generation Report" (2025.12). https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report
- [9] Martin Fowler. "How far can we push AI autonomy in code generation?". https://martinfowler.com/articles/pushing-ai-autonomy.html

#### Spec-Driven Development（SDD）・フレームワーク

- [10] Panaversity / Agent Factory. "Chapter 16: Spec-Driven Development with Claude Code". https://agentfactory.panaversity.org/docs/General-Agents-Foundations/spec-driven-development
- [11] BMAD-METHOD (GitHub). https://github.com/bmad-code-org/BMAD-METHOD
- [12] CGI. "Spec-driven development: From vibe coding to intent engineering" (2026.03). https://www.cgi.com/en/blog/artificial-intelligence/spec-driven-development
- [13] Augment Code. "6 Best Spec-Driven Development Tools for AI Coding in 2026". https://www.augmentcode.com/tools/best-spec-driven-development-tools

#### CC 実践・活用事例

- [14] alexop.dev. "Forcing Claude Code to TDD: An Agentic Red-Green-Refactor Loop" (2025.11). https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/
- [15] alexop.dev. "Spec-Driven Development with Claude Code in Action" (2026.02). https://alexop.dev/posts/spec-driven-development-claude-code-in-action/
- [16] DataCamp. "Claude Code Best Practices: Planning, Context Transfer, TDD" (2026.03). https://www.datacamp.com/tutorial/claude-code-best-practices
- [17] Dean Blank. "A Mental Model for Claude Code: Skills, Subagents, and Plugins" (2026.03). https://levelup.gitconnected.com/a-mental-model-for-claude-code-skills-subagents-and-plugins-3dea9924bf05
- [18] Shrivu Shankar. "How I Use Every Claude Code Feature" (2025.11). https://blog.sshh.io/p/how-i-use-every-claude-code-feature
- [19] Codingscape. "How Anthropic engineering teams use Claude Code every day" (2025.12). https://codingscape.com/blog/how-anthropic-engineering-teams-use-claude-code-every-day
- [20] ranthebuilder.cloud. "Claude Code Best Practices: Lessons From Real Projects" (2026.03). https://ranthebuilder.cloud/blog/claude-code-best-practices-lessons-from-real-projects/

#### ADR（Architecture Decision Records）

- [21] adr.github.io. "Architectural Decision Records". https://adr.github.io/
- [22] Adolfi.dev. "AI generated Architecture Decision Records" (2025.11). https://adolfi.dev/blog/ai-generated-adr/

#### その他

- [23] Fujitsu. "Software analysis and visualization service" (2025.02). https://info.archives.global.fujitsu/global/about/resources/news/press-releases/2025/0204-01.html
- [24] Pasqualepillitteri.it. "Superpowers Claude Code Complete Guide" (2026). https://www.pasqualepillitteri.it/en/news/215/superpowers-claude-code-complete-guide
- [25] Pasqualepillitteri.it. "Spec-Driven Development AI Framework Guide" (2026). https://www.pasqualepillitteri.it/en/news/158/framework-ai-spec-driven-development-guide-bmad-gsd-ralph-loop

### E. 本ドキュメントの性質について

J-SIX は著者が設計したオリジナルの開発プロセス提案であり、上記参考文献の知見を統合・再構成したものである。具体的には以下の通り。

- **J-SIX の7Phase 構成、3層ドキュメント戦略、自律度5段階モデル**: 著者のオリジナル設計
- **SDD の原則（Spec First, Phase Gate, TDD）**: 世界標準の SDD コミュニティの共有知見 [10][12]
- **CC ネイティブ機能の活用パターン**: Anthropic 公式ドキュメント [1][5][6][7] および実践者の知見 [14][15][17][18] に基づく
- **品質データ**: 公開された調査報告 [3][8] に基づく
- **日本品質レイヤー**: 日本のSI業界の実務慣行に基づく著者の設計

期待効果の数値（工数削減率等）は著者の推定であり、実プロジェクトでの検証はこれからの課題である。

---

> **改訂履歴**
>
> | 版 | 日付 | 内容 |
> |---|---|---|
> | 1.0 | 2026-03-29 (H.Sekita) | 初版（4論点の議論を統合） |
> | 1.0.1 | 2026-04-18 (H.Sekita) | データ時点注記を追加。IPA リンク修正 |

---

**License**: CC BY 4.0（クリエイティブ・コモンズ 表示 4.0 国際）
