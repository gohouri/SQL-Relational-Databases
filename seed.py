"""Seed the example database with sample data (books, authors, loans)."""
from datetime import date
from pathlib import Path

from db import Database

SAMPLE_DB = Path("./data/library.db")


def seed(path: Path | str = SAMPLE_DB) -> None:
    db = Database(path)
    db.create_tables()

    # Authors + books (diverse titles; qty >= 2)
    hp = db.add_book("Harry Potter and the Philosopher's Stone", "J. K. Rowling", qty=3)
    dune = db.add_book("Dune", "Frank Herbert", qty=2)
    sql_book = db.add_book("Learning SQL", "Alan Beaulieu", qty=2)
    pragmatic = db.add_book("The Pragmatic Programmer", "Andrew Hunt", qty=2)
    clean = db.add_book("Clean Code", "Robert C. Martin", qty=2)
    deep = db.add_book("Deep Work", "Cal Newport", qty=2)
    algo = db.add_book("Introduction to Algorithms", "Cormen et al.", qty=2)
    hobbit = db.add_book("The Hobbit", "J. R. R. Tolkien", qty=2)

    # Loans with varying dates to demonstrate date-range filtering
    db.loan_book(dune, "Sam", loan_date=date(2024, 11, 5))
    db.loan_book(hp, "Riley", loan_date=date(2025, 2, 10))
    db.loan_book(hp, "Taylor", loan_date=date(2025, 6, 1))
    db.loan_book(sql_book, "Jordan", loan_date=date(2025, 7, 20))
    db.loan_book(pragmatic, "Alex", loan_date=date(2025, 3, 15))
    db.loan_book(clean, "Morgan", loan_date=date(2025, 8, 1))

    print(f"seeded sample data into {db.path}")
    db.close()


if __name__ == "__main__":
    seed()