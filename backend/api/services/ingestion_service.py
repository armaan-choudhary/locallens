import os
from typing import List
from ingestion.preprocessor import process_path
from embeddings.text_embedder import embed_texts
from embeddings.image_embedder import embed_images
from storage.postgres_store import (
    insert_document, bulk_insert_text_chunks, bulk_insert_image_regions
)
from storage.milvus_store import insert_text_vectors, insert_image_vectors
from retrieval.bm25_retriever import mark_dirty
from config import STORAGE_IMAGES_DIR

# Global jobs tracker
jobs = {}

def process_ingestion(job_id: str, file_paths: List[str]):
    for i, filepath in enumerate(file_paths):
        filename = os.path.basename(filepath)
        jobs[job_id]["filename"] = filename
        jobs[job_id]["log_lines"].append(f"Ingesting: {filename}")
        
        try:
            jobs[job_id]["stage"] = "extracting"
            documents, all_text_chunks, all_image_crops = process_path(filepath)
            
            doc_id = documents[0]["doc_id"]
            jobs[job_id]["total_pages"] = documents[0]["page_count"]
            
            insert_document(doc_id, filename, filepath, documents[0]["page_count"])
            
            if all_text_chunks:
                jobs[job_id]["stage"] = "embedding"
                text_texts = [c["text"] for c in all_text_chunks]
                text_embs = embed_texts(text_texts)
                
                jobs[job_id]["stage"] = "indexing"
                milvus_ids = insert_text_vectors(text_embs, [doc_id]*len(all_text_chunks))
                
                chunks_data = []
                for j, chunk in enumerate(all_text_chunks):
                    m_id = milvus_ids[j] if milvus_ids and j < len(milvus_ids) else -1
                    chunks_data.append((
                        chunk["chunk_id"], doc_id, chunk["page_number"],
                        chunk["chunk_index"], chunk["char_start"], chunk["char_end"],
                        chunk["text"], chunk["source"], m_id
                    ))
                bulk_insert_text_chunks(chunks_data)
                mark_dirty()

                if all_image_crops:
                    jobs[job_id]["stage"] = "embedding_images"
                    img_objs = [c["image"] for c in all_image_crops]
                    img_embs = embed_images(img_objs)
                    milvus_ids = insert_image_vectors(img_embs, [doc_id]*len(all_image_crops))
                    
                    regions_data = []
                    for j, crop in enumerate(all_image_crops):
                        img_id = crop["image_id"]
                        m_id = milvus_ids[j] if milvus_ids and j < len(milvus_ids) else -1
                        bbox = crop["bbox"]
                        
                        img_path = os.path.join(STORAGE_IMAGES_DIR, f"{img_id}.png")
                        crop["image"].save(img_path)
                        
                        regions_data.append((
                            img_id, doc_id, crop["page_number"],
                            crop["image_index"], bbox[0], bbox[1], bbox[2], bbox[3], m_id, None, img_path
                        ))
                    bulk_insert_image_regions(regions_data)
            
            jobs[job_id]["log_lines"].append(f"✓ {filename} complete.")
            
        except Exception as e:
            jobs[job_id]["stage"] = "error"
            jobs[job_id]["log_lines"].append(f"✗ Failed: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    jobs[job_id]["stage"] = "done"
