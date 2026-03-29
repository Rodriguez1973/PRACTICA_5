# PRÁCTICA 5: Integración, Automatización y Modelos de Negocio
# Aplicaciones de Inteligencia Artificial

## 📋 Descripción General

Esta práctica integra el modelo LSTM desarrollado en **Práctica 4** con tecnologías reales, automatiza procesos de negocio y analiza modelos de negocio viables basados en IA.

### Objetivos
- ✅ Integrar la IA con plataformas tecnológicas (web, bots, APIs)
- ✅ Demostrar automatización de procesos reales
- ✅ Analizar modelos de negocio sostenibles
- ✅ Explorar convergencia tecnológica (IoT, Blockchain)

---

## 🗂️ Estructura del Proyecto

```
d:\PRACTICA_5\
├── web_client\
│   ├── index.html           # Cliente web (UI moderna)
│   ├── styles.css           # Estilos CSS
│   └── app.js               # Lógica JavaScript
│
├── python_client\
│   └── ai_client.py         # Cliente Python para la API
│
├── integration_examples\
│   ├── discord_bot.py       # Bot de Discord
│   ├── telegram_bot.py      # Bot de Telegram
│   ├── tts_integration.py   # Integración Text-to-Speech
│   └── iot_blockchain_example.py  # IoT + Blockchain
│
├── business_analysis\
│   └── BUSINESS_PLAN.md     # Informe completo de negocio
│
├── README.md                # Este archivo
├── .env.example             # Ejemplo de configuración
└── requirements.txt         # Dependencias Python
```

---

## 🚀 Inicio Rápido

### 1. Levantar la API (incluida en esta práctica)

```powershell
# Opción A – Script automático (recomendado)
cd d:\PRACTICA_5
.\scripts\start_all.ps1
```

```powershell
# Opción B – Manual desde la raíz de PRACTICA_5
cd d:\PRACTICA_5
$env:MODEL_PATH='modelo/model_final.keras'; $env:TOKENIZER_PATH='tokenizer/tokenizer.json'
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

**Output esperado:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Cargando modelo desde: model_final.keras
INFO:     Modelo cargado. Seq_len=50
```

### 2. Probar Cliente Python

```bash
# Terminal 2
cd d:\PRACTICA_5\python_client
python -m venv venv
venv\Scripts\activate
pip install requests python-dotenv

python ai_client.py
```

**Output esperado:**
```
🤖 Cliente Python - Generador de Texto con IA
✅ Estado: ok
   Modelo: Cargado ✓
✨ Generando ejemplos...
```

### 3. Abrir Cliente Web

```bash
# Terminal 3: Servir archivos web (si tienes Python)
cd d:\PRACTICA_5\web_client
python -m http.server 8080
```

Luego abre: http://localhost:8080

---

## 📚 Guías por Sección

### A. Cliente Web (`web_client/`)

**Características:**
- Interfaz moderna y responsiva
- Generación con 3 estrategias (greedy, sampling, top-k)
- Control de temperatura y parámetros
- Historial local (localStorage)
- Health check de API

**Uso:**
1. Abre `index.html` en navegador
2. Configura URL de API: `http://localhost:8000`
3. Configura API Key: `changeme-secret-key`
4. Clickea "📡 Verificar Conexión"
5. Genera texto y experimenta

### B. Cliente Python (`python_client/`)

**Instalación:**
```bash
pip install requests python-dotenv
```

**Uso Básico:**
```python
from ai_client import TextGenerationClient

client = TextGenerationClient(
    base_url="http://localhost:8000",
    api_key="changeme-secret-key"
)

result = client.generate(
    seed="el científico descubrió",
    n_words=50,
    strategy="sampling"
)

print(result)
client.save_result(result, "output.json")
```

**Métodos disponibles:**
- `health_check()` - Verifica estado API
- `generate()` - Genera texto
- `batch_generate()` - Genera múltiples
- `save_result()` - Guarda JSON

### C. Bots de Integración (`integration_examples/`)

#### Discord Bot

**Requisitos:**
```bash
pip install discord.py python-dotenv
```

**Configuración (.env):**
```
DISCORD_TOKEN=tu_token_aqui
API_URL=http://localhost:8000
API_KEY=changeme-secret-key
```

**Comandos:**
- `!generar <texto>` - Genera continuación
- `!info` - Información del bot
- `!help` - Ayuda

**Ejecución:**
```bash
python integration_examples/discord_bot.py
```

#### Telegram Bot

**Requisitos:**
```bash
pip install python-telegram-bot python-dotenv
```

**Configuración (.env):**
```
TELEGRAM_TOKEN=tu_token_aqui
API_URL=http://localhost:8000
API_KEY=changeme-secret-key
```

