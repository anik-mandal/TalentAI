import chromadb
import os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
print(f"Looking for chroma_db at: {path}")
print(f"Folder exists: {os.path.exists(path)}")

if os.path.exists(path):
    client = chromadb.PersistentClient(path=path)
    collections = client.list_collections()
    print(f"Collections found: {[c.name for c in collections]}")
    for c in collections:
        col = client.get_collection(c.name)
        print(f"  '{c.name}' has {col.count()} documents")
        if col.count() > 0:
            print(f"  IDs: {col.get()['ids']}")
else:
    print("chroma_db folder does NOT exist — Member 4 has never successfully stored a job")