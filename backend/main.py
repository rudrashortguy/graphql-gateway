import logging
import os
import asyncio
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("gateway")

app = FastAPI(title="GraphQL Schema Stitching Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


class StitchRequest(BaseModel):
    endpoints: list[HttpUrl]
    query: str


async def fetch_schema(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    resp = await client.post(
        url,
        json={"query": "{ __schema { types { name kind description fields { name type { name kind ofType { name kind } } } } } }"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


async def execute_query(client: httpx.AsyncClient, url: str, query: str) -> dict[str, Any]:
    resp = await client.post(url, json={"query": query}, timeout=30)
    resp.raise_for_status()
    return resp.json()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/stitch")
async def stitch(req: StitchRequest):
    urls = [str(u) for u in req.endpoints]
    if not urls:
        raise HTTPException(400, "At least one endpoint required")
    if not req.query.strip():
        raise HTTPException(400, "Query required")

    async with httpx.AsyncClient() as client:
        raw = await asyncio.gather(*[fetch_schema(client, u) for u in urls], return_exceptions=True)
        for i, s in enumerate(raw):
            if isinstance(s, Exception):
                raise HTTPException(502, f"Endpoint {urls[i]}: {s}")

        ok_schemas: list[dict] = []
        for s in raw:
            if not isinstance(s, Exception):
                ok_schemas.append(s)  # type: ignore[arg-type]
        try:
            schema_text = "\n---\n".join(
                f"Endpoint {i}: {s.get('data', {}).get('__schema', {}).get('types', [])[:5]}"
                for i, s in enumerate(ok_schemas)
            )
            prompt = (
                f"Given these GraphQL schemas:\n{schema_text}\n\n"
                f"User query: {req.query}\n"
                "Return a JSON object with keys being endpoint indices (0, 1, ...) "
                "and values being the GraphQL query for that endpoint. "
                "Only return valid JSON, no explanation."
            )
            resp = await client.post(
                OLLAMA_URL,
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                timeout=60,
            )
            resp.raise_for_status()
            queries = resp.json().get("response", "{}")
        except Exception:
            queries = None

        queries_map: dict[str, str] = {}
        if queries:
            try:
                import json
                parsed = json.loads(queries)
                if isinstance(parsed, dict):
                    queries_map = {str(k): str(v) for k, v in parsed.items()}
            except Exception:
                pass

        tasks = []
        for i, u in enumerate(urls):
            q = queries_map.get(str(i), req.query)
            tasks.append(execute_query(client, u, q))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        merged: dict[str, Any] = {}
        errors = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                errors.append({"endpoint": urls[i], "error": str(r)})
            else:
                merged[str(i)] = r

        return {"data": merged, "errors": errors or None}
