"""Seed the example database with sample data (books, authors, loans)."""
from datetime import date
from pathlib import Path

from db import Database

SAMPLE_DB = Path("./data/library.db")


def seed(path: Path | str = SAMPLE_DB) -> None:
    db = Database(path)
    db.create_tables()

    # Authors + books
    hp = db.add_book("Harry Potter and the Philosopher's Stone", "J. K. Rowling", qty=3)
    dune = db.add_book("Dune", "Frank Herbert", qty=2)
    sql = db.add_book("Learning SQL", "Alan Beaulieu", qty=1)

    # Loans with varying dates to demonstrate date-range filtering
    db.loan_book(dune, "Sam", loan_date=date(2024, 11, 5))
    db.loan_book(hp, "Riley", loan_date=date(2025, 2, 10))
    db.loan_book(hp, "Taylor", loan_date=date(2025, 6, 1))
    db.loan_book(sql, "Jordan", loan_date=date(2025, 7, 20))

    print(f"seeded sample data into {db.path}")
    db.close()


if __name__ == "__main__":
    seed()