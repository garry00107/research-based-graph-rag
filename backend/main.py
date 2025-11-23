from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ingestion import download_paper, load_documents, search_papers
from rag_engine import RAGEngine
from cache import cache
from celery.result import AsyncResult
from celery_tasks import ingest_paper_task, ingest_batch_task
from chat_history import chat_history
from papers_library import papers_library
import os
import json
import asyncio

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

class BatchIngestRequest(BaseModel):
    arxiv_ids: list[str]

class SearchRequest(BaseModel):
    query: str
    max_results: int = 10
    category: str = None
    year: str = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: str = "default"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/cache/stats")
def cache_stats():
    """Get cache statistics"""
    stats = cache.get_stats()
    rag_stats = rag.get_stats()
    return {
        "cache": stats,
        "index": rag_stats
    }

@app.post("/search")
def search(request: SearchRequest):
    try:
        print(f"Searching for: {request.query}")
        results = search_papers(
            request.query, 
            max_results=request.max_results,
            category=request.category,
            year=request.year
        )
        return {"status": "success", "results": results}
    except Exception as e:
        print(f"Error searching: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
def ingest_paper(request: IngestRequest):
    try:
        print(f"Ingesting {request.arxiv_id}...")
        
        # Search for paper metadata
        search_results = search_papers(request.arxiv_id, max_results=1)
        paper_metadata = search_results[0] if search_results else None
        
        path = download_paper(request.arxiv_id)
        documents = load_documents(path)
        rag.add_documents(documents)
        
        # Add to library
        if paper_metadata:
            papers_library.add_paper(
                arxiv_id=request.arxiv_id,
                title=paper_metadata.get('title', 'Unknown'),
                authors=paper_metadata.get('authors', []),
                summary=paper_metadata.get('summary', ''),
                pages=len(documents)
            )
        
        return {"status": "success", "message": f"Ingested {request.arxiv_id}", "pages": len(documents)}
    except Exception as e:
        print(f"Error ingesting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest-batch")
def ingest_batch(request: BatchIngestRequest):
    try:
        results = []
        total_pages = 0
        for arxiv_id in request.arxiv_ids:
            print(f"Ingesting {arxiv_id}...")
            
            # Search for paper metadata
            search_results = search_papers(arxiv_id, max_results=1)
            paper_metadata = search_results[0] if search_results else None
            
            path = download_paper(arxiv_id)
            documents = load_documents(path)
            rag.add_documents(documents)
            total_pages += len(documents)
            results.append({"arxiv_id": arxiv_id, "pages": len(documents)})
            
            # Add to library
            if paper_metadata:
                papers_library.add_paper(
                    arxiv_id=arxiv_id,
                    title=paper_metadata.get('title', 'Unknown'),
                    authors=paper_metadata.get('authors', []),
                    summary=paper_metadata.get('summary', ''),
                    pages=len(documents)
                )
        
        return {"status": "success", "message": f"Ingested {len(request.arxiv_ids)} papers", "total_pages": total_pages, "results": results}
    except Exception as e:
        print(f"Error batch ingesting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest-async")
def ingest_async(request: IngestRequest):
    """Start async ingestion task"""
    try:
        task = ingest_paper_task.delay(request.arxiv_id)
        return {
            "status": "queued",
            "task_id": task.id,
            "message": f"Ingestion task started for {request.arxiv_id}"
        }
    except Exception as e:
        print(f"Error starting async ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest-batch-async")
def ingest_batch_async(request: BatchIngestRequest):
    """Start async batch ingestion task"""
    try:
        task = ingest_batch_task.delay(request.arxiv_ids)
        return {
            "status": "queued",
            "task_id": task.id,
            "message": f"Batch ingestion task started for {len(request.arxiv_ids)} papers"
        }
    except Exception as e:
        print(f"Error starting async batch ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task-status/{task_id}")
def get_task_status(task_id: str):
    """Get status of async task"""
    try:
        task = AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'status': 'Task is waiting to be processed',
                'progress': 0
            }
        elif task.state == 'PROGRESS':
            response = {
                'state': task.state,
                'status': task.info.get('status', ''),
                'progress': task.info.get('progress', 0)
            }
        elif task.state == 'SUCCESS':
            response = {
                'state': task.state,
                'status': 'Task completed successfully',
                'progress': 100,
                'result': task.result
            }
        elif task.state == 'FAILURE':
            response = {
                'state': task.state,
                'status': str(task.info),
                'progress': 0,
                'error': str(task.info)
            }
        else:
            response = {
                'state': task.state,
                'status': str(task.info),
                'progress': 0
            }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat(request: ChatRequest):
    try:
        # Add user message to history
        chat_history.add_message(request.conversation_id, "user", request.message)
        
        # Get response
        response = rag.query(request.message)
        
        # Add assistant response to history
        chat_history.add_message(request.conversation_id, "assistant", str(response))
        
        # Extract citations
        citations = []
        if hasattr(response, 'source_nodes'):
            for node in response.source_nodes:
                citations.append({
                    "text": node.node.get_text()[:200] + "...",
                    "score": node.score,
                    "metadata": node.node.metadata
                })
        
        return {
            "response": str(response),
            "citations": citations,
            "conversation_id": request.conversation_id
        }
    except Exception as e:
        print(f"Error chatting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat-stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint with SSE"""
    async def generate():
        try:
            # Add user message to history
            chat_history.add_message(request.conversation_id, "user", request.message)
            
            # Get response
            response = rag.query(request.message)
            response_text = str(response)
            
            # Stream response word by word
            words = response_text.split()
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"
                await asyncio.sleep(0.05)  # Small delay for streaming effect
            
            # Add assistant response to history
            chat_history.add_message(request.conversation_id, "assistant", response_text)
            
            # Extract citations
            citations = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    citations.append({
                        "text": node.node.get_text()[:200] + "...",
                        "score": node.score,
                        "metadata": node.node.metadata
                    })
            
            # Send final message with citations
            yield f"data: {json.dumps({'done': True, 'citations': citations, 'conversation_id': request.conversation_id})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.get("/chat-history/{conversation_id}")
def get_chat_history(conversation_id: str):
    """Get conversation history"""
    try:
        history = chat_history.get_history(conversation_id)
        return {"conversation_id": conversation_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat-history/{conversation_id}")
def clear_chat_history(conversation_id: str):
    """Clear conversation history"""
    try:
        chat_history.clear_history(conversation_id)
        return {"status": "success", "message": f"Cleared history for {conversation_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/papers")
def get_papers():
    """Get all ingested papers"""
    try:
        papers = papers_library.get_all_papers()
        stats = papers_library.get_stats()
        return {"papers": papers, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/papers/{arxiv_id}")
def get_paper(arxiv_id: str):
    """Get a specific paper"""
    try:
        paper = papers_library.get_paper(arxiv_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        return paper
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/papers/{arxiv_id}")
def delete_paper(arxiv_id: str):
    """Delete a paper from library (note: does not remove from vector store)"""
    try:
        success = papers_library.delete_paper(arxiv_id)
        if not success:
            raise HTTPException(status_code=404, detail="Paper not found")
        return {"status": "success", "message": f"Deleted {arxiv_id} from library"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/papers/search/{query}")
def search_library(query: str):
    """Search papers in library"""
    try:
        results = papers_library.search_papers(query)
        return {"query": query, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
