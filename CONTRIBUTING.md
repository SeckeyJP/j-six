# コントリビューションガイド

J-SIX プロジェクトへの貢献に感謝します。

## フィードバックの方法

### Issue

バグ報告、改善提案、質問は [GitHub Issues](https://github.com/SeckeyJP/j-six/issues) で受け付けています。

以下の観点でのフィードバックを特に歓迎します:

- 実プロジェクトでの適用経験・改善提案
- 設計書逆生成の品質に関する知見
- TDD × Claude Code の実践パターン
- 日本のSI業界特有の課題・制約への対応

### Pull Request

1. Fork してブランチを作成してください
2. 変更を加えてください
3. Pull Request を作成してください

## ドキュメント変更時のルール

### 品質基準

- 主張には出典を付ける（`docs/REFERENCES_AUDIT.md` の方針に従う）
- 著者推定の数値は「著者推定」と明記する
- プロセス名は **J-SIX** に統一（CC-Full は使わない）
- バージョン文字列をハードコードしない

### 更新チェックリスト

複数ファイルに影響する変更を行った場合は、以下の整合性を確認してください:

- [ ] `docs/J-SIX.md` — ヘッダの Version / Date、付録A・B、改訂履歴
- [ ] `README.md` — ドキュメント説明文、「今後の展開」テーブル
- [ ] `CHANGELOG.md` — 変更内容の追記
- [ ] `docs/REFERENCES_AUDIT.md` — データ修正があった場合は該当エントリ
- [ ] `plugin/.claude-plugin/plugin.json` — Plugin 変更時は version 更新

## Plugin への貢献

Plugin（`plugin/`）の変更については:

- Skills は `plugin/skills/<skill-name>/SKILL.md` 形式
- Agents は `plugin/agents/<agent-name>.md` 形式
- Hooks は `plugin/hooks/hooks.json` に追記
- 変更後は `plugin/README.md` の対応テーブルも更新

## ライセンス

貢献いただいた内容は [CC BY 4.0](LICENSE) の下で公開されます。
