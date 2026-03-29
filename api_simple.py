# -*- coding: utf-8 -*-
"""
              PRÁCTICA 5: Integración, automatización y modelo de negocio
                       API de Generación de Texto con FastAPI
                       Programación de Inteligencia Artificial

Implementa una API RESTful con FastAPI que actúe como proxy hacia la API de generación de texto desarrollada en la práctica anterior. La API debe exponer un endpoint POST /generate-proxy que reciba los mismos parámetros que la API remota, los valide y los reenvíe a la API remota, devolviendo la respuesta al cliente. Además, implementa un endpoint GET /health-remote para verificar la conectividad con la API remota. Asegúrate de manejar adecuadamente los errores y de incluir medidas de seguridad como autenticación por API Key y limitación de tasa para proteger el servicio.

DESARROLLADO POR:   José A. Rodríguez López
FECHA: 29 de Marzo, 2026
PROYECTO: Programación de Inteligencia Artificial
================================================================================
"""

from fastapi import FastAPI, HTTPException, Request # Librería principal para crear la API y manejar excepciones
from fastapi.middleware.cors import CORSMiddleware # Librería para manejar CORS
from fastapi.responses import FileResponse # Librería para servir archivos estáticos
from fastapi.staticfiles import StaticFiles # Librería para servir archivos estáticos desde un directorio
from pydantic import BaseModel, Field, field_validator # Librería para validación de datos y modelos
from typing import Literal # Librería para tipos literales en validación de datos
import httpx # Librería para realizar solicitudes HTTP asíncronas
import os # Librería para manejar variables de entorno y operaciones del sistema
import re # Librería para expresiones regulares, utilizada para limpiar el texto generado

MAX_PROXY_WORDS = 200
PROXY_WORDS_STEP = 20

# Configuración de la API remota a través de variables de entorno, con valores por defecto para desarrollo local
REMOTE_API_BASE_URL = os.getenv(
    "REMOTE_API_BASE_URL",
    "https://ca-practica4.wittycoast-99cc6956.westeurope.azurecontainerapps.io",
).rstrip("/")
REMOTE_API_KEY = os.getenv("REMOTE_API_KEY", "")
WEB_DIR = "web"
INDEX_FILE = os.path.join(WEB_DIR, "index.html")

