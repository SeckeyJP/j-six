# 論点1：既存SDD をベースにするか、独自設計するか

## — CC ネイティブ機能と日本品質基準から導く最適解 —

---

## 1. 結論を先に

**CC ネイティブ機能をベースに、日本品質レイヤーを追加する「ハイブリッド」が最適解**と考える。

理由：
1. CC 自体が SDD の主要機能をネイティブに吸収済み（CLAUDE.md、Subagents、Tasks、Hooks）
2. BMAD 等の外部フレームワークは CC の上に独自のレイヤーを被せており、CC のネイティブ進化と衝突するリスクがある
3. 日本のSI品質基準は「フレームワーク」ではなく「品質レイヤー」として上乗せすべき

---

## 2. CC ネイティブ機能の棚卸（2026年3月時点）

CC は単なる「コード生成ツール」ではなく、**自律エージェントプラットフォーム**に進化している。

### 2.1 CC の7つの拡張メカニズム

| # | 機能 | 分類 | 役割 |
|---|---|---|---|
| 1 | **CLAUDE.md** | Knowledge（常時ON） | プロジェクト憲法。全セッションで自動読込 |
| 2 | **Skills** | Knowledge（オンデマンド） | 特定ワークフローの手順書。必要時にのみ読込 |
| 3 | **Subagents** | Worker（独立） | 独立タスクの委譲。別コンテキストで実行、結果のみ返却 |
| 4 | **Agent Teams** | Worker（協調） | 複数エージェントが共有タスクリストとメッセージで協調 |
| 5 | **Hooks** | ライフサイクル制御 | イベント駆動のガードレール（commit前lint、テスト自動実行等） |
| 6 | **MCP Servers** | 外部接続 | DB、Slack、GitHub等の外部ツールとの統合 |
| 7 | **Plugins** | パッケージ | Skills+Agents+Hooksをバンドルして共有 |

### 2.2 SDD の各フェーズに対する CC ネイティブ機能の対応

```
SDD フェーズ              CC ネイティブ機能
─────────────────────────────────────────────────────
Specify（仕様策定）   →   Subagents（並列リサーチ）
                          ask_user_question（インタビューモード）
                          Plan Mode（設計探索）

Design（技術設計）    →   Plan Mode + Subagents（並列技術調査）
                          CLAUDE.md（設計方針の永続化）

Tasks（タスク分解）   →   Native Tasks システム
                          依存関係の自動分析
                          Subagent への自動委譲

Implement（実装）     →   Subagents（TDD の Red/Green/Refactor 分離）
                          Agent Teams（並列実装）
                          git worktree（並列作業空間）
                          Hooks（品質チェックの自動実行）
                          /batch（一括変更）
```

**重要な発見**: SDD の4フェーズに必要な機能は、CC にすべてネイティブで存在する。外部フレームワークを導入しなくても、CC の機能だけで SDD を実現できる。

---

## 3. 既存フレームワークの評価

### 3.1 BMAD Method

**長所**:
- 最も包括的（21エージェント、50以上のワークフロー）
- アジャイル統合（スプリント対応）
- ロール分離が明確（PM、アーキテクト、QA等）
- 大規模プロジェクト向けの構造

**短所**:
- **オーバーヘッドが大きい**: エージェント間のファイルベース受け渡しが煩雑
- **CC ネイティブ機能との重複**: BMAD の Architect Agent ↔ CC の Plan Mode、BMAD の Developer Agent ↔ CC の Subagent 等
- **CC 進化との衝突リスク**: BMAD が CC の上に独自レイヤーを被せているため、CC のアップデート時に破綻する可能性
- **5人未満のチームには非推奨**との公式見解あり（Augment Code, 2026）
- **実際の報告**: 設計変更が必要になった場合、エージェント間の厳格なアクセス制御が足かせになるケースあり

### 3.2 Superpowers

**長所**:
- Anthropic 公式マーケットプレイス入り（品質保証）
- TDD を中心としたシンプルな7フェーズ
- Skills としてインストール可能

