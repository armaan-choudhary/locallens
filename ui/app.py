import gradio as gr
import time
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
from generation.llm_runner import generate as generate_answer
from generation.hallucination_checker import verify_answer
from citation.citation_mapper import map_citations
import numpy as np

# Global state for indexed docs
indexed_docs = []

CSS = """
/* Monochrome Design System */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg-page: #09090b;
    --bg-surface: #111113;
    --bg-elevated: #18181b;
    --border-base: #27272a;
    --icon-muted: #3f3f46;
    --text-metadata: #52525b;
    --text-secondary: #71717a;
    --text-body: #a1a1aa;
    --text-primary: #e4e4e7;
    --text-headings: #fafafa;
}

body, .gradio-container {
    background-color: var(--bg-page) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--text-body) !important;
}

/* All inputs, textboxes */
input, textarea, .gr-textbox, .gr-input {
    background-color: var(--bg-elevated) !important;
    border: 1px solid var(--border-base) !important;
    color: var(--text-primary) !important;
}

/* Sidebar */
.sidebar {
    background-color: var(--bg-page);
    border-right: 1px solid var(--border-base);
    padding: 24px;
    height: 100vh;
}

.nav-item {
    background-color: transparent !important;
    border: none !important;
    color: var(--text-metadata) !important;
    text-align: left !important;
    padding: 8px 12px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    box-shadow: none !important;
    display: block !important;
    width: 100% !important;
}

.nav-item.active {
    color: var(--text-headings) !important;
    border-left: 2px solid var(--text-primary) !important;
    border-radius: 0 !important;
}

.section-label {
    font-family: monospace;
    font-size: 11px;
    text-transform: uppercase;
    color: var(--icon-muted);
    margin-top: 24px;
    margin-bottom: 8px;
}

/* Buttons */
.gr-button {
    background-color: var(--bg-page) !important;
    border: 1px solid var(--border-base) !important;
    color: var(--text-headings) !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    transition: background-color 0.2s !important;
    box-shadow: none !important;
}

.gr-button:hover {
    background-color: var(--bg-elevated) !important;
}

/* Onboarding Feature Rows */
.feature-row {
    display: flex;
    align-items: center;
    padding: 16px 0;
    border-bottom: 1px solid var(--bg-elevated);
}

.feature-chevron {
    color: var(--icon-muted);
    margin-right: 12px;
}

/* Drag and Drop Zone */
.drop-zone {
    background-color: var(--bg-surface) !important;
    border: 1.5px dashed var(--border-base) !important;
    border-radius: 10px !important;
    padding: 48px !important;
}

.drop-zone:hover {
    border-color: var(--text-metadata) !important;
    background-color: var(--bg-elevated) !important;
}

/* Progress Bar */
.progress-bar {
    height: 2px !important;
    background-color: var(--border-base) !important;
}
.progress-bar > div {
    background-color: var(--text-body) !important;
    border-radius: 0 !important;
}

/* Cards & Citations */
.card {
    background-color: var(--bg-surface);
    border: 1px solid var(--border-base);
    border-radius: 8px;
    padding: 16px;
}

.citation-card {
    border-left: 2px solid var(--icon-muted);
    margin-bottom: 12px;
}

.citation-badge {
    background-color: var(--bg-elevated);
    border: 1px solid var(--border-base);
    color: var(--text-metadata);
    padding: 2px 6px;
    font-size: 10px;
    text-transform: uppercase;
    border-radius: 4px;
}

/* Hallucination Variant */
.hallucination-warning {
    background-color: var(--bg-surface) !important;
    border-left: 2px solid var(--text-metadata) !important;
    padding: 12px !important;
    color: var(--text-secondary) !important;
    margin-bottom: 16px !important;
}

/* Table */
.activity-table th {
    font-size: 11px;
    text-transform: uppercase;
    color: var(--text-metadata);
    border-bottom: 1px solid var(--border-base);
}

.activity-table td {
    border-bottom: 1px solid var(--bg-elevated);
    color: var(--text-body);
}

/* Monospace Helpers */
.monospace {
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 12px;
    color: var(--text-metadata);
}

footer {
    display: none !important;
}
"""

