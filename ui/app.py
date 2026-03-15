import gradio as gr
import time
import threading
from config import TOP_K_RETRIEVAL

from ingestion.preprocessor import process_path
from embeddings.text_embedder import embed_texts
from embeddings.image_embedder import embed_images
from storage.postgres_store import insert_document, insert_text_chunk, insert_image_region, get_all_chunks
from storage.milvus_store import insert_text_vectors, insert_image_vectors
from retrieval.dense_retriever import run_dense_retrieval
from retrieval.bm25_retriever import search as bm25_search, mark_dirty
from retrieval.rrf_fusion import rrf_fusion
from generation.prompt_builder import build_prompt
from generation.llm_runner import generate as generate_answer, generate_stream
from generation.hallucination_checker import verify_answer
from citation.citation_mapper import map_citations
import numpy as np

# Global state
indexed_docs = []

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-page:       #08080a;
    --bg-surface:    #0f0f12;
    --bg-elevated:   #161619;
    --bg-card:       #1a1a1f;
    --border-dim:    #1f1f24;
    --border-base:   #2a2a32;
    --border-focus:  #3a3a48;
    --icon-muted:    #3a3a48;
    --text-disabled: #40404d;
    --text-metadata: #5a5a6e;
    --text-secondary:#7a7a90;
    --text-body:     #a0a0b8;
    --text-primary:  #d4d4e8;
    --text-headings: #f0f0f8;
    --accent:        #7c6af7;
    --accent-dim:    rgba(124,106,247,0.12);
    --accent-glow:   rgba(124,106,247,0.25);
    --success:       #34d399;
    --warning:       #fbbf24;
    --error:         #f87171;
    --terminal-bg:   #04040a;
    --terminal-text: #50fa7b;
    --terminal-dim:  #44475a;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .gradio-container {
    background: var(--bg-page) !important;
    font-family: 'Inter', system-ui, sans-serif !important;
    color: var(--text-body) !important;
    min-height: 100vh;
    overflow-x: hidden;
}

/* ── Scrollbar ─────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-base); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--border-focus); }

/* ── Inputs ─────────────────────────────────────────── */
input, textarea, .gr-textbox, .gr-input {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-base) !important;
    color: var(--text-primary) !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.2s !important;
}
input:focus, textarea:focus {
    border-color: var(--border-focus) !important;
    outline: none !important;
    box-shadow: 0 0 0 3px var(--accent-dim) !important;
}

/* ── Buttons ────────────────────────────────────────── */
.gr-button {
    font-family: 'Inter', sans-serif !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    letter-spacing: 0.01em !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    box-shadow: none !important;
}
.gr-button-primary {
    background: var(--accent) !important;
    border: 1px solid transparent !important;
    color: #ffffff !important;
}
.gr-button-primary:hover {
    background: #6b59e8 !important;
    box-shadow: 0 0 16px var(--accent-glow) !important;
}
.gr-button-secondary, .gr-button {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-base) !important;
    color: var(--text-primary) !important;
}
.gr-button-secondary:hover, .gr-button:hover {
    background: var(--bg-card) !important;
    border-color: var(--border-focus) !important;
}

/* ── Sidebar ────────────────────────────────────────── */
.sidebar {
    background: var(--bg-surface) !important;
    border-right: 1px solid var(--border-dim) !important;
    padding: 24px 16px !important;
    min-height: 100vh !important;
}

.logo-text {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-headings);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 32px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.logo-text::before {
    content: "◈";
    color: var(--accent);
    font-size: 16px;
}

.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-disabled);
    margin: 20px 0 6px;
    padding: 0 4px;
}

.nav-item {
    background: transparent !important;
    border: none !important;
    color: var(--text-metadata) !important;
    text-align: left !important;
    padding: 7px 10px !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    cursor: pointer !important;
    border-radius: 6px !important;
    display: block !important;
    width: 100% !important;
    transition: all 0.15s !important;
}
.nav-item:hover { background: var(--bg-elevated) !important; color: var(--text-body) !important; }
.nav-item.active {
    background: var(--accent-dim) !important;
    color: var(--text-headings) !important;
    font-weight: 500 !important;
}

/* ── Onboarding ─────────────────────────────────────── */
.onboarding-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 90vh;
    width: 100%;
}

