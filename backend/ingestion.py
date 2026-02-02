import os
import arxiv
from llama_index.core import Document, SimpleDirectoryReader
from typing import List
import re

def normalize_arxiv_id(arxiv_id: str) -> str:
    """
    Normalize ArXiv ID by removing version numbers and cleaning format.
    Examples:
        1706.03762v1 -> 1706.03762
        0503536v1 -> 0503536
        2301.12345 -> 2301.12345
    """
    # Remove version number (vN at the end)
    arxiv_id = re.sub(r'v\d+$', '', arxiv_id)
    # Remove any trailing slashes or whitespace
    arxiv_id = arxiv_id.strip().rstrip('/')
    return arxiv_id

def download_paper(arxiv_id: str, download_dir: str = "data/papers") -> str:
    """
    Downloads a paper from ArXiv given its ID.
    Returns the file path.
    """
    # Normalize the ArXiv ID
    original_id = arxiv_id
    arxiv_id = normalize_arxiv_id(arxiv_id)
    
    os.makedirs(download_dir, exist_ok=True)
    
    client = arxiv.Client()
    
    # Try different ID formats for old papers
    id_formats = [arxiv_id]
    
    # For old format IDs (e.g., 0503536), try with category prefix
    if len(arxiv_id) == 7 and arxiv_id.isdigit():
        # Common old categories
        id_formats.extend([
            f"astro-ph/{arxiv_id}",
            f"hep-th/{arxiv_id}",
            f"math/{arxiv_id}",
            f"cs/{arxiv_id}",
            f"physics/{arxiv_id}"
        ])
    
    paper = None
    for id_format in id_formats:
        try:
            search = arxiv.Search(id_list=[id_format])
            paper = next(client.results(search))
            arxiv_id = id_format  # Use the working format
            break
        except (StopIteration, Exception) as e:
            continue
    
    if paper is None:
        raise ValueError(f"ArXiv ID {original_id} not found. Try searching for the paper by title instead.")
    
    # Use normalized ID for filename
    filename = f"{normalize_arxiv_id(original_id)}.pdf"
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

def search_papers(query: str, max_results: int = 10, category: str = None, year: str = None):
    """
    Search ArXiv for papers matching the query with optional filters.
    Returns a list of paper metadata.
    """
    # If the query is long (likely a title) and doesn't contain field prefixes, try searching in title specifically
    if len(query.split()) > 3 and ":" not in query:
        # Construct a query that boosts title matches but falls back to all fields
        # This syntax depends on how arxiv library passes it to the API. 
        # Standard API supports "ti:title".
        # We will try a simple search first, but if max_results is low, we might miss it.
        # Let's try to be smart: search for title specifically if it seems like a specific paper.
        search_query = f'ti:"{query}" OR abs:"{query}" OR "{query}"'
    else:
        search_query = query
    
    # Add filters to query
    if category and category != "all":
        search_query = f"({search_query}) AND cat:{category}"
    
    if year:
        search_query = f"({search_query}) AND submittedDate:[{year}01010000 TO {year}12312359]"

    client = arxiv.Client()
    search = arxiv.Search(
        query=search_query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    results = []
    for paper in client.results(search):
        # Extract and normalize ArXiv ID
        raw_id = paper.entry_id.split('/')[-1]
        normalized_id = normalize_arxiv_id(raw_id)
        
        results.append({
            "arxiv_id": normalized_id,
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary,
            "published": paper.published.isoformat(),
            "pdf_url": paper.pdf_url,
            "categories": paper.categories
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
