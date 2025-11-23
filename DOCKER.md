# Docker Deployment Guide

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- NVIDIA API Key from [build.nvidia.com](https://build.nvidia.com)

### 1. Set Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your NVIDIA API key
nano .env
```

### 2. Start All Services

```bash
# Build and start all containers
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8002
- **Redis**: localhost:6379

### 4. Stop Services

```bash
# Stop all containers
docker-compose down

# Stop and remove volumes (clears data)
docker-compose down -v
```

## Services

### Backend
- **Port**: 8002
- **Image**: Built from `./backend/Dockerfile`
- **Volumes**: 
  - `./backend/chroma_db` - Vector database storage
  - `./backend/data` - Downloaded papers
- **Dependencies**: Redis

### Frontend
- **Port**: 3000
- **Image**: Built from `./frontend/Dockerfile`
- **Dependencies**: Backend

### Redis
- **Port**: 6379
- **Image**: `redis:7-alpine`
- **Volume**: `redis-data` - Persistent cache storage

## Development vs Production

### Development (Current Setup)
```bash
# Backend
cd backend
python main.py

# Frontend
cd frontend
npm run dev
```

### Production (Docker)
```bash
docker-compose up -d
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
lsof -ti:8002 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Rebuild After Code Changes
```bash
docker-compose up --build
```

### Clear All Data
```bash
# Stop containers and remove volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NVIDIA_API_KEY` | - | **Required** NVIDIA NIM API key |
| `CHROMA_PERSIST_DIR` | `/app/chroma_db` | Vector database directory |
| `REDIS_URL` | `redis://redis:6379` | Redis connection URL |
| `REDIS_ENABLED` | `false` | Enable Redis caching |
| `HOST` | `0.0.0.0` | Backend host |
| `PORT` | `8002` | Backend port |
| `BATCH_SIZE` | `32` | Embedding batch size |
| `MAX_WORKERS` | `4` | Concurrent workers |

## Data Persistence

Data is persisted in:
- `./backend/chroma_db` - Vector embeddings
- `./backend/data/papers` - Downloaded PDFs
- `redis-data` volume - Redis cache

These directories survive container restarts.
