"""
app.py - API REST con FastAPI para el modelo de lenguaje
Práctica 4: Entrenamiento, Evaluación y Despliegue

Seguridad implementada:
    1. Autenticación por API Key (cabecera X-API-Key).
       Previene acceso no autorizado al servicio.
    2. Limitación de tasa de peticiones / Rate Limiting (slowapi).
       Previene abuso (DoS, scraping masivo): máx. 10 req/min por IP.
    3. Validación y saneamiento de entradas (Pydantic).
       Previene entradas maliciosas o excesivamente largas.
    4. Cabeceras de seguridad HTTP (middleware).
       Mitiga ataques comunes (XSS, clickjacking).

Uso:
    uvicorn app:app --host 0.0.0.0 --port 8000

Variables de entorno:
    MODEL_PATH       Ruta al modelo .keras        (default: modelo/model_final.keras)
    TOKENIZER_PATH   Ruta al tokenizer.json       (default: tokenizer/tokenizer.json)
    API_KEY          Clave secreta de acceso       (default: changeme-secret-key)
    RATE_LIMIT       Peticiones por minuto por IP  (default: 10)
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

import numpy as np
import tensorflow as tf
from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from train import TextTokenizer

# ── Configuración ─────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

MODEL_PATH     = os.getenv("MODEL_PATH",     "modelo/model_final.keras")
TOKENIZER_PATH = os.getenv("TOKENIZER_PATH", "tokenizer/tokenizer.json")
API_KEY        = os.getenv("API_KEY",        "%KhJh-yj44k[RMuJpy")
RATE_LIMIT_VAL = os.getenv("RATE_LIMIT",     "10")

# ── Estado global del modelo ──────────────────────────────────────────────────
class ModelState:
    model: Optional[tf.keras.Model] = None
    tokenizer: Optional[TextTokenizer] = None
    seq_len: int = 50
    vocab_size: int = 10000

state = ModelState()

# ── Rate limiter (slowapi) ────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── Ciclo de vida de la app (carga del modelo al arrancar) ────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Cargando modelo desde: %s", MODEL_PATH)
    try:
        state.model = tf.keras.models.load_model(MODEL_PATH)
        state.seq_len = state.model.input_shape[1]
        log.info("Modelo cargado. Seq_len=%d", state.seq_len)
    except Exception as e:
        log.error("No se pudo cargar el modelo: %s", e)

    log.info("Cargando tokenizador desde: %s", TOKENIZER_PATH)
    try:
        state.tokenizer = TextTokenizer.load(TOKENIZER_PATH)
        state.vocab_size = state.tokenizer.vocab_size
        log.info("Tokenizador cargado. Vocab=%d", state.vocab_size)
    except Exception as e:
        log.error("No se pudo cargar el tokenizador: %s", e)

    yield  # La app está en ejecución

    # Limpieza al apagar
    log.info("Apagando servidor...")
    tf.keras.backend.clear_session()


# ── Aplicación FastAPI ────────────────────────────────────────────────────────
app = FastAPI(
    title="API de Generación de Texto con IA",
    description="Modelo LSTM de lenguaje desplegado como servicio REST.",
    version="1.0.0",
    lifespan=lifespan,
)

# Registro del manejador de errores de rate limit
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: permite peticiones desde cualquier origen (ajustar en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Middleware: cabeceras de seguridad HTTP ────────────────────────────────────
@app.middleware("http")
async def security_headers(request: Request, call_next):
    """
    Añade cabeceras HTTP de seguridad en cada respuesta.
    Mitiga ataques XSS, clickjacking y filtración de información.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


# ── Seguridad: autenticación por API Key ──────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str = Security(api_key_header)) -> str:
    """
    Dependencia de FastAPI que valida la API Key en la cabecera X-API-Key.
    Si la clave es incorrecta o falta, devuelve HTTP 401.

    Medida de seguridad #1: Autenticación por clave de API.
    """
    if not key or key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida o no proporcionada.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return key


# ── Esquemas Pydantic ─────────────────────────────────────────────────────────
class GenerateRequest(BaseModel):
    seed: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Texto inicial (seed) para la generación.",
        examples=["la inteligencia artifical es"],
    )
    n_words: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Número de palabras a generar (1-200).",
    )
    strategy: str = Field(
        default="sampling",
        description="Estrategia: 'greedy', 'sampling' o 'top_k'.",
    )
    temperature: float = Field(
        default=1.0,
        ge=0.1,
        le=2.0,
        description="Temperatura para muestreo (0.1-2.0).",
    )
    top_k: int = Field(
        default=40,
        ge=1,
        le=500,
        description="K para top-K sampling.",
    )

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        allowed = {"greedy", "sampling", "top_k"}
        if v not in allowed:
            raise ValueError(f"Estrategia inválida. Opciones: {allowed}")
        return v

    @field_validator("seed")
    @classmethod
    def sanitize_seed(cls, v: str) -> str:
        # Eliminar caracteres de control
        return "".join(c for c in v if c.isprintable())


class GenerateResponse(BaseModel):
    seed: str
    generated_text: str
    strategy: str
    n_words_generated: int
    elapsed_ms: float


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    tokenizer_loaded: bool
    vocab_size: int


