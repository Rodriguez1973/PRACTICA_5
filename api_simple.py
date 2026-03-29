# -*- coding: utf-8 -*-
"""
Práctica 5 - Integración independiente (sin usar PRACTICA_4 en ejecución).
Backend proxy seguro para consumir la API remota de Azure sin exponer API key.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from typing import Literal
import httpx
import os
import re

REMOTE_API_BASE_URL = os.getenv(
    "REMOTE_API_BASE_URL",
    "https://ca-practica4.wittycoast-99cc6956.westeurope.azurecontainerapps.io",
).rstrip("/")
REMOTE_API_KEY = os.getenv("REMOTE_API_KEY", "")
WEB_DIR = "web"
INDEX_FILE = os.path.join(WEB_DIR, "index.html")

app = FastAPI(title="Practica 5 Integracion", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.isdir(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cache-Control"] = "no-store"
    return response


class GenerateRequest(BaseModel):
    seed: str = Field(..., min_length=1, max_length=500)
    n_words: int = Field(default=50, ge=1, le=200)
    strategy: Literal["greedy", "sampling", "top_k"] = "sampling"
    temperature: float = Field(default=1.0, ge=0.1, le=2.0)
    top_k: int = Field(default=40, ge=1, le=500)

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, value: str) -> str:
        allowed = {"greedy", "sampling", "top_k"}
        if value not in allowed:
            raise ValueError(f"La estrategia debe ser una de {allowed}")
        return value


class GenerateResponse(BaseModel):
    seed: str
    generated_text: str
    strategy: str
    n_words_generated: int
    elapsed_ms: float


def _require_remote_config() -> tuple[str, str]:
    if not REMOTE_API_BASE_URL:
        raise HTTPException(status_code=500, detail="REMOTE_API_BASE_URL no configurada")
    if not REMOTE_API_KEY:
        raise HTTPException(status_code=500, detail="REMOTE_API_KEY no configurada")
    return REMOTE_API_BASE_URL, REMOTE_API_KEY


def _clean_generated_text(text: str) -> str:
    """
    Elimina tokens especiales visibles del texto generado remoto.
    """
    if not text:
        return text
    cleaned = re.sub(r"</?(UNK|PAD|BOS|EOS)>", " ", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(UNK|PAD|BOS|EOS)\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()

    # Capitaliza el inicio del texto y la primera letra tras fin de oración.
    chars = list(cleaned)
    capitalize_next = True
    for i, ch in enumerate(chars):
        if capitalize_next and ch.isalpha():
            chars[i] = ch.upper()
            capitalize_next = False
        if ch in ".!?":
            capitalize_next = True
    return "".join(chars)


@app.get("/")
async def root():
    return {"message": "Practica 5 Integracion", "docs": "/docs", "app": "/app"}


@app.get("/app")
async def web_app():
    if not os.path.exists(INDEX_FILE):
        raise HTTPException(status_code=404, detail="Frontend no encontrado en /web")
    return FileResponse(INDEX_FILE)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = os.path.join(WEB_DIR, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    raise HTTPException(status_code=404, detail="favicon.ico no encontrado")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "practica5-proxy",
        "remote_api_base_url": REMOTE_API_BASE_URL,
        "remote_key_configured": bool(REMOTE_API_KEY),
    }


@app.get("/web-config")
async def web_config():
    return {
        "mode": "proxy",
        "remote_api_base_url": REMOTE_API_BASE_URL,
        "remote_key_configured": bool(REMOTE_API_KEY),
    }


@app.get("/health-remote")
async def health_remote():
    base_url, _ = _require_remote_config()
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(f"{base_url}/health")
        response.raise_for_status()
        return {"status": "ok", "remote": response.json()}
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Error conectando con API remota: {exc}") from exc


@app.post("/generate-proxy", response_model=GenerateResponse)
async def generate_proxy(body: GenerateRequest):
    base_url, remote_key = _require_remote_config()
    headers = {"Content-Type": "application/json", "X-API-Key": remote_key}
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/generate",
                json=body.model_dump(),
                headers=headers,
            )
        if response.status_code >= 400:
            detail = response.json().get("detail", f"HTTP {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail=detail)
        data = response.json()
        data["generated_text"] = _clean_generated_text(data.get("generated_text", ""))
        return GenerateResponse(**data)
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Error de proxy hacia API remota: {exc}") from exc
