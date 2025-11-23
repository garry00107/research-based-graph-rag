from fastapi import FastAPI, HTTPException, Request
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
import time

app = FastAPI(title="Graph RAG Agent")

# Middleware for analytics
@app.middleware("http")
async def track_analytics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Skip health checks and options
    if request.url.path == "/health" or request.method == "OPTIONS":
        return response
        
    if cache.enabled:
        try:
            # Increment total requests
            cache.client.incr("analytics:total_requests")
            
            # Track status codes
            cache.client.hincrby("analytics:status_codes", str(response.status_code), 1)
            
            # Track latency (avg) - simplified moving average or just total time/count
            # For simplicity, let's store total time and count to calc avg on read
            cache.client.incr("analytics:total_latency_ms", int(process_time * 1000))
            
            # Track endpoint usage
            endpoint = f"{request.method} {request.url.path}"
            cache.client.hincrby("analytics:endpoints", endpoint, 1)
            
        except Exception as e:
            print(f"Error tracking analytics: {e}")
            
    return response

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

# Initialize Paper Recommender
from paper_recommender import PaperRecommender
paper_recommender = PaperRecommender(rag)

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

class FeedbackRequest(BaseModel):
    message_id: str
    feedback: str  # "up" or "down"
    conversation_id: str = "default"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/analytics")
def get_analytics():
    """Get usage analytics"""
    if not cache.enabled:
        return {"error": "Redis not enabled"}
        
    try:
        total_requests = int(cache.client.get("analytics:total_requests") or 0)
        total_latency = int(cache.client.get("analytics:total_latency_ms") or 0)
        avg_latency = total_latency / total_requests if total_requests > 0 else 0
        
        status_codes = cache.client.hgetall("analytics:status_codes")
        status_codes = {k.decode(): int(v) for k, v in status_codes.items()}
        
        endpoints = cache.client.hgetall("analytics:endpoints")
        endpoints = {k.decode(): int(v) for k, v in endpoints.items()}
        
        # Get cache stats too
        cache_stats = cache.get_stats()
        
        return {
            "total_requests": total_requests,
            "avg_latency_ms": round(avg_latency, 2),
            "status_codes": status_codes,
            "endpoints": endpoints,
            "cache_stats": cache_stats
        }
    except Exception as e:
        print(f"Error fetching analytics: {e}")
        return {"error": str(e)}

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
            
            # Check if this is a library listing query
            query_lower = request.message.lower()
            list_keywords = ['list', 'show', 'what are', 'tell me', 'display']
            paper_keywords = ['papers', 'documents', 'articles', 'ingested', 'library', 'all papers']
            
            is_list_query = any(kw in query_lower for kw in list_keywords) and any(kw in query_lower for kw in paper_keywords)
            
            if is_list_query:
                # Get papers from library instead of RAG search
                papers = papers_library.get_all_papers()
                
                if not papers:
                    response_text = "No papers have been ingested yet. Use the Admin Panel to add papers to the library."
                else:
                    response_text = f"I have {len(papers)} papers in the library:\n\n"
                    for i, paper in enumerate(papers, 1):
                        authors_str = ", ".join(paper['authors'][:2])
                        if len(paper['authors']) > 2:
                            authors_str += f" et al."
                        response_text += f"{i}. **{paper['title']}**\n   Authors: {authors_str}\n   ArXiv ID: {paper['arxiv_id']}\n\n"
                
                citations = []
            else:
                # Normal RAG query
                response = rag.query(request.message)
                response_text = str(response)
                
                # Extract citations
                citations = []
                if hasattr(response, 'source_nodes'):
                    for node in response.source_nodes:
                        # Extract clean ArXiv ID from metadata
                        file_name = node.node.metadata.get('file_name', '') or node.node.metadata.get('source', '') or node.node.metadata.get('file_path', '')
                        arxiv_id = file_name.replace('.pdf', '')
                        if '/' in arxiv_id:
                            arxiv_id = arxiv_id.split('/')[-1]
                        # Remove version numbers
                        import re
                        arxiv_id = re.sub(r'v\d+$', '', arxiv_id)
                        
                        # Validate ArXiv ID format
                        # Old format: 7 digits or less (e.g., 0503536) - these need category prefix
                        # New format: YYMM.NNNNN (e.g., 1706.03762, 2105.02358)
                        is_valid_arxiv = False
                        if arxiv_id and len(arxiv_id) >= 9 and '.' in arxiv_id:
                            # New format - valid
                            is_valid_arxiv = True
                        elif arxiv_id and len(arxiv_id) <= 7 and arxiv_id.isdigit():
                            # Old format - check if we have it in library with proper ID
                            paper = papers_library.get_paper(arxiv_id)
                            if paper:
                                # Use the library's arxiv_id which might have category
                                arxiv_id = paper['arxiv_id']
                                is_valid_arxiv = True
                            else:
                                # Can't resolve old format ID, don't include link
                                arxiv_id = None
                        
                        citation_metadata = node.node.metadata.copy()
                        citation_metadata['arxiv_id'] = arxiv_id if is_valid_arxiv else None
                        
                        citations.append({
                            "text": node.node.get_text()[:200] + "...",
                            "score": node.score,
                            "metadata": citation_metadata
                        })
            
            # Stream response word by word
            words = response_text.split()
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield f"data: {json.dumps({'token': chunk, 'done': False})}\n\n"
                await asyncio.sleep(0.05)  # Small delay for streaming effect
            
            # Add assistant response to history
            chat_history.add_message(request.conversation_id, "assistant", response_text)
            
            # Send final message with citations
            yield f"data: {json.dumps({'done': True, 'citations': citations, 'conversation_id': request.conversation_id})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/feedback")
