# 論点3：CC 自律実行の範囲

## — リスクベースの自律度フレームワーク —

---

## 1. 現実のデータから出発する

CC の自律実行能力について、楽観論でも悲観論でもなく、データに基づいて判断する。

### 1.1 公開されている実績データ

| 指標 | 数値 | 出典 |
|---|---|---|
| CC 初回自律実行成功率 | **約33%** | Anthropic RL Engineering チームの報告（複数の二次ソースで引用）[※1] |
| AI生成PRのイシュー率（人間比） | **約1.7倍** | CodeRabbit調査（2025.12、470PR分析）[※2] |
| ロジック/正確性エラー | 人間の **約1.75倍** | 同上 [※2] |
| セキュリティイシュー | 人間の **最大2.74倍** | 同上 [※2] |
| エラーハンドリングの抜け | 人間の **約2倍** | 同上 [※2] |
| Sonnet 4.5 コード編集エラー率 | **0%**（内部ベンチマーク） | Anthropic公式発表（2026.02）[※3] |
| タスク複雑度の推移（Anthropic社内） | 平均 3.2 → 3.8（5段階） | Anthropic Economic Index（2025.8）[※4] |

> ※1 https://claude.com/blog/how-anthropic-teams-use-claude-code / https://codingscape.com/blog/how-anthropic-engineering-teams-use-claude-code-every-day / https://www.datacamp.com/tutorial/claude-code-best-practices
> ※2 https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report
> ※3 https://www.anthropic.com/news/claude-sonnet-4-5
> ※4 https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic

### 1.2 このデータが意味すること

**CCは「速いが雑な新人開発者」のような特性を持つ。**

- 単純なタスクは高い成功率
- 複雑なタスクでは初回成功率が低い（約33%）が、リトライにより改善
- ロジックエラー・セキュリティ問題は人間より多い
- ただし、テストによるフィードバックループがあれば自己修正可能
- モデルの進化は急速で、Sonnet 4.5ではコード編集エラーが0%を達成

**結論**: CC に「任せっきり」は危険だが、「適切なガードレール付きの自律実行」は実用水準にある。

---

## 2. 自律度の5段階モデル

CC の自律実行範囲を、自動運転のレベル分類に倣い5段階で定義する。

```
Level 0: 手動           人間が全て実行、CCは参考回答のみ
Level 1: CC支援         人間が主導、CCが補助（コード補完・提案）
Level 2: CC主導/人間承認  CCが実行案を作成、人間が毎回承認して実行
Level 3: CC自律/人間監督  CCが自律実行、人間は結果を監督・異常時介入
Level 4: CC完全自律      CCが自律実行、人間は介入しない（自動テストのみ）
```

### 2.1 各レベルの詳細

| Level | CC の動き | 人間の動き | 品質保証メカニズム |
|---|---|---|---|
| **L0: 手動** | 質問に回答 | 全て自分で実行 | 従来通り |
| **L1: CC支援** | コード補完・提案 | 提案を採否判断・修正 | 人間のレビュー |
| **L2: CC主導/人間承認** | コード生成・変更案作成 | 各変更を承認/却下 | 人間の逐次承認 |
| **L3: CC自律/人間監督** | 自律的にコード生成・テスト実行・コミット | 結果を事後レビュー | 自動テスト + CC相互レビュー + 人間サンプリング |
| **L4: CC完全自律** | 全て自律実行（CIパイプライン内） | 介入しない | 自動テスト + 自動品質チェックのみ |

---

## 3. リスクベースの自律度決定フレームワーク

### 3.1 基本原則

> **「影響範囲が大きい判断ほど人間が行い、影響範囲が小さい実行ほど CC に任せる」**

これを「判断 vs 実行」と「影響範囲の大小」の2軸で整理する。

```
              影響範囲：大                    影響範囲：小
          ┌─────────────────────┬─────────────────────┐
          │                     │                     │
  判断    │  L0-L1: 人間が判断  │  L2: CCが提案、      │
 （何を   │                     │      人間が承認      │
  するか）│  ・アーキテクチャ    │  ・命名規則の適用    │
          │  ・技術スタック選定  │  ・リファクタリング  │
          │  ・セキュリティ方針  │    パターンの選択    │
          │  ・業務ロジックの    │  ・テスト戦略の      │
          │    解釈              │    微調整            │
          │                     │                     │
          ├─────────────────────┼─────────────────────┤
          │                     │                     │
  実行    │  L2-L3: CC が実行、 │  L3-L4: CC が自律    │
 （どう   │  人間が結果を検証   │  実行                │
  するか）│                     │                     │
          │  ・コア業務ロジック  │  ・CRUD実装          │
          │    の実装            │  ・テストコード作成  │
          │  ・セキュリティ関連  │  ・コードフォーマット│
          │    の実装            │  ・ドキュメント生成  │
          │  ・外部IF連携実装    │  ・バグ修正（軽微）  │
          │                     │  ・Lint対応          │
          │                     │                     │
          └─────────────────────┴─────────────────────┘
```

