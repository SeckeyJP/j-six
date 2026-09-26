# J-SIX プロジェクト：出典・参考文献 監査レポート

## — 全ドキュメントの主張に対する根拠の整理 —

**監査日**: 2026-03-29（初版） / 2026-04-18（v2.0 改訂時に更新） / 2026-06-14（鮮度レビュー: 出典リンク・数値の有効性を再確認、変更なし） / 2026-09-10（v2.1 改訂: 品質ゲート関連の出典 A36-A43 を追加、四半期鮮度レビューを実施） / 2026-09-19（工程成果物テンプレートの追加に伴い、IPA 合意形成ガイドと国税庁 Q&A を A44-A46 として追加。非機能要件の分類に伴い IPA 非機能要求グレードを A47-A48 として追加） / 2026-09-20（[3] の一次情報を再確認し、公開日と連続自律アクション数を訂正。参考文献一覧の  / 2026-09-22（追加調査: ICSSP 2024・JSEP を確認し A65・A66 を追加。IEEE 掲載3件の書誌を確定。隣接研究 [60][61] を A63・A64 として追加） / 2026-09-22（J-SIX Hub 構想 `docs/control-plane/concept.md` の関連研究を A49-A62、著者見解を B21-B23、参考文献 [35]-[59] として追加。Unpaywall 等の外部 API には識別情報を送らない運用とした）

2026-09-23 追記：レビュー R02・R04〜R09 の設計具体化を B25 に登録。新しい外部文献の確認・追加は行っていない。

---

2026-09-26追記: Property対応・逆生成/IDトレースの保証範囲・G3省略時の自律度を著者設計B26として整理。新たな外部実績の追加・全出典の再監査は行っていない。

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
| A1 | CC 自律実行時の人間介入頻度の減少 | 33%減少（6.2→4.1ターン/タスク） | Anthropic "How AI is Transforming Work at Anthropic"（2025.12） | https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic | J-SIX v1.0 第1章, 論点3 |
| A2 | AI生成PRのイシュー率（人間比） | 約1.7倍 | CodeRabbit "State of AI vs Human Code Generation Report"（2025.12） | https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report | J-SIX v1.0 第1章, 論点3 |
| A3 | ロジック/正確性エラー（人間比） | 1.75倍 | 同上（ACM 2025 との記載もあり、FlorianBruniaux guide 経由） | 同上 | 論点1a, 論点3 |
| A4 | セキュリティイシュー（人間比） | 最大2.74倍 | 同上 | 同上 | J-SIX v1.0 第1章, 論点3 |
| A5 | エラーハンドリングの抜け（人間比） | 約2倍 | 同上 | 同上 | 論点3 |
| A6 | Sonnet 4.5 コード編集エラー率 | 9%→0%（Replit 内部ベンチマーク、Sonnet 4→4.5） | Anthropic 公式発表 "Introducing Claude Sonnet 4.5"（2025.09） | https://www.anthropic.com/news/claude-sonnet-4-5 | J-SIX v1.0 第1章, 論点3 |
| A7 | Anthropic社内タスク複雑度の推移 | 平均 3.2→3.8（5段階） | Anthropic "How AI is Transforming Work at Anthropic"（2025.12） | https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic | 論点3 |
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

### 2.7 品質ゲート・検証（v2.1 で追加）