.onboard-logo {
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 16px;
}

.onboard-title {
    font-size: 36px;
    font-weight: 700;
    color: var(--text-headings);
    text-align: center;
    letter-spacing: -0.02em;
    line-height: 1.15;
    margin-bottom: 10px;
}

.onboard-sub {
    font-size: 15px;
    color: var(--text-secondary);
    text-align: center;
    max-width: 400px;
    line-height: 1.6;
    margin-bottom: 40px;
}

.feature-list {
    width: 100%;
    max-width: 440px;
    border: 1px solid var(--border-dim);
    border-radius: 12px;
    background: var(--bg-surface);
    overflow: hidden;
    margin-bottom: 32px;
}

.feature-row {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-dim);
}
.feature-row:last-child { border-bottom: none; }

.feature-icon {
    width: 34px;
    height: 34px;
    border-radius: 8px;
    background: var(--accent-dim);
    border: 1px solid var(--accent-glow);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    flex-shrink: 0;
}

.feature-text-wrap {}
.feature-name {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 2px;
}
.feature-desc {
    font-size: 12px;
    color: var(--text-metadata);
}

.onboard-footer {
    font-size: 11px;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-disabled);
    text-align: center;
    margin-top: 16px;
}

/* ── Ingest Screen ──────────────────────────────────── */
.screen-header { margin-bottom: 28px; }
.screen-title {
    font-size: 22px;
    font-weight: 700;
    color: var(--text-headings);
    letter-spacing: -0.015em;
    margin-bottom: 4px;
}
.screen-sub { font-size: 13px; color: var(--text-secondary); }

.drop-zone {
    background: var(--bg-surface) !important;
    border: 1.5px dashed var(--border-base) !important;
    border-radius: 12px !important;
    min-height: 140px !important;
    transition: all 0.2s !important;
}
.drop-zone:hover {
    border-color: var(--accent) !important;
    background: var(--accent-dim) !important;
    box-shadow: 0 0 24px var(--accent-dim) !important;
}

/* Terminal log */
.terminal-panel {
    background: var(--terminal-bg);
    border: 1px solid var(--border-dim);
    border-radius: 10px;
    padding: 14px 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    line-height: 1.7;
    min-height: 130px;
    max-height: 200px;
    overflow-y: auto;
    color: var(--terminal-text);
    white-space: pre-wrap;
    word-break: break-all;
}

/* Progress bar override */
.gr-progress { height: 3px !important; border-radius: 2px !important; }

/* Activity table */
.activity-table table { width: 100%; border-collapse: collapse; }
.activity-table th {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-disabled) !important;
    border-bottom: 1px solid var(--border-dim) !important;
    padding: 8px 10px !important;
    background: transparent !important;
}
.activity-table td {
    font-size: 13px;
    color: var(--text-body) !important;
    border-bottom: 1px solid var(--border-dim) !important;
    padding: 10px !important;
    background: transparent !important;
}
.activity-table tr:hover td { background: var(--bg-elevated) !important; }

/* ── Query Screen ───────────────────────────────────── */
.search-bar-wrap {
    display: flex;
    gap: 10px;
    align-items: flex-end;
    margin-bottom: 24px;
}

.answer-panel {
    background: var(--bg-surface);
    border: 1px solid var(--border-dim);
    border-radius: 12px;
    padding: 22px 24px;
    min-height: 260px;
}

.answer-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-disabled);
    margin-bottom: 14px;
}

.answer-placeholder {
    color: var(--text-disabled);
    font-size: 14px;
    font-style: italic;
}

/* ── Citation Cards ─────────────────────────────────── */
.citations-panel {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.citation-card {
    background: var(--bg-card);
    border: 1px solid var(--border-dim);
    border-left: 3px solid var(--accent);
    border-radius: 10px;
    padding: 14px 16px;
    transition: border-color 0.2s;
}
.citation-card:hover {
    border-color: var(--border-focus);
    border-left-color: var(--accent);
}

.cit-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    flex-wrap: wrap;
}

.cit-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 2px 7px;
    border-radius: 4px;
    background: var(--accent-dim);
    color: var(--accent);
    border: 1px solid var(--accent-glow);
}
.cit-badge.img { background: rgba(52,211,153,0.08); color: var(--success); border-color: rgba(52,211,153,0.2); }

