# J-SIX CLAUDE.md テンプレート ガイド

**Author**: H.Sekita | **Version**: 1.0 | **Date**: 2026-03-29

---

## 1. CLAUDE.md とは何か

CLAUDE.md は Claude Code がセッション開始時に自動で読み込む **プロジェクト憲法** である。ここに書かれたルールが CC の全出力を制約する。

J-SIX プロセスでは、従来の「開発標準書」「コーディング規約」「プロジェクト計画書」に相当する情報を CLAUDE.md に集約し、CC が理解・実行可能な形式で記述する。

### なぜ重要か

Anthropic 社内の調査（2025）で、**CLAUDE.md の充実度と CC 出力品質は直接相関する** と報告されている。CLAUDE.md が貧弱なプロジェクトでは CC が毎回異なるスタイルでコードを生成し、品質が安定しない。

### CLAUDE.md vs Skills

| | CLAUDE.md | Skills |
|---|---|---|
| 読み込みタイミング | **毎セッション自動** | 必要時にオンデマンド |
| 適切な内容 | 常に守るべきルール | 特定ワークフローの手順 |
| 例 | コーディング規約、ビルドコマンド | 設計書逆生成、TDDサイクル |

**原則**: 全セッションで適用すべきルールは CLAUDE.md に、特定タスクでのみ必要な手順は Skills に分離する。

---

## 2. テンプレートの構成

J-SIX では CLAUDE.md を **共通部分** と **プロジェクト固有部分** に分離する。

```
プロジェクトルート/
├── CLAUDE.md                    ← プロジェクト固有（本ファイルをカスタマイズ）
└── .claude/
    └── settings.json            ← CC の権限設定
```

テンプレートは以下の3種類を用意している。

| テンプレート | 対象 | ファイル |
|---|---|---|
| **base** | 全プロジェクト共通の基盤 | `base.md` |
| **web-app** | Web アプリケーション | `web-app.md` |
| **api-service** | API / バックエンドサービス | `api-service.md` |

使い方: `base.md` の内容をベースに、プロジェクト種別のテンプレート（`web-app.md` 等）の内容をマージしてプロジェクトの CLAUDE.md を作成する。

---

## 3. カスタマイズの手順

### Step 1: テンプレートのコピー

```bash
cp templates/claude-md/base.md ./CLAUDE.md
```

### Step 2: プロジェクト固有情報の記入

`[TODO: ...]` と記載された箇所を埋める。

### Step 3: プロジェクト種別セクションの追加

Web アプリなら `web-app.md`、API サービスなら `api-service.md` の該当セクションを追記。

### Step 4: 育てる

CLAUDE.md は **生きたドキュメント** である。CC を使う中で不足に気づいたら随時追記する。特に以下のタイミングで更新する。

- CC が規約に反するコードを生成した → ルールを追記
- CC が同じ質問を繰り返す → 回答を CLAUDE.md に記載
- 新しいライブラリ/ツールを導入した → 技術スタック・コマンドを更新
- 設計判断が確定した → ADR を作成し、CLAUDE.md から参照

---

## 4. アンチパターン

| アンチパターン | 問題 | 対策 |
|---|---|---|
| **巨大すぎる CLAUDE.md** | コンテキストウィンドウを圧迫し、CC の性能が低下 | 25KB / 200行以内を目安に。詳細は Skills や外部ファイルに分離 |
| **曖昧な指示** | CC が解釈を誤る | 「良いコードを書け」ではなく「関数は30行以内、引数は4つ以内」と具体的に |
| **禁止のみで代替案なし** | CC が行き詰まる | 「X は禁止。代わりに Y を使え」と必ず代替を示す |
| **更新されない CLAUDE.md** | 実態と乖離してCC が混乱 | Sprint ごと / Phase ごとにレビュー・更新 |
| **全てを CLAUDE.md に詰め込む** | 特定タスク用の手順でコンテキストを浪費 | Skills / 外部ファイルに分離し「詳細は docs/xxx.md 参照」と記述 |

---

## 参考文献

- Anthropic. "Best Practices for Claude Code". https://code.claude.com/docs/en/best-practices
- Anthropic. "How Anthropic teams use Claude Code" (2025.07). https://claude.com/blog/how-anthropic-teams-use-claude-code
- Codingscape. "How Anthropic engineering teams use Claude Code every day" (2025.12). https://codingscape.com/blog/how-anthropic-engineering-teams-use-claude-code-every-day