**短所**:
- 主にソロ開発者〜小チーム向け
- 日本のSI案件のような組織的プロセスは未考慮

### 3.3 cc-sdd (Kiro 風)

**長所**:
- 軽量で導入しやすい
- Claude Code のスラッシュコマンドとして統合
- 13言語対応

**短所**:
- タスク管理に特化しており、品質管理レイヤーが薄い
- 上流工程（要件定義）の支援が限定的

### 3.4 GitHub Spec Kit

**長所**:
- GitHub 公式
- CLI 提供で CI/CD 統合しやすい

**短所**:
- GitHub エコシステム前提
- フレームワークというよりツール

### 3.5 評価サマリ

| 評価軸 | BMAD | Superpowers | cc-sdd | Spec Kit |
|---|---|---|---|---|
| CC ネイティブ活用度 | 中（独自レイヤー） | 高（Skills統合） | 高（コマンド統合） | 中 |
| 大規模SI案件適性 | ○ | △ | △ | △ |
| 日本品質基準対応 | ×（追加要） | ×（追加要） | ×（追加要） | ×（追加要） |
| 導入・学習コスト | 高 | 低 | 低 | 中 |
| CC進化への追従性 | 低リスク | 高 | 高 | 中 |
| TDD統合 | ○ | ◎ | △ | △ |

**結論**: どのフレームワークも「そのまま使う」のは不適。日本品質レイヤーが欠如している。

---

## 4. 提案：CC-Native + 日本品質レイヤー

### 4.1 アーキテクチャ

```
┌────────────────────────────────────────────────────┐
│              日本品質レイヤー（独自設計）             │
│                                                    │
│  ・品質ゲート定義（Phase Gate 基準）               │
│  ・設計書テンプレート（逆生成用）                   │
│  ・品質メトリクス基準（バグ密度・カバレッジ等）     │
│  ・レビュー手順・チェックリスト                     │
│  ・トレーサビリティ管理                             │
│  ・IPA/共通フレームマッピング                       │
│  ・納品物フォーマット定義                           │
│                                                    │
├────────────────────────────────────────────────────┤
│              SDD プロセス（世界標準準拠）             │
│                                                    │
│  Specify → Design → Tasks → Implement → Verify    │
│                                                    │
│  ※ SDD の4フェーズ + 品質検証フェーズ              │
│                                                    │
├────────────────────────────────────────────────────┤
│              CC ネイティブ機能（基盤）                │
│                                                    │
│  CLAUDE.md │ Skills │ Subagents │ Agent Teams │    │
│  Hooks │ MCP │ Plugins │ Tasks │ git worktree │    │
│  Plan Mode │ /batch │ /loop                        │
│                                                    │
└────────────────────────────────────────────────────┘
```

### 4.2 各レイヤーの責務

**CC ネイティブ機能（基盤）**: プロセスの「実行エンジン」
- 何かを「する」力。コード生成、テスト実行、並列処理、外部連携等
- Anthropic が継続的にアップデートするため、ここに依存するのが最も安全

**SDD プロセス（世界標準準拠）**: プロセスの「骨格」
- SDD の原則（Spec First、Phase Gate、TDD）に準拠
- 特定のフレームワーク実装には依存せず、原則レベルで採用
- CC ネイティブ機能で実装するため、外部フレームワーク不要

**日本品質レイヤー（独自設計）**: プロセスの「品質保証」
- 日本のSI業界固有の品質基準・成果物文化に対応
- Skills + Hooks + CLAUDE.md として CC に統合
- この部分が本プロジェクトの独自価値

### 4.3 具体的な実装形態

日本品質レイヤーは、以下の CC ネイティブ機能として実装する。

