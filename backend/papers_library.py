from typing import List, Dict, Optional
from datetime import datetime
import json
import os
from cache import cache

class PapersLibrary:
    def __init__(self):
        self.cache = cache
        self.papers_key = "papers:library"
        self.papers_file = "data/papers_metadata.json"
    
    def _load_from_file(self) -> List[Dict]:
        """Load papers metadata from file"""
        if os.path.exists(self.papers_file):
            try:
                with open(self.papers_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading papers metadata: {e}")
        return []
    
    def _save_to_file(self, papers: List[Dict]):
        """Save papers metadata to file"""
        try:
            os.makedirs(os.path.dirname(self.papers_file), exist_ok=True)
            with open(self.papers_file, 'w') as f:
                json.dump(papers, f, indent=2)
        except Exception as e:
            print(f"Error saving papers metadata: {e}")
    
    def add_paper(self, arxiv_id: str, title: str, authors: List[str], 
                  summary: str, pages: int):
        """Add a paper to the library"""
        papers = self.get_all_papers()
        
        # Check if already exists
        for paper in papers:
            if paper['arxiv_id'] == arxiv_id:
                # Update existing
                paper['updated_at'] = datetime.utcnow().isoformat()
                paper['pages'] = pages
                self._save_to_file(papers)
                return
        
        # Add new paper
        paper = {
            'arxiv_id': arxiv_id,
            'title': title,
            'authors': authors,
            'summary': summary,
            'pages': pages,
            'ingested_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        papers.append(paper)
        self._save_to_file(papers)
        
        # Cache it
        if self.cache.enabled:
            try:
                self.cache.client.setex(
                    self.papers_key,
                    86400,  # 24 hours
                    json.dumps(papers)
                )
            except Exception as e:
                print(f"Error caching papers: {e}")
    
    def get_all_papers(self) -> List[Dict]:
        """Get all ingested papers"""
        # Try cache first
        if self.cache.enabled:
            try:
                cached = self.cache.client.get(self.papers_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                print(f"Error loading from cache: {e}")
        
        # Load from file
        return self._load_from_file()
    
    def get_paper(self, arxiv_id: str) -> Optional[Dict]:
        """Get a specific paper"""
        papers = self.get_all_papers()
        for paper in papers:
            if paper['arxiv_id'] == arxiv_id:
                return paper
        return None
    
    def delete_paper(self, arxiv_id: str) -> bool:
        """Remove a paper from the library"""
        papers = self.get_all_papers()
        filtered = [p for p in papers if p['arxiv_id'] != arxiv_id]
        
        if len(filtered) < len(papers):
            self._save_to_file(filtered)
            
            # Update cache
            if self.cache.enabled:
                try:
                    self.cache.client.setex(
                        self.papers_key,
                        86400,
                        json.dumps(filtered)
                    )
                except Exception as e:
                    print(f"Error updating cache: {e}")
            
            return True
        return False
    
    def search_papers(self, query: str) -> List[Dict]:
        """Search papers by title, authors, or summary"""
        papers = self.get_all_papers()
        query_lower = query.lower()
        
        results = []
        for paper in papers:
            if (query_lower in paper['title'].lower() or
                query_lower in paper['summary'].lower() or
                any(query_lower in author.lower() for author in paper['authors'])):
                results.append(paper)
        
        return results
    
    def get_stats(self) -> Dict:
        """Get library statistics"""
        papers = self.get_all_papers()
        total_pages = sum(p.get('pages', 0) for p in papers)
        
        return {
            'total_papers': len(papers),
            'total_pages': total_pages,
            'oldest': papers[0]['ingested_at'] if papers else None,
            'newest': papers[-1]['ingested_at'] if papers else None
        }

# Global instance
papers_library = PapersLibrary()
