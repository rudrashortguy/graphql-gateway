# GraphQL Schema Stitching Gateway

Merges multiple GraphQL endpoints behind a single proxy. Introspects each
endpoint, uses Ollama to suggest per-endpoint sub-queries, executes them in
parallel, and returns the combined result.

## Usage

```bash
docker compose up --build
```

Frontend at http://localhost:5173, backend at http://localhost:8000.

### API

**POST /stitch**
```json
{ "endpoints": ["http://service-a:4001/graphql"], "query": "{ users { id name } }" }
```

**GET /health** — `{ "status": "ok" }`

## How it works

1. Introspect schemas from all provided endpoints
2. Send schemas + user query to Ollama for per-endpoint query decomposition
3. Execute sub-queries in parallel via httpx
4. Merge results into one response

## Supported features

- Parallel query execution
- Error isolation (per-endpoint errors don't block others)
- Ollama-powered schema mapping
- Dark-mode frontend with Zustand state management
- Axios retry on frontend, CORS enabled