**Comandos:**
- `/generar <texto>` - Genera continuación
- `/info` - Información del bot
- `/help` - Ayuda

**Ejecución:**
```bash
python integration_examples/telegram_bot.py
```

#### Text-to-Speech

**Requisitos:**
```bash
pip install gtts pyttsx3 python-dotenv
```

**Métodos:**
- **gTTS** - Google TTS (online, voz natural)
- **pyttsx3** - Offline, voces del sistema

**Ejecución:**
```bash
python integration_examples/tts_integration.py
```

Genera archivos `.mp3` o `.wav` con el texto.

### D. IoT + Blockchain Demo (`iot_blockchain_example.py`)

Demuestra convergencia tecnológica:

1. **Sensores IoT** → Lecturas de temperatura, presión, vibración
2. **IA** → Análisis automático y reportes en lenguaje natural
3. **Blockchain** → Certificación inmutable de reportes
4. **Smart Contract** → Acciones automáticas (alertas, pausa producción)

**Ejecución:**
```bash
python integration_examples/iot_blockchain_example.py
```

**Output de ejemplo:**
```
========== CICLO: OPERACIÓN NORMAL ==========
📊 PASO 1: Lectura de Sensores IoT
  [HORNO-01] T=320.5°C P=2.3bar V=1.2mm/s
  [PRENSA-02] T=280.0°C P=3.1bar V=0.8mm/s

🔍 PASO 2: Análisis de Anomalías
  ✅ Sin anomalías. Sistema normal.

🤖 PASO 3: Análisis IA
  Reporte generado: ...
```

---

## 📊 Análisis de Negocio

Ver `business_analysis/BUSINESS_PLAN.md` para análisis completo incluyendo:

### 1. Modelo de Automatización
- Casos reales de automatización (marketing, e-commerce, soporte)
- Métricas de eficiencia y ROI
- Ejemplos de procesos automatizados

### 2. Modelo de Negocio
- **SaaS**: Suscripción mensual (€29-€499)
- **Pay-Per-Use**: Pago por consumo (€0.01/1k tokens)
- **Freemium**: Gratis limitado + Premium

### 3. Estrategia Corporativa
- Cómo integrarse en empresas existentes
- Ventajas competitivas
- Timeline de implementación

### 4. Convergencia Tecnológica
- **IoT + IA**: Informes automáticos de sensores
- **Blockchain + IA**: Certificación de autoría
- **Vision + IA**: Análisis de documentos

---

## 🔧 Configuración Detallada

### Variables de Entorno (.env)

Crear archivo `.env` en raíz del proyecto:

```bash
# API REST (Práctica 4)
API_URL=http://localhost:8000
API_KEY=changeme-secret-key

# Discord (si usas discord_bot.py)
DISCORD_TOKEN=tu_token_de_bot_aqui

# Telegram (si usas telegram_bot.py)
TELEGRAM_TOKEN=tu_token_de_bot_aqui
```

### Instalación de Dependencias Completa

```bash
# Cliente Python
pip install requests python-dotenv

# Bots
pip install discord.py python-telegram-bot

# Text-to-Speech
pip install gtts pyttsx3

# Recomendado: todo junto
pip install requests python-dotenv discord.py python-telegram-bot gtts pyttsx3
```

---

## 📈 Casos de Uso Prácticos

### 1. Automatizar Emails de Marketing

```python
from ai_client import TextGenerationClient

client = TextGenerationClient()

# Generar asunto
subject = client.generate("Oferta especial", n_words=3, strategy="greedy")

# Generar cuerpo
body = client.generate(
    "Estimado cliente, te ofrecemos...",
    n_words=80
)

print(f"Subject: {subject.generated_text}")
print(f"Body: {body.generated_text}")
```

### 2. Chatbot Multi-plataforma

```
Usuario Discord: "!generar hola mundo"
        ↓
Discord Bot llama API
        ↓
Respuesta: "hola mundo es un programa clásico que..."
        ↓
Envía a Discord → Telegram → Web chat
```

### 3. Monitoreo Industrial (IoT + IA)

```
Sensor: Temperatura = 350°C
  ↓
Script Python verifica cada 5 minutos
  ↓
Si T > 340°C → IA genera alerta
  ↓
Envía email/SMS al supervisor
```

---

## 🧪 Pruebas y Validación

### Checklist de Pruebas

- [ ] API Práctica 4 ejecutándose en puerto 8000
- [ ] Cliente web abre en navegador
- [ ] Health check muestra "✅ Conectado"
- [ ] Generación de texto funciona
- [ ] Cliente Python genera resultados
- [ ] Discord bot responde comandos
- [ ] Telegram bot responde comandos
- [ ] TTS genera archivos de audio

### Comando Quick Test

