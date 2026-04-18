# J-SIX プロジェクト

## プロジェクト概要

J-SIX (Japanese SI Transformation) のプロセス定義・テンプレート・Plugin 管理リポジトリ。
著者: H.Sekita / GitHub: SeckeyJP
ライセンス: CC BY 4.0

## リポジトリ構成

- `docs/J-SIX_v1.0.md` — メインドキュメント（プロセス定義）
- `docs/discussions/` — 設計議論の記録（変更しない）
- `docs/REFERENCES_AUDIT.md` — 出典監査レポート
- `templates/` — CLAUDE.md / Spec / ADR テンプレート
- `plugin/` — Claude Code Plugin（Skills / Agents / Hooks）

## 品質ルール

- 主張には出典を付ける（REFERENCES_AUDIT.md 参照）
- 著者推定の数値は「著者推定」と明記する
- CC-Full は使わない。J-SIX に統一
- ドキュメント内のバージョン文字列をハードコードしない（「J-SIX の補足資料」のように書く）

## ドキュメント更新チェックリスト

バージョン更新・データ修正・機能追加を行った際は以下を確認すること:

- [ ] `docs/J-SIX_v1.0.md` — ヘッダの Version / Date、付録A（成果物一覧）、付録B（展開予定テーブル）、改訂履歴
- [ ] `README.md` — メインドキュメント説明文、「今後の展開」テーブル
- [ ] `CHANGELOG.md` — 変更内容を追記（リリース時ではなくコミット時に書く）
- [ ] `docs/REFERENCES_AUDIT.md` — 監査日、データ修正があった場合は該当エントリ
- [ ] `plugin/.claude-plugin/plugin.json` — version フィールド（Plugin 変更時）
- [ ] `plugin/README.md` — Hooks テーブル等（Plugin 変更時）
- [ ] 補足ドキュメント内の本文参照が古くなっていないか（walkthrough, legacy guide）