| # | 主張 | 数値・内容 | 出典 | URL | 使用箇所 |
|---|---|---|---|---|---|
| A36 | 決定論的検証器をすべて通してから LLM judge を走らせる（順序固定） | 「judge は標準の検証ループに含まれ、他の検証器がすべて完了した後に走る」 | Spotify Engineering "Honk, Part 3" (2025.12.09) | https://engineering.atspotify.com/2025/12/feedback-loops-background-coding-agents-part-3 | J-SIX 第3章 Phase 4 メカニズム② |
| A37 | LLM judge の却下率 | 「数千のエージェントセッションのうち、judge は約4分の1を veto する。その際エージェントは半分の割合で自己修正できる」 | 同上 | 同上 | J-SIX 第3章 Phase 4（本文では「約1/4」と表記） |
| A38 | Spotify は後に judge を撤去した | 「LLM as judge は硬直的で妥当な変更まで止めたため、モデルの改善に伴い最終的に撤去され、プロンプト内の検証手順で十分になった」 | InfoQ "QCon London 2026: Rewriting All of Spotify's Code Base" (2026.03.18) | https://www.infoq.com/news/2026/03/spotify-honk-rewrite/ | J-SIX 第3章 Phase 4「G3 は固定装備ではない」 |
| A39 | reward hacking は可視テストと hold-out テストの pass 率差で測れる | フロンティアエージェントはいずれも可視スイートを飽和させるが hold-out との差は残る。差はタスク長（コード量10倍あたり28pt）で拡大し、**テスト網羅度ではなくタスク難度とモデル能力の差**で駆動される | Weco AI "SpecBench" (2026.05), arXiv:2605.21384 | https://arxiv.org/abs/2605.21384 | J-SIX 第2章 2.3, 第3章 Phase 4 |
| A40 | 受入条件 → Property → PBT の流れ | Kiro は Gherkin 形式の要件から property を抽出し、「for any」で始まる textual property を実行可能な property-based test に変換する（fast-check を使用） | Kiro "Does your code match your spec?" / Kiro Docs "Correctness" | https://kiro.dev/blog/property-based-testing/ , https://kiro.dev/docs/specs/correctness/ | J-SIX 第3章 Phase 2 |
| A41 | Stop hook は8回連続ブロックで自動解除される | 「Claude Code overrides the hook and ends the turn after 8 consecutive blocks」 | Anthropic "Best practices for Claude Code" | https://code.claude.com/docs/en/best-practices | J-SIX 第3章 Phase 4 エスカレーション, 第4章 4.4 |
| A42 | gap を探せと指示されたレビュアーは健全な作業でも何かを報告する | 「A reviewer prompted to find gaps will usually report some, even when the work is sound... Chasing every finding leads to over-engineering」 | 同上 | 同上 | J-SIX 第3章 Phase 4「G3 にスタイル指摘の禁止を明記する理由」 |
| A43 | AI 導入により検証・レビューの負荷が増える / 30%が AI 生成コードをほぼ信頼していない | 「コードを書く時間は減るが、AI を見張りレビューする時間が増える」「開発者の30%が AI 生成コードにほとんど信頼を置いていない」 | DORA "Balancing AI tensions" (2026.03.10) | https://dora.dev/insights/balancing-ai-tensions/ | J-SIX 第3章 Phase 5 |

> **A37 の表記について**: 一次ソースの原文は "about a quarter" であり、パーセント表記ではない。
> 本文でも「約1/4」と記し、「25%」のような有効数字を持つ数値としては表記しない。

> **A38 を併記する理由**: A36・A37 は G3（LLM judge）を導入する根拠だが、同じ事例の**後日談**として
> judge が撤去されたことも記録しておかないと、読者に「judge は恒久的に必要」という誤った印象を与える。
> J-SIX では G3 を却下率で評価し、不要になれば外す前提で記述している。

---

### 2.8 工程成果物・合意形成・非機能要求（工程成果物テンプレートで追加）

