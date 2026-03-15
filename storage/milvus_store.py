import numpy as np
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
from config import MILVUS_HOST, MILVUS_PORT, MILVUS_COLLECTION_TEXT, MILVUS_COLLECTION_IMAGE

def init_milvus():
    print(f"Connecting to Milvus at {MILVUS_HOST}:{MILVUS_PORT}")
    connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
    
    # Text collection
    if not utility.has_collection(MILVUS_COLLECTION_TEXT):
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)
        ]
        schema = CollectionSchema(fields, description="Text Embeddings")
        collection = Collection(MILVUS_COLLECTION_TEXT, schema)
        
        # Create HNSW index
        index_params = {
            "metric_type": "L2",
            "index_type": "HNSW",
            "params": {"M": 16, "efConstruction": 200}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
    
    # Image collection
    if not utility.has_collection(MILVUS_COLLECTION_IMAGE):
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=512)
        ]
        schema = CollectionSchema(fields, description="Image Embeddings")
        collection = Collection(MILVUS_COLLECTION_IMAGE, schema)
        
        index_params = {
            "metric_type": "L2", # CLIP usually trained with cosine, but normalized L2 == cosine
            "index_type": "HNSW",
            "params": {"M": 16, "efConstruction": 200}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
    
    # Load into memory
    Collection(MILVUS_COLLECTION_TEXT).load()
    Collection(MILVUS_COLLECTION_IMAGE).load()

def insert_text_vectors(embeddings: np.ndarray, doc_ids: list) -> list[int]:
    if embeddings.shape[0] == 0:
        return []
        
    collection = Collection(MILVUS_COLLECTION_TEXT)
    data = [
        doc_ids,
        embeddings.tolist()
    ]
    res = collection.insert(data)
    collection.flush()
    return res.primary_keys

def insert_image_vectors(embeddings: np.ndarray, doc_ids: list) -> list[int]:
    if embeddings.shape[0] == 0:
        return []
        
    collection = Collection(MILVUS_COLLECTION_IMAGE)
    data = [
        doc_ids,
        embeddings.tolist()
    ]
    res = collection.insert(data)
    collection.flush()
    return res.primary_keys

def search_text(query_embedding: np.ndarray, top_k: int) -> list[dict]:
    # Query embedding should be [1, dim]
    collection = Collection(MILVUS_COLLECTION_TEXT)
    
    search_params = {"metric_type": "L2", "params": {"ef": min(max(top_k * 2, 64), 200)}}
    results = collection.search(
        data=query_embedding.tolist(),
        anns_field="embedding",
        param=search_params,
        limit=top_k,
        output_fields=["doc_id"]
    )
    
    # results is a list of lists of Hits
    output = []
    if results and len(results) > 0:
        for hit in results[0]:
            output.append({
                "milvus_id": hit.id,
                "score": hit.distance
            })
    return output

def search_image(query_embedding: np.ndarray, top_k: int) -> list[dict]:
    collection = Collection(MILVUS_COLLECTION_IMAGE)
    
    search_params = {"metric_type": "L2", "params": {"ef": min(max(top_k * 2, 64), 200)}}
    results = collection.search(
        data=query_embedding.tolist(),
        anns_field="embedding",
        param=search_params,
        limit=top_k,
        output_fields=["doc_id"]
    )
    
    output = []
    if results and len(results) > 0:
        for hit in results[0]:
            output.append({
                "milvus_id": hit.id,
                "score": hit.distance
            })
    return output

def delete_by_doc_id(doc_id: str):
    """For re-ingestion, delete existing vectors dynamically."""
    text_coll = Collection(MILVUS_COLLECTION_TEXT)
    text_coll.delete(expr=f"doc_id == '{doc_id}'")
    
    image_coll = Collection(MILVUS_COLLECTION_IMAGE)
    image_coll.delete(expr=f"doc_id == '{doc_id}'")
