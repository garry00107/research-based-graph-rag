from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ingestion import download_paper, load_documents
from rag_engine import RAGEngine
import os

app = FastAPI(title="Graph RAG Agent")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG Engine
# We initialize it lazily or at startup. 
# It might take time if loading large index.
rag = RAGEngine()

class IngestRequest(BaseModel):
    arxiv_id: str

class ChatRequest(BaseModel):
    message: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest")
def ingest_paper(request: IngestRequest):
    try:
        print(f"Ingesting {request.arxiv_id}...")
        path = download_paper(request.arxiv_id)
        documents = load_documents(path)
        rag.add_documents(documents)
        return {"status": "success", "message": f"Ingested {request.arxiv_id}", "pages": len(documents)}
    except Exception as e:
        print(f"Error ingesting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat(request: ChatRequest):
    try:
        response = rag.query(request.message)
        
        # Extract citations
        citations = []
        if hasattr(response, 'source_nodes'):
            for node in response.source_nodes:
                citations.append({
                    "text": node.node.get_text()[:200] + "...", # Truncate for display
                    "score": node.score,
                    "metadata": node.node.metadata
                })
        
        return {
            "response": str(response),
            "citations": citations
        }
    except Exception as e:
        print(f"Error chatting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