# ── Lógica de generación ──────────────────────────────────────────────────────
def _generate(req: GenerateRequest) -> tuple[str, int]:
    """
    Genera texto usando la estrategia especificada.
    Produce al menos n_words tokens y continúa hasta encontrar
    una palabra que termine en '.' (máximo 100 palabras extra).
    Devuelve (texto_limpio, palabras_generadas).
    """
    if state.model is None or state.tokenizer is None:
        raise HTTPException(status_code=503, detail="Modelo no disponible.")

    tokens = state.tokenizer.encode(req.seed)
    seed_len = len(tokens)
    seq_len = state.seq_len
    MAX_EXTRA = 100  # palabras extra máximas buscando el punto final

    def _next_token() -> int:
        padded = tokens[-seq_len:]
        padded = [0] * (seq_len - len(padded)) + padded
        x = np.array([padded])

        raw = state.model.predict(x, verbose=0)
        arr = np.array(raw)
        if arr.ndim == 3:
            probs = arr[0, -1, :]   # (vocab_size,)
        else:
            probs = arr.flatten()   # fallback (vocab_size,) o (1, vocab_size)

        if req.strategy == "greedy":
            return int(np.argmax(probs))

        elif req.strategy == "sampling":
            log_probs = np.log(probs.astype(np.float64) + 1e-10) / req.temperature
            log_probs -= log_probs.max()
            scaled = np.exp(log_probs)
            scaled /= scaled.sum()
            return int(np.random.choice(len(scaled), p=scaled))

        else:  # top_k
            k = min(req.top_k, len(probs))
            top_k_idx = np.argsort(probs)[-k:]
            top_k_probs = probs[top_k_idx].astype(np.float64)
            log_probs = np.log(top_k_probs + 1e-10) / req.temperature
            log_probs -= log_probs.max()
            scaled = np.exp(log_probs)
            scaled /= scaled.sum()
            return int(np.random.choice(top_k_idx, p=scaled))

    # Fase 1: generar el mínimo de palabras solicitado
    for _ in range(req.n_words):
        tokens.append(_next_token())

    # Fase 2: generar primero, luego comprobar si el token recién añadido termina en '.'
    found_period = state.tokenizer.decode([tokens[-1]]).endswith('.')
    for _ in range(MAX_EXTRA):
        if found_period:
            break
        tokens.append(_next_token())
        found_period = state.tokenizer.decode([tokens[-1]]).endswith('.')

    raw_text = state.tokenizer.decode(tokens)
    # Filtrar tokens especiales del resultado final
    special = {state.tokenizer.PAD, state.tokenizer.UNK,
               state.tokenizer.BOS, state.tokenizer.EOS}
    words = [w for w in raw_text.split() if w not in special]

    if not found_period:
        # Fase 3: buscar el último punto hacia atrás en las palabras generadas
        seed_words = len(req.seed.split())
        cutoff = -1
        for i in range(len(words) - 1, seed_words - 1, -1):
            if '.' in words[i]:
                cutoff = i
                break
        if cutoff != -1:
            words = words[:cutoff + 1]
        else:
            # Sin ningún punto: añadir punto al final
            words[-1] = words[-1].rstrip('.,;:!?') + '.'

    clean = " ".join(words)
    generated_count = len(words) - len(req.seed.split())
    return clean, generated_count


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "API de Generación de Texto. Ver /docs para documentación."}


@app.get("/health", response_model=HealthResponse, tags=["Estado"])
async def health():
    """Endpoint de health check. No requiere autenticación."""
    return HealthResponse(
        status="ok" if state.model is not None else "degraded",
        model_loaded=state.model is not None,
        tokenizer_loaded=state.tokenizer is not None,
        vocab_size=state.vocab_size,
    )


@app.post(
    "/generate",
    response_model=GenerateResponse,
    tags=["Generación"],
    summary="Generar texto con IA",
    dependencies=[Depends(require_api_key)],
)
@limiter.limit(f"{RATE_LIMIT_VAL}/minute")
async def generate(request: Request, body: GenerateRequest):
    """
    Genera texto a partir de un seed usando el modelo LSTM.

    **Requiere cabecera:** `X-API-Key: <tu_clave>`

    **Medida de seguridad #2 (Rate Limiting):** máximo {RATE_LIMIT_VAL} peticiones
    por minuto por dirección IP. Superar el límite devuelve HTTP 429.
    """
    t0 = time.perf_counter()
    generated, n_generated = _generate(body)
    elapsed = (time.perf_counter() - t0) * 1000

    log.info(
        "Generación completada | strategy=%s | n_words=%d | total_generado=%d | elapsed=%.1f ms",
        body.strategy, body.n_words, n_generated, elapsed
    )

    return GenerateResponse(
        seed=body.seed,
        generated_text=generated,
        strategy=body.strategy,
        n_words_generated=n_generated,
        elapsed_ms=round(elapsed, 2),
    )


@app.get(
    "/strategies",
    tags=["Generación"],
    summary="Listar estrategias disponibles",
    dependencies=[Depends(require_api_key)],
)
async def list_strategies():
    """Devuelve las estrategias de generación disponibles y sus parámetros."""
    return {
        "strategies": {
            "greedy":   "Selecciona siempre el token más probable. Determinista.",
            "sampling": "Muestreo según la distribución de probabilidad. Controlado con 'temperature'.",
            "top_k":    "Limita el muestreo a los K tokens más probables. Controlado con 'top_k' y 'temperature'.",
        }
    }


# ── Punto de entrada ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
