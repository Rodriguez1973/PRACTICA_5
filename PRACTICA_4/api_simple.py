# -*- coding: utf-8 -*-
"""
                 PRÁCTICA 4: Entrenamiento, Evaluación y Despliegue.
                       API de Generación de Texto con FastAPI
                       Programación de Inteligencia Artificial

Este módulo implementa una API RESTful para generar texto utilizando un modelo de lenguaje entrenado. La API ofrece un endpoint para generar texto a partir de una semilla dada, con opciones de configuración para la estrategia de generación y el número de palabras a generar. Se incluyen medidas de seguridad como autenticación por API Key y limitación de tasa para proteger el servicio.

DESARROLLADO POR:   José A. Rodríguez López
FECHA: 27 de Marzo, 2026
PROYECTO: Programación de Inteligencia Artificial
================================================================================
"""

from fastapi import FastAPI, HTTPException, Request, Security # Librerías de FastAPI para crear la API, manejar excepciones, solicitudes y seguridad
from fastapi.middleware.cors import CORSMiddleware # Librería para manejar CORS (Cross-Origin Resource Sharing)
from fastapi.security.api_key import APIKeyHeader # Librería para manejar autenticación por API Key
from fastapi.responses import JSONResponse # Librería para enviar respuestas JSON
from pydantic import BaseModel, Field, field_validator # Librerías de Pydantic para definir modelos de datos y validación de campos
import numpy as np # Librería para manejar arrays y operaciones numéricas, utilizada para procesar las probabilidades de generación de texto
import tensorflow as tf # Librería para cargar el modelo de lenguaje entrenado y realizar predicciones
from train_utils import TextTokenizer # Importación de la clase TextTokenizer desde el módulo train_utils, utilizada para tokenizar y detokenizar texto
import os # Librería para manejar variables de entorno, utilizada para configurar la API Key y el límite de tasa desde el entorno de ejecución
import time # Librería para medir el tiempo de generación de texto, utilizada para calcular el tiempo transcurrido en la generación de texto y devolverlo en la respuesta

# slowapi es opcional en entornos donde no esté instalado.
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler # Librerías de slowapi para implementar limitación de tasa (rate limiting) en la API, protegiendo el servicio contra abusos y sobrecargas
    from slowapi.errors import RateLimitExceeded # Excepción que se lanza cuando se excede el límite de tasa
    from slowapi.util import get_remote_address # Función para obtener la dirección IP del cliente, utilizada para aplicar la limitación de tasa basada en la IP
    SLOWAPI_AVAILABLE = True
except ModuleNotFoundError:
    SLOWAPI_AVAILABLE = False

    class RateLimitExceeded(Exception):
        """
        Excepción ficticia para manejar casos donde slowapi no está disponible
        Args:
            Exception: La clase base de excepciones en Python, utilizada para definir una excepción personalizada que se lanzará cuando se exceda el límite de tasa, aunque en este caso no se aplicará realmente debido a la ausencia de slowapi.
        """
        pass

    def get_remote_address(request):
        """
        Función ficticia para obtener la dirección IP del cliente cuando slowapi no está disponible.
        Args:
            request (Request): La solicitud HTTP entrante.
        Returns:
            str: Una cadena fija "local" para indicar que la limitación de tasa no se está aplicando realmente.
        """
        return "local"

    def _rate_limit_exceeded_handler(request, exc):
        """
        Manejador ficticio para cuando se excede el límite de tasa y slowapi no está disponible.
        Args:
            request (Request): La solicitud HTTP que causó la excepción.
            exc (Exception): La excepción que se lanzó.
        """
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

    class Limiter:
        """
        Clase ficticia para manejar la limitación de tasa cuando slowapi no está disponible.
        """
        def __init__(self, key_func=None):
            """
            Inicializa el limitador de tasa con una función de clave personalizada, aunque en este caso no hará nada debido a la ausencia de slowapi.
            Args:
                key_func (callable, optional): Una función que toma una solicitud y devuelve una clave única para aplicar la limitación de tasa, como la dirección IP del cliente. En este caso, se puede proporcionar una función personalizada, pero no se aplicará realmente debido a la ausencia de slowapi
            """
            self.key_func = key_func

        def limit(self, _rule):
            """
            Decorador ficticio para aplicar la limitación de tasa a un endpoint, aunque en este caso no hará nada debido a la ausencia de slowapi.
            Args:
                _rule (str): La regla de limitación de tasa, por ejemplo "10/minute".
            """
            def decorator(func):
                return func

            return decorator


