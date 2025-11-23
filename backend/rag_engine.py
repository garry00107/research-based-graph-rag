import os
import shutil
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from llama_index.core import (
    VectorStoreIndex, 
    Settings, 
    StorageContext,
    Document
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.nvidia import NVIDIA
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from config import settings
from cache import cache

class RAGEngine:
    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.vector_store = None
        self.cache = cache
        self._setup_models()
        self._setup_vector_store()
        self.index = self._load_or_create_index()

    def _setup_models(self):
        """Initialize NVIDIA LLM and embedding models"""
        api_key = settings.nvidia_api_key
        if not api_key:
            raise ValueError("NVIDIA_API_KEY not found in environment variables")
            
        # Initialize NVIDIA models
        self.llm = NVIDIA(model="meta/llama-3.2-3b-instruct", api_key=api_key)
        self.embed_model = NVIDIAEmbedding(
            model="nvidia/nv-embedqa-e5-v5", 
            truncate="END", 
            api_key=api_key
        )
        
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        print("✓ NVIDIA models initialized")

    def _setup_vector_store(self):
        """Initialize ChromaDB vector store"""
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        
        # Initialize Chroma client with persistence
        self.chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection("research_papers")
            print(f"✓ Loaded existing collection with {self.collection.count()} documents")
        except:
            self.collection = self.chroma_client.create_collection(
                name="research_papers",
                metadata={"description": "Research papers vector store"}
            )
            print("✓ Created new collection")
        
        # Create LlamaIndex vector store wrapper
        self.vector_store = ChromaVectorStore(chroma_collection=self.collection)

    def _load_or_create_index(self) -> Optional[VectorStoreIndex]:
        """Load existing index or create new one"""
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
        if self.collection.count() > 0:
            print("✓ Loading index from ChromaDB...")
            return VectorStoreIndex.from_vector_store(
                self.vector_store,
                storage_context=storage_context
            )
        else:
            print("✓ Creating new empty index")
            return VectorStoreIndex.from_documents(
                [],
                storage_context=storage_context
            )

    def add_documents(self, documents: List[Document]):
        """Add documents to the index"""
        print(f"Adding {len(documents)} documents to index...")
        
        if self.index is None:
            storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
            self.index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context,
                show_progress=True
            )
        else:
            for doc in documents:
                self.index.insert(doc)
        
        print(f"✓ Index now contains {self.collection.count()} document chunks")

    def query(self, query_text: str, top_k: int = 5):
        """Query the index with caching"""
        if self.index is None or self.collection.count() == 0:
            return "Index is empty. Please ingest some papers first."
        
        # Check cache first
        cached_result = self.cache.get_query_result(query_text)
        if cached_result:
            print("✓ Cache hit for query")
            return cached_result
            
        query_engine = self.index.as_query_engine(
            similarity_top_k=top_k,
            response_mode="compact"
        )
        response = query_engine.query(query_text)
        
        # Cache the result
        self.cache.set_query_result(query_text, response)
        return response

    def get_stats(self):
        """Get index statistics"""
        return {
            "total_chunks": self.collection.count(),
            "collection_name": self.collection.name,
            "persist_dir": settings.chroma_persist_dir
        }

    def clear_index(self):
        """Clear all data from the index"""
        if self.collection:
            self.chroma_client.delete_collection("research_papers")
            print("✓ Collection deleted")
            self._setup_vector_store()
            self.index = self._load_or_create_index()
            print("✓ Index cleared and recreated")
