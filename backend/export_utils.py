from typing import List, Dict
from datetime import datetime
from chat_history import chat_history
from papers_library import papers_library
import re

def generate_markdown(conversation_id: str) -> str:
    """
    Generate Markdown export of a chat conversation.
    """
    messages = chat_history.get_history(conversation_id)
    
    if not messages:
        return "# Chat History\n\nNo messages found."
    
    # Build Markdown content
    lines = [
        "# Research Assistant Chat",
        f"\n**Conversation ID:** `{conversation_id}`",
        f"\n**Exported:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "\n---\n"
    ]
    
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")
        
        if role == "user":
            lines.append(f"\n## 👤 User")
            if timestamp:
                lines.append(f"\n*{timestamp}*\n")
            lines.append(f"\n{content}\n")
        elif role == "assistant":
            lines.append(f"\n## 🤖 Assistant")
            if timestamp:
                lines.append(f"\n*{timestamp}*\n")
            lines.append(f"\n{content}\n")
    
    return "\n".join(lines)


def generate_bibtex(arxiv_id: str) -> str:
    """
    Generate BibTeX citation for a paper from the library.
    """
    paper = papers_library.get_paper(arxiv_id)
    
    if not paper:
        return f"% Paper {arxiv_id} not found in library"
    
    # Create citation key (first_author_year)
    authors = paper.get("authors", [])
    first_author = authors[0] if authors else "Unknown"
    last_name = first_author.split()[-1].lower()
    
    # Extract year from ingested_at or use current year
    ingested_at = paper.get("ingested_at", "")
    year = ingested_at[:4] if ingested_at else datetime.utcnow().year
    
    citation_key = f"{last_name}{year}"
    
    # Clean title (remove newlines and extra spaces)
    title = re.sub(r'\s+', ' ', paper.get("title", "Untitled")).strip()
    
    # Format authors for BibTeX
    author_list = " and ".join(authors)
    
    # Build BibTeX entry
    bibtex = f"""@article{{{citation_key},
  title={{{title}}},
  author={{{author_list}}},
  journal={{arXiv preprint arXiv:{arxiv_id}}},
  year={{{year}}},
  url={{https://arxiv.org/abs/{arxiv_id}}}
}}"""
    
    return bibtex


def generate_bibtex_from_library() -> str:
    """
    Generate BibTeX citations for all papers in the library.
    """
    papers = papers_library.get_all_papers()
    
    if not papers:
        return "% No papers in library"
    
    bibtex_entries = []
    for paper in papers:
        arxiv_id = paper.get("arxiv_id", "")
        if arxiv_id:
            bibtex_entries.append(generate_bibtex(arxiv_id))
    
    return "\n\n".join(bibtex_entries)