# Configuración de la aplicación FastAPI y middleware para CORS y seguridad
app = FastAPI(title="Practica 5 Integracion", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monta el directorio de archivos estáticos si existe, para servir el frontend desde /static
if os.path.isdir(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

# Middleware para agregar encabezados de seguridad a todas las respuestas HTTP
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cache-Control"] = "no-store"
    return response

# Modelos de datos para la solicitud y respuesta del endpoint de generación de texto, con validación de campos
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
    """
    Verifica que la configuración de la API remota esté presente.
    Returns:
        Tuple con la URL base de la API remota y la clave de API.
    Raises:
        HTTPException con código 500 si falta alguna configuración.
    """
    if not REMOTE_API_BASE_URL:
        raise HTTPException(status_code=500, detail="REMOTE_API_BASE_URL no configurada")
    if not REMOTE_API_KEY:
        raise HTTPException(status_code=500, detail="REMOTE_API_KEY no configurada")
    return REMOTE_API_BASE_URL, REMOTE_API_KEY


def _clean_generated_text(text: str) -> str:
    """
    Elimina tokens especiales visibles del texto generado remoto.
    Args:
        text: El texto generado que puede contener tokens como <UNK>, <PAD>, <BOS>, <EOS>.
    Returns:
        El texto limpio, con tokens eliminados y formato mejorado.
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


def _trim_to_last_period(text: str) -> str:
    """
    Si el texto no termina en punto, recorta hasta el último punto encontrado.
    Si no hay puntos, devuelve el texto limpio sin modificar.
    """
    cleaned = (text or "").strip()
    if not cleaned or cleaned.endswith("."):
        return cleaned

    last_period = cleaned.rfind(".")
    if last_period == -1:
        return cleaned
    return cleaned[: last_period + 1].strip()


def _count_words(text: str) -> int:
    """
    Cuenta palabras no vacías en un texto.
    """
    return len(re.findall(r"\S+", text or ""))


@app.get("/")
async def root():
    """
    Endpoint raíz que proporciona información básica sobre la API y enlaces a la documentación y aplicación web.
    Returns:
        Un diccionario con un mensaje de bienvenida y enlaces a la documentación y aplicación.
    """
    return {"message": "Practica 5 Integracion", "docs": "/docs", "app": "/app"}


@app.get("/app")
async def web_app():
    """
    Endpoint que sirve la aplicación web desde el archivo index.html.
    Returns:
        FileResponse con el archivo index.html si existe, HTTPException 404 si no.
    """
    if not os.path.exists(INDEX_FILE):
        raise HTTPException(status_code=404, detail="Frontend no encontrado en /web")
    return FileResponse(INDEX_FILE)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
    Endpoint que sirve el favicon.ico desde el directorio web.
    Returns:
        FileResponse con el archivo favicon.ico si existe, HTTPException 404 si no.
    """
    favicon_path = os.path.join(WEB_DIR, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    raise HTTPException(status_code=404, detail="favicon.ico no encontrado")


@app.get("/health")
async def health():
    """
    Endpoint de salud que verifica la configuración de la API remota y devuelve información básica sobre el servicio.
    Returns:
        Un diccionario con el estado del servicio, la URL base de la API remota y si la clave remota está configurada.
    """
    return {
        "status": "ok",
        "service": "practica5-proxy",
        "remote_api_base_url": REMOTE_API_BASE_URL,
        "remote_key_configured": bool(REMOTE_API_KEY),
    }


@app.get("/web-config")
async def web_config():
    """
    Endpoint que proporciona la configuración de la API remota para el frontend.
    Returns:
        Un diccionario con la configuración de la API remota para el frontend.
    """
    return {
        "mode": "proxy",
        "remote_api_base_url": REMOTE_API_BASE_URL,
        "remote_key_configured": bool(REMOTE_API_KEY),
    }


@app.get("/health-remote")
async def health_remote():
    """
    Endpoint que verifica la conectividad con la API remota realizando una solicitud al endpoint de salud remoto.
    Returns:
        Un diccionario con el estado de la API remota si la conexión es exitosa.
    Raises:
        HTTPException con código 502 si hay un error al conectar con la API remota.
    """
    base_url, _ = _require_remote_config()
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(f"{base_url}/health")
        response.raise_for_status()
        return {"status": "ok", "remote": response.json()}
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Error conectando con API remota. {exc}") from exc


@app.post("/generate-proxy", response_model=GenerateResponse)
async def generate_proxy(body: GenerateRequest):
    """
    Endpoint que actúa como proxy para la generación de texto utilizando la API remota.
    Args:
        body: Una instancia de GenerateRequest con los parámetros de generación.
    Returns:
        Una instancia de GenerateResponse con el texto generado.
    Raises:
        HTTPException con código 502 si hay un error al conectar con la API remota.
    """
    base_url, remote_key = _require_remote_config()
    headers = {"Content-Type": "application/json", "X-API-Key": remote_key}
    try:
        target_words = body.n_words
        total_elapsed_ms = 0.0
        last_data: dict | None = None

        async with httpx.AsyncClient(timeout=60.0) as client:
            while target_words <= MAX_PROXY_WORDS:
                payload = body.model_dump()
                payload["n_words"] = target_words

                response = await client.post(
                    f"{base_url}/generate",
                    json=payload,
                    headers=headers,
                )

                if response.status_code >= 400:
                    detail = response.json().get("detail", f"HTTP {response.status_code}")
                    raise HTTPException(status_code=response.status_code, detail=detail)

                data = response.json()
                total_elapsed_ms += float(data.get("elapsed_ms", 0.0) or 0.0)

                cleaned_text = _clean_generated_text(data.get("generated_text", ""))
                data["generated_text"] = cleaned_text
                data["elapsed_ms"] = total_elapsed_ms
                last_data = data

                # Si ya hay al menos un punto, se recorta hasta el último punto y se devuelve.
                if "." in cleaned_text:
                    data["generated_text"] = _trim_to_last_period(cleaned_text)
                    data["n_words_generated"] = _count_words(data["generated_text"])
                    return GenerateResponse(**data)

                target_words += PROXY_WORDS_STEP

        # Si no se encontró punto dentro del límite, se devuelve la mejor salida disponible.
        if last_data is None:
            raise HTTPException(status_code=502, detail="No se recibió respuesta válida de la API remota")

        last_data["n_words_generated"] = _count_words(last_data.get("generated_text", ""))
        return GenerateResponse(**last_data)
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Error de proxy hacia API remota. {exc}") from exc