.cit-filename {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.cit-page {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: var(--text-metadata);
    white-space: nowrap;
}

.cit-chunk {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    line-height: 1.65;
    color: var(--text-secondary);
    background: var(--bg-surface);
    border: 1px solid var(--border-dim);
    border-radius: 6px;
    padding: 10px 12px;
    margin-bottom: 10px;
    max-height: 100px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-word;
}

.cit-bbox {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: var(--text-disabled);
    letter-spacing: 0.05em;
}

/* ── Hallucination warning ──────────────────────────── */
.hallucination-warning {
    background: rgba(251,191,36,0.06) !important;
    border: 1px solid rgba(251,191,36,0.2) !important;
    border-left: 3px solid var(--warning) !important;
    border-radius: 8px !important;
    padding: 11px 14px !important;
    color: var(--warning) !important;
    font-size: 13px !important;
    margin-bottom: 14px !important;
}

/* ── Status bar ─────────────────────────────────────── */
.status-bar {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--text-disabled);
    padding: 12px 0 4px;
    border-top: 1px solid var(--border-dim);
    margin-top: 16px;
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
}
.status-dot { color: var(--success); }

/* ── Sidebar doc list ───────────────────────────────── */
.doc-item {
    padding: 6px 4px;
    border-bottom: 1px solid var(--border-dim);
    font-size: 12px;
    color: var(--text-secondary);
}
.doc-item-name { color: var(--text-body); font-weight: 500; margin-bottom: 1px; }
.doc-item-meta { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--text-disabled); }

/* ── Misc ───────────────────────────────────────────── */
footer { display: none !important; }

.gr-markdown p, .gr-markdown li {
    color: var(--text-body) !important;
    line-height: 1.7 !important;
    font-size: 14px !important;
}
.gr-markdown h1, .gr-markdown h2, .gr-markdown h3 {
    color: var(--text-headings) !important;
    font-weight: 600 !important;
}
.gr-markdown code {
    font-family: 'JetBrains Mono', monospace !important;
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-base) !important;
    border-radius: 4px !important;
    padding: 1px 5px !important;
    font-size: 12px !important;
    color: var(--text-primary) !important;
}
"""

# ─── Ingestion backend ──────────────────────────────────────────────────────

def run_ingestion(files: list, progress=gr.Progress()):
    if not files:
        return [], "<span style='color:var(--text-disabled)'>No files provided.</span>", _doc_html()

    log_lines = []

    def emit(msg: str):
        log_lines.append(msg)

    results = []
    total = len(files)

    for i, file_obj in enumerate(files):
        filename = file_obj.name.split('/')[-1]
        progress(i / total, desc=f"[{i+1}/{total}] {filename}")
        emit(f"[{i+1}/{total}] ▶  {filename}")

        filepath = file_obj.name
        emit(f"       → parsing PDF with PyPDF2 …")
        documents, all_text_chunks, all_image_crops = process_path(filepath)
        emit(f"       → extracted {len(all_text_chunks)} text chunks, {len(all_image_crops)} image regions")

        for doc in documents:
            insert_document(doc["doc_id"], doc["filename"], doc["filepath"], doc["page_count"])
            if doc["filename"] not in indexed_docs:
                indexed_docs.append(doc["filename"])
            results.append([doc["filename"], str(doc["page_count"]), str(len(all_text_chunks)), "✓", "Just now"])

        if all_text_chunks:
            emit(f"       → embedding {len(all_text_chunks)} chunks …")
            text_texts = [c["text"] for c in all_text_chunks]
            text_embs = embed_texts(text_texts)
            doc_ids = [c["doc_id"] for c in all_text_chunks]
            milvus_ids = insert_text_vectors(text_embs, doc_ids)
            for j, chunk in enumerate(all_text_chunks):
                m_id = milvus_ids[j] if milvus_ids and j < len(milvus_ids) else -1
                insert_text_chunk(
                    chunk["chunk_id"], chunk["doc_id"], chunk["page_number"],
                    chunk["chunk_index"], chunk["char_start"], chunk["char_end"],
                    chunk["text"], chunk["source"], m_id
                )
            mark_dirty()
            emit(f"       → text vectors stored in Milvus ✓")

        if all_image_crops:
            emit(f"       → OCR + embedding {len(all_image_crops)} image regions …")
            img_objs = [c["image"] for c in all_image_crops]
            img_embs = embed_images(img_objs)
            doc_ids = [c["doc_id"] for c in all_image_crops]
            milvus_ids = insert_image_vectors(img_embs, doc_ids)
            for j, crop in enumerate(all_image_crops):
                nearby_chunk_id = None
                if all_text_chunks:
                    page_chunks = [c for c in all_text_chunks if c["page_number"] == crop["page_number"]]
                    if page_chunks:
                        nearby_chunk_id = page_chunks[0]["chunk_id"]
                m_id = milvus_ids[j] if milvus_ids and j < len(milvus_ids) else -1
                insert_image_region(
                    crop["image_id"], crop["doc_id"], crop["page_number"],
                    crop["image_index"], crop["bbox"], m_id, nearby_chunk_id
                )
            emit(f"       → image vectors stored in Milvus ✓")

        emit(f"       ✔  done — {doc['page_count']} pages indexed\n")

    progress(1.0, desc="✔ Ingestion complete")
    emit("─" * 38)
    emit(f"✔  Pipeline complete. {len(results)} document(s) indexed.")

    terminal_text = "\n".join(log_lines)
    return results, terminal_text, _doc_html()


def _doc_html():
    if not indexed_docs:
        return "<div style='color:var(--text-disabled); font-size:12px;'>No documents yet.</div>"
    html = ""
    for name in indexed_docs:
        html += f"""<div class="doc-item">
  <div class="doc-item-name">{name}</div>
