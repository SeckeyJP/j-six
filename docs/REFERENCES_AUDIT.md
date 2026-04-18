# J-SIX プロジェクト：出典・参考文献 監査レポート

## — 全ドキュメントの主張に対する根拠の整理 —

**監査日**: 2026-03-29

---

## 1. 監査方針

本プロジェクトのドキュメントに含まれる主張を以下の3カテゴリに分類し、それぞれの根拠を明示する。

| カテゴリ | 定義 | 表記 |
|---|---|---|
| **A. 出典あり（ファクト）** | 外部のデータ・調査・公式発表に基づく具体的数値・事実 | 🔵 URL付きで引用 |
| **B. 推定・著者見解** | 著者の分析・推定・提案。定量値は推定値であることを明示 | 🟡 「推定」「著者見解」と明記 |
| **C. 一般知識** | 広く知られた概念・手法。特定の出典を要しない | ⚪ 出典不要 |

---

## 2. カテゴリA：出典ありの主張（要引用）

### 2.1 CC の能力・実績データ

| # | 主張 | 数値 | 出典 | URL | 使用箇所 |
|---|---|---|---|---|---|
| A1 | CC 初回自律実行成功率 | 約33% | Anthropic 社内報告 "How Anthropic teams use Claude Code"（2025.07） | https://claude.com/blog/how-anthropic-teams-use-claude-code | J-SIX v1.0 第1章, 論点3 |
| A2 | AI生成PRのイシュー率（人間比） | 約1.7倍 | CodeRabbit "State of AI vs Human Code Generation Report"（2025.12） | https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report | J-SIX v1.0 第1章, 論点3 |
| A3 | ロジック/正確性エラー（人間比） | 1.75倍 | 同上（ACM 2025 との記載もあり、FlorianBruniaux guide 経由） | 同上 | 論点1a, 論点3 |
| A4 | セキュリティイシュー（人間比） | 最大2.74倍 | 同上 | 同上 | J-SIX v1.0 第1章, 論点3 |
| A5 | エラーハンドリングの抜け（人間比） | 約2倍 | 同上 | 同上 | 論点3 |
| A6 | Sonnet 4.5 コード編集エラー率 | 0%（内部ベンチマーク） | Anthropic 公式発表 "Introducing Claude Sonnet 4.5"（2026.02） | https://www.anthropic.com/news/claude-sonnet-4-5 | J-SIX v1.0 第1章, 論点3 |
| A7 | Anthropic社内タスク複雑度の推移 | 平均 3.2→3.8（5段階） | Anthropic "How AI is Transforming Work at Anthropic"（2025） | https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic | 論点3 |
| A8 | コンテキスト70%で精度低下 | 70%超で精度低下、85%で幻覚増加 | FlorianBruniaux "claude-code-ultimate-guide" | https://github.com/FlorianBruniaux/claude-code-ultimate-guide | 論点3 |
| A9 | CC $2.5B ARR（2026.02時点） | $2.5B 年間ランレート | devFlokers "How to Use Claude in March 2026" | https://www.devflokers.com/blog/how-to-use-claude-march-2026-enterprise-guide | 参考情報 |
| A10 | Anthropic 評価額 $380B | $380B（2026.02 Series G） | 同上 | 同上 | 参考情報 |

### 2.2 SDD・フレームワーク関連

| # | 主張 | 出典 | URL | 使用箇所 |
|---|---|---|---|---|
| A11 | BMAD Method: 21専門エージェント、50以上のワークフロー | BMAD公式 / Pasqualepillitteri.it 解説 | https://github.com/bmad-code-org/BMAD-METHOD / https://www.pasqualepillitteri.it/en/news/158/framework-ai-spec-driven-development-guide-bmad-gsd-ralph-loop | 論点1, 論点2 |
| A12 | BMAD: 5人未満のチームには非推奨 | Augment Code "6 Best Spec-Driven Development Tools"（2026） | https://www.augmentcode.com/tools/best-spec-driven-development-tools | 論点2 |
| A13 | BMAD のエージェント間ハンドオフ問題 | 同上（実際のプロジェクトでの報告） | 同上 | 論点2 |
| A14 | Superpowers: 42,000+ GitHub stars、Anthropic公式マーケットプレイス入り（2026.01） | Pasqualepillitteri.it "Superpowers Claude Code Complete Guide" | https://www.pasqualepillitteri.it/en/news/215/superpowers-claude-code-complete-guide | 論点2 |
| A15 | SDD の定義・概念（Spec-Driven Development） | CGI.com "Spec-driven development: From vibe coding to intent engineering" | https://www.cgi.com/en/blog/artificial-intelligence/spec-driven-development | 論点1a, 論点2 |
| A16 | GitHub Spec Kit: 2024年9月リリース | Medium Vishal Mysore 記事 | https://medium.com/@visrow/comprehensive-guide-to-spec-driven-development-kiro-github-spec-kit-and-bmad-method-5d28ff61b9b1 | 論点2 |
| A17 | SDD の4フェーズワークフロー（Specify→Design→Tasks→Implement） | Agent Factory / Panaversity "Chapter 16: SDD with Claude Code" | https://agentfactory.panaversity.org/docs/General-Agents-Foundations/spec-driven-development | 論点2 |

