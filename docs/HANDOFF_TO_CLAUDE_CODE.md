# J-SIX プロジェクト 引き継ぎ資料

## — Claude Code での継続作業用 —

**作成日**: 2026-03-29
**著者**: H.Sekita
**GitHub**: SeckeyJP

---

## 1. プロジェクト概要

**J-SIX**（Japanese SI Transformation）は、日本のSI業界向けに Claude Code をフル活用した AI ネイティブ開発プロセスを提案するプロジェクト。

**目的**: Qiita/Zenn での記事公開 + GitHub でのドキュメント・テンプレート公開

---

## 2. 完了済みの作業

### 2.1 プロセス設計（全4論点の議論完了）

| 論点 | 結論 | ドキュメント |
|---|---|---|
| 1. 既存SDD vs 独自設計 | CC ネイティブ + 日本品質レイヤーのハイブリッド | 02_discussion_sdd_vs_custom.md |
| 2. 設計書逆生成の限界 | 3層戦略（Spec + ADR + 逆生成設計書） | 03_discussion_reverse_doc_gen.md |
| 3. CC自律実行の範囲 | 自律度5段階モデル（L0-L4）。Phase4をL3-L4で運用 | 04_discussion_autonomy_scope.md |
| 4. 段階的移行パス | 3ステージ（V字+CC補助→ハイブリッド→J-SIX全面） | 05_discussion_migration_path.md |

### 2.2 成果物一覧

**リポジトリ1: j-six（本体）— 21ファイル**

```
j-six/
├── README.md                              # リポジトリ説明
├── LICENSE                                # CC BY 4.0
├── CHANGELOG.md                           # リリースノート
├── docs/
│   ├── J-SIX_v1.0.md                     # ★メインドキュメント（660行）
│   ├── REFERENCES_AUDIT.md                # 出典監査（ファクト35件/推定14件）
│   ├── walkthrough-phase4-tdd.md          # TDDワークスルー（291行）
│   ├── guide-legacy-code.md               # レガシーコード適用ガイド（214行）
│   ├── article-plan.md                    # 記事公開計画
│   ├── discussions/
│   │   ├── 01a_cc_full_process_discussion.md  # Phase 0-6 初期提案
│   │   ├── 02_discussion_sdd_vs_custom.md     # 論点1
│   │   ├── 03_discussion_reverse_doc_gen.md   # 論点2
│   │   ├── 04_discussion_autonomy_scope.md    # 論点3
│   │   └── 05_discussion_migration_path.md    # 論点4
│   └── archive/
│       └── 01_process_overview.md             # 初版（V字+CC補助版。参考）
├── templates/
│   ├── README.md
│   ├── claude-md/
│   │   ├── GUIDE.md              # テンプレート利用ガイド
│   │   ├── base.md               # 全プロジェクト共通（241行）
│   │   ├── web-app.md            # Web アプリ向け追加
│   │   └── api-service.md        # API サービス向け追加
│   ├── spec/
│   │   ├── requirement-spec.md   # 要求Spec テンプレート
│   │   └── design-spec.md        # Design Spec テンプレート
│   └── adr/
│       └── template.md           # ADR テンプレート
```

**リポジトリ2: j-six-articles（記事管理）— 7ファイル**

```
j-six-articles/
├── .github/workflows/publish.yml   # zenn-qiita-sync 設定済み
├── .gitignore
├── README.md
├── package.json                    # Zenn CLI 用
├── articles/
│   └── j-six-00-overview.md        # ★概要編（#0）本文入り（204行）published: false
├── images/.gitkeep
└── qiita/public/.gitkeep
```

### 2.3 出典・品質管理

- 参考文献25件を付録Dに整理（J-SIX_v1.0.md）
- 出典監査レポート作成済み（REFERENCES_AUDIT.md）
  - カテゴリA（ファクト）: 35件（全URLあり）
  - カテゴリB（著者推定）: 14件（明示済み）
  - カテゴリC（一般知識）: 6件
- 「ACM 2025」の不確実な引用 → CodeRabbit（1.7倍）に統一済み
- 全数値に「著者推定」の注記済み

### 2.4 命名・ブランディング

- プロセス名: **J-SIX**（Japanese SI Transformation）
- 旧名「CC-Full」は全ファイルから排除済み（確認済み）
- 著者: **H.Sekita**（全ドキュメントに記載済み）
- GitHub: **SeckeyJP**（全リンク埋め込み済み）
- ライセンス: CC BY 4.0

---

## 3. 未完了の作業（優先順位順）

### 3.1 最優先: GitHub 公開

