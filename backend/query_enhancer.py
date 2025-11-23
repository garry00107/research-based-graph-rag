from typing import List
from llama_index.llms.nvidia import NVIDIA
from config import settings

class QueryEnhancer:
    """Enhance user queries for better retrieval"""
    
    def __init__(self):
        self.llm = NVIDIA(
            model="meta/llama-3.2-3b-instruct",
            api_key=settings.nvidia_api_key
        )
    
    def rewrite_query(self, query: str) -> str:
        """
        Rewrite user query to be more specific and retrieval-friendly.
        """
        prompt = f"""You are a research assistant helping to improve search queries for academic papers.

Original query: "{query}"

Rewrite this query to be more specific and effective for searching research papers. 
Focus on:
- Using technical/academic terminology
- Being more specific about the research topic
- Removing conversational filler words
- Keeping it concise (1-2 sentences max)

Rewritten query:"""

        response = self.llm.complete(prompt)
        rewritten = str(response).strip()
        
        # Fallback to original if rewriting fails
        if not rewritten or len(rewritten) < 5:
            return query
            
        return rewritten
    
    def generate_multi_queries(self, query: str, num_queries: int = 3) -> List[str]:
        """
        Generate multiple variations of the query for better coverage.
        """
        prompt = f"""You are a research assistant helping to search academic papers.

Original query: "{query}"

Generate {num_queries} different variations of this query that would help find relevant research papers.
Each variation should approach the topic from a slightly different angle or use different terminology.

Return ONLY the queries, one per line, without numbering or explanations.

Variations:"""

        response = self.llm.complete(prompt)
        variations = str(response).strip().split('\n')
        
        # Clean up variations
        queries = [query]  # Always include original
        for var in variations:
            cleaned = var.strip().lstrip('123456789.-) ')
            if cleaned and len(cleaned) > 5:
                queries.append(cleaned)
        
        return queries[:num_queries + 1]  # Return original + variations
    
    def classify_intent(self, query: str) -> str:
        """
        Classify the query intent to help with retrieval strategy.
        Returns: 'factual', 'comparative', 'exploratory', 'methodological'
        """
        prompt = f"""Classify the following research query into ONE category:

Query: "{query}"

Categories:
- factual: Asking for specific facts, definitions, or explanations
- comparative: Comparing different approaches, methods, or papers
- exploratory: Broad exploration of a topic or field
- methodological: Asking about how to do something or implement a technique

Return ONLY the category name, nothing else.

Category:"""

        response = self.llm.complete(prompt)
        intent = str(response).strip().lower()
        
        # Validate intent
        valid_intents = ['factual', 'comparative', 'exploratory', 'methodological']
        if intent in valid_intents:
            return intent
        
        return 'factual'  # Default fallback

# Global instance
query_enhancer = QueryEnhancer()
