# Research Paper Assistant

AI-powered research assistant using graph-based retrieval for ArXiv papers. Built with FastAPI, LlamaIndex, NVIDIA models, and Next.js.

## ✨ Features

### 🔍 Smart Paper Search
- Search ArXiv papers by title or keywords
- View results with titles, authors, and abstracts
- Multi-select papers for batch ingestion

### 🤖 AI-Powered Q&A
- Ask questions about ingested papers
- Get answers with source citations
- Powered by NVIDIA's LLM (`meta/llama-3.2-3b-instruct`)

### 📊 Vector-Based Retrieval
- Fast semantic search using embeddings (`nvidia/nv-embedqa-e5-v5`)
- VectorStoreIndex for efficient document retrieval
- Persistent storage for ingested papers

### 💬 Modern UI
- Clean chat interface with streaming responses
- Citation cards showing source text and relevance scores
- Responsive design with TailwindCSS + Shadcn/UI

## 🛠️ Tech Stack

**Backend:**
- FastAPI
- LlamaIndex
- NVIDIA NIM (LLM + Embeddings)
- ArXiv API

**Frontend:**
- Next.js 14 (App Router)
- TypeScript
- TailwindCSS
- Shadcn/UI
- Zustand (state management)

## 📋 Prerequisites

- Python 3.10+
- Node.js 18+
- NVIDIA NIM API Key ([Get one here](https://build.nvidia.com))

## 🚀 Setup

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Set your API Key:**
```bash
cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY
```

**Start the server:**
```bash
python main.py
```
Server runs on `http://127.0.0.1:8002`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```
Frontend runs on `http://localhost:3000`

## 📖 Usage

### Ingesting Papers

1. Open the frontend at `http://localhost:3000`
2. Click the **Settings** icon (⚙️) to open the Admin Panel
3. **Search** for papers by entering keywords (e.g., "transformer", "attention mechanism")
4. **Select** one or more papers by clicking on the cards
5. Click **"Ingest Selected"** to add them to the knowledge base
6. Wait for ingestion to complete (~30s per paper)

### Asking Questions

1. Type your question in the chat input
2. Press Enter or click Send
3. View the AI's response with citations
4. Click on citation cards to see source text and relevance scores

## 📁 Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI app with endpoints
│   ├── rag_engine.py        # RAG logic with LlamaIndex
│   ├── ingestion.py         # ArXiv search & PDF processing
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # API keys (not in git)
├── frontend/
│   ├── app/                 # Next.js pages
│   ├── components/          # React components
│   │   ├── chat-interface.tsx
│   │   └── admin-panel.tsx
│   ├── lib/
│   │   ├── api.ts          # Backend API client
│   │   └── store.ts        # Zustand state
│   └── package.json
└── README.md
```

## 🔑 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/search` | POST | Search ArXiv papers by query |
| `/ingest` | POST | Ingest a single paper by ArXiv ID |
| `/ingest-batch` | POST | Ingest multiple papers |
| `/chat` | POST | Ask a question about ingested papers |

## 🎯 Example Queries

After ingesting "Attention is All You Need" (ArXiv ID: `1706.03762`):

- "What is the transformer architecture?"
- "Explain the attention mechanism"
- "What are the key innovations in this paper?"
- "How does multi-head attention work?"

## 🐛 Troubleshooting

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

## ⚡ Performance Notes

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

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Commit: `git commit -m "feat: your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

## 📝 License

MIT

## 🙏 Acknowledgments

- [LlamaIndex](https://www.llamaindex.ai/) for the RAG framework
- [NVIDIA NIM](https://build.nvidia.com) for LLM and embedding models
- [ArXiv](https://arxiv.org/) for the research paper API
