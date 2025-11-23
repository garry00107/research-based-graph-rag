from typing import List, Dict
from papers_library import papers_library
from rag_engine import RAGEngine
import numpy as np

class PaperRecommender:
    """Recommend related papers based on queries and paper content"""
    
    def __init__(self, rag_engine: RAGEngine):
        self.rag = rag_engine
        self.embed_model = rag_engine.embed_model
    
    def recommend_from_query(self, query: str, top_k: int = 5, exclude_ids: List[str] = None) -> List[Dict]:
        """
        Recommend papers related to a query.
        Returns papers from the library that are most relevant to the query.
        """
        if exclude_ids is None:
            exclude_ids = []
        
        # Get all papers from library
        all_papers = papers_library.get_all_papers()
        if not all_papers:
            return []
        
        # Get query embedding
        query_embedding = self.embed_model.get_text_embedding(query)
        
        # Calculate similarity for each paper
        paper_scores = []
        for paper in all_papers:
            if paper['arxiv_id'] in exclude_ids:
                continue
            
            # Create paper text from title and summary
            paper_text = f"{paper['title']}. {paper['summary']}"
            paper_embedding = self.embed_model.get_text_embedding(paper_text)
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, paper_embedding)
            
            paper_scores.append({
                'arxiv_id': paper['arxiv_id'],
                'title': paper['title'],
                'authors': paper['authors'],
                'summary': paper['summary'][:200] + '...',
                'score': similarity
            })
        
        # Sort by score and return top_k
        paper_scores.sort(key=lambda x: x['score'], reverse=True)
        return paper_scores[:top_k]
    
    def recommend_similar_papers(self, arxiv_id: str, top_k: int = 5) -> List[Dict]:
        """
        Recommend papers similar to a given paper.
        """
        # Get the source paper
        source_paper = papers_library.get_paper(arxiv_id)
        if not source_paper:
            return []
        
        # Use the paper's title and summary as query
        query = f"{source_paper['title']}. {source_paper['summary']}"
        
        # Get recommendations, excluding the source paper
        return self.recommend_from_query(query, top_k=top_k, exclude_ids=[arxiv_id])
    
    def recommend_from_citations(self, arxiv_id: str, top_k: int = 5) -> List[Dict]:
        """
        Recommend papers based on what was retrieved for this paper.
        Uses the vector store to find papers that appear in similar contexts.
        """
        source_paper = papers_library.get_paper(arxiv_id)
        if not source_paper:
            return []
        
        # Query the vector store with the paper's content
        query = f"{source_paper['title']}"
        
        try:
            # Get similar chunks from vector store
            response = self.rag.query(query, top_k=top_k * 2, use_enhancement=False)
            
            if not hasattr(response, 'source_nodes'):
                return []
            
            # Extract unique papers from source nodes
            seen_papers = set([arxiv_id])
            recommendations = []
            
            for node in response.source_nodes:
                # Extract arxiv_id from metadata
                file_name = node.node.metadata.get('file_name', '') or node.node.metadata.get('source', '')
                paper_arxiv_id = file_name.replace('.pdf', '').split('/')[-1]
                
                # Remove version numbers
                import re
                paper_arxiv_id = re.sub(r'v\d+$', '', paper_arxiv_id)
                
                if paper_arxiv_id and paper_arxiv_id not in seen_papers:
                    seen_papers.add(paper_arxiv_id)
                    
                    # Get full paper details from library
                    paper = papers_library.get_paper(paper_arxiv_id)
                    if paper:
                        recommendations.append({
                            'arxiv_id': paper['arxiv_id'],
                            'title': paper['title'],
                            'authors': paper['authors'],
                            'summary': paper['summary'][:200] + '...',
                            'score': node.score
                        })
                
                if len(recommendations) >= top_k:
                    break
            
            return recommendations
            
        except Exception as e:
            print(f"Error in citation-based recommendations: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))

# Will be initialized in main.py
paper_recommender = None
