# Plugin の評価ケース（`claude plugin eval`）

j-six Plugin を実際に Claude Code に読み込ませて Skill を動かし、結果を採点する評価ケース。
Plugin を変更したときの**受入試験**として使う（ROADMAP C13）。

スクリプトの単体テスト（`plugin/scripts/tests/`）は、部品が仕様どおりかしか確かめられない。
[Plugin 実動検証 #1](https://github.com/SeckeyJP/j-six/blob/main/docs/plugin-field-test-01.md) で
見つかった不具合8件の大半は、Plugin を実際に読み込ませないと見つからない種類だった
（マニフェスト不正で Plugin が読み込まれない、テンプレートの参照先、権限の制約など）。
本ディレクトリの評価ケースは、それらの再発を検知する。

## ケース

| ケース | 検知する不具合 | 採点 |
|---|---|---|
| [`spec-create-bundled-template`](spec-create-bundled-template/) | Plugin が読み込まれない／同梱テンプレートを読めない（参照先の誤り・`!` 展開の制約） | 同梱テンプレートの Read、Spec の出力、非機能要求グレードの6大項目、モデルシステム、REQ / PROP、移行性、合意していない REQ を足していないこと |
| [`doc-reverse-gen-data`](doc-reverse-gen-data/) | 同梱の工程成果物テンプレートを読めない | 同梱テンプレートの Read、テンプレートと同じファイル名での出力、コードの属性の反映、由来の表示 |

採点はすべて無料の決定論的な採点（ツール呼び出し・ファイルの有無・正規表現）で行い、
LLM による判定は使っていない。試行では、LLM 判定（既定の Haiku）が条件をすべて満たした
Spec を3票とも不合格にし、回帰テストとして安定しなかったため。

## 実行

```bash
claude plugin eval plugin \
  --ablation none --scaffold --trust-plugin --allow-tools Write Edit \
  --max-cost-usd 10 --no-publish
```

| オプション | 理由 |
|---|---|
| `--ablation none` | Plugin なしの比較は行わない。プロンプトが `/j-six:...` で始まるため、Plugin が無いと成立しない |
| `--scaffold` | `doc-reverse-gen-data` は準備スクリプト（`scaffold.sh`）で対象コードを生成する。スクリプトは本リポジトリで書いたもの |
| `--allow-tools Write Edit` | 成果物を書くため。評価の実行では明示的な許可が要る |
| `--max-cost-usd` | 費用の上限 |

**費用と時間の目安**（2026-09-19 の実測。モデルは既定）: 1回あたり spec-create $0.42〜0.46・85〜128秒、
doc-reverse-gen $0.73〜0.98・136〜184秒。既定の各3回（計6回）で合計 $3.79・約13分、6回とも満点。CI では実行しない
（API の認証情報と費用が要るため）。Plugin の Skill・Hook・同梱テンプレートを変更したとき、
およびリリース前に手元で実行する。

## ケースを書くときの注意

試行で踏んだものを残す。

- **`case.yaml` では `max_turns` / `timeout_seconds` / `allowed_tools` を `execution:` の下に書く。**
  最上位に書くと無視され、既定値（10ターン・300秒・ツール指定なし）で動く。ツール指定が無いと、
  作業ディレクトリの外（Plugin の同梱ファイル）の Read が拒否される。`prompt.md` の frontmatter では最上位でよい
- **プロンプトを `/j-six:...` で始めると、Skill はツール呼び出しを介さずに展開される。**
  `tool_used: Skill` では判定できないので、同梱ファイルの Read などで確かめる
- **準備スクリプトは `scaffold_script: <ファイル名>`（ケースのディレクトリからの相対パス）で指定する。**
  スクリプト本文を直接書くことはできない
- **LLM 判定の対象ファイルは `focus`、正規表現の対象ファイルは `target` で指定する**
- `tool_used` は呼び出し回数を数えるだけで、成功したかは見ない。権限で拒否された Read も1回に数える
- Bash を許可する評価は、Docker の認証情報のディレクトリにシンボリックリンクがある環境では実行できない
  （Bash のサンドボックスが除外できないため）
