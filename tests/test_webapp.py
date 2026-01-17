from pathlib import Path
from datetime import date

import pytest

from webapp import create_app
from db import Database


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "w.db"
    app = create_app(db_path)
    # create schema
    Database(db_path).create_tables()
    with app.test_client() as c:
        yield c


def test_books_and_loan_flow(client, tmp_path):
    # initially empty
    r = client.get('/api/books')
    assert r.status_code == 200
    assert r.json == []

    # add a book directly via Database
    db = Database(tmp_path / 'w.db')
    bid = db.add_book('WebBook', 'WebAuthor', qty=1)
    db.close()

    r = client.get('/api/books')
    assert any(b['title'] == 'WebBook' for b in r.json)

    # loan the book
    r = client.post('/api/loan', json={'book_id': bid, 'borrower': 'QA'})
    assert r.status_code == 201
    assert 'loan_id' in r.json

    # confirm qty decreased
    r = client.get('/api/books')
    wb = [b for b in r.json if b['id'] == bid][0]
    assert wb['qty'] == 0

    # return the loan
    loan_id = r = client.get('/api/stats').json['top_books'][0].get('times_loaned')

    # basic index page loads
    r = client.get('/')
    assert r.status_code == 200
    assert b'Library Catalog' in r.data