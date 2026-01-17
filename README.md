# Overview

**Goal:** build a small, robust tool that demonstrates practical software engineering with a SQL relational database — focusing on reliable CRUD, reporting, and simple UI/automation to reinforce learning about schema design and application–DB integration.

This repository contains a lightweight **Library Catalog** implemented in Python that persists data in a SQLite relational database. The program exposes a CLI (`app.py`), a tiny JSON API + browser UI (`webapp.py`), and a reusable `db.py` module that constructs and executes SQL. Use the software to add books/authors, create and return loans, and run reports (joins, aggregates, date filters).

Purpose: practice designing normalized tables, writing safe parameterized SQL from application code, and building repeatable developer workflows (seed data, tests, and a small UI) to validate behaviors.

[Software Demo Video] https://www.loom.com/share/8306dad399c8485e958fe799f8b732e6

---

# Relational Database

Database engine: **SQLite** (file-based, included with Python) — stored at `data/library.db` by default.

Schema (key tables):
- `authors` — (id PK, name) — unique authors
- `books` — (id PK, title, author_id FK -> authors.id, qty) — inventory per title
- `loans` — (id PK, book_id FK -> books.id, borrower, loan_date, return_date) — transactional history

Relationships and constraints:
- `books.author_id` is a foreign key referencing `authors.id` (ON DELETE CASCADE).
- `loans.book_id` references `books.id`.
- Dates are stored as ISO strings (YYYY-MM-DD) for easy filtering.

Example queries demonstrated in code:
- Join (books → authors):
  `SELECT b.title, a.name FROM books b JOIN authors a ON a.id = b.author_id`
- Aggregate (loan counts):
  `SELECT b.id, COUNT(l.id) FROM books b LEFT JOIN loans l ON l.book_id=b.id GROUP BY b.id`
- Date-range filter:
  `SELECT * FROM loans WHERE loan_date BETWEEN '2025-01-01' AND '2025-12-31'`

---

# Development Environment

- OS: Windows (tested) 🪟
- Language: Python 3.13 (project uses standard `sqlite3`) 🐍
- Primary libraries: `Flask` (web UI), `pytest` (tests)
- Project layout (important files):
  - `db.py` — database access layer (schema + CRUD + reports)
  - `app.py` — command-line interface (examples + demos)
  - `webapp.py` — small Flask JSON API + HTML UI
  - `sample_data/seed.sql` and `seed.py` — reproducible seed data
  - `tests/` — automated tests (unit + integration)

Getting started (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
python seed.py          # create ./data/library.db with example rows
python app.py list-books # CLI
python webapp.py        # open http://127.0.0.1:5000
# CLI: update/delete examples
python app.py update-book --book-id 1 --title "New Title" --qty 4
python app.py delete-book --book-id 2          # interactive confirmation
python app.py delete-book --book-id 2 --yes     # skip prompt
pytest -q
```

Notes for developers:
- Use parameterized queries (see `db.py`) to avoid injection and to simplify testing.
- Tests create temporary databases (no global state).

---

# Useful Websites

- [SQLite Documentation](https://sqlite.org/docs.html)
- [Python sqlite3 — stdlib docs](https://docs.python.org/3/library/sqlite3.html)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQL Tutorial (joins, aggregates)](https://sqlbolt.com/)
- [BYU CSE310 SQL README template](https://byui-cse.github.io/cse310-ww-course/modules/sql_database/README.md)

---

# Future Work

- Implement atomic loan operation (single UPDATE that decrements `qty` only when > 0) and add concurrency tests. ✅ high priority
- Add user-friendly return functionality in the browser UI and allow returning from the loans list. 
- Add authentication/authorization for administrative actions (add/delete books). 
- Add CI (GitHub Actions) to run tests and a lightweight smoke test for the web UI. 
- Add export/import (CSV) and an endpoint for bulk seeding.

---

If you want a condensed submission package (README + SQL seed) or a GitHub Actions workflow added, say which and I'll prepare it.

## Adding data

You can add data three ways:

- CLI: `python app.py add-book --title "My New Book" --author "An Author" --qty 2`
- API (JSON):
  `curl -X POST -H "Content-Type: application/json" -d '{"title":"New Book","author":"An Author","qty":2}' http://127.0.0.1:5000/api/books`
- Browser UI: open the web UI at `http://127.0.0.1:5000` and use the **Add a book** form on the right.

Note: the UI **Edit** action prefills current values and allows editing `title`, `author`, and `quantity` (with validation); you can change one or more fields without retyping the others.

All three paths validate `qty` (must be >= 1) and create the author automatically if it does not exist.