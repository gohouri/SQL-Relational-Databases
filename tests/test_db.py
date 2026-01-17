import tempfile
from datetime import date

import pytest

from db import Database


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


def test_create_and_basic_crud(db_path):
    db = Database(db_path)
    db.create_tables()
    b1 = db.add_book("Test Book", "Author A", qty=2)
    books = db.get_books()
    assert any(b.title == "Test Book" for b in books)

    # loan decreases qty
    loan_id = db.loan_book(b1, "Pat", loan_date=date(2025, 1, 2))
    books = db.get_books()
    assert [b for b in books if b.id == b1][0].qty == 1

    # return increases qty
    db.return_loan(loan_id, return_date=date(2025, 1, 5))
    assert [b for b in db.get_books() if b.id == b1][0].qty == 2
    db.close()


def test_join_and_aggregates(db_path):
    db = Database(db_path)
    db.create_tables()
    b1 = db.add_book("A", "X", qty=2)
    b2 = db.add_book("B", "Y", qty=1)
    db.loan_book(b1, "u1", loan_date=date(2025, 3, 1))
    db.loan_book(b1, "u2", loan_date=date(2025, 3, 2))
    db.loan_book(b2, "u3", loan_date=date(2025, 3, 3))

    counts = dict((bid, times) for bid, _title, _author, times in db.book_loan_counts())
    assert counts[b1] == 2
    total, avg = db.loan_aggregates()
    assert total == 3
    assert avg >= 1.0
    db.close()


def test_date_range_filter(db_path):
    db = Database(db_path)
    db.create_tables()
    b = db.add_book("DR", "Z", qty=2)
    db.loan_book(b, "Alpha", loan_date=date(2024, 12, 31))
    db.loan_book(b, "Beta", loan_date=date(2025, 6, 1))

    rows = db.loans_in_date_range("2025-01-01", "2025-12-31")
    assert all(date.fromisoformat(r['loan_date']).year == 2025 for r in rows)
    db.close()