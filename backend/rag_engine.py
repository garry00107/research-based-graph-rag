import os
import shutil
from typing import List, Optional
from llama_index.core import (
    VectorStoreIndex, 
    Settings, 
    StorageContext, 
    load_index_from_storage,
    Document
)
from llama_index.llms.nvidia import NVIDIA
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from dotenv import load_dotenv

load_dotenv()

class RAGEngine:
    def __init__(self, persist_dir: str = "./storage"):
        self.persist_dir = persist_dir
        self._setup_models()
        self.index = self._load_index()

    def _setup_models(self):
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            print("Warning: NVIDIA_API_KEY not found. RAG functionality will fail.")
            
        # Initialize NVIDIA models
        # Using specific models as requested
        self.llm = NVIDIA(model="meta/llama-3.2-3b-instruct", api_key=api_key)
        self.embed_model = NVIDIAEmbedding(model="nvidia/nv-embedqa-e5-v5", truncate="END", api_key=api_key)
        
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model

    def _load_index(self) -> Optional[VectorStoreIndex]:
        if os.path.exists(self.persist_dir):
            try:
                print("Loading index from storage...")
                storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
                return load_index_from_storage(storage_context)
            except Exception as e:
                print(f"Failed to load index: {e}")
                return None
        return None

    def add_documents(self, documents: List[Document]):
        print(f"Adding {len(documents)} documents to index...")
        
        if self.index is None:
            print("Creating new VectorStoreIndex...")
            self.index = VectorStoreIndex.from_documents(
                documents,
                show_progress=True
            )
        else:
            print("Updating existing index...")
            for doc in documents:
                self.index.insert(doc)
        
        # Persist
        os.makedirs(self.persist_dir, exist_ok=True)
        self.index.storage_context.persist(persist_dir=self.persist_dir)
        print("Index persisted.")

    def query(self, query_text: str):
        if self.index is None:
            return "Index is empty. Please ingest some papers first."
            
        # Create a query engine
        # We can customize this to use the graph capabilities
        query_engine = self.index.as_query_engine(
            include_text=True,
            similarity_top_k=5
        )
        response = query_engine.query(query_text)
        return response

    def clear_index(self):
        if os.path.exists(self.persist_dir):
            shutil.rmtree(self.persist_dir)
        self.index = None
        print("Index cleared.")
