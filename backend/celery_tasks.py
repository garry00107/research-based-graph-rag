from celery_app import celery_app
from ingestion import download_paper, load_documents
from rag_engine import RAGEngine
from typing import List

# Initialize RAG engine for tasks
rag = None

def get_rag_engine():
    """Lazy initialization of RAG engine"""
    global rag
    if rag is None:
        rag = RAGEngine()
    return rag

@celery_app.task(bind=True, name="ingest_paper")
def ingest_paper_task(self, arxiv_id: str):
    """Background task to ingest a single paper"""
    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': f'Downloading paper {arxiv_id}...', 'progress': 10}
        )
        
        # Download paper
        path = download_paper(arxiv_id)
        
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Extracting text from PDF...', 'progress': 30}
        )
        
        # Load documents
        documents = load_documents(path)
        
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Generating embeddings...', 'progress': 50}
        )
        
        # Add to index
        rag_engine = get_rag_engine()
        rag_engine.add_documents(documents)
        
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Finalizing...', 'progress': 90}
        )
        
        return {
            'status': 'success',
            'arxiv_id': arxiv_id,
            'pages': len(documents),
            'message': f'Successfully ingested {arxiv_id}'
        }
    
    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'status': f'Error: {str(e)}', 'progress': 0}
        )
        raise

@celery_app.task(bind=True, name="ingest_batch")
def ingest_batch_task(self, arxiv_ids: List[str]):
    """Background task to ingest multiple papers"""
    try:
        results = []
        total = len(arxiv_ids)
        
        for i, arxiv_id in enumerate(arxiv_ids):
            progress = int((i / total) * 100)
            self.update_state(
                state='PROGRESS',
                meta={
                    'status': f'Processing {i+1}/{total}: {arxiv_id}',
                    'progress': progress,
                    'current': i + 1,
                    'total': total
                }
            )
            
            # Download and process
            path = download_paper(arxiv_id)
            documents = load_documents(path)
            
            rag_engine = get_rag_engine()
            rag_engine.add_documents(documents)
            
            results.append({
                'arxiv_id': arxiv_id,
                'pages': len(documents),
                'status': 'success'
            })
        
        return {
            'status': 'success',
            'total_papers': total,
            'results': results,
            'message': f'Successfully ingested {total} papers'
        }
    
    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={'status': f'Error: {str(e)}', 'progress': 0}
        )
        raise
