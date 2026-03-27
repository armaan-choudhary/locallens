import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
from config import POSTGRES_DSN
import json

_pool = None

def get_pool():
    """Get or initialize the Postgres connection pool."""
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(1, 20, POSTGRES_DSN)
    return _pool

def init_postgres():
    """Initialize Postgres schema and perform necessary migrations."""
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        schema_sql = f.read()

    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='image_regions' AND column_name='image_path'")
            if not cur.fetchone():
                cur.execute("ALTER TABLE image_regions ADD COLUMN image_path TEXT")
            
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='chat_messages' AND column_name='support_scores'")
            if not cur.fetchone():
                cur.execute("ALTER TABLE chat_messages ADD COLUMN support_scores JSONB")
                cur.execute("ALTER TABLE chat_messages ADD COLUMN flagged_sentences JSONB")
                cur.execute("ALTER TABLE chat_messages ADD COLUMN verified BOOLEAN DEFAULT TRUE")
            
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='chat_messages' AND column_name='scoped_docs'")
            if not cur.fetchone():
                cur.execute("ALTER TABLE chat_messages ADD COLUMN scoped_docs JSONB")
                
        conn.commit()
    finally:
        pool.putconn(conn)

def insert_document(doc_id: str, filename: str, filepath: str, page_count: int):
    """Insert document metadata."""
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

def bulk_insert_text_chunks(chunks_data: list[tuple]):
    """Insert text chunks in bulk."""
    if not chunks_data:
        return
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            from psycopg2.extras import execute_values
            execute_values(
                cur,
                """INSERT INTO text_chunks 
                   (chunk_id, doc_id, page_number, chunk_index, char_start, char_end, text, source, milvus_id) 
                   VALUES %s ON CONFLICT DO NOTHING""",
                chunks_data
            )
        conn.commit()
    finally:
        pool.putconn(conn)

def bulk_insert_image_regions(regions_data: list[tuple]):
    """Insert image regions in bulk."""
    if not regions_data:
        return
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            from psycopg2.extras import execute_values
            execute_values(
                cur,
                """INSERT INTO image_regions 
                   (image_id, doc_id, page_number, image_index, bbox_x1, bbox_y1, bbox_x2, bbox_y2, milvus_id, nearby_chunk_id, image_path) 
                   VALUES %s ON CONFLICT DO NOTHING""",
                regions_data
            )
        conn.commit()
    finally:
        pool.putconn(conn)

def get_chunk_by_milvus_id(milvus_id: int) -> dict:
    """Retrieve text chunk metadata by Milvus ID."""
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
    """Retrieve image region metadata by Milvus ID."""
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
    """Retrieve all text chunks for a specific document and page."""
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
    """Retrieve metadata for all ingested documents."""
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
    """Retrieve all text chunks from all documents."""
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
    """Delete all database records associated with a document ID."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM text_chunks WHERE doc_id = %s", (doc_id,))
            cur.execute("DELETE FROM image_regions WHERE doc_id = %s", (doc_id,))
            cur.execute("DELETE FROM documents WHERE doc_id = %s", (doc_id,))
        conn.commit()
    finally:
        pool.putconn(conn)

def create_session(session_id: str, title: str):
    """Create a new chat session."""
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
    """Retrieve all chat sessions."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM chat_sessions ORDER BY updated_at DESC")
            return cur.fetchall()
    finally:
        pool.putconn(conn)

def delete_session(session_id: str):
    """Delete a chat session."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chat_sessions WHERE session_id = %s", (session_id,))
        conn.commit()
    finally:
        pool.putconn(conn)

def add_message(message_id: str, session_id: str, role: str, content: str, citations: list = None, support_scores: list = None, flagged_sentences: list = None, verified: bool = True, scoped_docs: list = None):
    """Add a message to a chat session."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO chat_messages (message_id, session_id, role, content, citations, support_scores, flagged_sentences, verified, scoped_docs)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (message_id, session_id, role, content, 
                 json.dumps(citations) if citations else None,
                 json.dumps(support_scores) if support_scores else None,
                 json.dumps(flagged_sentences) if flagged_sentences else None,
                 verified,
                 json.dumps(scoped_docs) if scoped_docs else None)
            )
            cur.execute(
                "UPDATE chat_sessions SET updated_at = NOW() WHERE session_id = %s",
                (session_id,)
            )
        conn.commit()
    finally:
        pool.putconn(conn)

def get_messages_for_session(session_id: str) -> list:
    """Retrieve all messages for a specific chat session."""
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
                if r["support_scores"]:
                    r["support_scores"] = json.loads(r["support_scores"]) if isinstance(r["support_scores"], str) else r["support_scores"]
                if r["flagged_sentences"]:
                    r["flagged_sentences"] = json.loads(r["flagged_sentences"]) if isinstance(r["flagged_sentences"], str) else r["flagged_sentences"]
                if r["scoped_docs"]:
                    r["scoped_docs"] = json.loads(r["scoped_docs"]) if isinstance(r["scoped_docs"], str) else r["scoped_docs"]
            return rows
    finally:
        pool.putconn(conn)

def add_doc_to_session(session_id: str, doc_id: str):
    """Associate a document with a chat session."""
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
    """Disassociate a document from a chat session."""
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
    """Retrieve all document IDs associated with a chat session."""
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
