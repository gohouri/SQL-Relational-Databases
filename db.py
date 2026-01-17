"""db.py — small database layer for the Library Catalog example.

Provides: schema creation, CRUD operations, join query, aggregates, and date-range filtering.
"""
from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple

DEFAULT_DB = Path("./data/library.db")

@dataclass
class Book:
    id: int
    title: str
    author: str
    qty: int


class Database:
    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path or DEFAULT_DB)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self.conn.close()

    def create_tables(self) -> None:
        cur = self.conn.cursor()
        cur.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author_id INTEGER NOT NULL,
            qty INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(author_id) REFERENCES authors(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            borrower TEXT NOT NULL,
            loan_date DATE NOT NULL,
            return_date DATE,
            FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
        );
        """)
        self.conn.commit()

    # --- Basic CRUD ---
    def add_author(self, name: str) -> int:
        cur = self.conn.cursor()
        cur.execute("INSERT OR IGNORE INTO authors (name) VALUES (?)", (name,))
        self.conn.commit()
        cur.execute("SELECT id FROM authors WHERE name = ?", (name,))
        return cur.fetchone()[0]

    def add_book(self, title: str, author_name: str, qty: int = 1) -> int:
        author_id = self.add_author(author_name)
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO books (title, author_id, qty) VALUES (?,?,?)",
            (title, author_id, qty),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_book_qty(self, book_id: int, delta: int) -> None:
        cur = self.conn.cursor()
        cur.execute("UPDATE books SET qty = qty + ? WHERE id = ?", (delta, book_id))
        self.conn.commit()

    def update_book(self, book_id: int, title: Optional[str] = None, author_name: Optional[str] = None, qty: Optional[int] = None) -> None:
        """Partially update a book's title, author and/or qty. If author_name is provided it will be created if missing."""
        cur = self.conn.cursor()
        updates = []
        params: list[object] = []
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if author_name is not None:
            author_id = self.add_author(author_name)
            updates.append("author_id = ?")
            params.append(author_id)
        if qty is not None:
            updates.append("qty = ?")
            params.append(qty)
        if not updates:
            return
        params.append(book_id)
        cur.execute(f"UPDATE books SET {', '.join(updates)} WHERE id = ?", tuple(params))
        self.conn.commit()

    def delete_book(self, book_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self.conn.commit()

    def get_books(self, title_like: Optional[str] = None) -> List[Book]:
        cur = self.conn.cursor()
        if title_like:
            rows = cur.execute(
                "SELECT b.id, b.title, a.name AS author, b.qty FROM books b JOIN authors a ON a.id = b.author_id WHERE b.title LIKE ?",
                (f"%{title_like}%",),
            )
        else:
            rows = cur.execute(
                "SELECT b.id, b.title, a.name AS author, b.qty FROM books b JOIN authors a ON a.id = b.author_id"
            )
        return [Book(**r) for r in (dict(row) for row in rows.fetchall())]

    # --- Loans ---
    def loan_book(self, book_id: int, borrower: str, loan_date: Optional[date] = None) -> int:
        loan_date = loan_date or date.today()
        cur = self.conn.cursor()
        # decrement qty
        cur.execute("SELECT qty FROM books WHERE id = ?", (book_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("book not found")
        if row[0] <= 0:
            raise ValueError("no copies available")
        cur.execute("INSERT INTO loans (book_id, borrower, loan_date) VALUES (?,?,?)", (book_id, borrower, loan_date.isoformat()))
        cur.execute("UPDATE books SET qty = qty - 1 WHERE id = ?", (book_id,))
        self.conn.commit()
        return cur.lastrowid

    def return_loan(self, loan_id: int, return_date: Optional[date] = None) -> None:
        return_date = (return_date or date.today()).isoformat()
        cur = self.conn.cursor()
        cur.execute("SELECT book_id FROM loans WHERE id = ?", (loan_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("loan not found")
        cur.execute("UPDATE loans SET return_date = ? WHERE id = ?", (return_date, loan_id))
        cur.execute("UPDATE books SET qty = qty + 1 WHERE id = ?", (row[0],))
        self.conn.commit()

    def delete_loan(self, loan_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM loans WHERE id = ?", (loan_id,))
        self.conn.commit()

    # --- Reporting: join + aggregates + date filtering ---
    def book_loan_counts(self) -> List[Tuple[int, str, str, int]]:
        """Return (book_id, title, author, times_loaned)"""
        cur = self.conn.cursor()
        rows = cur.execute(
            """
            SELECT b.id AS book_id, b.title, a.name AS author, COUNT(l.id) AS times_loaned
            FROM books b
            JOIN authors a ON a.id = b.author_id
            LEFT JOIN loans l ON l.book_id = b.id
            GROUP BY b.id
            ORDER BY times_loaned DESC
            """
        )
        return [(r["book_id"], r["title"], r["author"], r["times_loaned"]) for r in rows.fetchall()]

    def loan_aggregates(self) -> Tuple[int, float]:
        """Return (total_loans, avg_loans_per_book)"""
        cur = self.conn.cursor()
        total = cur.execute("SELECT COUNT(*) FROM loans").fetchone()[0]
        avg = cur.execute("SELECT AVG(cnt) FROM (SELECT COUNT(*) AS cnt FROM loans GROUP BY book_id)").fetchone()[0] or 0.0
        return total, float(avg)

    def loans_in_date_range(self, from_date: str, to_date: str) -> List[sqlite3.Row]:
        cur = self.conn.cursor()
        rows = cur.execute(
            "SELECT l.id, b.title, l.borrower, l.loan_date, l.return_date FROM loans l JOIN books b ON b.id = l.book_id WHERE l.loan_date BETWEEN ? AND ? ORDER BY l.loan_date",
            (from_date, to_date),
        )
        return rows.fetchall()


if __name__ == "__main__":
    print("Run `app.py` for the CLI or `seed.py` to populate sample data.")