"""
main.py - Punto de entrada de PRACTICA_5
Lanza la API REST y el servidor web estático en terminales independientes,
verifica el endpoint /health y abre el navegador automáticamente.

Uso:
    python main.py
    python main.py --api-port 8000 --web-port 8080 --api-key changeme-secret-key
"""

import argparse
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import urllib.request
import urllib.error
import json

# ── Rutas base ────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parent
MODEL_PATH  = ROOT / "modelo"    / "model_final.keras"
TOKEN_PATH  = ROOT / "tokenizer" / "tokenizer.json"
APP_PY      = ROOT / "app.py"
WEB_DIR     = ROOT / "web_client"
VENV_DIR    = ROOT / ".venv"

# ── Argumentos CLI ────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Lanzador de PRACTICA_5")
parser.add_argument("--api-port",  type=int, default=8000)
parser.add_argument("--web-port",  type=int, default=8080)
parser.add_argument("--api-key",   default="%KhJh-yj44k[RMuJpy")
parser.add_argument("--rate-limit", default="10")
args = parser.parse_args()

API_PORT   = args.api_port
WEB_PORT   = args.web_port
API_KEY    = args.api_key
RATE_LIMIT = args.rate_limit

# ── Verificaciones previas ────────────────────────────────────────────────────
def check_files():
    missing = []
    for p in (MODEL_PATH, TOKEN_PATH, APP_PY, WEB_DIR):
        if not p.exists():
            missing.append(str(p))
    if missing:
        print("[ERROR] Archivos requeridos no encontrados:")
        for m in missing:
            print(f"        {m}")
        sys.exit(1)

# ── Localizar Python del venv ─────────────────────────────────────────────────
def find_venv_python() -> str:
    candidates = [
        VENV_DIR / "Scripts" / "python.exe",
        VENV_DIR / "Scripts" / "python3.exe",
        VENV_DIR / "bin"     / "python",
        VENV_DIR / "bin"     / "python3",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return sys.executable  # fallback: Python que corre este script

# ── Crear venv e instalar dependencias si hacen falta ────────────────────────
DEPS_PY313 = [
    "tensorflow==2.21.0",
    "numpy>=2.1.0,<3.0.0",
    "fastapi>=0.115.0,<1.0.0",
    "uvicorn[standard]>=0.35.0,<1.0.0",
    "pydantic>=2.11.0,<3.0.0",
    "slowapi==0.1.9",
    "python-dotenv==1.0.1",
]
DEPS_LEGACY = [
    "tensorflow==2.21.0",
    "numpy==1.26.4",
    "fastapi==0.111.0",
    "uvicorn[standard]==0.30.1",
    "pydantic==2.7.1",
    "slowapi==0.1.9",
    "python-dotenv==1.0.1",
]

def ensure_venv():
    python_exe = find_venv_python()
    if python_exe == sys.executable and not (VENV_DIR / "Scripts").exists():
        print("[INFO] Creando entorno virtual en .venv ...")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        python_exe = find_venv_python()

    # Detectar versión del venv
    result = subprocess.run(
        [python_exe, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
        capture_output=True, text=True
    )
    version = result.stdout.strip()
    print(f"[INFO] Python en .venv: {version}")

    deps = DEPS_PY313 if version == "3.13" else DEPS_LEGACY
    print("[INFO] Actualizando pip e instalando dependencias ...")
    subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([python_exe, "-m", "pip", "install"] + deps, check=True)

    return python_exe

# ── Lanzar proceso en nueva ventana de terminal ───────────────────────────────
def launch_in_new_terminal(title: str, command: str):
    """Abre una nueva ventana pwsh con el comando dado."""
    subprocess.Popen(
        ["pwsh", "-NoExit", "-Command", command],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )

# ── Health check con reintentos ───────────────────────────────────────────────
def wait_for_api(url: str, retries: int = 15, delay: float = 2.0) -> bool:
    print(f"[INFO] Esperando a que la API responda en {url} ...")
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read())
            print(f"[OK]   API lista: status={data.get('status')}, "
                  f"model_loaded={data.get('model_loaded')}, "
                  f"tokenizer_loaded={data.get('tokenizer_loaded')}")
            return True
        except Exception:
            print(f"[INFO] Intento {i+1}/{retries} — esperando {delay}s ...")
            time.sleep(delay)
    print("[WARN] No se pudo confirmar /health. La API puede tardar un poco más.")
    return False

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  PRACTICA_5 — Lanzador unificado")
    print("=" * 60)

    check_files()
    python_exe = ensure_venv()

    # Comando API
    api_cmd = (
        f"$env:MODEL_PATH='modelo/model_final.keras'; "
        f"$env:TOKENIZER_PATH='tokenizer/tokenizer.json'; "
        f"$env:API_KEY='{API_KEY}'; "
        f"$env:RATE_LIMIT='{RATE_LIMIT}'; "
        f"Set-Location '{ROOT}'; "
        f"& '{python_exe}' -m uvicorn app:app --host 0.0.0.0 --port {API_PORT}"
    )

    # Comando servidor web estático
    web_cmd = (
        f"Set-Location '{ROOT / 'web_client'}'; "
        f"& '{sys.executable}' -m http.server {WEB_PORT}"
    )

    print(f"[INFO] Iniciando API REST  → http://localhost:{API_PORT}/docs")
    launch_in_new_terminal("API REST", api_cmd)

    time.sleep(3)

    print(f"[INFO] Iniciando cliente web → http://localhost:{WEB_PORT}")
    launch_in_new_terminal("Web Client", web_cmd)

    # Esperar a que la API arranque
    wait_for_api(f"http://localhost:{API_PORT}/health")

    # Abrir navegador
    web_url = f"http://localhost:{WEB_PORT}"
    print(f"[INFO] Abriendo navegador en {web_url}")
    webbrowser.open(web_url)

    print()
    print("Listo.")
    print(f"  1) API docs : http://localhost:{API_PORT}/docs")
    print(f"  2) Web app  : http://localhost:{WEB_PORT}")
    print(f"  3) API Key  : {API_KEY}")
    print()
    print("Cierra las terminales abiertas o usa stop_all.ps1 para detener los servicios.")


if __name__ == "__main__":
    main()
