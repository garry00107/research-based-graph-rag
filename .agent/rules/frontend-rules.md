# Frontend Development Rules

## Components
- Use Shadcn/UI for base components
- Icons from `lucide-react`
- Components must be responsive (mobile-friendly)

## State Management
- Use `useState` for local UI state
- Use `useEffect` for data fetching (or React Query in future)
- API calls must go through `lib/api.ts`

## Features
- **Chat Interface**: Handles streaming responses (SSE) and citations
- **Papers Library**: Displays ingested papers, stats, and search
- **Chat History**: Shows conversation log from Redis
- **Admin Panel**: Handles paper search and ingestion

## API Integration
- All endpoints must handle errors gracefully
- Use `axios` for HTTP requests
- Streaming endpoints use `EventSource` or custom reader
