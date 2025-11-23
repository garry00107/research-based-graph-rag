import os
import arxiv
from llama_index.core import Document, SimpleDirectoryReader
from typing import List

def download_paper(arxiv_id: str, download_dir: str = "data/papers") -> str:
    """
    Downloads a paper from ArXiv given its ID.
    Returns the file path.
    """
    os.makedirs(download_dir, exist_ok=True)
    
    client = arxiv.Client()
    search = arxiv.Search(id_list=[arxiv_id])
    try:
        paper = next(client.results(search))
    except StopIteration:
        raise ValueError(f"ArXiv ID {arxiv_id} not found.")
    
    filename = f"{arxiv_id}.pdf"
    file_path = os.path.join(download_dir, filename)
    
    if not os.path.exists(file_path):
        paper.download_pdf(dirpath=download_dir, filename=filename)
        print(f"Downloaded {paper.title}")
    else:
        print(f"File {filename} already exists.")
        
    return file_path

def load_documents(file_path: str) -> List[Document]:
    """
    Loads documents from a PDF file.
    """
    # SimpleDirectoryReader handles PDFs automatically if pypdf is installed.
    # llama-index usually comes with pypdf or we might need to install it.
    # The user requirements didn't specify pypdf, but it's a common dependency.
    # We will assume it's there or add it.
    reader = SimpleDirectoryReader(input_files=[file_path])
    documents = reader.load_data()
    return documents

def search_papers(query: str, max_results: int = 10):
    """
    Search ArXiv for papers matching the query.
    Returns a list of paper metadata.
    """
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    results = []
    for paper in client.results(search):
        results.append({
            "arxiv_id": paper.entry_id.split('/')[-1],
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary,
            "published": paper.published.isoformat(),
            "pdf_url": paper.pdf_url
        })
    
    return results

if __name__ == "__main__":
    # Test
    pid = "1706.03762" # Attention is All You Need
    try:
        path = download_paper(pid)
        print(f"Downloaded to {path}")
        docs = load_documents(path)
        print(f"Loaded {len(docs)} pages")
    except Exception as e:
        print(f"Error: {e}")
