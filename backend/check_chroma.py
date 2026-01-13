import chromadb
from config import settings

client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
collection = client.get_collection("research_papers")

# Get all metadata
results = collection.get(include=["metadatas"])
metadatas = results["metadatas"]

titles = set()
for m in metadatas:
    if m and "title" in m:
        titles.add(m["title"])

print(f"Total chunks: {len(metadatas)}")
print(f"Unique papers: {len(titles)}")
for t in titles:
    print(f"- {t}")