API_KEY = os.getenv("API_KEY", "%KhJh-yj44k[RMuJpy") # La clave de API se obtiene de una variable de entorno, con un valor predeterminado para desarrollo. En producción, se recomienda establecer esta variable de entorno a un valor seguro y único para proteger el acceso a la API.
RATE_LIMIT = os.getenv("RATE_LIMIT", "10") # El límite de tasa. En producción, se recomienda ajustar este valor según las necesidades del servicio y la capacidad del servidor para manejar solicitudes concurrentes.
MODEL_PATH = "output/model_final.keras" # La ruta al modelo de lenguaje 
TOKENIZER_PATH = "output/tokenizer.json" # La ruta al tokenizador 

# Cargar el modelo y el tokenizador al iniciar la aplicación.
model = tf.keras.models.load_model(MODEL_PATH)
tokenizer = TextTokenizer.load(TOKENIZER_PATH)
seq_len = model.input_shape[1]

# Configuración de la aplicación FastAPI, incluyendo limitación de tasa, manejo de excepciones y middleware para seguridad y CORS.
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="API de Generación de Texto", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para agregar encabezados de seguridad a todas las respuestas, protegiendo contra ataques comunes como XSS, clickjacking y sniffing de contenido, además de deshabilitar el almacenamiento en caché para garantizar que los clientes siempre reciban la respuesta más reciente.
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cache-Control"] = "no-store"
    return response

# Configuración de seguridad para la autenticación por API Key. Se define un encabezado personalizado "X-API-Key" que los clientes deben incluir en sus solicitudes para autenticarse. La función verify_api_key verifica que la clave proporcionada sea válida y coincide con la clave configurada en el servidor, devolviendo un error 401 si la clave es inválida o ausente.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(key: str = Security(api_key_header)) -> str:
    """
    Verifica la clave de API proporcionada en el encabezado de la solicitud. Si la clave es válida, se devuelve; de lo contrario, se lanza una excepción HTTP 401.
    Args:
        key (str, optional): La clave de API proporcionada en el encabezado de la solicitud. 
    Raises:
        HTTPException: Se lanza una excepción HTTP 401 si la clave de API es inválida o ausente.
    Returns:
        str: La clave de API válida.
    """
    if not key or key != API_KEY:
        raise HTTPException(status_code=401, detail="API Key inválida o ausente")
    return key

