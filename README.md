# Research Paper Assistant 🤖📚

An AI-powered research assistant that helps you find, read, and understand ArXiv research papers. Built with **FastAPI**, **LlamaIndex**, **NVIDIA NIM**, and **Next.js**.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

## 🚀 Features

### Core Capabilities
- **🔍 Smart Paper Search**: Search ArXiv by title, author, or keywords.
- **🎯 Advanced Filters**: Filter search results by category (e.g., AI, CV) and publication year.
- **📥 Batch Ingestion**: Select multiple papers and ingest them simultaneously.
- **⚡ Async Processing**: Non-blocking ingestion using Celery background workers.
- **💬 AI Chat**: Ask questions about the papers with citation-backed answers.
- **🌊 Streaming Responses**: Real-time token-by-token responses for a smooth experience.

### Advanced Features
- **💾 Vector Database**: Uses **ChromaDB** for fast, persistent vector storage.
- **🚀 Redis Caching**: Caches embeddings and chat history for performance.
- **📚 Papers Library**: View, manage, and search your ingested papers.
- **🕐 Chat History**: Persists conversation history for context-aware answers.
- **🐳 Docker Support**: Full stack deployment with a single command.

## 🛠️ Tech Stack

- **Backend**: FastAPI, Celery, Redis
- **AI Engine**: LlamaIndex, NVIDIA NIM (Llama 3.2 3B, NV-EmbedQA)
- **Vector Store**: ChromaDB
- **Frontend**: Next.js 14, TailwindCSS, Shadcn/UI
- **Infrastructure**: Docker Compose

## 🏁 Quick Start

### Prerequisites
- Docker & Docker Compose
- NVIDIA API Key (from [build.nvidia.com](https://build.nvidia.com))

### 1. Clone & Configure
```bash
git clone https://github.com/yourusername/research-paper-assistant.git
cd research-paper-assistant

# Create .env file
cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY
```

### 2. Run with Docker
```bash
docker-compose up --build
```
Access the app at **http://localhost:3000**

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

## 📖 Usage Guide

1. **Search Papers**: Click the ⚙️ icon to open the Admin Panel. Search for papers (e.g., "RAG agents").
2. **Ingest**: Select papers and click "Ingest Selected".
3. **Chat**: Ask questions like "What are the key findings of these papers?".
4. **Library**: Click the 📚 icon to view your ingested papers.
5. **History**: Click the 🕐 icon to view past conversations.

## 🏗️ Project Structure

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

## 🤝 Contributing
Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