### 3.2 J-SIX プロセスの各 Phase における自律度

| Phase | 推奨自律度 | 根拠 |
|---|---|---|
| **Phase 0: プロジェクト憲法策定** | L1（CC支援） | CLAUDE.md は全ての基盤。人間が主導して策定すべき |
| **Phase 1: 要求の合意** | L1-L2 | 業務理解・顧客合意は人間の領域。CCはドラフト生成と曖昧性検出 |
| **Phase 2: 技術設計** | L2 | アーキテクチャ判断は人間。CCは具現化（DDL生成、プロトタイプ等） |
| **Phase 3: タスク分解** | L2 | CCがタスク提案、人間が承認。ここが自律実行圏への最後のゲート |
| **Phase 4: TDD実装** | **L3-L4** | **CCが自律実行。TDDのテストがガードレール** |
| **Phase 5: 品質検証** | L2-L3 | 自動テスト（L4）+ 人間サンプリング検証（L2） |
| **Phase 6: ドキュメント生成** | L3 | CC自律生成 + 人間レビュー |

**最も重要な結論**: Phase 4（TDD実装）を **L3-L4 で運用する** ことが、J-SIX プロセスの生産性の源泉。

---

## 4. Phase 4（TDD実装）の自律実行設計

### 4.1 なぜ Phase 4 で L3-L4 が可能か

Phase 4 が高い自律度で運用できる理由は以下の3点。

**① TDD がガードレールとして機能する**
- テストが先に存在するため、CC は「テストを通す」という明確な成功基準がある
- テストが通らない限り、タスクは完了しない
- Anthropic 社内でも「TDD は CC と組み合わせる最強のパターン」と認識

**② サブエージェント分離でコンテキスト汚染を防止**
- テスト作成者（Red Agent）と実装者（Green Agent）を分離
- 実装者がテストを改変して「通ったことにする」問題を防止
- テストをコミットしてからハンドオフすることで追加の安全策

**③ Writer/Reviewer パターンで自己バイアスを排除**
- コードを生成したCC と別のCCインスタンスがレビュー
- 自分が書いたコードへのバイアスがないため、客観的なレビューが可能

### 4.2 Phase 4 の自律実行フロー

```
┌──────────────────────────────────────────────────────────┐
│ タスクN の実行フロー（L3-L4）                             │
│                                                          │
│  ① CC-Lead がタスク一覧から次のタスクを選択              │
│     ↓                                                    │
│  ② Red Agent（サブエージェント）がテスト作成              │
│     ↓ テストが失敗することを確認                         │
│     ↓ テストをコミット ← 【チェックポイント】           │
│     ↓                                                    │
│  ③ Green Agent（サブエージェント）が最小実装              │
│     ↓ テストが通ることを確認                             │
│     ↓ 実装をコミット ← 【チェックポイント】             │
│     ↓                                                    │
│  ④ Refactor Agent（サブエージェント）がリファクタリング   │
│     ↓ テストが通ることを再確認                           │
│     ↓ リファクタリングをコミット                         │
│     ↓                                                    │
│  ⑤ Review Agent（別セッション）がコードレビュー          │
│     ↓                                                    │
│  ⑥ 品質チェック Hook 実行                                │
│     ├─ カバレッジ閾値チェック                            │
│     ├─ 静的解析チェック                                  │
│     └─ Lint チェック                                     │
│     ↓                                                    │
│  ⑦ 全チェック通過 → タスク完了                           │
│     全チェック未通過 → CC-Lead が修正を指示（③に戻る）   │
│                                                          │
│  ※ 設計判断が発生した場合 → ADR 自動記録（論点2 参照）   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 4.3 自律実行中の「エスカレーション」条件

CC が自律実行中でも、以下の条件が検出された場合は **人間に判断を仰ぐ** 。

| エスカレーション条件 | 理由 | 実装方法 |
|---|---|---|
| **Spec に記載のない要件が必要と判明** | 業務判断は人間の領域 | CC が ask_user_question で確認 |
| **セキュリティに関わる判断** | セキュリティリスクの判断は人間が行うべき | Hook でセキュリティ関連ファイル変更を検出 |
| **外部IF仕様の変更が必要** | 他システムへの影響は人間が判断 | IF定義ファイル変更時に Hook で停止 |
| **テストが3回連続で失敗** | 根本的な設計問題の可能性 | Hook でリトライ回数を監視 |
| **アーキテクチャ変更が必要** | 影響範囲が大きい | CLAUDE.md で「変更禁止ファイル」を定義 |
| **コンテキストウィンドウ70%超** | 出力品質低下のリスク | CC が自動的に /compact 実行 or セッション分割 |

### 4.4 Hook による自律実行のガードレール実装

```
hooks/
├── pre-commit/
│   ├── coverage-check.sh        # カバレッジ閾値チェック
│   ├── lint-check.sh            # Lint チェック
│   ├── security-scan.sh         # セキュリティスキャン
│   └── forbidden-files.sh       # 変更禁止ファイルの検出
├── pre-tool-use/
│   ├── dangerous-command.sh     # 危険なコマンドの検出
│   └── production-guard.sh      # 本番環境操作の検出
├── post-tool-use/
│   └── adr-check.sh             # 設計判断の検出 → ADR 提案
└── stop/
    ├── quality-gate.sh           # Phase 完了時の品質ゲート判定
    └── retry-monitor.sh          # 連続失敗時のエスカレーション