**状態**: アーカイブ（tar.gz）作成済み。push のみ未実行。

**手順**:
```bash
# セットアップスクリプトが用意済み（setup-github.sh）
# 3ファイルを同じディレクトリに配置して実行:
#   - setup-github.sh
#   - j-six-repo.tar.gz
#   - j-six-articles-repo.tar.gz
bash setup-github.sh
```

**手動作業**（ブラウザ必要）:
1. Zenn 連携: https://zenn.dev/dashboard/deploys で j-six-articles を接続
2. Qiita トークン: https://qiita.com/settings/tokens/new で発行 → リポジトリ Secrets に QIITA_TOKEN 登録

### 3.2 記事公開

**概要編（#0）**: 本文作成済み（articles/j-six-00-overview.md）。レビュー後に published: true にして push。

**シリーズ記事（#1-#5）**: 構成設計済み（docs/article-plan.md）。本文は未執筆。

| # | slug | タイトル | ソース | 状態 |
|---|---|---|---|---|
| #0 | j-six-00-overview | J-SIX概論 | 全体要約 | ★本文済み |
| #1 | j-six-01-sdd | V字モデル前提崩壊とSDD | 01a, 02 | 構成のみ |
| #2 | j-six-02-3layer-doc | 3層ドキュメント戦略 | 03 | 構成のみ |
| #3 | j-six-03-tdd-cc | TDD × Claude Code | 04 + ワークスルー | 構成のみ |
| #4 | j-six-04-claude-md | CLAUDE.md実践ガイド | テンプレート類 | 構成のみ |
| #5 | j-six-05-migration | 段階的移行パス | 05 + レガシーガイド | 構成のみ |

**記事作成手順**:
```bash
cd j-six-articles
npx zenn new:article --slug j-six-01-sdd --title "タイトル"
# articles/j-six-01-sdd.md を編集
# published: true にして push → Zenn/Qiita に自動公開
```

### 3.3 Plugin 実装（中期）

docs/J-SIX_v1.0.md 第4章で設計済み。j-six-plugin として CC Plugin 化する。

```
j-six-plugin/
├── skills/          # Spec作成、設計書逆生成、TDDサイクル、品質メトリクス等
├── agents/          # Red/Green/Refactor Agent、QA Reviewer等
├── hooks/           # pre-commit品質チェック、ADR検出、エスカレーション監視等
└── templates/       # 既存テンプレート統合
```

### 3.4 設計書逆生成 Skill 実装（中期）

実装済みコードから基本設計書・詳細設計書・IF設計書・DB設計書を自動生成する Skill。

---

## 4. J-SIX プロセスの核心（Claude Code が理解すべきこと）

### 4.1 4つの設計原則

1. **CC ネイティブ**: 外部FW（BMAD等）非依存。CC の CLAUDE.md / Skills / Subagents / Hooks / Agent Teams で構築
2. **3層ドキュメント**: Spec（Why）+ ADR（Why Not）+ 逆生成設計書（What/How）
3. **TDD が品質の中核**: テストファースト + サブエージェント分離 + Writer/Reviewer
4. **段階的移行**: Stage 1（V字+CC補助）→ Stage 2（ハイブリッド）→ Stage 3（J-SIX全面）

### 4.2 7つの Phase

```
Phase 0: CLAUDE.md 策定         [L1]
Phase 1: 要求の合意（Spec）     [L1-L2] 🚪顧客承認
Phase 2: 技術設計（Design Spec） [L2]   🚪設計レビュー
Phase 3: タスク分解             [L2]   🚪タスク承認
Phase 4: TDD実装 ★生産性の源泉  [L3-L4] 🚪自動テスト+CC相互レビュー
Phase 5: 品質検証               [L2-L3] 🚪品質基準達成
Phase 6: ドキュメント生成       [L3]   🚪納品物レビュー
```

### 4.3 自律度5段階（L0-L4）

- L0: 手動（CCは参考回答のみ）
- L1: CC支援（人間が主導）
- L2: CC主導/人間承認（毎回承認）
- L3: CC自律/人間監督（結果を事後確認）
- L4: CC完全自律（自動テストのみ）

### 4.4 重要なデータ（出典付き）

| データ | 値 | 出典 |
|---|---|---|
| CC初回自律実行成功率 | 約33% | Anthropic社内（How Anthropic teams use CC） |
| AI生成コードのイシュー率 | 人間の約1.7倍 | CodeRabbit（2025.12、470PR分析） |
| セキュリティイシュー | 最大2.74倍 | 同上 |
| Sonnet 4.5 コード編集エラー率 | 0% | Anthropic公式（2026.02） |

