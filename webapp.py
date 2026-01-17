"""webapp.py — small Flask UI + JSON API for the Library Catalog.

Provides:
- GET  /api/books       -> list books (JSON)
- POST /api/loan        -> create a loan (JSON body: book_id, borrower)
- POST /api/return      -> return a loan (JSON body: loan_id)
- GET  /api/stats       -> aggregates
- GET  /                -> simple HTML UI

The app is created with `create_app(db_path)` so tests can provide a temporary DB.
"""
from __future__ import annotations
from flask import Flask, jsonify, request, render_template
from pathlib import Path
from typing import Optional

from db import Database


def create_app(db_path: Optional[Path] = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["DB_PATH"] = db_path or Path("./data/library.db")

    def get_db():
        return Database(app.config["DB_PATH"])

    @app.route("/api/books", methods=["GET"])
    def api_books():
        db = get_db()
        books = db.get_books()
        db.close()
        return jsonify([b.__dict__ for b in books])

    @app.route("/api/books", methods=["POST"])
    def api_create_book():
        payload = request.get_json(force=True)
        if not payload or "title" not in payload or "author" not in payload:
            return jsonify({"error": "title and author required"}), 400
        try:
            qty = int(payload.get("qty", 1))
        except Exception:
            return jsonify({"error": "qty must be an integer"}), 400
        if qty < 1:
            return jsonify({"error": "qty must be >= 1"}), 400
        db = get_db()
        try:
            book_id = db.add_book(payload["title"], payload["author"], qty=qty)
        except Exception as exc:
            db.close()
            return jsonify({"error": str(exc)}), 400
        db.close()
        return jsonify({"book_id": book_id}), 201

    @app.route("/api/loan", methods=["POST"])
    def api_loan():
        payload = request.get_json(force=True)
        if not payload or "book_id" not in payload or "borrower" not in payload:
            return jsonify({"error": "book_id and borrower required"}), 400
        db = get_db()
        try:
            loan_id = db.loan_book(int(payload["book_id"]), payload["borrower"])
        except ValueError as exc:
            db.close()
            return jsonify({"error": str(exc)}), 400
        db.close()
        return jsonify({"loan_id": loan_id}), 201

    @app.route("/api/return", methods=["POST"])
    def api_return():
        payload = request.get_json(force=True)
        if not payload or "loan_id" not in payload:
            return jsonify({"error": "loan_id required"}), 400
        db = get_db()
        try:
            db.return_loan(int(payload["loan_id"]))
        except ValueError as exc:
            db.close()
            return jsonify({"error": str(exc)}), 400
        db.close()
        return jsonify({"ok": True})

    @app.route("/api/books/<int:book_id>", methods=["PATCH"])
    def api_patch_book(book_id: int):
        payload = request.get_json(force=True)
        if not payload:
            return jsonify({"error": "no payload"}), 400
        db = get_db()
        try:
            db.update_book(book_id, title=payload.get("title"), author_name=payload.get("author"), qty=payload.get("qty"))
        except Exception as exc:
            db.close()
            return jsonify({"error": str(exc)}), 400
        db.close()
        return jsonify({"ok": True})

    @app.route("/api/books/<int:book_id>", methods=["DELETE"])
    def api_delete_book(book_id: int):
        db = get_db()
        db.delete_book(book_id)
        db.close()
        return jsonify({"ok": True})

    @app.route("/api/loans/<int:loan_id>", methods=["PATCH"])
    def api_patch_loan(loan_id: int):
        payload = request.get_json(force=True)
        if not payload:
            return jsonify({"error": "no payload"}), 400
        db = get_db()
        try:
            if "return_date" in payload:
                db.return_loan(loan_id, return_date=payload.get("return_date"))
            if "borrower" in payload:
                db.conn.execute("UPDATE loans SET borrower = ? WHERE id = ?", (payload.get("borrower"), loan_id))
                db.conn.commit()
        except ValueError as exc:
            db.close()
            return jsonify({"error": str(exc)}), 400
        db.close()
        return jsonify({"ok": True})

    @app.route("/api/loans/<int:loan_id>", methods=["DELETE"])
    def api_delete_loan(loan_id: int):
        db = get_db()
        db.delete_loan(loan_id)
        db.close()
        return jsonify({"ok": True})

    @app.route("/api/stats", methods=["GET"])
    def api_stats():
        db = get_db()
        total, avg = db.loan_aggregates()
        counts = db.book_loan_counts()
        db.close()
        return jsonify({"total_loans": total, "avg_loans_per_book": avg, "top_books": [dict(book_id=b[0], title=b[1], author=b[2], times_loaned=b[3]) for b in counts]})

    @app.route("/", methods=["GET"])
    def index():
        db = get_db()
        books = db.get_books()
        db.close()
        return render_template("index.html", books=books)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=5000, debug=True)
