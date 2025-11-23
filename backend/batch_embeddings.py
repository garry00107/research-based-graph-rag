from typing import List
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from config import settings
from cache import cache

class BatchEmbeddingWrapper:
    """Wrapper around NVIDIA embedding model with batching and caching"""
    
    def __init__(self, embed_model: NVIDIAEmbedding):
        self.embed_model = embed_model
        self.batch_size = settings.batch_size
        self.cache = cache
    
    def get_text_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text with caching"""
        # Check cache first
        cached = self.cache.get_embedding(text)
        if cached:
            return cached
        
        # Get from API
        embedding = self.embed_model.get_text_embedding(text)
        
        # Cache it
        self.cache.set_embedding(text, embedding)
        return embedding
    
    def get_text_embedding_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts with batching and caching"""
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache for each text
        for i, text in enumerate(texts):
            cached = self.cache.get_embedding(text)
            if cached:
                embeddings.append(cached)
            else:
                embeddings.append(None)  # Placeholder
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Batch process uncached texts
        if uncached_texts:
            print(f"✓ Fetching {len(uncached_texts)} embeddings (batch size: {self.batch_size})")
            
            # Process in batches
            for i in range(0, len(uncached_texts), self.batch_size):
                batch = uncached_texts[i:i + self.batch_size]
                batch_embeddings = self.embed_model.get_text_embedding_batch(batch)
                
                # Cache and store results
                for text, embedding in zip(batch, batch_embeddings):
                    self.cache.set_embedding(text, embedding)
                
                # Fill in the placeholders
                for j, embedding in enumerate(batch_embeddings):
                    original_idx = uncached_indices[i + j]
                    embeddings[original_idx] = embedding
        
        return embeddings