def run_ingestion(files: list, progress=gr.Progress()):
    if not files:
        return []
        
    results = []
    
    for i, file_obj in enumerate(files):
        filename = file_obj.name.split('/')[-1]
        progress(i / len(files), desc=f"Ingesting: {filename}...")
        
        filepath = file_obj.name
        documents, all_text_chunks, all_image_crops = process_path(filepath)
        
        for doc in documents:
            insert_document(doc["doc_id"], doc["filename"], doc["filepath"], doc["page_count"])
            if doc["filename"] not in indexed_docs:
                indexed_docs.append(doc["filename"])
            results.append([doc["filename"], f"{doc['page_count']}", f"{len(all_text_chunks)}", "✓", "Just now"])
                
        if all_text_chunks:
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
            
        if all_image_crops:
            img_objs = [c["image"] for c in all_image_crops]
            img_embs = embed_images(img_objs)
            doc_ids = [c["doc_id"] for c in all_image_crops]
            
            milvus_ids = insert_image_vectors(img_embs, doc_ids)
            
            for j, crop in enumerate(all_image_crops):
                nearby_chunk_id = None
                if all_text_chunks:
                    page_chunks = [c for c in all_text_chunks if c["page_number"] == crop["page_number"]]
                    if page_chunks:
                        nearby_chunk = page_chunks[0]
                        nearby_chunk_id = nearby_chunk["chunk_id"]

                m_id = milvus_ids[j] if milvus_ids and j < len(milvus_ids) else -1
                insert_image_region(
                    crop["image_id"], crop["doc_id"], crop["page_number"],
                    crop["image_index"], crop["bbox"], m_id, nearby_chunk_id
                )
            
    progress(1.0, desc="Done")
    return results

def handle_query(query: str):
    start_time = time.time()
    
    text_dense, image_dense = run_dense_retrieval(query)
    text_bm25 = bm25_search(query, TOP_K_RETRIEVAL)
    ranked_chunks = rrf_fusion(text_dense, image_dense, text_bm25)
    
    prompt = build_prompt(query, ranked_chunks)
    generated_text = generate_answer(prompt)
    check_results = verify_answer(generated_text, ranked_chunks)
    
    warning_html = ""
    if not check_results["verified"]:
        warning_html = '<div class="hallucination-warning">⚠ Parts of this answer could not be fully verified against source documents.</div>'
        
    citations_html = ""
    for idx, card in enumerate(cards := map_citations(generated_text, ranked_chunks)):
        type_badge = f'<span class="citation-badge">{card["source_type"]}</span>'
        
        citations_html += f"""
        <div class="card citation-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span class="monospace" style="font-size:11px;">{type_badge} · {card['doc_name']} (Page {card['page_number']})</span>
                <span style="color:#52525b; font-size:12px;">↗</span>
            </div>
            <div class="monospace" style="line-height:1.6;">{card.get('chunk_text', 'Image reference at the specified page.')}</div>
        </div>
        """
            
    end_time = time.time()
    latency = f"{end_time - start_time:.1f}s"
    
    stats_html = f"Model: LOCALLENS-LOCAL-01 &nbsp;·&nbsp; Latency: {latency} &nbsp;·&nbsp; System Operational"
    
    return [
        warning_html,
        generated_text,
        citations_html,
        stats_html
    ]

