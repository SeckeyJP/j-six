---
type: regex
target: {source: file, path: docs/specs/requirement-spec-kintai.md}
pattern: "REQ-0(0[4-9]|[1-9][0-9])"
match: not_contains
---

与えていない業務ルール（REQ-004 以降）を、合意済みであるかのように追加していないこと。
未確定の事項は「未確定」として書くべきである。