| # | 主張 | 内容 | 出典 | URL | 使用箇所 |
|---|---|---|---|---|---|
| A44 | 外部設計工程には業界標準の工程成果物が存在せず、工程成果物と設計書は1対1ではない | 「外部設計工程には、現時点では業界として標準とされる『工程成果物』が存在しません。…設計書の作成単位や構成が、本ガイドで想定している『工程成果物』と一致しないことがあります」（概要編 2.1） | IPA「機能要件の合意形成ガイド ver.1.0」(2010.03.31) | https://www.ipa.go.jp/archive/files/000004517.pdf | `templates/deliverables/README.md`、`examples/monthly-billing/docs/deliverables/README.md`、`templates/deliverables/assembly/`（GUIDE / 詳細設計書の組立例） |
| A45 | 合意成熟度の3段階（仕掛／充実／完成レベル） | 発注者が「言い切った」・開発者が「聞き切った」＝仕掛レベル、図表とレビューで合意内容が充実＝充実レベル、合意内容が管理され双方が確認できた＝完成レベル（3.1.1） | 同上 | 同上 | 同上、`templates/deliverables/assembly/GUIDE.md`（提出時期と合意成熟度） |
| A46 | 適格請求書の消費税額は一の請求につき税率ごとに1回のみ端数処理する | 明細ごとに端数処理して合計する方法は認められない | 国税庁「インボイス制度に関するQ&A」問57 | https://www.nta.go.jp/taxes/shiraberu/zeimokubetsu/shohi/keigenzeiritsu/pdf/qa/57.pdf | `examples/monthly-billing/`（REQ-005 / ADR-0001、帳票編集定義） |
| A47 | 非機能要求を6大項目・34中項目・116小項目・238メトリクスに体系化し、開発コストや品質への影響が大きい92項目を重要項目とする | 6大項目は可用性 / 性能・拡張性 / 運用・保守性 / 移行性 / セキュリティ / システム環境・エコロジー。対象はシステム基盤の非機能要求 | IPA「非機能要求グレード2018」（講義資料: IPA セミナー「非機能要求グレード」実践セミナー, 2019.03.04） | https://www.ipa.go.jp/archive/digital/iot-en-ci/jyouryuu/hikinou/ent03-b.html （講義資料 https://www.ipa.go.jp/archive/files/000072715.pdf ） | `templates/spec/requirement-spec.md` 3.5、`templates/spec/design-spec.md` 7、`docs/J-SIX.md` Phase 1 |
| A48 | 3つのモデルシステム（社会的影響がほとんど無い／限定される／極めて大きいシステム）を選び、重要項目の要求レベルの例示値を出発点にする | 限定される＝企業活動の基盤で取引先や顧客にも影響、極めて大きい＝国民生活・社会経済活動の基盤 | 同上 | 同上 | `templates/spec/requirement-spec.md` 3.5.1、`examples/monthly-billing/docs/requirement-spec.md` |

> **非機能要求グレードの扱いについて**: 同グレードの PDF 版は改変・再配布に制限があり（著作権表示 "(c) 2010-2018 IPA" が必要）、
> Excel 版は著作権表示を付ければ改変できる（使用条件: https://www.ipa.go.jp/archive/digital/iot-en-ci/jyouryuu/hikinou/ent03-b-1.html ）。
> J-SIX のテンプレートには**6大項目の名称と構成だけ**を載せ、メトリクスとレベルの定義は利用者が IPA の Excel 版を入手して使う形にした。
> テンプレート内の例示（「運用スケジュール」等）は講義資料の大項目ごとの要求例に拠る。また同グレードは IPA のアーカイブに置かれている
> （最新は2018年改訂版）。7.2（陳腐化しうる情報）の観点では、6大項目の区分は安定しているが、クラウド前提のシステムでは
> システム環境・エコロジーの多くが対象外になるなど、現在の構成とのずれがありうる（著者見解）。

> **工程成果物27点の一覧について**: 領域区分（システム振舞い・画面・データモデル・外部インタフェース・
> バッチ・帳票）と各成果物の名称は A44 のガイドを参照しているが、**テンプレートの様式は独自**である。
> ガイドの帳票様式を引き写したものではない。

---

### 2.9 J-SIX Hub の関連研究（構想文書で追加）

使用箇所はいずれも `docs/control-plane/concept.md`（以下 concept）。確認日は 2026-09-22。
「確認方法」欄は、書誌と主張の根拠をどこで確かめたかを示す。