</div>"""
    return html


# ─── Query backend ──────────────────────────────────────────────────────────

def handle_query(query: str):
    if not query.strip():
        return "", "", "<div class='answer-placeholder'>Ask a question to get started.</div>", \
               "<div style='color:var(--text-disabled); font-size:13px;'>No references.</div>", \
               _status_html("—")

    start_time = time.time()

    text_dense, image_dense = run_dense_retrieval(query)
    text_bm25 = bm25_search(query, TOP_K_RETRIEVAL)
    ranked_chunks = rrf_fusion(text_dense, image_dense, text_bm25)

    prompt = build_prompt(query, ranked_chunks)

    # Stream the answer
    full_text = ""
    for partial in generate_stream(prompt):
        full_text = partial
        yield "", full_text, _citations_html(full_text, ranked_chunks, verified=True), \
              "<div style='color:var(--text-disabled); font-size:13px;'>...</div>", \
              _status_html("streaming…")

    check_results = verify_answer(full_text, ranked_chunks)
    verified = check_results.get("verified", True)

    warning_html = ""
    if not verified:
        warning_html = (
            '<div class="hallucination-warning">'
            '⚠ Parts of this answer could not be fully verified against source documents.'
            '</div>'
        )

    citations_html = _citations_html(full_text, ranked_chunks, verified=verified)
    end_time = time.time()

    yield warning_html, full_text, citations_html, citations_html, _status_html(f"{end_time - start_time:.1f}s")


def _citations_html(answer: str, ranked_chunks: list, verified: bool = True) -> str:
    cards = map_citations(answer, ranked_chunks)
    if not cards:
        return "<div style='color:var(--text-disabled); font-size:13px;'>No references found.</div>"

    html = "<div class='citations-panel'>"
    for card in cards:
        stype = card.get("source_type", "text")
        badge_cls = "cit-badge img" if stype == "image" else "cit-badge"
        badge_label = "OCR/IMG" if stype == "image" else "TEXT"

        chunk_txt = card.get("chunk_text", "")
        # Truncate for display
        display_chunk = (chunk_txt[:320] + "…") if len(chunk_txt) > 320 else chunk_txt

        bbox = card.get("bbox")
        bbox_str = ""
        if bbox and any(v != 0 for v in bbox):
            bbox_str = f"<div class='cit-bbox'>BBOX · x₀={bbox[0]:.0f} y₀={bbox[1]:.0f} x₁={bbox[2]:.0f} y₁={bbox[3]:.0f}</div>"

        html += f"""
<div class='citation-card'>
  <div class='cit-header'>
    <span class='{badge_cls}'>{badge_label}</span>
    <span class='cit-filename'>{card['doc_name']}</span>
    <span class='cit-page'>pg {card['page_number']}</span>
  </div>
  <div class='cit-chunk'>{display_chunk}</div>
  {bbox_str}