| 品質レイヤーの要素 | CC での実装形態 | 内容 |
|---|---|---|
| **品質ゲート定義** | CLAUDE.md + Hooks | Phase完了時に自動チェックするHook + 基準をCLAUDE.mdに記述 |
| **設計書テンプレート** | Skills | 設計書逆生成のスキル（基本設計書、詳細設計書、IF設計書等） |
| **品質メトリクス基準** | CLAUDE.md + Hooks | カバレッジ閾値、バグ密度基準をCLAUDE.mdに定義、Hookで自動計測 |
| **レビュー手順** | Skills + Subagents | レビューチェックリストをSkillとして定義、Subagentがレビュー実行 |
| **トレーサビリティ** | Skills + CLAUDE.md | 要件→Spec→タスク→テスト→コードの追跡をSkillで管理 |
| **納品物生成** | Skills | 従来フォーマット（Excel/Word）での設計書出力スキル |

### 4.4 Plugin としてのパッケージング

上記をまとめて、CC Plugin として配布可能な形にする。

```
j-six-plugin/
├── CLAUDE.md                 # 日本品質基準のベースライン
├── skills/
│   ├── spec-create/          # Spec 策定スキル（日本語テンプレート）
│   ├── design-review/        # 設計レビュースキル
│   ├── doc-reverse-gen/      # 設計書逆生成スキル
│   │   ├── basic-design/     #   基本設計書
│   │   ├── detail-design/    #   詳細設計書
│   │   ├── if-design/        #   IF設計書
│   │   └── db-design/        #   DB設計書
│   ├── quality-metrics/      # 品質メトリクス計測スキル
│   └── traceability/         # トレーサビリティ管理スキル
├── agents/
│   ├── qa-reviewer/          # 品質レビューエージェント
│   ├── security-reviewer/    # セキュリティレビューエージェント
│   └── doc-generator/        # ドキュメント生成エージェント
├── hooks/
│   ├── pre-commit-quality/   # コミット前品質チェック
│   ├── phase-gate-check/     # Phase Gate 自動判定
│   └── coverage-check/       # カバレッジ閾値チェック
└── templates/
    ├── claude-md/            # プロジェクト種別ごとのCLAUDE.mdテンプレート
    │   ├── web-app.md
    │   ├── batch-system.md
    │   └── api-service.md
    └── spec/                 # Specテンプレート（日本語）
        ├── requirement-spec.md
        └── design-spec.md
```

---

## 5. この方式のメリット

### 5.1 CC 進化への追従性

BMAD 等の外部フレームワークは CC の上に独自レイヤーを構築しているため、CC のメジャーアップデート時に互換性問題が発生するリスクがある。

本提案は CC ネイティブ機能のみで構築するため：
- CC のアップデートに自然に追従
- 新機能（Agent Teams、/loop 等）を即座に活用可能
- Anthropic の推奨パターンに常に準拠

### 5.2 段階的導入の容易さ

Plugin として提供するため：
- `npx j-six install` 等のワンコマンドで導入可能
- プロジェクトに応じて使うスキルを取捨選択可能
- 既存プロジェクトへの後付け導入も可能

### 5.3 コミュニティ貢献

- Plugin として公開することで、日本のSI業界全体で共有可能
- 各社のカスタマイズ（設計書テンプレート等）も容易
- GitHub での共同改善が可能

---

## 6. 参考にすべき先行事例のエッセンス

完全採用はしないが、各フレームワークから取り入れるべきエッセンスがある。

| フレームワーク | 取り入れるエッセンス | CC-Native での実現方法 |
|---|---|---|
| **BMAD** | ロール分離（PM/Architect/QA）の考え方 | Subagent の description で役割を定義 |
| **BMAD** | Phase Gate の厳格な管理 | Hooks で Phase 完了条件を自動チェック |
| **Superpowers** | TDD の Red-Green-Refactor 分離 | Subagent 分離（テスト作成/実装/リファクタリング） |
| **Superpowers** | Socratic Brainstorming | Plan Mode + ask_user_question の活用 |
| **cc-sdd** | Kiro 風コマンド体系 | Skills をスラッシュコマンドとして定義 |
| **Agent Factory** | Master-Clone アーキテクチャ | Task(...) で汎用エージェントを委譲 |
| **Anthropic 社内** | Writer/Reviewer パターン | 別セッションの CC でコードレビュー |
| **Anthropic 社内** | CLAUDE.md の徹底活用 | 日本向けテンプレートを充実 |