| # | 主張 | 内容 | 出典 | 確認方法 | 使用箇所 |
|---|---|---|---|---|---|
| A49 | SASE の構成要素（SE4H / SE4A、ACE / AEE、MRP / CRP / VCR、BriefingScript / LoopScript / MentorScript） | 各定義。実証評価を含まないビジョン論文である | [35] | arXiv の HTML 版（v1・v3）を通読。節番号は v3 | concept §6.1 |
| A50 | SASE は硬直した普遍的プロセスを避けるが、組織が定義するプロセスをタスクごとの上書きを記録したうえで使うことは認める | "SE is a "wicked problem" where rigid, universal processes are futile."（§1）／"This process can be defined at an organizational level by process engineers (e.g., for regulatory purposes) and optionally overridden by the coach for a specific ticket, with the override being recorded."（§4.2.3） | [35] | 同上 | concept §6.1 |
| A51 | SASE は PSEE・Osterweil を参照していない | v1・v3 の本文と参考文献に "Osterweil" "process-centered" "PSEE" が出現しない | [35] | 同上（全文検索） | concept §6.1 |
| A52 | ソフトウェアプロセスをソフトウェアとして記述する研究の系譜と PSEE | 書誌のみ使用 | [36][37][38][39][40] | Crossref / OpenAlex の DOI メタデータ。[36] は本文 PDF のみ確認（7.1） | concept §6.2 |
| A53 | プロセス支援システムは広く普及せず、主要な欠点の一つは想定外の状況への対処の仕組みが不十分なことだった | "One of their major drawbacks is that they do not offer adequate mechanisms to cope with unforeseen situations. They are good at supporting business processes if all proceeds as expected, but if an unexpected situation is met, which would require one to deviate from the process model, they often become more an obstacle than a help." | [41] | OpenAlex の抄録（本文は未読） | concept §4.3, §6.2 |
| A54 | 逸脱と不整合の許容はプロセス技術の本質的な要件である | 抄録 | [42] | OpenAlex の抄録 | concept §6.2 |
| A55 | MetaGPT は SOP をプロンプト列に埋め込む | "MetaGPT encodes Standardized Operating Procedures (SOPs) into prompt sequences…"（抄録）。"Code = SOP(Team)" は論文ではなく GitHub README の表現なので使わない | [43] | arXiv PDF | concept §6.3 |
| A56 | ChatDev はウォーターフォールモデルに倣い、設計・コーディング・テストを順に進める | "ChatDev thus adopts the core principles of the waterfall model…"（arXiv v5, p.3） | [44] | arXiv PDF、ACL Anthology の書誌 | concept §6.3 |
| A57 | GitHub Agent HQ / Enterprise AI Controls の統制の中心はポリシー・監査ログ・アクセス管理・カスタムエージェント定義 | 公式ブログ・Changelog | [45][46] | 公式ページ（要約ツール経由で閲覧。引用文の逐語照合は未実施のため、concept では引用せず要旨のみ記載） | concept §6.5 |
| A58 | Copilot のエージェントにも既存のブランチ保護・必須チェックが適用され、依頼者は自分が依頼した PR を承認できない | 公式ドキュメント | [47] | 同上 | concept §6.5 |
| A59 | Kiro の Spec は `.kiro/specs` に保存され、コードとともにコミットすることが推奨されている | 公式ドキュメント | [48] | 同上 | concept §6.5 |
| A60 | Spec Kit は constitution → specify → plan → tasks → implement の段階を持つ | "Constitution once per project; specify → plan → tasks → implement → converge per feature." | [49] | README の原文を直接取得 | concept §6.5 |
| A61 | エージェントの工程を状態機械で外部から統制する研究は既にある（フェーズ状態機械、要求→ファイル→テストのトレーサビリティ、モデル外の状態機械によるゲート） | Madatha: "gates feature work through a phase state machine with requirement-to-file-to-test traceability"／Moreira: "the gate is enforced by a state machine outside the model: the agent may request advancement, not grant it" | [50][54] | arXiv の抄録を直接確認 | concept §6.4, §6.6 |
| A62 | 承認ゲート・証跡・組織横断の受入れを扱う近年の研究 | 各抄録 | [51][52][53][55][56][57][58][59] | arXiv の抄録。[51][52][53] は 2026-09-22 に OpenAlex・Semantic Scholar で書誌を確定（巻号・頁・DOI）。いずれも単一組織内の保守工程・アーキテクチャ統制が対象で、契約型・多重下請けは扱っていない | concept §6.4, §6.6 |
| A63 | 実行時の証跡が統制上の問いに答えるに足るかを測るベンチマーク | 8つの証跡レジームで比較し、trace / schema を用いる基準線は 75% で過大主張になると報告 | [60] | arXiv の抄録 | concept §6.6 |
| A64 | 組織をまたぐエージェント協調で、実装（IP）を出さずに型付き I/O と信頼階層だけを公開する提案 | 複数主体のエージェントが PR レビューを分担する | [61] | arXiv の抄録 | concept §6.6 |
| A65 | ICSSP 2024 に LLM エージェントの工程統制を扱う論文は無い | プロセス制約違反への是正ガイダンス生成、プロセスのサービス化などはある | ICSSP 2024 プログラム | https://icssp2024.events.isspa-process.org/program/ を確認（2026-09-22） | concept §6.6 |
| A66 | Journal of Software: Evolution and Process（2024-2026）に、LLM エージェントの工程統制・ガバナンスを扱う論文は無い | 近接は規制領域の成果物モデル生成、自然文からの検査制約生成、プロセス制約充足のガイダンス | OpenAlex での網羅検索（source S4210172359、10 語） | 2026-09-22 実施 | concept §6.6 |

