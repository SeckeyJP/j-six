# ローカル実験

企業PJ・本番Hubに流用しない合成検証用。結果と未検証範囲は[報告](../../docs/local-validation.md)。期待値は[oracle.json](oracle.json)、実AIの予定条件は[protocol.md](protocol.md)。後者のモデル呼出しは今回実施していない。

## 判定・Plugin

Pythonとcryptography（確認版50.0.1）を用いる。下記はリポジトリルートから実行する例。`-O`でassertを無効にしない。

```sh
python tools/experiments/validate_local.py --output /tmp/jsix-synthetic-results.json
python tools/experiments/validate_plugin.py
python -m pytest plugin/scripts/tests -q
```

検査・承認はその都度生成する試験鍵で署名した架空記録。公開鍵・秘密鍵は保存せず、外部へ送信しない。36ケースはCの期待値を実装前に固定したもの。CASはインメモリ、実行器は作用数カウンタであり、実Git・コンテナ・外部サービスの原子性を検証するコードではない。L/C/Hの比較は規則集合の差の確認に限定する。

## 文書生成

Pythonのpython-docx（確認版1.2.0）とNodeのartifact-tool（確認版2.8.59）を使用する。依存の場所は環境に合わせて指定する。Codex環境ではdocuments/spreadsheetsスキルのバンドルを使用した。追加インストールは行っていない。

```sh
python tools/experiments/build_document.py --output /tmp/jsix-export
node tools/experiments/build_workbook.mjs /absolute/path/to/artifact-tool-entry.mjs /tmp/jsix-export
```

Word生成時にentity.jsonを同時生成する。Excelはその同じ値を入力とする。スクリプトはdataテンプレートの列構成に合わせた限定的な変換であり、任意Markdownのコンバータではない。元コードを変更すると出力内SHAも変わるため、両形式を再生成する。

DOCXはdocumentsスキルのrender_docx.pyでLibreOffice→PNGへ変換し全ページを目視する。今回のmacOSバンドルは日本語フォントの解決に局所fontconfigを要した。既存フォントのディレクトリと書込み可能な専用キャッシュを指定し、FONTCONFIG_FILEをレンダープロセスにだけ渡した。マシン共通設定は変更していない。設定例（パスは実環境に合わせる）:

```xml
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
  <dir>/System/Library/Fonts</dir>
  <dir>/Library/Fonts</dir>
  <cachedir>/tmp/jsix-font-cache</cachedir>
</fontconfig>
```

XLSX生成スクリプトは全表セルとCOUNTの入力追従を検査し、Entityシートの画像を保存する。別途、保存されたZIP/XMLからセル値・COUNT式・キャッシュ値3・エラーセルなしを照合した。実Officeアプリの動作は確認していない。