---

## 7. 残る論点と次のステップ

### 7.1 本論点の結論

**CC ネイティブ + 日本品質レイヤーのハイブリッド方式を採用する**。

外部フレームワーク（BMAD等）は「参考」にとどめ、CC ネイティブ機能上に日本品質レイヤーを独自設計し、CC Plugin として実装・配布する。

### 7.2 次の論点への接続

| 優先度 | 論点 | 本論点の結論との関係 |
|---|---|---|
| **2** | 設計書逆生成の限界と対策 | doc-reverse-gen スキルの設計に直結 |
| **3** | CC自律実行の範囲 | Phase Gate と Hooks の設計に直結 |
| **4** | 段階的移行パス | Plugin の段階的導入設計に直結 |

次に論点2「設計書逆生成の限界と対策」に進むか、あるいは本論点についてさらに議論を深めるか。

---

> **改訂履歴**
>
> | 版 | 日付 | 内容 |
> |---|---|---|
> | 0.1 | 2026-03-29 (H.Sekita) | 初版作成 |

---

### 参考文献

**CC ネイティブ機能**
- Anthropic. "Best Practices for Claude Code". https://code.claude.com/docs/en/best-practices
- Anthropic. "Create custom subagents". https://code.claude.com/docs/en/sub-agents
- Anthropic. "How Anthropic teams use Claude Code" (2025.07). https://claude.com/blog/how-anthropic-teams-use-claude-code
- Anthropic. "Enabling Claude Code to work more autonomously". https://www.anthropic.com/news/enabling-claude-code-to-work-more-autonomously
- Dean Blank. "A Mental Model for Claude Code" (2026.03). https://levelup.gitconnected.com/a-mental-model-for-claude-code-skills-subagents-and-plugins-3dea9924bf05
- Shrivu Shankar. "How I Use Every Claude Code Feature" (2025.11). https://blog.sshh.io/p/how-i-use-every-claude-code-feature
- ClaudeFast. "Claude Code Agent Teams: The Complete Guide 2026". https://claudefa.st/blog/guide/agents/agent-teams

**SDD フレームワーク**
- BMAD-METHOD (GitHub). https://github.com/bmad-code-org/BMAD-METHOD
- BMAD Documentation. https://docs.bmad-method.org/
- Augment Code. "6 Best Spec-Driven Development Tools for AI Coding in 2026". https://www.augmentcode.com/tools/best-spec-driven-development-tools
- Panaversity / Agent Factory. "Chapter 16: SDD with Claude Code". https://agentfactory.panaversity.org/docs/General-Agents-Foundations/spec-driven-development
- cc-sdd (GitHub). https://github.com/gotalab/cc-sdd
- Pasqualepillitteri.it. "Superpowers Claude Code Complete Guide". https://www.pasqualepillitteri.it/en/news/215/superpowers-claude-code-complete-guide
- CGI. "Spec-driven development: From vibe coding to intent engineering" (2026.03). https://www.cgi.com/en/blog/artificial-intelligence/spec-driven-development

**CC 実践事例**
- alexop.dev. "Forcing Claude Code to TDD" (2025.11). https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/
- alexop.dev. "Spec-Driven Development with Claude Code in Action" (2026.02). https://alexop.dev/posts/spec-driven-development-claude-code-in-action/
- Codingscape. "How Anthropic engineering teams use Claude Code every day" (2025.12). https://codingscape.com/blog/how-anthropic-engineering-teams-use-claude-code-every-day
- ranthebuilder.cloud. "Claude Code Best Practices: Lessons From Real Projects" (2026.03). https://ranthebuilder.cloud/blog/claude-code-best-practices-lessons-from-real-projects/

※ 本ドキュメントの結論（CC ネイティブ + 日本品質レイヤーのハイブリッド方式、Plugin 構成）は著者のオリジナル設計。各フレームワークの評価は上記参考文献と著者の分析に基づく。