> **A61 の意味**: H1 以前の検討では「フェーズ状態機械によるプロセス適合性の強制は既存に見当たらない」としていたが、
> A61 により**否定された**。concept §6.6 では、独自性を単独の機構ではなく4点の組み合わせと適用先（契約型開発）に改め、
> かつ「本調査の範囲では確認できなかった」という限定付きの表現にしている（B23）。

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
| B15 | 4層品質ゲート（G1-G4）の層構成 | A36（順序）・A39（hold-out）・A40（PBT）を統合し、日本の SI 向けに G4（証跡）を加えた著者設計 | 「著者設計。順序と各層の根拠は A36/A39/A40」 | J-SIX v2.1 第3章 Phase 4 |
| B16 | mutation score の閾値 | **未実測**。ハンドオフ時の仮置き値（70）は根拠がないため、Plugin の既定値としては採用しない | 「実測前のため既定値を置かない。ケーススタディ #2 で実測してから決める」 | J-SIX v2.1 エグゼクティブサマリー ※7 |
| B17 | hold-out テストの規模（UC 1件につき最低1テスト） | A39 は hold-out の必要性を示すが規模には言及がない。運用可能性からの著者推奨 | 「著者推奨。プロジェクト規模に応じて調整すべき」 | J-SIX v2.1 第3章 Phase 4 |
| B18 | G3 却下2回目で人間へエスカレーション | A37 の「veto されたうち半分は自己修正できる」から、1回の自動修正には合理性があると判断した著者の推奨値 | 「著者推奨。A37 の自己修正率から設定」 | J-SIX v2.1 第3章 Phase 4 |
| B19 | Stop hook 連続ブロック6回目で人間へ通知 | A41 の8回上限に対し、到達前に判断を仰ぐための著者設定値 | 「著者推奨。A41 の上限に対するマージン」 | J-SIX v2.1 第3章 Phase 4 |
| B20 | 証跡パッケージの3区分（証跡 / 参考所見 / 承認） | 日本の SI の納品・監査慣行に基づく著者設計。外部の標準に対応するものではない | 「著者設計」 | J-SIX v2.1 第9章 |
| B21 | 大規模・複数チームで J-SIX を各開発者の規律に委ねると、環境のばらつき・工程順序の個人依存・承認と証跡の散在・チーム間境界の侵害・例外の不可視化が起きる | 著者の実務経験に基づく見解。定量データはない | 「著者見解」 | concept §1 |
| B22 | J-SIX Hub の仮説 H-1〜H-4（統制による逸脱・迂回の減少、トレーサビリティ欠落の減少、逸脱回収による停止時間の抑制、Phase 境界限定での承認負荷） | 未検証の仮説。予備実験の設計のみ（concept §7.3） | 「仮説（未検証）」 | concept §7 |
| B23 | 4点（契約型開発の工程に沿った統制と逸脱回収、証跡の顧客納品物化、多重下請け・複数ベンダーでの中央統制、Interface Contract によるエージェント拘束）を**統合して**扱った研究・製品は確認できない | A49-A66 の調査範囲に限った判断。2026-09-22 に ICSSP 2024・JSEP を追加確認した。Google Scholar の被引用一覧は未確認（7.1）。隣接研究（[60][61][53]）は個別に存在する | 「本調査の範囲では、4点を統合して扱ったものは確認できなかった」。「存在しない」とは書かない。隣接研究を併記する | concept §6.6 |