</div>"""

    html += "</div>"
    return html


def _status_html(latency: str) -> str:
    return (
        f"<div class='status-bar'>"
        f"<span class='status-dot'>●</span> LOCALLENS-LOCAL-01"
        f"&nbsp;&nbsp;·&nbsp;&nbsp;Latency: {latency}"
        f"&nbsp;&nbsp;·&nbsp;&nbsp;Milvus ✓&nbsp;&nbsp;PostgreSQL ✓"
        f"</div>"
    )


# ─── UI builder ─────────────────────────────────────────────────────────────

def build_ui():
    with gr.Blocks(title="LocalLens — Private Document AI", css=CSS, theme=gr.themes.Base()) as app:

        # ══════════════════════════════════════════════
        # SCREEN 4: ONBOARDING
        # ══════════════════════════════════════════════
        with gr.Column(visible=True, elem_id="onboarding-screen") as onboarding_screen:
            gr.HTML("""
<div class="onboarding-wrap">
  <div class="onboard-logo">LocalLens</div>
  <h1 class="onboard-title">Your documents,<br>answered privately.</h1>
  <p class="onboard-sub">
    Semantic search, multimodal RAG, and verified citations —
    all running on your machine. Zero cloud. Zero leaks.
  </p>

  <div class="feature-list">
    <div class="feature-row">
      <div class="feature-icon">🔒</div>
      <div class="feature-text-wrap">
        <div class="feature-name">100 % Offline</div>
        <div class="feature-desc">Every model and index stays on your device.</div>
      </div>
    </div>
    <div class="feature-row">
      <div class="feature-icon">📎</div>
      <div class="feature-text-wrap">
        <div class="feature-name">Verified Citations</div>
        <div class="feature-desc">Every answer traced to exact page &amp; chunk.</div>
      </div>
    </div>
    <div class="feature-row">
      <div class="feature-icon">🖼</div>
      <div class="feature-text-wrap">
        <div class="feature-name">Text + Images</div>
        <div class="feature-desc">OCR &amp; CLIP-based multimodal retrieval.</div>
      </div>
    </div>
  </div>
</div>
""")
            with gr.Row(elem_id="onboard-cta-row"):
                with gr.Column(scale=3): gr.HTML("")
                with gr.Column(scale=2):
                    start_btn = gr.Button("Import Your First PDF →", variant="primary", size="lg")
                with gr.Column(scale=3): gr.HTML("")
            gr.HTML("<div class='onboard-footer'>No accounts · No API keys · No internet</div>")

        # ══════════════════════════════════════════════
        # MAIN SHELL (sidebar + content)
        # ══════════════════════════════════════════════
        with gr.Row(visible=False, elem_id="main-shell") as main_shell:

            # ── Sidebar ───────────────────────────────
            with gr.Column(scale=1, min_width=220, elem_classes=["sidebar"]):
                gr.HTML('<div class="logo-text">LocalLens</div>')

                nav_ingest = gr.Button("⬆  Ingest", elem_classes=["nav-item", "active"])
                nav_query  = gr.Button("🔍  Search", elem_classes=["nav-item"])

                gr.HTML('<div class="section-label">Indexed Documents</div>')
                doc_list_html = gr.HTML('<div style="color:var(--text-disabled); font-size:12px;">No documents yet.</div>')

                gr.HTML('<div style="margin-top:auto; padding-top:60px;"></div>')
                gr.HTML('<div style="font-family:\'JetBrains Mono\',monospace; font-size:10px; color:var(--text-disabled);">· MILVUS · POSTGRESQL</div>')

            # ── Main Content ───────────────────────────
            with gr.Column(scale=5, elem_id="main-content"):

                # ── SCREEN 1: INGEST ──────────────────
                with gr.Column(visible=True, elem_id="ingest-view") as ingest_view:
                    gr.HTML("""
<div class="screen-header">
  <div class="screen-title">Ingest Documents</div>
  <div class="screen-sub">
    Drop individual PDFs or an entire folder. PyPDF2 extracts text; Tesseract handles image-only pages.
  </div>