```

---

## 5. 並列実行と自律度の関係

### 5.1 並列実行パターン

J-SIX プロセスでは、Phase 4 のタスクを **並列実行** することで生産性を最大化する。

```
タスク A ─── [Red] → [Green] → [Refactor] → [Review] → ✅
タスク B ─── [Red] → [Green] → [Refactor] → [Review] → ✅  ← 並列
タスク C ─── [Red] → [Green] → [Refactor] → [Review] → ✅  ← 並列
タスク D ─── [待機：タスクAに依存] → 開始 → ...

実現手段：
  ・git worktree（各タスクが独立した作業ディレクトリ）
  ・Agent Teams（複数 CC が共有タスクリストで協調）
  ・tmux / デスクトップアプリで複数セッション管理
```

### 5.2 並列実行時の自律度考慮

| 並列パターン | 推奨自律度 | 理由 |
|---|---|---|
| 独立タスクの並列（依存関係なし） | L4 | 相互影響がないため完全自律可能 |
| 依存タスクの逐次実行 | L3 | 先行タスクの結果を踏まえた判断が必要 |
| 共有リソース（DB等）を操作するタスク | L2-L3 | 競合リスクがあるため人間の監督必要 |
| 複数モジュール横断の変更 | L2 | 影響範囲が大きいため人間承認必要 |

---

## 6. 「33% 初回成功率」への対処

### 6.1 リトライ前提のプロセス設計

CC の初回成功率が約33%というデータは、**リトライを前提としたプロセス設計** が必要であることを意味する。

**Ralph Wiggum パターン（成功基準定義型自律実行）**:
1. 成功基準（テスト通過 + 品質チェック通過）を事前に定義
2. CC に自律実行させる
3. 失敗した場合、CC が自動的にエラーを分析してリトライ
4. 成功するまで繰り返す（上限回数あり）
5. 上限を超えたら人間にエスカレーション

**これが機能する前提条件**:
- 成功基準が明確に定義されていること（= テストが書かれていること）
- チェックポイントがあり、いつでもロールバック可能
- リトライ上限が設定されていること

### 6.2 コスト考慮

リトライはトークンを消費するため、コストの考慮が必要。

| パターン | 平均リトライ回数（推定） | コスト影響 |
|---|---|---|
| CRUD 実装 | 1-2回 | 低 |
| ビジネスロジック実装 | 2-4回 | 中 |
| 複雑なアルゴリズム | 3-6回 | 高 |
| 外部IF連携 | 3-5回 | 高 |

**コスト最適化の方針**:
- 単純タスク → Sonnet（高速・低コスト）
- 複雑タスク → Opus（高精度・高コスト、但しリトライ減でトータル安）
- バッチ処理可能なタスク → Message Batches API（50%コスト削減）

---

## 7. Phase 別の自律度まとめと CC 機能マッピング

| Phase | 自律度 | 人間の介入点 | CC 機能 | ガードレール |
|---|---|---|---|---|
| **P0: 憲法策定** | L1 | CLAUDE.md の策定・承認 | Plan Mode | — |
| **P1: 要求合意** | L1-L2 | Spec の承認、顧客折衝 | ask_user_question, Subagents（リサーチ） | — |
| **P2: 技術設計** | L2 | Design Spec の承認、アーキテクチャ判断 | Plan Mode, Subagents（並列調査） | — |
| **P3: タスク分解** | L2 | タスク一覧の承認 | Native Tasks | — |
| **P4: TDD実装** | **L3-L4** | **エスカレーション時のみ** | Subagents（TDD分離）, Agent Teams（並列）, git worktree | **Hooks, TDD, Writer/Reviewer, チェックポイント** |
| **P5: 品質検証** | L2-L3 | サンプリング検証、探索的テスト | Hooks（自動品質チェック） | 品質メトリクス閾値 |
| **P6: ドキュメント生成** | L3 | 設計書レビュー・承認 | Skills（逆生成） | テンプレート整合性チェック |

---

## 8. 日本SI案件における自律度の段階的引き上げ

日本のSI案件では、いきなり L3-L4 を適用することへの組織的・心理的抵抗が予想される。段階的に自律度を引き上げるアプローチを推奨する。

### Step 1: L1-L2 から開始（信頼構築期）

**期間**: 1-2ヶ月
**対象**: 新規モジュールの実装（既存コードへの影響なし）
**内容**:
- CC がコード生成、人間が毎回レビュー・承認
- テストコードは CC が生成、人間が検証
- 品質メトリクスを記録し、CC 生成コードの品質を定量的に把握

### Step 2: L3 への移行（部分自律期）

**期間**: 2-3ヶ月
**対象**: 単純な CRUD 実装、テストコード生成
**前提条件**:
- Step 1 で CC 生成コードの品質が許容範囲であることを確認
- TDD フローが確立されていること
- Hooks によるガードレールが設定済み
**内容**:
- CC が自律的に TDD サイクルを実行
- 人間はコードレビューを事後サンプリングに移行
- エスカレーション条件を実運用で検証

### Step 3: L4 への移行（完全自律期）

**期間**: 3ヶ月以降
**対象**: 独立性の高いタスク（依存関係なし、影響範囲小）
**前提条件**:
- Step 2 で自律実行の品質が安定していることを確認
- チェックポイントによるロールバックが運用に組み込まれていること
- 品質メトリクスの自動監視が稼働中
**内容**:
- CC が完全自律で実行、人間は品質ダッシュボードを監視
- 異常検知時のみ介入

---

## 9. 結論

### 9.1 自律度の原則

1. **判断（What/Why）は人間、実行（How）はCC** — これが基本原則
2. **Phase 4（TDD実装）を L3-L4 で運用** — J-SIX の生産性の源泉
3. **TDD + Hooks + チェックポイント** — 3つのガードレールで品質を担保
4. **エスカレーション条件の明確化** — CC が「判断すべきでない場面」を自動検出
5. **段階的引き上げ** — L1-L2 → L3 → L4 の段階を踏む

### 9.2 次の論点への接続

論点4「段階的移行パス（V字→J-SIX）」では、本論点の「Step 1→2→3 の段階的引き上げ」をより具体的に、既存のV字モデル案件からの移行パスとして設計する。

---

> **改訂履歴**
>
> | 版 | 日付 | 内容 |
> |---|---|---|
> | 0.1 | 2026-03-29 (H.Sekita) | 初版作成 |

---

### 参考文献

**CC 能力・品質データ**
- Anthropic. "How Anthropic teams use Claude Code" (2025.07). https://claude.com/blog/how-anthropic-teams-use-claude-code
- Anthropic. "How AI is Transforming Work at Anthropic" (2025). https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic
- Anthropic. "Introducing Claude Sonnet 4.5" (2026.02). https://www.anthropic.com/news/claude-sonnet-4-5
- CodeRabbit. "State of AI vs Human Code Generation Report" (2025.12). https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report
- DataCamp. "Claude Code Best Practices" (2026.03). https://www.datacamp.com/tutorial/claude-code-best-practices
- Codingscape. "How Anthropic engineering teams use Claude Code every day" (2025.12). https://codingscape.com/blog/how-anthropic-engineering-teams-use-claude-code-every-day
- FlorianBruniaux. "claude-code-ultimate-guide" (GitHub). https://github.com/FlorianBruniaux/claude-code-ultimate-guide

**CC 自律実行・ワークフロー**
- Anthropic. "Best Practices for Claude Code". https://code.claude.com/docs/en/best-practices
- Anthropic. "Enabling Claude Code to work more autonomously". https://www.anthropic.com/news/enabling-claude-code-to-work-more-autonomously
- Anthropic. "How Claude Code works". https://code.claude.com/docs/en/how-claude-code-works
- JIN. "Claude Code's New Autonomous Execution: The Ralph Wiggum Pattern" (2026.02). https://jinlow.medium.com/claude-codes-new-autonomous-execution-the-ralph-wiggum-pattern-that-s-reshaping-ai-development-3cb9c13d169b
- alexop.dev. "Forcing Claude Code to TDD" (2025.11). https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/
- Martin Fowler. "How far can we push AI autonomy in code generation?". https://martinfowler.com/articles/pushing-ai-autonomy.html
- ClaudeFast. "Claude Code Agent Teams: The Complete Guide 2026". https://claudefa.st/blog/guide/agents/agent-teams

※ 本ドキュメントの自律度5段階モデル（L0-L4）は、SAE J3016（自動運転レベル分類）に着想を得た著者のオリジナル分類。リスクベースの自律度決定フレームワーク、エスカレーション条件、段階的引き上げプランは著者の設計。