### 2.3 CC の機能・アーキテクチャ

| # | 主張 | 出典 | URL | 使用箇所 |
|---|---|---|---|---|
| A18 | CC の7つの拡張メカニズム（CLAUDE.md, Skills, Subagents, Agent Teams, Hooks, MCP, Plugins） | Dean Blank "A Mental Model for Claude Code" (2026.03) | https://levelup.gitconnected.com/a-mental-model-for-claude-code-skills-subagents-and-plugins-3dea9924bf05 | 論点2 |
| A19 | Agent Teams: Opus 4.6 リリースと共に実験的機能として提供 | ClaudeFast "Claude Code Agent Teams: The Complete Guide 2026" | https://claudefa.st/blog/guide/agents/agent-teams | 論点2, 論点3 |
| A20 | Subagents の公式仕様・動作 | Anthropic 公式ドキュメント "Create custom subagents" | https://code.claude.com/docs/en/sub-agents | 論点2 |
| A21 | CC Best Practices（Plan Mode、Writer/Reviewer パターン、TDD推奨） | Anthropic 公式 "Best Practices for Claude Code" | https://code.claude.com/docs/en/best-practices | 論点2, 論点3, J-SIX v1.0 |
| A22 | Anthropic社内でのCLAUDE.md充実度とCC出力品質の相関 | Anthropic "How Anthropic teams use Claude Code" | https://claude.com/blog/how-anthropic-teams-use-claude-code / https://codingscape.com/blog/how-anthropic-engineering-teams-use-claude-code-every-day | J-SIX v1.0 Phase 0 |
| A23 | Security Engineering チームの TDD 活用（design doc→janky code からの変革） | 同上 | 同上 | 論点3 |
| A24 | Master-Clone アーキテクチャ（カスタムサブエージェントの代替提案） | Shrivu Shankar "How I Use Every Claude Code Feature" | https://blog.sshh.io/p/how-i-use-every-claude-code-feature | 論点2 |
| A25 | TDD でのサブエージェント分離によるコンテキスト汚染防止 | alexop.dev "Forcing Claude Code to TDD" (2025.11) | https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/ | 論点3, J-SIX v1.0 Phase 4 |
| A26 | Ralph Wiggum パターン（成功基準定義型自律実行） | JIN "Claude Code's New Autonomous Execution" (2026.02) | https://jinlow.medium.com/claude-codes-new-autonomous-execution-the-ralph-wiggum-pattern-that-s-reshaping-ai-development-3cb9c13d169b | 論点3 |
| A27 | CC Auto mode / Checkpoints | Anthropic 公式 "Enabling Claude Code to work more autonomously" | https://www.anthropic.com/news/enabling-claude-code-to-work-more-autonomously | 論点3 |
| A28 | CC Code Review 機能（研究プレビュー） | TechInformed "Anthropic adds code review to Claude Code" (2026.03) | https://techinformed.com/anthropic-adds-code-review-to-claude-code-for-enterprises/ | 論点2 |

### 2.4 ADR 関連

| # | 主張 | 出典 | URL | 使用箇所 |
|---|---|---|---|---|
| A29 | ADR の概念・テンプレート（Nygard形式） | adr.github.io（ADR 公式サイト） | https://adr.github.io/ | 論点3（設計書逆生成） |
| A30 | CC による ADR 自動スキャン・生成の実践例 | Adolfi.dev "AI generated Architecture Decision Records" (2025.11) | https://adolfi.dev/blog/ai-generated-adr/ | 論点3 |
| A31 | ADR の CC 自動読込機能リクエスト（Claude Code Issue #13853） | GitHub anthropics/claude-code Issues | https://github.com/anthropics/claude-code/issues/13853 | 論点3 |

