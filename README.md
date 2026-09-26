# J-SIX — Japanese SI Transformation

**Claude Code で日本のSI開発を再定義する、AI ネイティブ開発プロセス**

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

📖 **全体像（1枚で把握）: https://seckeyjp.github.io/j-six/**

---

## J-SIX とは

J-SIX（Japanese SI Transformation）は、日本のSI業界で広く採用されているV字モデル（ウォーターフォール）を、[Claude Code](https://code.claude.com/) の能力を前提にゼロから再設計した **AI ネイティブ開発プロセス** です。

従来のV字モデルにAIを「貼り付ける」のではなく、世界標準の Spec-Driven Development（SDD）の原則を採用しつつ、日本特有の品質基準・設計書文化・受発注構造に対応する **日本品質レイヤー** を独自に設計しています。

### 4つの設計原則

| # | 原則 | 内容 |
|---|---|---|
| 1 | **CC ネイティブ** | 外部フレームワーク（BMAD等）に依存せず、Claude Code のネイティブ機能のみで構築 |
| 2 | **3層ドキュメント** | Spec（Why）+ ADR（Why Not）+ 逆生成設計書（What/How）で従来設計書を超越 |
| 3 | **TDD が品質の中核** | テストファーストにより CC 自律実行の品質を担保 |
| 4 | **段階的移行** | 既存V字モデルから3ステージで移行。既存案件を止めない |

### 期待効果

- 実装工数 **60-70% 削減** 🟡 著者推定（未実測）
- 設計書とコードの乖離低減を目指す。対象版のOpenAPI一致を[ケーススタディ #1](docs/case-study-01.md)で確認。LLM記述・変換・変更後の再確認は別途必要。
- [実装と検証範囲](docs/implementation-status.md): G3省略時は最大L3、ID対応と要求充足の違い、Excel/Word変換の確認範囲。
- テストカバレッジ **85-95%**（TDD全面適用時）🟢 実測例あり（同ケースで99%。N=1）
- mutation score（テストスイート自体の有効性）🟢 実測例あり（[ケーススタディ #2](docs/case-study-02.md) で **カバレッジ 99% のコードが 91.8%**。性質テスト追加後 93.4%。N=1）

> 各数値の検証ステータス（実測／推定）は [J-SIX.md の期待効果テーブル](docs/J-SIX.md) と [ケーススタディ #1](docs/case-study-01.md) を参照。

### レビュー前の4層品質ゲート（v2.1）

人間レビューに出す前に、性質の異なる4つの監督面を**順に**通します。後段は前段を通過した場合のみ実行します。

| 層 | 内容 | 判定主体 |
|---|---|---|
| **G1** 決定論的検証 | build / lint / SAST / secret / 依存脆弱性 / スコープ検査 | script |
| **G2** テスト品質検証 | テスト通過 / カバレッジ / mutation score / テスト改変検出 / hold-out 受入テスト / トレーサビリティ | script |
| **G3** 意図・スコープ判定 | 正確性・要件未充足・スコープ逸脱**のみ**を fresh context の judge が判定 | LLM |
| **G4** 証跡パッケージ生成 | 人間レビュー用・顧客納品用の記録を構造化出力 | script + LLM（要約のみ） |

**なぜテスト通過だけでは足りないのか**: 監督面がテストスイート単独だと、エージェントはそれを
最適化対象として扱う（reward hacking）。詳細と出典は [J-SIX.md 第2章 2.3](docs/J-SIX.md) を参照。

---

## ドキュメント構成

### メインドキュメント

| ドキュメント | 内容 |
|---|---|
| **[J-SIX.md](docs/J-SIX.md)** | J-SIX プロセス定義 v2.1（全9章 + 付録） |
| [index.html](index.html) | **全体像を1枚にまとめた HTML**（ブラウザで開くだけ。原則・プロセス・移行・期待効果・実証・Plugin） |

### 実践ガイド

| ドキュメント | 内容 |
|---|---|
| [Phase 4 TDD ワークスルー](docs/walkthrough-phase4-tdd.md) | TDD サイクルの具体的なコマンド・プロンプト・出力例 |
| [レガシーコード適用ガイド](docs/guide-legacy-code.md) | 既存コードベースへの J-SIX 段階的適用戦略 |

### 実証（動くサンプル）

| ドキュメント | 内容 |
|---|---|
| [ケーススタディ #1](docs/case-study-01.md) | 申請承認ワークフローで J-SIX を一周。**実測値**と推定値を切り分けて提示 |
| [ケーススタディ #2](docs/case-study-02.md) | **「カバレッジ 99%」の mutation score を実測**。生存ミュータントから性質テスト（PBT）を導く |
| [examples/approval-workflow/](examples/approval-workflow/) | 上記の動くサンプル（FastAPI。ケーススタディ #2 時点で 45テスト + hold-out 10件 / カバレッジ99% / mutation 93.4%。実動検証 #1 の追加実装後は 81テスト + hold-out 72件 / 99.0% / 92.4%）。テンプレ記入済み実例も兼ねる |
| [examples/monthly-billing/](examples/monthly-billing/) | 第2サンプル「月次請求書発行」（画面・帳票・バッチ・外部IF。101テスト + hold-out 19件 / カバレッジ98.8% / mutation 91.9%）。工程成果物27点の記入済み実例を兼ねる |
| [Plugin 実動検証 #1](docs/plugin-field-test-01.md) | Plugin の Skill 7本をヘッドレス実行。不具合8件を発見・修正（大半は単体テストでは検出できない種類） |

### テンプレート

| ディレクトリ | 内容 |
|---|---|
| [templates/claude-md/](templates/claude-md/) | CLAUDE.md テンプレート（base / web-app / api-service）+ ガイド |
| [templates/spec/](templates/spec/) | Spec テンプレート（要求Spec / Design Spec） |
| [templates/adr/](templates/adr/) | ADR テンプレート |
| [templates/deliverables/](templates/deliverables/) | 工程成果物テンプレート27点（IPA 機能要件の合意形成ガイド準拠）＋ 基本設計書・詳細設計書への[組立定義](templates/deliverables/assembly/GUIDE.md) |

### Claude Code Plugin

| ディレクトリ | 内容 |
|---|---|
| [plugin/](plugin/) | J-SIX Plugin（Skills 7件 / Agents 7件 / Hooks / 決定論的チェック 11本 / 評価ケース） |

詳細は [plugin/README.md](plugin/README.md) を参照してください。

### 設計議論（Design Discussions）

J-SIX の設計判断に至る議論の過程を記録したドキュメント群です。

| # | ドキュメント | 論点 |
|---|---|---|
| 01a | [CC活用プロセスの探求](docs/discussions/01a_cc_full_process_discussion.md) | Phase 0-6 の初期提案 |
| 02 | [SDD vs 独自設計](docs/discussions/02_discussion_sdd_vs_custom.md) | CC ネイティブ + 日本品質レイヤーの設計根拠 |
| 03 | [設計書逆生成の限界と対策](docs/discussions/03_discussion_reverse_doc_gen.md) | 3層ドキュメント戦略の設計根拠 |
| 04 | [CC自律実行の範囲](docs/discussions/04_discussion_autonomy_scope.md) | 自律度5段階モデルの設計根拠 |
| 05 | [段階的移行パス](docs/discussions/05_discussion_migration_path.md) | V字→J-SIXの3ステージ移行 |

### 参考資料

| ドキュメント | 内容 |
|---|---|
| [ROADMAP.md](docs/ROADMAP.md) | 改善・追加機能ロードマップ（v2.1 → v2.5 想定） |
| [REFERENCES_AUDIT.md](docs/REFERENCES_AUDIT.md) | 出典・参考文献の監査レポート |
| [01_process_overview.md](docs/archive/01_process_overview.md) | 初版俯瞰図（V字+CC補助版。参考資料） |

---

## J-SIX プロセス概要

```
Phase 0: プロジェクト憲法策定（CLAUDE.md）     ← 人間が主導
Phase 1: 要求の合意（Spec 策定）               ← 人間が主導、CCが支援
Phase 2: 技術設計（Design Spec + プロトタイプ） ← 人間が判断、CCが具現化
Phase 3: タスク分解                            ← CCが提案、人間が承認
  ─── ここから CC 自律実行圏 ───
Phase 4: TDD 実装  ★生産性の源泉             ← CC自律実行（L3-L4）
Phase 5: 品質検証                              ← 自動 + 人間サンプリング
Phase 6: ドキュメント生成（3層戦略）           ← CCが逆生成、人間が承認
```

詳細は [J-SIX.md](docs/J-SIX.md) を参照してください。

---

## 段階的移行パス

既存のV字モデル案件を止めずに移行できる3ステージ移行を提案しています。

```
Stage 0 → Stage 1（3ヶ月）→ Stage 2（3-6ヶ月）→ Stage 3（6ヶ月〜）
従来V字    V字+CC補助        SDD+V字互換          J-SIX
L0         L1-L2             L2-L3                L3-L4
```

---

## 対象読者

- **PM・PL**: プロセス導入の判断材料として
- **経営層**: ROI・移行リスクの評価材料として
- **SE・開発者**: 実践ガイド + テンプレート + Plugin として
- **QA**: 品質管理の役割再定義の参考として

---

## 今後の展開

| # | テーマ | 形態 | 状態 |
|---|---|---|---|
| 1 | J-SIX シリーズ記事（#0-#5） | Qiita/Zenn 記事 | ✅ 全6本公開済 |
| 2 | 番外編記事（13本） | Qiita/Zenn 記事 | ✅ 全13本公開済 |
| 3 | CLAUDE.md テンプレート | テンプレート集 | ✅ 完成 |
| 4 | ADR テンプレート・運用ガイド | テンプレート + ガイド | ✅ 完成 |
| 5 | 設計書逆生成 Skill | Claude Code Skill | ✅ 完成 |
| 6 | j-six-plugin | Claude Code Plugin | ✅ 完成 |
| 7 | 4層品質ゲート（G1-G4）の Plugin 実装 | Plugin scripts / Agents / Skills | ✅ 完成 |
| 8 | 証跡パッケージ（顧客納品対応） | evidence-pack Skill | ✅ 完成 |
| 9 | [ケーススタディ #2](docs/case-study-02.md)（mutation score の実測） | 記事 + GitHub | ✅ 完成 |
| 10 | 工程成果物テンプレート（IPA 27点）・組立定義・第2サンプル [monthly-billing](examples/monthly-billing/) | テンプレート + 実例 | ✅ 完成 |
| 11 | [J-SIX Hub](docs/control-plane/)（大規模・複数チーム向けにプロセス適合性を中央で統制する構想） | 構想文書 + [リプレイ型サンプル](https://seckeyjp.github.io/j-six-hub/) + [ケーススタディ #3](docs/case-study-03.md) | 構想中（仮説であり未実装。サンプルは公開済み） |

次フェーズ（実証・テンプレート実例・Plugin 実用拡張）の計画は [ROADMAP.md](docs/ROADMAP.md) を参照してください。

---

## 本プロジェクトの性質

J-SIX は著者がオリジナルに設計した開発プロセス提案です。以下の知見を統合・再構成しています。

- **SDD の原則**: Spec-Driven Development コミュニティの共有知見
- **CC ネイティブ機能**: Anthropic 公式ドキュメントおよび実践者の知見
- **品質データ**: CodeRabbit、Anthropic 等の公開調査報告
- **日本品質レイヤー**: 日本のSI業界の実務慣行に基づく著者の設計

期待効果の数値は著者の推定であり、実プロジェクトでの検証はこれからの課題です。全ての出典は [REFERENCES_AUDIT.md](docs/REFERENCES_AUDIT.md) で確認できます。

---

## ライセンス

[CC BY 4.0](LICENSE)（クリエイティブ・コモンズ 表示 4.0 国際）

---

## 著者

**H.Sekita**

---

## コントリビュート

Issue や Pull Request を歓迎します。特に以下の観点でのフィードバックをお待ちしています。

- 実プロジェクトでの適用経験・改善提案
- 設計書逆生成の品質に関する知見
- TDD × Claude Code の実践パターン
- 日本のSI業界特有の課題・制約への対応

案件導入の準備には[適用条件と検証戦略](docs/adoption-and-verification.md)、[記入例](docs/verification-examples.md)、[共通フレームとの限定的対応](docs/process-mapping.md)を参照。現段階の検証はサンプル・合成例を対象とし、企業の実PJでの適用効果は未検証。
