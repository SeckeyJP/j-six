# J-SIX テンプレート集

J-SIX プロセスで使用するテンプレートを格納するディレクトリです。

## ディレクトリ構成

```
templates/
├── claude-md/              # CLAUDE.md テンプレート
│   ├── GUIDE.md            # テンプレート利用ガイド
│   ├── base.md             # 全プロジェクト共通の基盤テンプレート
│   ├── web-app.md          # Web アプリ向け追加セクション
│   └── api-service.md      # API / バックエンド向け追加セクション
├── spec/                   # Spec テンプレート
│   ├── requirement-spec.md # 要求 Spec（Phase 1）
│   └── design-spec.md      # Design Spec（Phase 2）
└── adr/                    # ADR テンプレート
    └── template.md         # ADR 基本テンプレート
```

## 使い方

1. `claude-md/GUIDE.md` を読む
2. `claude-md/base.md` をプロジェクトルートに `CLAUDE.md` としてコピー
3. `[TODO: ...]` 箇所を埋める
4. プロジェクト種別に応じて `web-app.md` や `api-service.md` の内容を追記
5. `spec/` と `adr/` のテンプレートを `docs/` 配下にコピーして使用
