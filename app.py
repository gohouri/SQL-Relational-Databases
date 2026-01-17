"""Simple CLI for the Library Catalog example.

Commands:
  - init-db
  - seed
  - list-books
  - add-book
  - loan-book
  - return-loan
  - report-loans
  - stats

"""
from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

from db import Database

DB_DEFAULT = Path("./data/library.db")


def cmd_init(args: argparse.Namespace) -> None:
    db = Database(args.db)
    db.create_tables()
    db.close()
    print(f"initialized database at {db.path}")


def cmd_seed(args: argparse.Namespace) -> None:
    import seed

    seed.seed(path=args.db)


def cmd_list_books(args: argparse.Namespace) -> None:
    db = Database(args.db)
    books = db.get_books(title_like=args.filter)
    for b in books:
        print(f"{b.id:3}  {b.title:<40}  {b.author:<20}  qty={b.qty}")
    db.close()


def cmd_add_book(args: argparse.Namespace) -> None:
    db = Database(args.db)
    book_id = db.add_book(args.title, args.author, args.qty)
    print(f"added book id={book_id}")
    db.close()


def cmd_loan_book(args: argparse.Namespace) -> None:
    db = Database(args.db)
    loan_id = db.loan_book(args.book_id, args.borrower, loan_date=args.date)
    print(f"loan created id={loan_id}")
    db.close()


def cmd_return_loan(args: argparse.Namespace) -> None:
    db = Database(args.db)
    db.return_loan(args.loan_id, return_date=args.date)
    print(f"loan {args.loan_id} marked returned")
    db.close()


def cmd_report_loans(args: argparse.Namespace) -> None:
    db = Database(args.db)
    rows = db.loans_in_date_range(args.from_date, args.to_date)
    if not rows:
        print("no loans in range")
    for r in rows:
        print(f"{r['id']:3}  {r['title']:<40}  {r['borrower']:<15}  {r['loan_date']} -> {r['return_date']}")
    db.close()


def cmd_stats(args: argparse.Namespace) -> None:
    db = Database(args.db)
    counts = db.book_loan_counts()
    total, avg = db.loan_aggregates()
    print(f"total loans: {total}, avg loans/book: {avg:.2f}\n")
    print("Top books by times loaned:")
    for book_id, title, author, times in counts:
        print(f"{times:3}  {title:<40}  {author}")
    db.close()


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="app.py", description="Library Catalog (SQLite) CLI")
    p.add_argument("--db", default=DB_DEFAULT, type=Path, help="path to sqlite db")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("init-db")
    sub.add_parser("seed")

    l = sub.add_parser("list-books")
    l.add_argument("--filter", help="title substring to filter")

    a = sub.add_parser("add-book")
    a.add_argument("--title", required=True)
    a.add_argument("--author", required=True)
    a.add_argument("--qty", type=int, default=1)

    loan = sub.add_parser("loan-book")
    loan.add_argument("--book-id", type=int, required=True)
    loan.add_argument("--borrower", required=True)
    loan.add_argument("--date", type=lambda s: datetime.fromisoformat(s).date(), required=False)

    ret = sub.add_parser("return-loan")
    ret.add_argument("--loan-id", type=int, required=True)
    ret.add_argument("--date", type=lambda s: datetime.fromisoformat(s).date(), required=False)

    rep = sub.add_parser("report-loans")
    rep.add_argument("--from", dest="from_date", required=True)
    rep.add_argument("--to", dest="to_date", required=True)

    sub.add_parser("stats")
    return p


def main(argv: Optional[list[str]] = None) -> None:
    p = make_parser()
    args = p.parse_args(argv)
    if not args.cmd:
        p.print_help()
        return
    {
        "init-db": cmd_init,
        "seed": cmd_seed,
        "list-books": cmd_list_books,
        "add-book": cmd_add_book,
        "loan-book": cmd_loan_book,
        "return-loan": cmd_return_loan,
        "report-loans": cmd_report_loans,
        "stats": cmd_stats,
    }[args.cmd](args)


if __name__ == "__main__":
    main()