class GenerateRequest(BaseModel):
    """
    Modelo de datos para la solicitud de generación de texto. Define los campos necesarios para configurar la generación de texto, incluyendo la semilla inicial, el número de palabras a generar, la estrategia de generación, la temperatura para muestreo y el valor de top_k para limitar las opciones de generación. Se incluyen validaciones para asegurar que los valores proporcionados sean válidos y dentro de los rangos permitidos.
    Args:
        seed (str): La semilla inicial para la generación de texto. Debe ser una cadena de texto con una longitud mínima de 1 y máxima de 500 caracteres.
        n_words (int): El número de palabras a generar. Debe ser un entero entre 1 y 200, con un valor predeterminado de 50.
        strategy (str): La estrategia de generación a utilizar. Puede ser "greedy" para selección del token con mayor probabilidad, "sampling" para muestreo basado en la distribución de probabilidades, o "top_k" para limitar las opciones a los k tokens más probables. El valor predeterminado es "greedy".
        temperature (float): El valor de temperatura para el muestreo, que controla la aleatoriedad de la generación. Debe ser un número flotante entre 0.1 y 2.0, con un valor predeterminado de 1.0.
        top_k (int): El valor de top_k para limitar las opciones de generación a los k tokens más probables. Debe ser un entero entre 1 y 500, con un valor predeterminado de 40. Este campo solo se utiliza si la estrategia seleccionada es "top_k".
    """
    seed: str = Field(..., min_length=1, max_length=500)
    n_words: int = Field(default=50, ge=1, le=200)
    strategy: str = Field(default="greedy")
    temperature: float = Field(default=1.0, ge=0.1, le=2.0)
    top_k: int = Field(default=40, ge=1, le=500)

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, value):
        """
        Valida que la estrategia de generación proporcionada sea una de las opciones permitidas: "greedy", "sampling" o "top_k". Si la estrategia no es válida, se lanza una excepción ValueError.
        Args:           
            value (str): La estrategia de generación a validar.
        Raises:            
            ValueError: Se lanza una excepción si la estrategia no es una de las opciones permitidas.
        Returns:
            str: La estrategia de generación válida.
        """
        allowed = {"greedy", "sampling", "top_k"}
        if value not in allowed:
            raise ValueError(f"La estrategia debe ser una de {allowed}")
        return value

class GenerateResponse(BaseModel):
    """
    Generación de texto. Define los campos que se incluirán en la respuesta de la API después de generar el texto, incluyendo la semilla utilizada, el texto generado, la estrategia de generación, el número de palabras generadas y el tiempo transcurrido en milisegundos para realizar la generación. Este modelo se utiliza para estructurar la respuesta JSON que se enviará al cliente después de procesar la solicitud de generación de texto.
    Args:
        BaseModel (_type_): La clase base de Pydantic para definir modelos de datos, utilizada para crear un modelo de respuesta estructurado que se convertirá automáticamente en JSON al ser devuelto por la API.    
    """
    seed: str
    generated_text: str
    strategy: str
    n_words_generated: int
    elapsed_ms: float

def _next_token_probs(x: np.ndarray) -> np.ndarray:
    """
    Calcula las probabilidades del siguiente token dado un input de tokens. Esta función toma una matriz de tokens como entrada, realiza una predicción utilizando el modelo de lenguaje cargado y procesa las probabilidades para asegurarse de que los tokens bloqueados (como PAD, UNK y BOS) tengan una probabilidad de 0. Si todas las probabilidades resultan en 0 después de bloquear los tokens, se asigna una distribución uniforme a los tokens restantes. Finalmente, se devuelve un array de probabilidades normalizado para el siguiente token.
    Args:    
        x (np.ndarray): Una matriz de tokens de entrada con forma (1, seq_len), donde seq_len es la longitud de la secuencia que el modelo espera como entrada.
    Returns:    
        np.ndarray: Un array de probabilidades normalizado para el siguiente token, con forma (vocab_size,), donde vocab_size es el tamaño del vocabulario del tokenizador. Las probabilidades de los tokens bloqueados (PAD, UNK, BOS) se establecen en 0, y las probabilidades restantes se normalizan para que sumen 1.
    """
    pred = model.predict(x, verbose=0)
    probs = pred[0, -1, :] if pred.ndim == 3 else pred[0]

    blocked = [
        tokenizer.word2idx.get(tokenizer.PAD),
        tokenizer.word2idx.get(tokenizer.UNK),
        tokenizer.word2idx.get(tokenizer.BOS),
    ]
    probs = probs.copy()
    for idx in blocked:
        if idx is not None and 0 <= idx < len(probs):
            probs[idx] = 0.0

    total = probs.sum()
    if total <= 0:
        probs = np.ones_like(probs, dtype=np.float64)
        for idx in blocked:
            if idx is not None and 0 <= idx < len(probs):
                probs[idx] = 0.0
        probs /= probs.sum()
    else:
        probs = probs / total

    return probs

