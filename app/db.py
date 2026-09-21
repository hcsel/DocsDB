# app/db.py
import sqlite3
from contextlib import contextmanager
from typing import Optional, Iterable
from app.config import DB_PATH
from app.models import Document


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id              INTEGER PRIMARY KEY,
    sheet           TEXT NOT NULL DEFAULT '',
    category        TEXT DEFAULT '',
    doc_type        TEXT DEFAULT '',
    doc_date        TEXT,
    doc_number      TEXT DEFAULT '',
    title           TEXT NOT NULL,
    changes         TEXT DEFAULT '',
    notes           TEXT DEFAULT '',
    file_path       TEXT,
    file_name       TEXT,
    raw_link        TEXT DEFAULT '',
    link_kind       TEXT DEFAULT 'empty',
    needs_review    INTEGER DEFAULT 0,
    review_reason   TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_doc_date ON documents(doc_date);
CREATE INDEX IF NOT EXISTS idx_documents_sheet    ON documents(sheet);

CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    title, changes, notes,
    content='documents', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
    INSERT INTO documents_fts(rowid, title, changes, notes)
    VALUES (new.id, new.title, new.changes, new.notes);
END;

CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, title, changes, notes)
    VALUES ('delete', old.id, old.title, old.changes, old.notes);
END;

CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
    INSERT INTO documents_fts(documents_fts, rowid, title, changes, notes)
    VALUES ('delete', old.id, old.title, old.changes, old.notes);
    INSERT INTO documents_fts(rowid, title, changes, notes)
    VALUES (new.id, new.title, new.changes, new.notes);
END;
"""


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with connect() as conn:
        conn.executescript(SCHEMA)


def row_to_document(r: sqlite3.Row) -> Document:
    return Document(
        id=r["id"],
        sheet=r["sheet"] or "",
        category=r["category"] or "",
        doc_type=r["doc_type"] or "",
        doc_date=r["doc_date"],
        doc_number=r["doc_number"] or "",
        title=r["title"] or "",
        changes=r["changes"] or "",
        notes=r["notes"] or "",
        file_path=r["file_path"],
        file_name=r["file_name"],
        raw_link=r["raw_link"] or "",
        link_kind=r["link_kind"] or "empty",
        needs_review=bool(r["needs_review"]),
        review_reason=r["review_reason"] or "",
    )


# ---------- чтение ----------

def search(
    query: str = "",
    category: str = "",
    doc_type: str = "",
    sheet: str = "",
    limit: int = 500,
) -> list[Document]:
    """Гибкий поиск. Пустые параметры игнорируются."""
    where = []
    params: list = []

    if query:
        # через FTS5
        where.append("d.id IN (SELECT rowid FROM documents_fts WHERE documents_fts MATCH ?)")
        params.append(query + "*")  # префиксный поиск
    if category:
        where.append("d.category = ?")
        params.append(category)
    if doc_type:
        where.append("d.doc_type = ?")
        params.append(doc_type)
    if sheet:
        where.append("d.sheet = ?")
        params.append(sheet)

    sql = "SELECT d.* FROM documents d"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY COALESCE(d.doc_date, '9999') DESC, d.id DESC LIMIT ?"
    params.append(limit)

    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [row_to_document(r) for r in rows]


def get(doc_id: int) -> Optional[Document]:
    with connect() as conn:
        r = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
    return row_to_document(r) if r else None


def distinct_values(column: str) -> list[str]:
    if column not in {"category", "doc_type", "sheet"}:
        raise ValueError("Недопустимая колонка")
    with connect() as conn:
        rows = conn.execute(
            f"SELECT DISTINCT {column} FROM documents "
            f"WHERE {column} IS NOT NULL AND {column} != '' "
            f"ORDER BY {column}"
        ).fetchall()
    return [r[0] for r in rows]


def counts() -> dict:
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        review = conn.execute("SELECT COUNT(*) FROM documents WHERE needs_review=1").fetchone()[0]
        with_file = conn.execute(
            "SELECT COUNT(*) FROM documents WHERE file_path IS NOT NULL AND file_path != ''"
        ).fetchone()[0]
    return {"total": total, "needs_review": review, "with_file": with_file}


# ---------- запись ----------

def insert(doc: Document) -> int:
    with connect() as conn:
        cur = conn.execute("""
            INSERT INTO documents
            (sheet, category, doc_type, doc_date, doc_number, title,
             changes, notes, file_path, file_name, raw_link, link_kind,
             needs_review, review_reason)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            doc.sheet, doc.category, doc.doc_type, doc.doc_date,
            doc.doc_number, doc.title, doc.changes, doc.notes,
            doc.file_path, doc.file_name, doc.raw_link, doc.link_kind,
            int(doc.needs_review), doc.review_reason,
        ))
        return cur.lastrowid


def update(doc: Document):
    with connect() as conn:
        conn.execute("""
            UPDATE documents SET
              sheet=?, category=?, doc_type=?, doc_date=?, doc_number=?,
              title=?, changes=?, notes=?, file_path=?, file_name=?,
              raw_link=?, link_kind=?, needs_review=?, review_reason=?
            WHERE id=?
        """, (
            doc.sheet, doc.category, doc.doc_type, doc.doc_date,
            doc.doc_number, doc.title, doc.changes, doc.notes,
            doc.file_path, doc.file_name, doc.raw_link, doc.link_kind,
            int(doc.needs_review), doc.review_reason, doc.id,
        ))


def delete(doc_id: int):
    with connect() as conn:
        conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))


def insert_many(docs: Iterable[Document]):
    for d in docs:
        insert(d)