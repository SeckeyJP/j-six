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
├── adr/                    # ADR テンプレート
│   └── template.md         # ADR 基本テンプレート
└── deliverables/           # 工程成果物テンプレート（IPA 27点）
    ├── README.md           # 索引・由来の内訳・作る順序
    ├── assembly/           # 顧客様式への束ね方（基本設計書／詳細設計書の組立例）
    ├── behavior/           # システム振舞い（4点）
    ├── screen/             # 画面（6点）
    ├── data/               # データモデル（4点）
    ├── external-if/        # 外部インタフェース（4点）
    ├── batch/              # バッチ（4点）
    └── report/             # 帳票（5点）
```

## 使い方

1. `claude-md/GUIDE.md` を読む
2. `claude-md/base.md` をプロジェクトルートに `CLAUDE.md` としてコピー
3. `[TODO: ...]` 箇所を埋める
4. プロジェクト種別に応じて `web-app.md` や `api-service.md` の内容を追記
5. `spec/` と `adr/` のテンプレートを `docs/` 配下にコピーして使用
6. 設計書の納品が必要な場合は `deliverables/` から該当領域をコピーして使用（Phase 6）

`deliverables/` の27点は**大半がコードから逆生成する**ため、Phase 1-2 で埋めるのは
人手更新の5点のみ。詳細は [`deliverables/README.md`](deliverables/README.md) を参照。

## 記入済み実例（テンプレ → 実例 → 該当 Skill）

各テンプレートを実プロジェクトで埋めた例を [`examples/approval-workflow/`](../examples/approval-workflow/)
（申請承認ワークフロー）に置いています。「空のテンプレ」と「埋まった実物」を見比べられます。

| テンプレート | 記入済み実例 | 関連 Skill |
|---|---|---|
| `claude-md/base.md` + `api-service.md` | [`examples/approval-workflow/CLAUDE.md`](../examples/approval-workflow/CLAUDE.md) | — |
| `spec/requirement-spec.md` | [`.../docs/requirement-spec.md`](../examples/approval-workflow/docs/requirement-spec.md) | `j-six:spec-create` |
| `spec/design-spec.md` | [`.../docs/design-spec.md`](../examples/approval-workflow/docs/design-spec.md) | `j-six:spec-create` |
| `adr/template.md` | [`.../docs/adr/0001-state-machine.md`](../examples/approval-workflow/docs/adr/0001-state-machine.md), [`0002`](../examples/approval-workflow/docs/adr/0002-audit-log.md) | `j-six:design-review` |
| （トレーサビリティ） | [`.../docs/traceability.md`](../examples/approval-workflow/docs/traceability.md) | `j-six:traceability` |
| `deliverables/`（27点） | [`examples/monthly-billing/docs/deliverables/`](../examples/monthly-billing/docs/deliverables/) | `j-six:doc-reverse-gen` |

工程成果物27点は、画面・帳票・バッチ・外部IF を持つ第2サンプル
[`examples/monthly-billing/`](../examples/monthly-billing/) で実例を用意している
（`approval-workflow` は API のみのため、画面6・帳票5・バッチ4 の実例を作れない）。

実測結果は [ケーススタディ #1](../docs/case-study-01.md) を参照。