def _generate(req: GenerateRequest) -> str:
    """
    Genera texto a partir de una semilla dada utilizando la estrategia de generación especificada en la solicitud. Esta función toma un objeto GenerateRequest como entrada, que contiene la semilla inicial, la estrategia de generación, el número de palabras a generar, la temperatura para muestreo y el valor de top_k. La función procesa la semilla para obtener los tokens iniciales, luego itera para generar el número especificado de palabras, utilizando la función _next_token_probs para obtener las probabilidades del siguiente token y aplicando la estrategia de generación seleccionada (greedy, sampling o top_k) para elegir el siguiente token. Finalmente, se decodifica la secuencia de tokens generados y se devuelve como texto.
    Args:
        req (GenerateRequest): La solicitud de generación de texto que contiene la semilla, la estrategia de generación, el número de palabras a generar, la temperatura y el valor de top_k.
    Returns:
        str: El texto generado a partir de la semilla proporcionada y la estrategia de generación especificada.
    """
    tokens = tokenizer.encode(req.seed)

    for _ in range(req.n_words):
        padded = tokens[-seq_len:]
        padded = [0] * (seq_len - len(padded)) + padded
        x = np.array([padded])
        probs = _next_token_probs(x)

        if req.strategy == "greedy":
            next_token = int(np.argmax(probs))
        elif req.strategy == "sampling":
            log_probs = np.log(probs + 1e-10) / req.temperature
            log_probs -= log_probs.max()
            scaled = np.exp(log_probs)
            scaled /= scaled.sum()
            next_token = int(np.random.choice(len(scaled), p=scaled))
        else:
            k = min(req.top_k, len(probs))
            top_k_idx = np.argsort(probs)[-k:]
            top_k_probs = probs[top_k_idx]
            log_probs = np.log(top_k_probs + 1e-10) / req.temperature
            log_probs -= log_probs.max()
            scaled = np.exp(log_probs)
            scaled /= scaled.sum()
            next_token = int(np.random.choice(top_k_idx, p=scaled))

        tokens.append(next_token)

    return tokenizer.decode(tokens)

@app.get("/")
async def root():
    """
    Endpoint raíz de la API. Devuelve un mensaje de bienvenida y una referencia a la documentación de la API.   
    Returns:
        dict: Un diccionario con un mensaje de bienvenida y la ruta a la documentación de la API.
    """
    return {"message": "API de Generación de Texto", "docs": "/docs"}

@app.get("/health")
async def health():
    """
    Endpoint de salud de la API. Devuelve información sobre el estado del modelo, el tokenizador y la configuración de limitación de tasa. Este endpoint se puede utilizar para verificar que la API está funcionando correctamente y que los componentes necesarios (modelo y tokenizador) están cargados y listos para generar texto.
    Returns:
        dict: Un diccionario con el estado de la API, incluyendo el estado del modelo, el tokenizador y la limitación de tasa.
    """
    return {
        "status": "ok",
        "model_loaded": True,
        "tokenizer_loaded": True,
        "rate_limiter_enabled": SLOWAPI_AVAILABLE,
    }

@app.post("/generate", response_model=GenerateResponse, dependencies=[Security(verify_api_key)])
@limiter.limit(f"{RATE_LIMIT}/minute")
async def generate(request: Request, body: GenerateRequest):
    """
    Endpoint para generar texto a partir de una semilla dada utilizando la estrategia de generación especificada en la solicitud.
    Args:
        request (Request): La solicitud HTTP entrante.
        body (GenerateRequest): La solicitud de generación de texto que contiene la semilla, la estrategia de generación, el número de palabras a generar, la temperatura y el valor de top_k.
    Returns:
        GenerateResponse: La respuesta de generación de texto que contiene la semilla, el texto generado, la estrategia utilizada, el número de palabras generadas y el tiempo transcurrido en milisegundos.
    """
    start = time.perf_counter()
    generated = _generate(body)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return GenerateResponse(
        seed=body.seed,
        generated_text=generated,
        strategy=body.strategy,
        n_words_generated=body.n_words,
        elapsed_ms=round(elapsed_ms, 2),
    )