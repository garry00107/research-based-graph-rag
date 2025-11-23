import chromadb
from config import settings
from papers_library import papers_library
from ingestion import normalize_arxiv_id
import arxiv
import re
import os

def restore_library():
    print("Starting library restoration...")
    
    # 1. Get unique papers from ChromaDB
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    collection = client.get_collection("research_papers")
    
    results = collection.get(include=["metadatas"])
    metadatas = results["metadatas"]
    
    # Extract unique ArXiv IDs from filenames/sources
    arxiv_ids = set()
    for m in metadatas:
        if not m: continue
        
        source = m.get("file_name") or m.get("source")
        if source:
            # Extract ID from filename (e.g., "1706.03762.pdf" -> "1706.03762")
            # Remove .pdf extension
            clean_name = source.replace(".pdf", "")
            # Remove version if present for normalization logic
            normalized = normalize_arxiv_id(clean_name)
            arxiv_ids.add(normalized)
            
    print(f"Found {len(arxiv_ids)} unique papers in Vector Store: {arxiv_ids}")
    
    # 2. Fetch metadata for each paper
    client = arxiv.Client()
    restored_count = 0
    
    for aid in arxiv_ids:
        try:
            print(f"Fetching metadata for {aid}...")
            search = arxiv.Search(id_list=[aid])
            try:
                paper = next(client.results(search))
            except StopIteration:
                print(f"Warning: Could not find metadata for {aid}")
                continue
                
            # 3. Add to library
            # We don't know exact page count without opening PDF, defaulting to 0 or estimation
            # If we really wanted pages, we'd need to check if PDF exists locally and count pages
            pages = 0
            pdf_path = f"data/papers/{aid}.pdf"
            if os.path.exists(pdf_path):
                # Try to count pages if pypdf is available, else 0
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(pdf_path)
                    pages = len(reader.pages)
                except:
                    pass

            papers_library.add_paper(
                arxiv_id=aid,
                title=paper.title,
                authors=[a.name for a in paper.authors],
                summary=paper.summary,
                pages=pages
            )
            print(f"✓ Restored: {paper.title}")
            restored_count += 1
            
        except Exception as e:
            print(f"Error restoring {aid}: {e}")
            
    print(f"Restoration complete. Restored {restored_count}/{len(arxiv_ids)} papers.")

if __name__ == "__main__":
    restore_library()
