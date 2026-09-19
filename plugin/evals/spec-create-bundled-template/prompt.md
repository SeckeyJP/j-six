---
description: >-
  spec-create が Skill に同梱したテンプレートを読んで要求 Spec を作れるか。
  Plugin 実動検証 #1 の不具合（マニフェスト不正で Plugin が読み込まれない／
  テンプレートをリポジトリルートから読もうとして失敗／!`cat` が作業ディレクトリ外を
  読めずに起動直後に止まる）の再発を検知する。
tags: [regression, spec-create, field-test-01]
runs: 3
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Write, Edit, Glob, Grep, Skill]
expected_outcome: >-
  同梱テンプレートを Read で読み、docs/specs/requirement-spec-kintai.md に
  非機能要求グレードの6大項目とモデルシステムを含む要求 Spec を書く。
---

/j-six:spec-create

要求 Spec を新規に作成してください。ヘッドレス実行のため対話はできません。以下を合意済みの内容として扱い、
足りない項目は「未確定」と明記してください。出力先は `docs/specs/requirement-spec-kintai.md` とします。

- システム: 小規模事業者向けの勤怠打刻（出勤・退勤の打刻と月次の勤務時間集計）
- 背景: 紙のタイムカードを月末に手で集計しており、転記ミスと集計の手間が課題
- 対象外: 給与計算、シフト作成
- ユースケース: UC-001 出勤打刻、UC-002 退勤打刻、UC-003 月次集計の閲覧
- 業務ルール: REQ-001 退勤は出勤より後でなければ打刻できない / REQ-002 同じ日に出勤を二重に打刻できない / REQ-003 月次の勤務時間は分単位で集計する
- 非機能: 利用者は1事業所の従業員20名以内。停止しても影響は事業所内にとどまる。平日 7:00〜22:00 に使う。移行元システムは無い（紙）
