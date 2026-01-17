-- Schema (same as created by db.create_tables)
PRAGMA foreign_keys = ON;

CREATE TABLE authors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE books (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  author_id INTEGER NOT NULL,
  qty INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY(author_id) REFERENCES authors(id) ON DELETE CASCADE
);

CREATE TABLE loans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  book_id INTEGER NOT NULL,
  borrower TEXT NOT NULL,
  loan_date DATE NOT NULL,
  return_date DATE,
  FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
);

-- Sample data
INSERT INTO authors (name) VALUES ('J. K. Rowling'), ('Frank Herbert'), ('Alan Beaulieu');

INSERT INTO books (title, author_id, qty) VALUES
('Harry Potter and the Philosopher''s Stone', 1, 3),
('Dune', 2, 2),
('Learning SQL', 3, 1);

INSERT INTO loans (book_id, borrower, loan_date) VALUES
(2, 'Sam', '2024-11-05'),
(1, 'Riley', '2025-02-10'),
(1, 'Taylor', '2025-06-01'),
(3, 'Jordan', '2025-07-20');