| B24 | Hub の適合性を成果物・作業履歴・承認手続に分け、対象と版、確認可能な主体、失効条件、ローカル退避の未検証範囲を追跡する | レビューを受けて明確化した著者の設計案。実行基盤では未実装・未検証であり、品質や組織的効果の保証ではない | 「著者提案（未実装・未検証）」 | concept §2.1・2.2・4.3.1、ADR-0001・0005 |
| B25 | Hub の主体別権限・必須検査・障害復旧・緊急失効・組織間開示・比較環境と集計単位 | レビューを受けた著者の設計案。実行基盤の効果・安全性は未検証 | 「著者提案（未実装・未検証）」 | concept §2.3・4.2.1・5.2・5.3・7.3、ADR-0006・0007 |
| B26 | Property導出の反例確認、逆生成の版/範囲/記述確認、ID対応と意味的充足の分離、G3省略時は最大L3 | 本文・データ定義・Pluginの説明を整合する著者設計。効果の実証ではない | 「著者設計」 | J-SIX.md Phase 2/4/6・第9章、implementation-status.md |

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
[3] Anthropic. "How AI is Transforming Work at Anthropic" (2025.12). https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic
[4] Anthropic. "Introducing Claude Sonnet 4.5" (2025.09). https://www.anthropic.com/news/claude-sonnet-4-5
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

