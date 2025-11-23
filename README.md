# Research Paper Assistant 🤖📚

An AI-powered research assistant that helps you find, read, and understand ArXiv research papers. Built with **FastAPI**, **LlamaIndex**, **NVIDIA NIM**, and **Next.js**.

##  Features

###  Smart Paper Search
- Search ArXiv papers by title or keywords
- View results with titles, authors, and abstracts
- Multi-select papers for batch ingestion

###  AI-Powered Q&A
- Ask questions about ingested papers
- Get answers with source citations
- Powered by NVIDIA's LLM (`meta/llama-3.2-3b-instruct`)

###  Vector-Based Retrieval
- Fast semantic search using embeddings (`nvidia/nv-embedqa-e5-v5`)
- VectorStoreIndex for efficient document retrieval
- Persistent storage for ingested papers

###  Modern UI
- Clean chat interface with streaming responses
- Citation cards showing source text and relevance scores
- Responsive design with TailwindCSS + Shadcn/UI

##  Tech Stack

- **Backend**: FastAPI, Celery, Redis
- **AI Engine**: LlamaIndex, NVIDIA NIM (Llama 3.2 3B, NV-EmbedQA)
- **Vector Store**: ChromaDB
- **Frontend**: Next.js 14, TailwindCSS, Shadcn/UI
- **Infrastructure**: Docker Compose

## 🏁 Quick Start

### Prerequisites
- Docker & Docker Compose
- NVIDIA API Key (from [build.nvidia.com](https://build.nvidia.com))

##  Prerequisites

# Create .env file
cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY
```

##  Setup

## 👨‍💻 Local Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start Redis (Required)
redis-server

# Start Celery Worker (for async ingestion)
./start-celery.sh

# Start Backend
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs on `http://localhost:3000`

##  Usage

### Ingesting Papers

1. Open the frontend at `http://localhost:3000`
2. Click the **Settings** icon (⚙️) to open the Admin Panel
3. **Search** for papers by entering keywords (e.g., "transformer", "attention mechanism")
4. **Select** one or more papers by clicking on the cards
5. Click **"Ingest Selected"** to add them to the knowledge base
6. Wait for ingestion to complete (~30s per paper)

## 📖 Usage Guide

1. **Search Papers**: Click the ⚙️ icon to open the Admin Panel. Search for papers (e.g., "RAG agents").
2. **Ingest**: Select papers and click "Ingest Selected".
3. **Chat**: Ask questions like "What are the key findings of these papers?".
4. **Library**: Click the 📚 icon to view your ingested papers.
5. **History**: Click the 🕐 icon to view past conversations.

##  Project Structure

```
├── backend/
│   ├── main.py           # FastAPI endpoints
│   ├── rag_engine.py     # RAG logic with ChromaDB
│   ├── ingestion.py      # ArXiv search & PDF processing
│   ├── cache.py          # Redis caching layer
│   ├── celery_app.py     # Async task configuration
│   ├── papers_library.py # Library management
│   └── chat_history.py   # Conversation memory
├── frontend/
│   ├── app/              # Next.js pages
│   ├── components/       # React components (Chat, Library, History)
│   └── lib/api.ts        # API client
└── docker-compose.yml    # Deployment config
```

##  API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/search` | POST | Search ArXiv papers by query |
| `/ingest` | POST | Ingest a single paper by ArXiv ID |
| `/ingest-batch` | POST | Ingest multiple papers |
| `/chat` | POST | Ask a question about ingested papers |

## � Example Queries

After ingesting "Attention is All You Need" (ArXiv ID: `1706.03762`):

- "What is the transformer architecture?"
- "Explain the attention mechanism"
- "What are the key innovations in this paper?"
- "How does multi-head attention work?"

##  Troubleshooting

**Ingestion is slow:**
- This is normal! Each paper requires multiple LLM/embedding API calls
- Expect ~30-60 seconds per paper depending on length
- See [Performance Notes](#-performance-notes) below

**Port already in use:**
```bash
# Backend (port 8002)
lsof -ti:8002 | xargs kill -9

# Frontend (port 3000)
lsof -ti:3000 | xargs kill -9
```

**NVIDIA API errors:**
- Verify your API key in `backend/.env`
- Check you have access to the models at [build.nvidia.com](https://build.nvidia.com)

##  Performance Notes

**Why is ingestion slow?**
- PDF parsing: ~1-2s
- Embedding generation: ~0.1-0.3s per chunk (network-bound)
- LLM calls for graph extraction: ~0.5-1s per page
- NVIDIA API rate limiting causes retries

**Future improvements:**
- Add Chroma/FAISS for faster vector storage
- Implement async ingestion queue (Celery/RQ)
- Batch embedding calls to reduce latency
- Cache downloaded PDFs

##  Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Commit: `git commit -m "feat: your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

##  License

MIT

##  Acknowledgments

- [LlamaIndex](https://www.llamaindex.ai/) for the RAG framework
- [NVIDIA NIM](https://build.nvidia.com) for LLM and embedding models
- [ArXiv](https://arxiv.org/) for the research paper API
