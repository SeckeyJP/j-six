# J-SIX — Japanese SI Transformation

**Claude Code で日本のSI開発を再定義する、AI ネイティブ開発プロセス**

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

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

### 期待効果（著者推定）

- 実装工数 **60-70% 削減**
- 設計書⇔コード乖離 **原理的にゼロ**
- テストカバレッジ **85-95%**（TDD全面適用時）

---

## ドキュメント構成

### メインドキュメント

| ドキュメント | 内容 |
|---|---|
| **[J-SIX_v1.0.md](docs/J-SIX_v1.0.md)** | J-SIX プロセス完成版（全8章） |

### 実践ガイド

| ドキュメント | 内容 |
|---|---|
| [Phase 4 TDD ワークスルー](docs/walkthrough-phase4-tdd.md) | TDD サイクルの具体的なコマンド・プロンプト・出力例 |
| [レガシーコード適用ガイド](docs/guide-legacy-code.md) | 既存コードベースへの J-SIX 段階的適用戦略 |

### テンプレート

| ディレクトリ | 内容 |
|---|---|
| [templates/claude-md/](templates/claude-md/) | CLAUDE.md テンプレート（base / web-app / api-service）+ ガイド |
| [templates/spec/](templates/spec/) | Spec テンプレート（要求Spec / Design Spec） |
| [templates/adr/](templates/adr/) | ADR テンプレート |

### Claude Code Plugin

| ディレクトリ | 内容 |
|---|---|
| [plugin/](plugin/) | J-SIX Plugin（Skills 6件 / Agents 5件 / Hooks） |

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

詳細は [J-SIX_v1.0.md](docs/J-SIX_v1.0.md) を参照してください。

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
| 1 | J-SIX 概論 | Qiita/Zenn 記事 | 予定 |
| 2 | CLAUDE.md テンプレート | テンプレート集 | ✅ 完成 |
| 3 | ADR テンプレート・運用ガイド | テンプレート + ガイド | ✅ 完成 |
| 4 | 設計書逆生成 Skill | Claude Code Skill | ✅ 完成 |
| 5 | j-six-plugin | Claude Code Plugin | ✅ 完成 |
| 6 | TDD × CC サブエージェント実践 | Qiita/Zenn 記事 | 予定 |

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