### 工程成果物・制度
[32] IPA.「機能要件の合意形成ガイド ver.1.0」(2010.03.31). https://www.ipa.go.jp/archive/files/000004517.pdf
[33] 国税庁.「インボイス制度に関するQ&A」問57. https://www.nta.go.jp/taxes/shiraberu/zeimokubetsu/shohi/keigenzeiritsu/pdf/qa/57.pdf
[34] IPA.「非機能要求グレード2018」. https://www.ipa.go.jp/archive/digital/iot-en-ci/jyouryuu/hikinou/ent03-b.html
### J-SIX Hub の関連研究（`docs/control-plane/concept.md` で使用）
[35] A. E. Hassan, H. Li, D. Lin, B. Adams, T.-H. Chen, Y. Kashiwa, D. Qiu. "Agentic Software Engineering: Foundational Pillars and a Research Roadmap". arXiv:2509.06216 (v1 2025.09 / v3 2026.06). https://arxiv.org/abs/2509.06216
[36] L. J. Osterweil. "Software Processes are Software Too". Proc. ICSE '87 (1987).（頁・DOI 要確認）
[37] L. J. Osterweil. "Software processes are software too, revisited". Proc. ICSE '97, pp. 540–548 (1997). https://doi.org/10.1145/253228.253440
[38] S. C. Bandinelli, A. Fuggetta, C. Ghezzi. "Software process model evolution in the SPADE environment". IEEE TSE 19(12), pp. 1128–1144 (1993). https://doi.org/10.1109/32.249659
[39] V. Ambriola, R. Conradi, A. Fuggetta. "Assessing process-centered software engineering environments". ACM TOSEM 6(3), pp. 283–328 (1997). https://doi.org/10.1145/258077.258080
[40] S. Arbaoui, J.-C. Derniame, F. Oquendo, H. Verjus. "A Comparative Review of Process-Centered Software Engineering Environments". Annals of Software Engineering 14, pp. 311–340 (2002). https://doi.org/10.1023/A:1020513911052
[41] G. Cugola. "Tolerating deviations in process support systems via flexible enactment of process models". IEEE TSE 24(11), pp. 982–1001 (1998). https://doi.org/10.1109/32.730546
[42] G. Cugola, E. Di Nitto, A. Fuggetta, C. Ghezzi. "A framework for formalizing inconsistencies and deviations in human-centered systems". ACM TOSEM 5(3), pp. 191–230 (1996). https://doi.org/10.1145/234426.234427
[43] S. Hong, M. Zhuge, et al. "MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework". ICLR 2024. https://arxiv.org/abs/2308.00352
[44] C. Qian, W. Liu, et al. "ChatDev: Communicative Agents for Software Development". ACL 2024, pp. 15174–15186. https://doi.org/10.18653/v1/2024.acl-long.810
[45] GitHub. "Welcome home, agents" (2025.10.28). https://github.blog/news-insights/company-news/welcome-home-agents/
[46] GitHub Changelog. "Enterprise AI controls & agent control plane now generally available" (2026.02.26). https://github.blog/changelog/2026-02-26-enterprise-ai-controls-agent-control-plane-now-generally-available/
[47] GitHub Docs. "Risks and mitigations for Copilot coding agent". https://docs.github.com/en/copilot/concepts/agents/coding-agent/risks-and-mitigations
[48] Kiro Docs. "Specs". https://kiro.dev/docs/specs/
[49] GitHub. "Spec Kit". https://github.com/github/spec-kit
[50] P. Madatha. "A Deterministic Control Plane for LLM Coding Agents". arXiv:2606.26924 (2026.06). https://arxiv.org/abs/2606.26924
[51] S. Vella, A. Ferworn, M. Sharieh. "ATeam: Governance-Aware LLM-Assisted Software Sustaining Engineering for Enterprise Systems". Proc. 2026 6th Int. Conf. on Electrical, Computer and Energy Technologies (ICECET), pp. 1-6, 2026. https://doi.org/10.1109/ICECET65726.2026.11633274
[52] S. Vella, S. Sharieh, M. Sharieh, A. Ferworn. "Executable Control Matters More Than Model Intelligence in LLM-Assisted Software Sustaining Engineering". Proc. 2026 2nd Int. Conf. on Federated Learning and Intelligent Computing Systems (FLICS), pp. 48-56, 2026. https://doi.org/10.1109/FLICS70075.2026.11621935
[53] F. Meawad. "Design-First Governance for Reliable AI-Assisted Software Development". Proc. 2026 IEEE 23rd Int. Conf. on Software Architecture Companion (ICSA-C), pp. 194-198, 2026. https://doi.org/10.1109/ICSA-C68850.2026.00048
[54] J. Moreira. "IACDM: Interactive Adversarial Convergence Development Methodology". arXiv:2604.16399 (v3 2026.08). https://arxiv.org/abs/2604.16399
[55] C. Koch. "Agentic Agile-V: From Vibe Coding to Verified Engineering in Software and Hardware Development". arXiv:2605.20456. https://arxiv.org/abs/2605.20456
[56] R. Kang. "Governed AI-Assisted Engineering: Graduated Human Oversight for Agentic Code Generation in Regulated Domains". arXiv:2606.22484. https://arxiv.org/abs/2606.22484
[57] X. Zhang, W. Sun. "Knowledge-Based Pull Requests: A Trusted Workflow for Agent-Mediated Knowledge Collaboration". arXiv:2606.26721. https://arxiv.org/abs/2606.26721
[58] Z. Wang, M. Liu. "Software Engineering in the Agent Era: From Trustworthy Change to Human Agent Software Organizations". arXiv:2609.04630. https://arxiv.org/abs/2609.04630
[59] P. Taghavi, S. Bhavani. "Spec Kit Agents: Context-Grounded Agentic Workflows". arXiv:2604.05278. https://arxiv.org/abs/2604.05278
[60] O. Solozobov. "DEMM-Bench: A Cross-Regime Benchmark for Agent-Runtime Governance-Evidence Sufficiency". arXiv:2606.20634. https://arxiv.org/abs/2606.20634
[61] Z. Zhao et al. "Skill-as-API: Confidential Multi-Agent Coordination for Agentic Software Engineering". arXiv:2609.01677. https://arxiv.org/abs/2609.01677
```

> **番号 [26]-[31] が本リストに無い理由**: この番号は `docs/J-SIX.md` の参考文献セクションで
> v2.1 の出典（SpecBench / Spotify Honk / Kiro / InfoQ / DORA）にすでに使用されている。
> 本リストは J-SIX.md の番号体系に追随するため、続きの [32] から採番している。

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
| 「DORA 2026 が verification tax（検証税）という語で AI 生成コードの検証負荷を定義している」 | **不採用（2026-09-10）**: 二次記事に頻出する表現だが、DORA の公開ページで当該用語を確認できなかった（報告書本体はフォーム経由の配布）。 | 用語「verification tax」は使用せず、DORA の公開ページ [31] で確認できた記述（検証負荷に関する開発者の声、30%が AI 生成コードをほぼ信頼していない）のみを引用する（A43） |
| ~~Anthropic社内「CC初回成功率33%」~~ | **訂正（2026-04-18）**: 一次ソース [3] の原文は「人間の介入ターン数が33%減少（6.2→4.1）」であり、「初回自律実行成功率33%」ではなかった。二次ソース [16] (DataCamp) で "unguided attempts 成功率約33%" と引用されていたが、原文の文脈と異なる可能性がある | J-SIX v1.0 を「人間の介入頻度33%減少」に修正。連続自律アクション数（約10→約20）を併記 |
| 「CC の連続自律アクション数 約10→約20（6ヶ月で2倍）」 | **訂正（2026-09-20）**: 一次ソース [3]（2025-12-02 公開）の原文は「連続ツール呼び出しの最大数が116%増加（約10→約21）」。あわせて [3] の公開日を「2025」から「2025.12」に、参考文献一覧の [4] の日付を 2026.02 → 2025.09 に訂正（J-SIX.md の [4] は v2.0 で訂正済みだったが、本レポートの一覧に残っていた） | J-SIX.md 第1章 1.3 を訂正。記事側（j-six-articles）に残っていた「初回自律実行成功率33%」の記述も同日に訂正した |
| 「PSEE は想定外の状況で人を支援できなかったために定着しなかった」 | **表現を弱めて採用（2026-09-22）**: 一次資料 [41] は対象を PSEE ではなくプロセス支援システム（PSS）全般とし、「主要な欠点の一つ」として述べている。普及しなかった原因を実証的に調べた研究は確認できなかった | concept では「主要な欠点の一つとして指摘されている」と書き、単一の原因として断定しない（A53） |
| Osterweil 1987 [36] の頁（pp. 2–13）と DOI | 本文 PDF は確認したが、会議録の書誌ページを確認できなかった（ACM DL が取得不可） | 頁・DOI を「要確認」のまま記載。論文化の前に ACM DL で確認する |
| [51][52][53] の書誌（IEEE 掲載） | Semantic Scholar API の書誌と抄録のみで確認。IEEE Xplore・dblp のページは取得できなかった | 「書誌は要確認」と明記。論文化の前に確認する |
| [45]-[48] の引用文 | 公式ページを要約ツール経由で閲覧したため、逐語の照合をしていない | concept では引用符付きの引用をせず、要旨のみ記載（A57-A59） |
| 関連研究の網羅性 | **2026-09-22 に一部を実施**：ICSSP 2024 のプログラムと JSEP（2024-2026）を確認し、該当論文が無いことを確かめた（A65・A66）。ICSSP 2025・2026 は開催記録を確認できず（シリーズ休止の可能性、要確認）。Google Scholar の被引用一覧は自動取得を拒否されるため未確認（表示は 76 件、Semantic Scholar では 60 件）。ChatDev の後継研究は未確認 | B23 の表現は「本調査の範囲では」に限定したまま。隣接研究（[60][61]）を concept §6.6 に明記した |

### 7.2 時間経過で陳腐化する可能性がある情報

| 情報 | リスク | 対応 |
|---|---|---|
| CC のモデル名・バージョン（Opus 4.7, 4.6, Sonnet 4.5 等） | 新モデルのリリースで陳腐化 | データ時点を明記。v2.0 で Opus 4.6/4.7 に言及追加済み |
| CC の機能一覧（Agent Teams, LSP, Monitors等） | 実験的機能が正式リリース/廃止される可能性 | v2.0 で LSP, Monitors, 新 Hook イベント等を追加済み |
| CC の料金（Max 5x $100/月） | 料金改定の可能性 | 「2026年3月時点の料金」を明記 |
| 各SDDフレームワークの比較 | フレームワークの急速な進化 | 「2026年3月時点の評価」を明記 |

### 7.3 鮮度レビューの運用（四半期）

7.2 のとおり CC のモデル名・機能・料金は陳腐化が速いため、**四半期ごと**に本レポートの
鮮度レビューを行う。手順は以下:

1. 7.2 の各行について、現行の事実と乖離がないかを確認する
2. カテゴリA（出典あり）のリンク切れ・数値の有効性を確認する
3. 変更の有無にかかわらず、冒頭「監査日」に確認日を追記する（変更なしの場合もその旨を記録）
4. 修正が生じた場合は CHANGELOG と該当ドキュメントへ反映する（CLAUDE.md チェックリスト参照）

| レビュー予定 | 状況 |
|---|---|
| 2026-06-14 | ✅ 実施（変更なし） |
| 2026-09-10 | ✅ 実施（v2.1 改訂と同時。A36-A43 追加、B15-B20 追加、verification tax の不採用を 7.1 に記録） |
| 2026-12（次回目安） | 予定 |

> 定期実行を自動化する場合は Claude Code の `/schedule`（routine）で四半期ジョブ化できる。

---

> **本監査レポートは、J-SIX プロジェクトの全ドキュメントの信頼性を担保するために作成された。**
> **記事公開・GitHub公開の前に、本レポートに基づいて各ドキュメントの出典表記を更新すること。**
