import chromadb
from config import settings

client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
collection = client.get_collection("research_papers")

results = collection.get(include=["metadatas"])
metadatas = results["metadatas"]

filenames = set()
for m in metadatas:
    if m:
        # Try common keys
        if "file_name" in m:
            filenames.add(m["file_name"])
        elif "source" in m:
            filenames.add(m["source"])
        elif "title" in m:
            filenames.add(m["title"])

print(f"Total chunks: {len(metadatas)}")
print(f"Unique papers (by filename/source): {len(filenames)}")
for f in filenames:
    print(f"- {f}")
