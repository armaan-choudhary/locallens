CREATE TABLE IF NOT EXISTS documents (
    doc_id      TEXT PRIMARY KEY,
    filename    TEXT NOT NULL,
    filepath    TEXT NOT NULL,
    page_count  INTEGER,
    ingested_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS text_chunks (
    chunk_id    TEXT PRIMARY KEY,
    doc_id      TEXT REFERENCES documents(doc_id) ON DELETE CASCADE,
    page_number INTEGER,
    chunk_index INTEGER,
    char_start  INTEGER,
    char_end    INTEGER,
    text        TEXT,
    source      TEXT,           -- 'pypdf2' or 'tesseract'
    milvus_id   BIGINT          -- maps to Milvus vector ID
);

CREATE TABLE IF NOT EXISTS image_regions (
    image_id    TEXT PRIMARY KEY,
    doc_id      TEXT REFERENCES documents(doc_id) ON DELETE CASCADE,
    page_number INTEGER,
    image_index INTEGER,
    bbox_x1     INTEGER,
    bbox_y1     INTEGER,
    bbox_x2     INTEGER,
    bbox_y2     INTEGER,
    milvus_id   BIGINT,         -- maps to Milvus vector ID,
    nearby_chunk_id TEXT REFERENCES text_chunks(chunk_id) ON DELETE SET NULL,
    image_path  TEXT            -- relative path to stored image file
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id  TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id  TEXT PRIMARY KEY,
    session_id  TEXT REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role        TEXT NOT NULL, -- 'user' or 'assistant'
    content     TEXT NOT NULL,
    citations   JSONB,         -- store the list of citations as JSON
    support_scores JSONB,      -- store support scores per sentence
    flagged_sentences JSONB,   -- store which sentences were flagged
    verified    BOOLEAN DEFAULT TRUE,
    scoped_docs JSONB,         -- store the list of documents active at the time
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS session_documents (
    session_id  TEXT REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    doc_id      TEXT REFERENCES documents(doc_id) ON DELETE CASCADE,
    added_at    TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (session_id, doc_id)
);
