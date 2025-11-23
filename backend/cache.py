import redis
import pickle
import hashlib
from typing import Optional, List, Any
from config import settings

class CacheManager:
    def __init__(self):
        self.enabled = settings.redis_enabled
        self.client = None
        if self.enabled:
            try:
                self.client = redis.from_url(
                    settings.redis_url,
                    decode_responses=False,
                    socket_connect_timeout=2
                )
                self.client.ping()
                print("✓ Redis cache connected")
            except Exception as e:
                print(f"⚠ Redis connection failed: {e}. Caching disabled.")
                self.enabled = False
    
    def _make_key(self, prefix: str, data: str) -> str:
        """Generate cache key from data hash"""
        hash_obj = hashlib.md5(data.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text"""
        if not self.enabled:
            return None
        
        try:
            key = self._make_key("emb", text)
            cached = self.client.get(key)
            if cached:
                return pickle.loads(cached)
        except Exception as e:
            print(f"Cache get error: {e}")
        return None
    
    def set_embedding(self, text: str, embedding: List[float], ttl: int = 86400):
        """Cache embedding with TTL (default 24h)"""
        if not self.enabled:
            return
        
        try:
            key = self._make_key("emb", text)
            self.client.setex(key, ttl, pickle.dumps(embedding))
        except Exception as e:
            print(f"Cache set error: {e}")
    
    def get_query_result(self, query: str) -> Optional[Any]:
        """Get cached query result"""
        if not self.enabled:
            return None
        
        try:
            key = self._make_key("query", query)
            cached = self.client.get(key)
            if cached:
                return pickle.loads(cached)
        except Exception as e:
            print(f"Cache get error: {e}")
        return None
    
    def set_query_result(self, query: str, result: Any, ttl: int = 3600):
        """Cache query result with TTL (default 1h)"""
        if not self.enabled:
            return
        
        try:
            key = self._make_key("query", query)
            self.client.setex(key, ttl, pickle.dumps(result))
        except Exception as e:
            print(f"Cache set error: {e}")
    
    def clear_all(self):
        """Clear all cache"""
        if not self.enabled:
            return
        
        try:
            self.client.flushdb()
            print("✓ Cache cleared")
        except Exception as e:
            print(f"Cache clear error: {e}")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = self.client.info()
            return {
                "enabled": True,
                "keys": self.client.dbsize(),
                "memory_used": info.get("used_memory_human", "N/A"),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            return {"enabled": True, "error": str(e)}

# Global cache instance
cache = CacheManager()
