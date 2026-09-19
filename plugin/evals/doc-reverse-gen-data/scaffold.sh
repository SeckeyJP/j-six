#!/bin/bash
# 評価は空の作業ディレクトリで始まる。対象のコードをその場で生成する
# （外部のファイルに依存させず、どの環境でも同じ入力にするため）。
set -euo pipefail
mkdir -p app
cat > app/__init__.py <<'PY'
PY
cat > app/models.py <<'PY'
"""蔵書貸出のドメインモデル。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Book:
    """蔵書。isbn は重複不可（REQ-001）。"""

    isbn: str
    title: str
    author: str


@dataclass
class Member:
    """会員。"""

    member_id: str
    name: str


@dataclass
class Loan:
    """貸出。1冊の蔵書は同時に1件しか貸し出せない（REQ-002）。"""

    loan_id: str
    isbn: str
    member_id: str
    due_date: date
    returned_on: Optional[date] = None
PY
cat > app/service.py <<'PY'
"""貸出サービス。"""
from __future__ import annotations

from datetime import date, timedelta

from .models import Book, Loan, Member


class LibraryService:
    def __init__(self) -> None:
        self.books: dict[str, Book] = {}
        self.members: dict[str, Member] = {}
        self.loans: dict[str, Loan] = {}

    def add_book(self, book: Book) -> None:
        if book.isbn in self.books:
            raise ValueError("isbn が重複しています")
        self.books[book.isbn] = book

    def lend(self, loan_id: str, isbn: str, member_id: str, today: date) -> Loan:
        if any(l.isbn == isbn and l.returned_on is None for l in self.loans.values()):
            raise ValueError("貸出中です")
        loan = Loan(loan_id, isbn, member_id, today + timedelta(days=14))
        self.loans[loan_id] = loan
        return loan

    def give_back(self, loan_id: str, today: date) -> None:
        self.loans[loan_id].returned_on = today
PY
