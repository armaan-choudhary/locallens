import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
from config import POSTGRES_DSN

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(1, 20, POSTGRES_DSN)
    return _pool

def init_postgres():
    """Run schema.sql if tables don't exist"""
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        schema_sql = f.read()

    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
    finally:
        pool.putconn(conn)

def insert_document(doc_id: str, filename: str, filepath: str, page_count: int):
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO documents (doc_id, filename, filepath, page_count) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (doc_id, filename, filepath, page_count)
            )
        conn.commit()
    finally:
        pool.putconn(conn)

def insert_text_chunk(chunk_id: str, doc_id: str, page: int, index: int, char_start: int, char_end: int, text: str, source: str, milvus_id: int):
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO text_chunks 
                   (chunk_id, doc_id, page_number, chunk_index, char_start, char_end, text, source, milvus_id) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                (chunk_id, doc_id, page, index, char_start, char_end, text, source, milvus_id)
            )
        conn.commit()
    finally:
        pool.putconn(conn)

def insert_image_region(image_id: str, doc_id: str, page: int, index: int, bbox: list, milvus_id: int, nearby_chunk_id: str):
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO image_regions 
                   (image_id, doc_id, page_number, image_index, bbox_x1, bbox_y1, bbox_x2, bbox_y2, milvus_id, nearby_chunk_id) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                (image_id, doc_id, page, index, bbox[0], bbox[1], bbox[2], bbox[3], milvus_id, nearby_chunk_id)
            )
        conn.commit()
    finally:
        pool.putconn(conn)

def get_chunk_by_milvus_id(milvus_id: int) -> dict:
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT c.*, d.filename 
                FROM text_chunks c 
                JOIN documents d ON c.doc_id = d.doc_id 
                WHERE milvus_id = %s
            """, (milvus_id,))
            return cur.fetchone()
    finally:
        pool.putconn(conn)

def get_image_by_milvus_id(milvus_id: int) -> dict:
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT i.*, d.filename 
                FROM image_regions i 
                JOIN documents d ON i.doc_id = d.doc_id 
                WHERE milvus_id = %s
            """, (milvus_id,))
            return cur.fetchone()
    finally:
        pool.putconn(conn)

def get_chunks_by_doc_and_page(doc_id: str, page: int) -> list:
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM text_chunks 
                WHERE doc_id = %s AND page_number = %s
                ORDER BY char_start ASC
            """, (doc_id, page))
            return cur.fetchall()
    finally:
        pool.putconn(conn)
        
def get_all_documents() -> list:
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT d.*, 
                       (SELECT count(*) FROM text_chunks WHERE doc_id = d.doc_id) as chunk_count,
                       (SELECT count(*) FROM image_regions WHERE doc_id = d.doc_id) as image_count
                FROM documents d
                ORDER BY d.ingested_at DESC
            """)
            return cur.fetchall()
    finally:
        pool.putconn(conn)

def get_all_chunks() -> list:
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT c.*, d.filename FROM text_chunks c
                JOIN documents d ON c.doc_id = d.doc_id
            """)
            return cur.fetchall()
    finally:
        pool.putconn(conn)


def delete_document_data(doc_id: str):
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            # Foreign keys should handle cascading if schema is set up with ON DELETE CASCADE,
            # otherwise we do it manually.
            cur.execute("DELETE FROM text_chunks WHERE doc_id = %s", (doc_id,))
            cur.execute("DELETE FROM image_regions WHERE doc_id = %s", (doc_id,))
            cur.execute("DELETE FROM documents WHERE doc_id = %s", (doc_id,))
        conn.commit()
    finally:
        pool.putconn(conn)

# ── Chat Support ─────────────────────────────────────────────────────────────

def create_session(session_id: str, title: str):
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chat_sessions (session_id, title) VALUES (%s, %s)",
                (session_id, title)
            )
        conn.commit()
    finally:
        pool.putconn(conn)

def get_all_sessions() -> list:
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM chat_sessions ORDER BY updated_at DESC")
            return cur.fetchall()
    finally:
        pool.putconn(conn)

def delete_session(session_id: str):
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chat_sessions WHERE session_id = %s", (session_id,))
        conn.commit()
    finally:
        pool.putconn(conn)

def add_message(message_id: str, session_id: str, role: str, content: str, citations: list = None):
    import json
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO chat_messages (message_id, session_id, role, content, citations)
                   VALUES (%s, %s, %s, %s, %s)""",
                (message_id, session_id, role, content, json.dumps(citations) if citations else None)
            )
            # Update session timestamp
            cur.execute(
                "UPDATE chat_sessions SET updated_at = NOW() WHERE session_id = %s",
                (session_id,)
            )
        conn.commit()
    finally:
        pool.putconn(conn)

def get_messages_for_session(session_id: str) -> list:
    import json
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM chat_messages WHERE session_id = %s ORDER BY created_at ASC",
                (session_id,)
            )
            rows = cur.fetchall()
            for r in rows:
                if r["citations"]:
                    r["citations"] = json.loads(r["citations"]) if isinstance(r["citations"], str) else r["citations"]
            return rows
    finally:
        pool.putconn(conn)

# ── Session Document Management ───────────────────────────────────────────────

def add_doc_to_session(session_id: str, doc_id: str):
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO session_documents (session_id, doc_id)
                   VALUES (%s, %s) ON CONFLICT DO NOTHING""",
                (session_id, doc_id)
            )
        conn.commit()
    finally:
        pool.putconn(conn)

def remove_doc_from_session(session_id: str, doc_id: str):
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM session_documents WHERE session_id = %s AND doc_id = %s",
                (session_id, doc_id)
            )
        conn.commit()
    finally:
        pool.putconn(conn)

def get_docs_for_session(session_id: str) -> list[str]:
    """Returns a list of doc_ids associated with a session."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT doc_id FROM session_documents WHERE session_id = %s",
                (session_id,)
            )
            return [row[0] for row in cur.fetchall()]
    finally:
        pool.putconn(conn)