def build_ui():
    with gr.Blocks(title="LocalLens") as app:
        
        # --- SCREEN 1: ONBOARDING ---
        with gr.Column(visible=True) as onboarding_screen:
            with gr.Column(scale=1):
                gr.HTML('<div style="margin-top:25vh;"></div>')
                with gr.Row():
                    gr.HTML('<div style="text-align:center; width:100%;"><span style="font-weight:500; font-size:15px; color:#fafafa; letter-spacing:0.05em;">LocalLens</span></div>')
                
                gr.HTML('<div style="border-bottom: 1px solid #18181b; margin: 24px auto; width: 40px;"></div>')
                
                gr.HTML('<div style="text-align:center; width:100%;"><h1 style="color:#fafafa; font-size:28px; font-weight:700; margin-bottom:8px;">Welcome to LocalLens</h1></div>')
                gr.HTML('<div style="text-align:center; width:100%;"><p style="color:#71717a; font-size:16px;">Your private document search. Everything runs locally.</p></div>')
                
                with gr.Column(elem_id="feature-list", scale=1):
                    gr.HTML('<div style="margin: 40px auto; max-width: 480px;">')
                    # Row 1
                    gr.HTML('<div class="feature-row"><span class="feature-chevron">→</span> <span style="color:#e4e4e7; font-weight:500; margin-right:12px;">100% Offline</span> <span style="color:#52525b; font-size:13px;">No data leaves your device.</span></div>')
                    # Row 2
                    gr.HTML('<div class="feature-row"><span class="feature-chevron">→</span> <span style="color:#e4e4e7; font-weight:500; margin-right:12px;">Verified Citations</span> <span style="color:#52525b; font-size:13px;">Every claim is traced back.</span></div>')
                    # Row 3
                    gr.HTML('<div class="feature-row"><span class="feature-chevron">→</span> <span style="color:#e4e4e7; font-weight:500; margin-right:12px;">Text + Images</span> <span style="color:#52525b; font-size:13px;">Multimodal RAG support.</span></div>')
                    gr.HTML('</div>')
                
                with gr.Row():
                    start_btn = gr.Button("Import Your First PDF", elem_id="start-btn")
                
                gr.HTML('<div style="text-align:center; color:#3f3f46; font-size:12px; margin-top:24px;">No accounts. No API keys. No internet required.</div>')

        # --- MAIN APP SHELL ---
        with gr.Row(visible=False) as main_shell:
            # Sidebar
            with gr.Column(scale=1, min_width=240, elem_classes="sidebar"):
                gr.HTML('<div style="font-weight:500; font-size:15px; color:#fafafa; margin-bottom:32px;">LocalLens</div>')
                
                nav_ingest = gr.Button("Ingest", elem_classes="nav-item active")
                nav_query = gr.Button("Search", elem_classes="nav-item")
                
                gr.HTML('<div class="section-label">INDEXED DOCUMENTS</div>')
                doc_list_container = gr.HTML('<div style="color:#52525b; font-size:13px;">No documents yet.</div>')
                
                with gr.Column():
                    gr.HTML('<div style="margin-top:auto; padding-top:40px;"></div>')
                    gr.HTML('<div style="color:#3f3f46; font-size:11px; font-family:monospace;">· MILVUS · POSTGRESQL</div>')

            # Main Content
            with gr.Column(scale=4):
                # --- SCREEN 2: INGEST ---
                with gr.Column(visible=True) as ingest_view:
                    gr.HTML('<div style="margin-bottom:24px;"><h1 style="color:#fafafa; font-size:24px; font-weight:700;">Ingest Documents</h1><p style="color:#71717a; font-size:14px;">Index local files for semantic search and private analysis.</p></div>')
                    
                    file_input = gr.File(label="", file_types=[".pdf"], file_count="multiple", elem_classes="drop-zone")
                    gr.HTML('<div style="text-align:center; color:#52525b; font-size:12px; margin-top:-20px;">PDF · DOCX · TXT up to 100MB</div>')
                    
                    with gr.Column(visible=False) as queue_section:
                        ingest_btn = gr.Button("Start Ingestion", variant="primary")
                    
                    gr.HTML('<div class="section-label" style="margin-top:40px;">Recent Activity</div>')
                    activity_table = gr.Dataframe(
                        headers=["DOCUMENT NAME", "PAGES", "CHUNKS", "STATUS", "TIME"],
                        datatype=["str", "str", "str", "str", "str"],
                        value=[],
                        interactive=False,
                        elem_classes="activity-table"
                    )

                # --- SCREEN 3: QUERY ---
                with gr.Column(visible=False) as query_view:
                    with gr.Row():
                        q_input = gr.Textbox(
                            show_label=False,
                            placeholder="Ask a follow-up or research a new topic...",
                            scale=10
                        )
                        search_btn = gr.Button("Search", scale=1)
                    
                    with gr.Row(elem_id="query-results"):
                        # Answer Column
                        with gr.Column(scale=2):
                            gr.HTML('<div class="section-label">ANSWER</div>')
                            hallucination_banner = gr.HTML("")
                            answer_md = gr.Markdown("")
                                
                        # Sources Column
                        with gr.Column(scale=1):
                            gr.HTML('<div class="section-label">SOURCES</div>')
                            citations_area = gr.HTML('<div style="color:#3f3f46; font-size:13px;">No references found.</div>')

                # Shared Monochromatic Footer Status
                with gr.Row():
                    stats_out = gr.HTML('<div class="monospace" style="font-size:12px; color:#3f3f46;">Model: LOCALLENS-LOCAL-01 &nbsp;·&nbsp; System Operational</div>')

        # --- NAVIGATION LOGIC ---
        def go_to_app():
            return [gr.update(visible=False), gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)]
        
        start_btn.click(fn=go_to_app, outputs=[onboarding_screen, main_shell, ingest_view, query_view])
        
        def switch_to_ingest():
            return [gr.update(visible=True), gr.update(visible=False), gr.update(elem_classes="nav-item active"), gr.update(elem_classes="nav-item")]
        def switch_to_query():
            return [gr.update(visible=False), gr.update(visible=True), gr.update(elem_classes="nav-item"), gr.update(elem_classes="nav-item active")]
            
        nav_ingest.click(fn=switch_to_ingest, outputs=[ingest_view, query_view, nav_ingest, nav_query])
        nav_query.click(fn=switch_to_query, outputs=[ingest_view, query_view, nav_ingest, nav_query])
        
        file_input.change(fn=lambda x: gr.update(visible=True if x else False), inputs=file_input, outputs=queue_section)
        
        def handle_ingest_wrapper(files):
            new_rows = run_ingestion(files)
            doc_html = "<div>"
            for row in new_rows:
                doc_html += f'<div style="margin-bottom:12px;"><div style="color:#fafafa; font-weight:500; font-size:13px;">{row[0]}</div><div style="color:#52525b; font-size:11px; font-family:monospace;">{row[2]} chunks · {row[1]} pages</div></div>'
            doc_html += "</div>"
            return new_rows, doc_html

        ingest_btn.click(fn=handle_ingest_wrapper, inputs=file_input, outputs=[activity_table, doc_list_container])
        
        search_btn.click(
            fn=handle_query,
            inputs=q_input,
            outputs=[hallucination_banner, answer_md, citations_area, stats_out]
        )

    return app

if __name__ == "__main__":
    app = build_ui()
    app.launch(css=CSS)