def submit_feedback(request: FeedbackRequest):
    """Submit feedback for a chat message"""
    try:
        success = chat_history.add_feedback(
            request.conversation_id, 
            request.message_id, 
            request.feedback
        )
        if not success:
            raise HTTPException(status_code=404, detail="Message not found or cache disabled")
        return {"status": "success", "message": "Feedback recorded"}
    except Exception as e:
        print(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

# Export endpoints
@app.get("/export/chat/{conversation_id}/markdown")
def export_chat_markdown(conversation_id: str):
    """Export chat conversation as Markdown"""
    try:
        from export_utils import generate_markdown
        from fastapi.responses import Response
        
        markdown_content = generate_markdown(conversation_id)
        
        # Return as downloadable file
        return Response(
            content=markdown_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=chat_{conversation_id}.md"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/export/bibtex/all")
def export_all_bibtex():
    """Get BibTeX citations for all papers in library"""
    try:
        from export_utils import generate_bibtex_from_library
        from fastapi.responses import Response
        
        bibtex_content = generate_bibtex_from_library()
        
        # Return as downloadable file
        return Response(
            content=bibtex_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": "attachment; filename=library.bib"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/export/bibtex/{arxiv_id}")
def export_bibtex(arxiv_id: str):
    """Get BibTeX citation for a specific paper"""
    try:
        from export_utils import generate_bibtex
        
        bibtex = generate_bibtex(arxiv_id)
        
        if bibtex.startswith("%"):
            raise HTTPException(status_code=404, detail="Paper not found in library")
        
        return {"arxiv_id": arxiv_id, "bibtex": bibtex}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Recommendation endpoints
@app.get("/recommendations/query")
def get_query_recommendations(query: str, top_k: int = 5):
    """Get paper recommendations based on a query"""
    try:
        recommendations = paper_recommender.recommend_from_query(query, top_k=top_k)
        return {"query": query, "recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommendations/similar/{arxiv_id}")
def get_similar_papers(arxiv_id: str, top_k: int = 5):
    """Get papers similar to a given paper"""
    try:
        recommendations = paper_recommender.recommend_similar_papers(arxiv_id, top_k=top_k)
        return {"arxiv_id": arxiv_id, "recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommendations/citations/{arxiv_id}")
def get_citation_based_recommendations(arxiv_id: str, top_k: int = 5):
    """Get recommendations based on citation context"""
    try:
        recommendations = paper_recommender.recommend_from_citations(arxiv_id, top_k=top_k)
        return {"arxiv_id": arxiv_id, "recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
