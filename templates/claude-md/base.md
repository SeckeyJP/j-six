# CLAUDE.md — [TODO: プロジェクト名]

> このファイルは Claude Code がセッション開始時に自動読込するプロジェクト憲法です。
> J-SIX (Japanese SI Transformation) プロセスに基づいています。

---

## プロジェクト概要

- **システム名**: [TODO: システム名]
- **目的**: [TODO: 1-2文でシステムの目的を記述]
- **主要ステークホルダー**: [TODO: 顧客名、利用部門等]
- **開発体制**: [TODO: 人数、役割分担]
- **J-SIX Stage**: [TODO: Stage 1 / Stage 2 / Stage 3]

### 技術スタック

- **言語**: [TODO: TypeScript / Java / Python 等]
- **フレームワーク**: [TODO: Next.js / Spring Boot / FastAPI 等]
- **DB**: [TODO: PostgreSQL / MySQL 等]
- **インフラ**: [TODO: AWS / Azure / GCP / オンプレ 等]
- **CI/CD**: [TODO: GitHub Actions / Jenkins 等]

### 主要ドキュメントの場所

- 要求 Spec: `docs/specs/requirement-spec.md`
- Design Spec: `docs/specs/design-spec.md`
- ADR: `docs/adr/`
- テスト戦略: `docs/test-strategy.md`（プロジェクトで作成）

---

## ビルド・テスト・実行コマンド

```bash
# 依存インストール
[TODO: npm install / pip install -r requirements.txt 等]

# ビルド
[TODO: npm run build 等]

# 全テスト実行
[TODO: npm test / pytest 等]

# 単一テスト実行
[TODO: npm test -- --testPathPattern=ファイル名 等]

# Lint
[TODO: npm run lint / flake8 等]

# 開発サーバー起動
[TODO: npm run dev 等]
```

> **重要**: テストは必ず実行して通ることを確認してからコミットすること。

---

## コーディング規約

### 命名規則

- **ファイル名**: [TODO: kebab-case / camelCase / snake_case]
- **クラス名**: PascalCase
- **関数名**: [TODO: camelCase / snake_case]
- **変数名**: [TODO: camelCase / snake_case]
- **定数名**: UPPER_SNAKE_CASE
- **DB テーブル名**: [TODO: snake_case / PascalCase]
- **DB カラム名**: [TODO: snake_case / camelCase]

### コードスタイル

- インデント: [TODO: スペース2 / スペース4 / タブ]
- 1関数の最大行数: 30行を目安。超える場合は分割を検討
- 1関数の最大引数: 4つまで。超える場合はオブジェクトにまとめる
- コメント: 「何をしているか」ではなく「なぜそうしているか」を書く
- TODO コメント: `// TODO(担当者名): 内容` の形式

### エラーハンドリング

- 例外は握りつぶさない。必ずログ出力またはリスローする
- ユーザー向けエラーメッセージとシステムログは分離する
- [TODO: プロジェクト固有のエラーハンドリング方針]

### インポート順序

[TODO: プロジェクトの言語に応じて記述。例:]
```
1. 標準ライブラリ
2. サードパーティライブラリ
3. プロジェクト内モジュール（絶対パス）
4. プロジェクト内モジュール（相対パス）
```

---

## ディレクトリ構成

```
[TODO: プロジェクトのディレクトリ構成を記述]
```

> 新規ファイルを作成する場合は、上記の構成に従うこと。不明な場合は確認を求めること。

---

## Git 運用ルール

### ブランチ戦略

- **main**: 本番リリース用。直接コミット禁止
- **develop**: 開発統合ブランチ
- **feature/xxx**: 機能開発ブランチ
- **fix/xxx**: バグ修正ブランチ
- **release/vX.X.X**: リリース準備ブランチ

### コミットメッセージ

Conventional Commits に準拠する。

```
<type>(<scope>): <description>

[optional body]
```

type: feat / fix / docs / style / refactor / test / chore
scope: 変更対象のモジュール名

例:
```
feat(auth): Google OAuth ログインを追加
fix(api): ユーザー検索の N+1 クエリを修正
test(auth): ログインバリデーションのテストを追加
```

### コミット粒度

- 1タスク = 1コミット を基本とする
- TDD サイクルでは Red（テスト追加）→ Green（実装）→ Refactor でそれぞれコミット

---

## 品質基準

### テスト

- 単体テストカバレッジ目標: [TODO: 80% / 85% / 90% 等]
- 新規コードには必ずテストを書く（TDD を推奨）
- テストファイルの配置: [TODO: __tests__/ / *.test.ts / tests/ 等]
- テストの命名: `[対象]_[条件]_[期待結果]` 形式を推奨

### 静的解析

- [TODO: ESLint / Pylint / SonarQube 等のルール]
- Lint エラーはコミット前に全て解消すること

### パフォーマンス基準

- API レスポンスタイム: [TODO: 200ms以内 等]
- ページ読込時間: [TODO: 3秒以内 等]
- [TODO: その他プロジェクト固有の基準]

---

## ADR（Architecture Decision Records）ルール

設計判断を行った場合は ADR を記録する。

### ADR が必須のケース

- 技術スタック / ライブラリの選定・変更
- DB 設計の重要な判断（テーブル構成、インデックス戦略等）
- API 設計方針の決定
- セキュリティ方針の決定
- パフォーマンスに影響する設計判断
- 代替案を検討して却下した場合

### ADR の作成手順

1. `docs/adr/NNNN-タイトル.md` に作成
2. テンプレート: `templates/adr/template.md` に従う
3. 内容: コンテキスト、判断、理由、検討した代替案、影響
4. 判断の発生時にドラフトを作成し、レビュー後に承認

---

## セキュリティ・禁止事項

### 禁止事項

- 本番環境のデータベースへの直接接続・操作
- 機密情報（API キー、パスワード、個人情報）のソースコードへのハードコーディング
- `.env` ファイルの Git コミット
- [TODO: プロジェクト固有の禁止事項]

### 使用禁止ライブラリ

- [TODO: 禁止ライブラリがあれば列挙。代替も示す]
- 例: `moment.js` は禁止。代わりに `dayjs` を使用

### 変更禁止ファイル

以下のファイルは CC による変更を禁止する。変更が必要な場合は人間に確認を求めること。

- [TODO: 例: docker-compose.prod.yml]
- [TODO: 例: .github/workflows/deploy.yml]
- [TODO: 例: infrastructure/ 配下]

### 機密情報の扱い

- 環境変数: `.env` ファイルで管理（`.env.example` のみコミット）
- シークレット: [TODO: AWS Secrets Manager / Vault 等]

---

## CC 自律実行の範囲（J-SIX 自律度設定）

### Phase 4（TDD 実装）での自律実行ルール

- テストを先に書き、失敗を確認してからコミットすること
- テストが通る最小の実装を行うこと。過剰な先回り実装は禁止
- テスト3回連続失敗した場合は、人間に相談すること
- 要求 Spec に記載のない要件が必要と判明した場合は、人間に確認を求めること

### エスカレーション条件

以下の場合は自律実行を中断し、人間に判断を仰ぐこと。

- 要求 Spec のスコープ外の機能が必要になった場合
- セキュリティに関わる設計判断が必要な場合
- 外部 IF の仕様変更が必要な場合
- 「変更禁止ファイル」の変更が必要な場合
- アーキテクチャ（ディレクトリ構成の大幅変更等）に影響する判断
- パフォーマンスに重大な影響がある設計判断

---

## プロジェクト固有ルール

[TODO: 上記カテゴリに収まらないプロジェクト固有のルールをここに追記]
