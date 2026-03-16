import os
import shutil
import psycopg2
from pymilvus import connections, utility
from config import POSTGRES_DSN, MILVUS_HOST, MILVUS_PORT, MILVUS_COLLECTION_TEXT, MILVUS_COLLECTION_IMAGE

def reset_db():
    # Purge and re-initialize the PostgreSQL relational store
    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(POSTGRES_DSN)
    cur = conn.cursor()
    
    tables = [
        "session_documents",
        "chat_messages",
        "chat_sessions",
        "image_regions",
        "text_chunks",
        "documents"
    ]
    
    for table in tables:
        print(f"Dropping table {table}...")
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    
    schema_path = os.path.join("storage", "schema.sql")
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    
    cur.execute(schema_sql)
    conn.commit()
    cur.close()
    conn.close()
    print("✓ PostgreSQL reset complete.")

    # Drop and recreate Milvus vector collections
    print(f"Connecting to Milvus at {MILVUS_HOST}:{MILVUS_PORT}...")
    connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
    
    for coll_name in [MILVUS_COLLECTION_TEXT, MILVUS_COLLECTION_IMAGE]:
        if utility.has_collection(coll_name):
            print(f"Dropping Milvus collection: {coll_name}...")
            utility.drop_collection(coll_name)
    
    from storage.milvus_store import init_milvus
    init_milvus()
    print("✓ Milvus reset complete.")

    # Wipe extracted image assets from filesystem
    image_dir = os.path.join("storage", "images")
    if os.path.exists(image_dir):
        print(f"Clearing images in {image_dir}...")
        for filename in os.listdir(image_dir):
            if filename.endswith(".png"):
                file_path = os.path.join(image_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')
    print("✓ Image storage cleared.")
    
    print("\n[SUCCESS] LocalLens environment reset.")

if __name__ == "__main__":
    reset_db()