</div>""")

                    file_input = gr.File(
                        label="",
                        file_types=[".pdf"],
                        file_count="multiple",
                        elem_classes=["drop-zone"]
                    )
                    gr.HTML('<div style="text-align:center; color:var(--text-disabled); font-size:11px; margin-top:-18px; font-family:\'JetBrains Mono\',monospace;">PDF · Drop files or an entire folder</div>')

                    with gr.Column(visible=False, elem_id="ingest-queue") as queue_section:
                        ingest_btn = gr.Button("▶  Start Ingestion", variant="primary")

                    gr.HTML('<div class="section-label" style="margin-top:28px;">Pipeline Log</div>')
                    terminal_log = gr.HTML(
                        '<div class="terminal-panel" style="color:var(--text-disabled); font-style:italic;">Waiting for ingestion…</div>'
                    )

                    gr.HTML('<div class="section-label" style="margin-top:24px;">Recent Activity</div>')
                    activity_table = gr.Dataframe(
                        headers=["Document Name", "Pages", "Chunks", "Status", "Time"],
                        datatype=["str", "str", "str", "str", "str"],
                        value=[],
                        interactive=False,
                        elem_classes=["activity-table"]
                    )

                # ── SCREEN 2: QUERY ───────────────────
                with gr.Column(visible=False, elem_id="query-view") as query_view:
                    with gr.Row(elem_id="search-row"):
                        q_input = gr.Textbox(
                            show_label=False,
                            placeholder="Ask anything about your documents…",
                            scale=9,
                            lines=1
                        )
                        search_btn = gr.Button("Search", variant="primary", scale=1)

                    with gr.Row(elem_id="results-row", equal_height=False):
                        # Answer pane (left, 60%)
                        with gr.Column(scale=3):
                            gr.HTML('<div class="answer-label">Answer</div>')
                            hallucination_banner = gr.HTML("")
                            answer_md = gr.Markdown(
                                """<div class="answer-placeholder">Ask a question to get started.</div>""",
                                elem_id="answer-md"
                            )

                        # Citations pane (right, 40%)
                        with gr.Column(scale=2):
                            gr.HTML('<div class="answer-label">Sources</div>')
                            citations_area = gr.HTML(
                                '<div style="color:var(--text-disabled); font-size:13px;">No references.</div>'
                            )

                    stats_out = gr.HTML(_status_html("—"))

        # ─── Navigation logic ─────────────────────────
        def go_to_app():
            return (
                gr.update(visible=False),   # onboarding
                gr.update(visible=True),    # main_shell
                gr.update(visible=True),    # ingest_view
                gr.update(visible=False),   # query_view
            )

        start_btn.click(
            fn=go_to_app,
            outputs=[onboarding_screen, main_shell, ingest_view, query_view]
        )

        def switch_to_ingest():
            return (
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(elem_classes=["nav-item", "active"]),
                gr.update(elem_classes=["nav-item"]),
            )

        def switch_to_query():
            return (
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(elem_classes=["nav-item"]),
                gr.update(elem_classes=["nav-item", "active"]),
            )

        nav_ingest.click(fn=switch_to_ingest, outputs=[ingest_view, query_view, nav_ingest, nav_query])
        nav_query.click(fn=switch_to_query,   outputs=[ingest_view, query_view, nav_ingest, nav_query])

        # Show ingest button when files are added
        file_input.change(
            fn=lambda x: gr.update(visible=bool(x)),
            inputs=file_input,
            outputs=queue_section
        )

        # Ingestion pipeline
        def handle_ingest_wrapper(files):
            rows, terminal_text, doc_html = run_ingestion(files)
            log_html = f'<div class="terminal-panel">{terminal_text}</div>'
            return rows, log_html, doc_html

        ingest_btn.click(
            fn=handle_ingest_wrapper,
            inputs=file_input,
            outputs=[activity_table, terminal_log, doc_list_html]
        )

        # Query (streaming)
        search_btn.click(
            fn=handle_query,
            inputs=q_input,
            outputs=[hallucination_banner, answer_md, citations_area, citations_area, stats_out]
        )
        q_input.submit(
            fn=handle_query,
            inputs=q_input,
            outputs=[hallucination_banner, answer_md, citations_area, citations_area, stats_out]
        )

    return app


if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=7860, show_error=True)