### 2.5 富士通の設計書リバースエンジニアリング

| # | 主張 | 出典 | URL | 使用箇所 |
|---|---|---|---|---|
| A32 | 富士通：AI による設計書リバースエンジニアリングサービス（50%効率化） | Fujitsu Global プレスリリース (2025.02) | https://info.archives.global.fujitsu/global/about/resources/news/press-releases/2025/0204-01.html | 論点3 |

### 2.6 AI コード品質全般

| # | 主張 | 出典 | URL | 使用箇所 |
|---|---|---|---|---|
| A33 | DORA Report: AI採用25%増で delivery throughput 1.5%低下、stability 7.2%低下 | TechInformed 記事（Google Cloud DORA 2024 引用） | https://techinformed.com/anthropic-adds-code-review-to-claude-code-for-enterprises/ | 参考情報 |
| A34 | Martin Fowler: AI 自律実行の限界と subtasking の有効性 | martinfowler.com "How far can we push AI autonomy in code generation?" | https://martinfowler.com/articles/pushing-ai-autonomy.html | 論点3 |
| A35 | DataCamp: unguided attempts 成功率約33%、セッション放棄率10-20% | DataCamp "Claude Code Best Practices" (2026.03) | https://www.datacamp.com/tutorial/claude-code-best-practices | 論点3 |

---

## 3. カテゴリB：推定・著者見解（明示が必要な箇所）

以下の数値・主張は、著者の分析・推定に基づくものであり、記事公開時にはその旨を明記する必要がある。

| # | 主張 | 根拠 | 表記案 | 使用箇所 |
|---|---|---|---|---|
| B1 | 実装工数 60-70% 削減 | 各種事例の集約と段階的効果の積み上げ推定。公式な大規模調査はない | 「著者推定。個別事例の報告を基に段階的効果を積み上げた目標値」 | J-SIX v1.0 エグゼクティブサマリー |
| B2 | テストカバレッジ 85-95% | TDD 全面適用時の一般的水準。CC 特有のデータではない | 「TDD全面適用時の一般的目標値」 | J-SIX v1.0 エグゼクティブサマリー |
| B3 | 手戻り率 5-10% | プロトタイプ駆動・TDD による早期発見効果の推定 | 「著者推定。上流プロトタイプとTDDによる早期検証効果を想定」 | J-SIX v1.0 エグゼクティブサマリー |
| B4 | 設計判断の記録率 80%以上 | ADR 運用の定着を前提とした目標値 | 「ADR運用定着時の目標値」 | J-SIX v1.0 エグゼクティブサマリー |
| B5 | Stage 1 工数削減率 20-30% | Anthropic 等の事例報告（40-60%削減）の控えめな推定 | 「著者推定。CC活用初期段階の控えめな見積」 | 論点4, J-SIX v1.0 第5章 |
| B6 | Stage 2 工数削減率 40-50% | 同上（TDD＋Spec駆動の追加効果を加味） | 同上 | 同上 |
| B7 | Stage 3 工数削減率 60-70% | 同上（全面自律実行の効果を加味） | 同上 | 同上 |
| B8 | ROI 試算（月額7.5万円 vs 削減100万円等） | CC Max 5x $100/人、人件費80万円/人月の仮定に基づく計算 | 「仮定条件に基づく試算。実際の数値はプロジェクトにより異なる」 | 論点4, J-SIX v1.0 第5章 |
| B9 | 「CC は速いが雑な新人開発者に類似」 | A1-A5 のデータから著者が導いた比喩的表現 | 「著者の解釈」 | J-SIX v1.0 第1章 |
| B10 | 自律度5段階モデル（L0-L4） | 自動運転レベル（SAE J3016）に着想を得た著者独自の分類 | 「著者が自動運転レベル分類に着想を得て定義」 | J-SIX v1.0 第2章, 論点3 |
| B11 | 3層ドキュメント戦略 | ADR + SDD + 逆生成を組み合わせた著者独自の提案 | 「著者提案」 | J-SIX v1.0 第3章 Phase 6, 論点3 |
| B12 | J-SIX の7Phase 構成 | SDD の4フェーズ + 日本品質要件から著者が設計 | 「著者設計。SDDの原則に日本品質基準を追加」 | J-SIX v1.0 全体 |
| B13 | エスカレーション条件（テスト3回連続失敗等） | 実務経験に基づく著者の推奨値 | 「著者推奨。プロジェクト特性に応じて調整すべき」 | J-SIX v1.0 Phase 4, 論点3 |
| B14 | Stage 完了基準の閾値（CC生成コードのバグ密度2倍以内等） | 実務的な判断に基づく著者の推奨値 | 「著者推奨の目安。組織の品質基準に応じて設定すべき」 | 論点4 |

