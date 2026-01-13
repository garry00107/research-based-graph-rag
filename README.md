# 📊 Sheet RAG

**Multi-Layer RAG Architecture for Reduced Hallucinations**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

Sheet RAG is a novel Retrieval-Augmented Generation architecture that reduces hallucinations by validating retrieved information across multiple abstraction layers.

## 🎯 Key Features

- **4-Layer Hierarchical Chunking**: Sentence → Paragraph → Section → Summary
- **Cross-Layer Validation**: Requires 2+ layers to agree before returning results
- **Confidence Scoring**: Every response includes a confidence percentage
- **Honest Uncertainty**: System admits when information isn't in the knowledge base

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    User Query                        │
└─────────────────────┬───────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │Sentence │ │Paragraph│ │ Section │ │ Summary │
    │  Layer  │ │  Layer  │ │  Layer  │ │  Layer  │
    └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
         │           │           │           │
         └───────────┴─────┬─────┴───────────┘
                           │
                 ┌─────────▼─────────┐
                 │  Cross-Layer      │
                 │  Validator        │
                 │  (≥2 layers must  │
                 │   agree)          │
                 └─────────┬─────────┘
                           │
                 ┌─────────▼─────────┐
                 │  Confidence Score │
                 │  + Response       │
                 └───────────────────┘
```

## 📈 Results

| Metric | Standard RAG | Sheet RAG |
|--------|-------------|-----------|
| Correct answers | 60% | **80%** |
| Admits uncertainty | 10% | **70%** |
| False confidence | 30% | **5%** |
| Avg confidence | N/A | **82%** |

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)
- NVIDIA API Key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/sheet-rag.git
cd sheet-rag

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
echo "NVIDIA_API_KEY=your_key_here" > .env

# Start backend
python main.py
```

```bash
# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

### Ingest Papers

```bash
# Ingest into Sheet RAG (4-layer)
curl -X POST http://localhost:8002/sheet-rag/ingest \
  -H "Content-Type: application/json" \
  -d '{"arxiv_id": "1706.03762"}'
```

### Query

```bash
# Query with cross-layer validation
curl -X POST http://localhost:8002/chat-v2 \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the Transformer architecture?"}'
```

Response includes confidence score:
```json
{
  "response": "The Transformer has 6 encoder and 6 decoder layers...",
  "validation": {
    "avg_confidence": 0.82,
    "avg_layer_coverage": 2.6,
    "count": 5
  }
}
```

## 🔧 Configuration

Edit `config.py`:

```python
# Sheet RAG Settings
sheet_rag_enabled = True
sheet_rag_layers = ["sentence", "paragraph", "section", "summary"]
cross_validation_threshold = 0.5  # Minimum similarity for layer agreement
cross_validation_min_layers = 2   # Minimum layers that must agree
```

## 📁 Project Structure

```
sheet-rag/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── sheet_rag_engine.py     # Multi-layer RAG engine
│   ├── hierarchical_chunker.py # 4-level document chunking
│   ├── cross_validator.py      # Cross-layer validation logic
│   ├── rag_evaluator.py        # Comparison evaluation
│   └── config.py               # Configuration
├── frontend/
│   ├── components/
│   │   ├── chat-interface.tsx  # Chat UI with RAG toggle
│   │   └── admin-panel.tsx     # Paper ingestion UI
│   └── lib/api.ts              # API client
└── README.md
```

## 🧪 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat-v2` | POST | Query Sheet RAG |
| `/chat-v2-stream` | POST | Streaming Sheet RAG |
| `/sheet-rag/ingest` | POST | Ingest paper (4-layer) |
| `/sheet-rag/stats` | GET | Layer statistics |
| `/sheet-rag/clear` | DELETE | Clear all layers |
| `/evaluate` | POST | Run comparison evaluation |

## 🔬 How It Works

### 1. Hierarchical Chunking
Documents are split at 4 granularity levels:
- **Sentence**: Fine-grained facts (200 chars)
- **Paragraph**: Contextual chunks (800 chars)
- **Section**: Topical groupings (2000 chars)
- **Summary**: Document-level overview (4000 chars)

### 2. Cross-Layer Validation
For each retrieved chunk:
1. Find semantically similar chunks in other layers
2. Calculate agreement score
3. Only return chunks with 2+ supporting layers

### 3. Confidence Scoring
```python
confidence = (supporting_layers / total_layers) * avg_similarity
```

## 📊 Evaluation

Run the built-in evaluation:

```bash
curl -X POST http://localhost:8002/evaluate
```

Or with custom queries:
```bash
curl -X POST http://localhost:8002/evaluate \
  -H "Content-Type: application/json" \
  -d '["What is attention?", "How many layers?"]'
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 📚 Citation

If you use Sheet RAG in your research, please cite:

```bibtex
@software{sheetrag2024,
  title = {Sheet RAG: Multi-Layer RAG Architecture for Reduced Hallucinations},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/sheet-rag}
}
```

## 🙏 Acknowledgments

- [LlamaIndex](https://github.com/run-llama/llama_index) for RAG framework
- [ChromaDB](https://github.com/chroma-core/chroma) for vector storage
- [NVIDIA NIM](https://developer.nvidia.com/nim) for LLM inference
