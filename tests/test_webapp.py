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

    # add a book via the API
    r = client.post('/api/books', json={'title': 'WebBook', 'author': 'WebAuthor', 'qty': 2})
    assert r.status_code == 201
    bid = r.json['book_id']

    r = client.get('/api/books')
    assert any(b['title'] == 'WebBook' for b in r.json)

    # loan the book
    r = client.post('/api/loan', json={'book_id': bid, 'borrower': 'QA'})
    assert r.status_code == 201
    loan_id = r.json['loan_id']

    # confirm qty decreased
    r = client.get('/api/books')
    wb = [b for b in r.json if b['id'] == bid][0]
    assert wb['qty'] == 1

    # PATCH book (update title + qty)
    r = client.patch(f'/api/books/{bid}', json={'title': 'WebBook 2', 'qty': 3, 'author': 'NewAuthor'})
    assert r.status_code == 200
    r = client.get('/api/books')
    wb = [b for b in r.json if b['id'] == bid][0]
    assert wb['title'] == 'WebBook 2' and wb['qty'] == 3 and wb['author'] == 'NewAuthor'

    # PATCH loan (change borrower)
    r = client.patch(f'/api/loans/{loan_id}', json={'borrower': 'QA2'})
    assert r.status_code == 200

    # DELETE loan
    r = client.delete(f'/api/loans/{loan_id}')
    assert r.status_code == 200

    # DELETE book (should remove book and any remaining loans)
    r = client.delete(f'/api/books/{bid}')
    assert r.status_code == 200
    r = client.get('/api/books')
    assert all(b['id'] != bid for b in r.json)

    # basic index page loads
    r = client.get('/')
    assert r.status_code == 200
    assert b'Library Catalog' in r.data