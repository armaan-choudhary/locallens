CREATE TABLE IF NOT EXISTS documents (
    doc_id      TEXT PRIMARY KEY,
    filename    TEXT NOT NULL,
    filepath    TEXT NOT NULL,
    page_count  INTEGER,
    ingested_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS text_chunks (
    chunk_id    TEXT PRIMARY KEY,
    doc_id      TEXT REFERENCES documents(doc_id),
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
    doc_id      TEXT REFERENCES documents(doc_id),
    page_number INTEGER,
    image_index INTEGER,
    bbox_x1     INTEGER,
    bbox_y1     INTEGER,
    bbox_x2     INTEGER,
    bbox_y2     INTEGER,
    milvus_id   BIGINT,         -- maps to Milvus vector ID
    nearby_chunk_id TEXT REFERENCES text_chunks(chunk_id)
    -- this is the cross-modal link: image is tied to its nearest text chunk
);