### 4.5 日本SI固有の対応

- 設計書文化: Phase 6 で逆生成。従来フォーマット（Excel/Word）対応
- 受発注構造: CLAUDE.md で全参加者のルール統一
- 品質保証部門: QA→「テスト戦略+サンプリング検証+探索的テスト」に再定義
- IPA/共通フレーム: Phase が共通フレームにマッピング可能

---

## 5. ファイルの取得方法

本セッションで作成した全ファイルは以下のアーカイブに格納済み。

```
j-six-repo.tar.gz           # 本体リポジトリ（21ファイル、72KB）
j-six-articles-repo.tar.gz  # 記事リポジトリ（7ファイル、7KB）
setup-github.sh              # GitHub公開セットアップスクリプト
```

展開方法:
```bash
tar xzf j-six-repo.tar.gz        # → repo/ ディレクトリ
tar xzf j-six-articles-repo.tar.gz  # → articles-repo/ ディレクトリ
```

---

## 6. Claude Code での作業時の注意事項

### 6.1 CLAUDE.md への記載推奨事項

Claude Code でこのプロジェクトを扱う際、以下を CLAUDE.md に記載することを推奨:

```markdown
# J-SIX プロジェクト

## プロジェクト概要
J-SIX (Japanese SI Transformation) のドキュメント・テンプレート・記事管理。
著者: H.Sekita / GitHub: SeckeyJP

## リポジトリ構成
- j-six/: 本体（プロセス定義・テンプレート）
- j-six-articles/: Qiita/Zenn 記事管理（Zenn CLI + zenn-qiita-sync）

## 品質ルール
- 主張には出典を付ける（REFERENCES_AUDIT.md 参照）
- 著者推定の数値は「著者推定」と明記する
- CC-Full は使わない。J-SIX に統一
- [USERNAME] は SeckeyJP に統一

## 記事のルール
- Zenn形式（articles/ 配下）で執筆
- published: false で作成、レビュー後に true
- シリーズタグ: j-six, claudecode, ai-development, si
- 出典は Zenn の脚注形式 [^name] で記載
```

### 6.2 記事執筆の進め方

シリーズ記事（#1-#5）を書く際のワークフロー:

1. `docs/article-plan.md` で該当記事の構成を確認
2. ソースとなるディスカッション文書を読む
3. `npx zenn new:article --slug j-six-NN-xxx --title "タイトル"` で記事ファイル作成
4. 記事計画の構成に沿って執筆
5. 出典は REFERENCES_AUDIT.md から参照
6. `npx zenn preview` でプレビュー確認
7. published: true にして push

### 6.3 Plugin 実装の進め方

1. `j-six/` リポジトリ内に `plugin/` ディレクトリを作成
2. J-SIX_v1.0.md 第4章 (4.3 CC Plugin 構成) の設計に従う
3. Skills → Agents → Hooks の順で実装
4. 既存テンプレート（templates/）を Skills に統合

---

## 7. 議論の経緯サマリー（コンテキスト復元用）

1. **初版**: V字モデルにCCを貼り付けた俯瞰図を作成
2. **転換**: 「CCフル活用のプロセスになっていない」との指摘 → 世界標準SDDを調査
3. **論点1**: BMAD等の既存FW vs 独自 → CC ネイティブ + 日本品質レイヤーに決定
4. **論点2**: 設計書逆生成の限界 → 3層ドキュメント戦略（Spec + ADR + 逆生成）
5. **論点3**: CC自律実行の範囲 → 5段階モデル、Phase 4 を L3-L4 で運用
6. **論点4**: 段階的移行 → 3ステージ（既存案件を止めない）
7. **統合**: 全論点を J-SIX_v1.0.md に統合
8. **出典監査**: 全主張を ファクト/推定/一般知識 に分類、参考文献25件整理
9. **命名**: CC-Full → J-SIX（Japanese SI Transformation）にリブランド
10. **リポジトリ設計**: 本体 + 記事の2リポジトリ構成
11. **テンプレート**: CLAUDE.md（base/web/api）、Spec、ADR を具体化
12. **補足ガイド**: TDDワークスルー + レガシーコード適用ガイド
13. **記事計画**: 概要編1本 + シリーズ5本の構成設計、概要編本文執筆
14. **記事管理**: zenn-qiita-sync による Zenn/Qiita 同時公開体制

---

> この資料があれば、Claude Code で本プロジェクトの全コンテキストを復元し、
> 任意の作業を継続できる。