---

## 4. カテゴリC：一般知識（出典不要）

以下は広く知られた概念であり、特定の出典は不要。ただし概念の初出や詳細を知りたい読者向けに参考リンクを提供することは望ましい。

| 概念 | 補足参考（任意） |
|---|---|
| V字モデル（ウォーターフォール） | IPA/SEC 共通フレーム |
| TDD（テスト駆動開発） | Kent Beck "Test-Driven Development: By Example" (2002) |
| ADR（Architecture Decision Records） | Michael Nygard (2011) / https://adr.github.io/ |
| SDD（Spec-Driven Development） | 2024-2025年に普及した概念。単一の原典はない |
| Red-Green-Refactor サイクル | TDD の標準的なプラクティス |
| IPA 共通フレーム | https://www.ipa.go.jp/digital/architecture/ |

---

## 5. 完成版ドキュメント（J-SIX v1.0）への反映指針

### 5.1 ドキュメント末尾に追加すべき参考文献セクション

以下の構成で参考文献を追加する。

```
## 参考文献

### Anthropic 公式
[1] Anthropic. "Best Practices for Claude Code". https://code.claude.com/docs/en/best-practices
[2] Anthropic. "How Anthropic teams use Claude Code" (2025.07). https://claude.com/blog/how-anthropic-teams-use-claude-code
[3] Anthropic. "How AI is Transforming Work at Anthropic" (2025). https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic
[4] Anthropic. "Introducing Claude Sonnet 4.5" (2026.02). https://www.anthropic.com/news/claude-sonnet-4-5
[5] Anthropic. "Enabling Claude Code to work more autonomously". https://www.anthropic.com/news/enabling-claude-code-to-work-more-autonomously
[6] Anthropic. "Create custom subagents". https://code.claude.com/docs/en/sub-agents
[7] Anthropic. "How Claude Code works". https://code.claude.com/docs/en/how-claude-code-works

### AI コード品質研究
[8] CodeRabbit. "State of AI vs Human Code Generation Report" (2025.12). https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report
[9] Martin Fowler. "How far can we push AI autonomy in code generation?". https://martinfowler.com/articles/pushing-ai-autonomy.html

### SDD・フレームワーク
[10] Agent Factory / Panaversity. "Chapter 16: Spec-Driven Development with Claude Code". https://agentfactory.panaversity.org/docs/General-Agents-Foundations/spec-driven-development
[11] BMAD-METHOD (GitHub). https://github.com/bmad-code-org/BMAD-METHOD
[12] CGI. "Spec-driven development: From vibe coding to intent engineering" (2026.03). https://www.cgi.com/en/blog/artificial-intelligence/spec-driven-development
[13] Augment Code. "6 Best Spec-Driven Development Tools for AI Coding in 2026". https://www.augmentcode.com/tools/best-spec-driven-development-tools

### CC 実践・活用事例
[14] alexop.dev. "Forcing Claude Code to TDD: An Agentic Red-Green-Refactor Loop" (2025.11). https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/
[15] alexop.dev. "Spec-Driven Development with Claude Code in Action" (2026.02). https://alexop.dev/posts/spec-driven-development-claude-code-in-action/
[16] DataCamp. "Claude Code Best Practices" (2026.03). https://www.datacamp.com/tutorial/claude-code-best-practices
[17] Dean Blank. "A Mental Model for Claude Code" (2026.03). https://levelup.gitconnected.com/a-mental-model-for-claude-code-skills-subagents-and-plugins-3dea9924bf05
[18] Shrivu Shankar. "How I Use Every Claude Code Feature" (2025.11). https://blog.sshh.io/p/how-i-use-every-claude-code-feature
[19] Codingscape. "How Anthropic engineering teams use Claude Code every day" (2025.12). https://codingscape.com/blog/how-anthropic-engineering-teams-use-claude-code-every-day
[20] ranthebuilder.cloud. "Claude Code Best Practices: Lessons From Real Projects" (2026.03). https://ranthebuilder.cloud/blog/claude-code-best-practices-lessons-from-real-projects/

### ADR
[21] adr.github.io. "Architectural Decision Records". https://adr.github.io/
[22] Adolfi.dev. "AI generated Architecture Decision Records" (2025.11). https://adolfi.dev/blog/ai-generated-adr/

### その他
[23] Fujitsu. "Software analysis and visualization service" (2025.02). https://info.archives.global.fujitsu/global/about/resources/news/press-releases/2025/0204-01.html
[24] Pasqualepillitteri.it. "Superpowers Claude Code Complete Guide" (2026). https://www.pasqualepillitteri.it/en/news/215/superpowers-claude-code-complete-guide
[25] Pasqualepillitteri.it. "Spec-Driven Development AI Framework Guide" (2026). https://www.pasqualepillitteri.it/en/news/158/framework-ai-spec-driven-development-guide-bmad-gsd-ralph-loop
```

