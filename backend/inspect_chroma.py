import chromadb
from config import settings
import json

client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
collection = client.get_collection("research_papers")

results = collection.get(limit=1, include=["metadatas"])
if results["metadatas"] and len(results["metadatas"]) > 0:
    print("Keys:", list(results["metadatas"][0].keys()))
    print("Values:", results["metadatas"][0])
else:
    print("No metadata found")