```bash
# Todos los clientes en paralelo (3 terminales)

# Terminal 1: API (desde adjuntos locales)
cd d:\PRACTICA_5\adjuntos; $env:MODEL_PATH='model_final.keras'; $env:TOKENIZER_PATH='tokenizer.json'; python -m uvicorn app:app --port 8000

# Terminal 2: Cliente Python
cd d:\PRACTICA_5\python_client && python ai_client.py

# Terminal 3: Cliente Web
cd d:\PRACTICA_5\web_client && python -m http.server 8080

# Luego en navegador: http://localhost:8080
```

---

## 💡 Ideas para Ampliar

1. **CLI Application**: Crear CLI interactiva
2. **REST API Wrapper**: Exposer cliente Python como API
3. **Database**: Guardar histórico de generaciones
4. **Authentication**: JWT para seguridad
5. **Caching**: Redis para respuestas frecuentes
6. **Swagger Docs**: Auto-documenting API
7. **Tests**: Unit tests y integration tests
8. **Docker**: Containerizar todo
9. **Monitoring**: logs del sistema y métricas
10. **UI Avanzada**: Dashboard con gráficos

---

## 📞 Soporte y Troubleshooting

### Error: "No se puede conectar a http://localhost:8000"

**Solución:**
1. Verifica que Práctica 4 está ejecutándose
2. Cambia PORT si hay conflicto: `--port 8001`
3. Usa IP pública: `http://192.168.x.x:8000`

### Error: "API Key inválida"

**Solución:**
1. Verifica variable `API_KEY` en `.env`
2. Por defecto es: `changeme-secret-key`
3. Cambia en `app.py` de Práctica 4 si es necesario

### Error: "Rate limit exceeded"

**Solución:**
1. Máximo 10 requests/minuto por IP (configurable)
2. Espera 1 minuto
3. Cambia en `app.py`: `RATE_LIMIT=30`

### Discord/Telegram no responden

**Solución:**
1. Verifica tokens en `.env`
2. Bot debe tener permisos de mensaje
3. Revisa logs: `logging.basicConfig(level=logging.DEBUG)`

---

## 📝 Guía de Entrega

Entregar como ZIP con estructura:

```
PRACTICA_5.zip
├── web_client/ (index.html, styles.css, app.js)
├── python_client/ (ai_client.py)
├── integration_examples/ (discord_bot.py, telegram_bot.py, tts_integration.py, iot_blockchain_example.py)
├── business_analysis/ (BUSINESS_PLAN.md)
├── README.md (este archivo)
├── INFORME.md o .docx (si requiere presentación formal)
└── .env.example
```

**Documentación requerida:**
- ✅ README con instrucciones
- ✅ BUSINESS_PLAN.md completo
- ✅ Diagramas/mockups de UI (si es posible)
- ✅ Video demo (10-15 min) - OPCIONAL

---

## 🏆 Evaluación

| Criterio | Puntos |
|----------|--------|
| Cliente Web Funcional | 20 |
| Cliente Python | 15 |
| Integración (Discord/Telegram) | 20 |
| IoT + Blockchain Integration | 15 |
| Business Plan Completo | 20 |
| Documentación | 10 |
| **TOTAL** | **100** |

---

## 📚 Recursos Recomendados

### Documentación
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Python Telegram Bot](https://python-telegram-bot.readthedocs.io/)
- [gTTS Documentation](https://gtts.readthedocs.io/)

### Herramientas Online
- Probar API: [Postman](https://www.postman.com/), [Insomnia](https://insomnia.rest/)
- Crear bots Discord: [@BotFather en Discord](https://discord.gg/discord-developers)
- Crear bots Telegram: [@BotFather en Telegram](https://telegram.me/botfather)
- Blockchain: [Remix.ethereum.org](https://remix.ethereum.org/)

### Cursos/Tutoriales
- [FastAPI Full Course](https://www.youtube.com/results?search_query=fastapi+full+course)
- [Discord.py Bot Tutorial](https://www.youtube.com/results?search_query=discord+bot+python)
- [Blockchain Basics](https://www.coursera.org/learn/blockchain-basics)

---

## 📄 Licencia y Créditos

- **Práctica 4**: Modelo LSTM entrenado
- **Práctica 5**: Integración y análisis de negocio
- Desarrollado para: Asignatura de IA
- Año: 2026

---

## ✍️ Notas Finales

Esta práctica demuestra que **la IA no es un producto final**, sino un **componente tecnológico** que cobra valor al integrarse en contextos reales.

**Conceptos clave:**
- Integración > Innovación pura
- User Experience > Precisión del modelo
- ROI medible > Features bonitas
- Escalabilidad > Perfección inicial

Implementa MVP primero, luego itera basándote en feedback real.

---

**Última actualización:** Marzo 2026  
**Versión:** 1.0  
**Estado:** Completo y funcional