### 5.2 本文中の修正が必要な箇所

| 箇所 | 現状 | 修正案 |
|---|---|---|
| エグゼクティブサマリーの期待効果 | 数値のみ記載 | 各数値に「著者推定」を注記。脚注で根拠を簡潔に説明 |
| 第1章 1.3 の表 | 「出典」列はあるが簡略 | 参考文献番号 [N] を追記 |
| Phase 0 の「CLAUDE.md充実度と品質の相関」 | 出典なし | [2][19] を追記 |
| Phase 4 の TDD サブエージェント分離 | 概念のみ | [14] を追記 |
| 第5章 ROI 試算 | 数値のみ | 「仮定条件に基づく試算」を冒頭に明記 |

---

## 6. 記事公開時の出典表記ガイドライン

### 6.1 Qiita/Zenn 記事向け

- 本文中で主張の根拠を示す場合: `（参考: [タイトル](URL)）` の形式
- 具体的数値を引用する場合: 「〜との報告がある（[出典名](URL)）」
- 著者推定の場合: 「筆者の推定では〜」「以下は目標値として設定した〜」と明記
- 記事末尾に参考文献一覧を掲載

### 6.2 GitHub MD 向け

- 参考文献セクションをドキュメント末尾に配置（上記 5.1 の形式）
- 本文中は `[N]` 形式で参照
- 著者推定値には `※著者推定` を付記

### 6.3 共通ルール

- **他者の成果物の名称・概念を紹介する場合は必ず出典を記載**
- **データを引用する場合は一次ソースを優先**（ブログ経由ではなく公式サイト）
- **著者の推定・提案は明確に区別**し、読者が判断できるようにする
- **J-SIX 自体が著者のオリジナル提案**であることを冒頭で明示

---

## 7. 注意事項

### 7.1 一次ソースが確認できなかった主張

| 主張 | 状況 | 対応案 |
|---|---|---|
| 「ACM 2025 の報告でCC生成コードは1.75倍のロジックエラー」 | FlorianBruniaux guide 経由の記述。ACMの具体的な論文タイトルは未特定 | CodeRabbit レポート [8] の1.7倍を一次ソースとして使用。ACM への言及は削除 |
| Anthropic社内「CC初回成功率33%」 | 複数の二次ソースで引用（[2][16][19]）されているが、原文の正確な文脈は「RL Engineering team」の報告 | 「Anthropic RL Engineering チームの報告として複数のソースで引用」と表記 |

### 7.2 時間経過で陳腐化する可能性がある情報

| 情報 | リスク | 対応 |
|---|---|---|
| CC のモデル名・バージョン（Opus 4.6, Sonnet 4.5） | 新モデルのリリースで陳腐化 | 「2026年3月時点」を明記 |
| CC の機能一覧（Agent Teams等） | 実験的機能が正式リリース/廃止される可能性 | 「2026年3月時点の機能」を明記 |
| CC の料金（Max 5x $100/月） | 料金改定の可能性 | 「2026年3月時点の料金」を明記 |
| 各SDDフレームワークの比較 | フレームワークの急速な進化 | 「2026年3月時点の評価」を明記 |

---

> **本監査レポートは、J-SIX プロジェクトの全ドキュメントの信頼性を担保するために作成された。**
> **記事公開・GitHub公開の前に、本レポートに基づいて各ドキュメントの出典表記を更新すること。**
