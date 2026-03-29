# GUÍA RÁPIDA DE EJECUCIÓN - Práctica 5

## ⚡ Inicio Super Rápido (5 minutos)

### Paso 1: Levantar la API local (adjuntos de esta práctica)

```powershell
# PowerShell - Terminal 1 (script automático)
cd d:\PRACTICA_5
.\scripts\start_all.ps1
```

```powershell
# O manualmente desde la carpeta adjuntos:
cd d:\PRACTICA_5\adjuntos
$env:MODEL_PATH='model_final.keras'; $env:TOKENIZER_PATH='tokenizer.json'
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

Espera hasta ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Cargando modelo...
```

### Paso 2: Ejecutar Cliente Web

```powershell
# PowerShell - Terminal 2
cd d:\PRACTICA_5\web_client
python -m http.server 8080
```

Abre navegador: **http://localhost:8080**

1. Haz click en "📡 Verificar Conexión" (debe mostrar ✅)
2. Escribe en "Texto Inicial": `el científico descubrió`
3. Haz click en "✨ Generar Texto"
4. ¡Listo! Deberías ver texto generado

### Paso 3: Cliente Python (Opcional)

```powershell
# PowerShell - Terminal 3
cd d:\PRACTICA_5\python_client
python -m venv venv
venv\Scripts\activate
pip install requests python-dotenv
python ai_client.py
```

---

## 🤖 Ejecutar Bots (Requiere tokens)

### Discord Bot

1. Crea archivo `.env` en `d:\PRACTICA_5`:
```
DISCORD_TOKEN=tu_token_aqui
API_URL=http://localhost:8000
API_KEY=changeme-secret-key
```

2. Instala dependencias:
```powershell
pip install discord.py python-dotenv
```

3. Ejecuta:
```powershell
python d:\PRACTICA_5\integration_examples\discord_bot.py
```

4. En Discord:
```
!generar el futuro de la IA es
```

### Telegram Bot

1. Actualiza `.env`:
```
TELEGRAM_TOKEN=tu_token_aqui
API_URL=http://localhost:8000
API_KEY=changeme-secret-key
```

2. Instala:
```powershell
pip install python-telegram-bot python-dotenv
```

3. Ejecuta:
```powershell
python d:\PRACTICA_5\integration_examples\telegram_bot.py
```

4. En Telegram:
```
/generar el futuro de la IA es
```

---

## 🎤 Text-to-Speech

```powershell
cd d:\PRACTICA_5\integration_examples
pip install gtts pyttsx3 python-dotenv

python tts_integration.py
```

Espera a que genere archivos `.mp3` o `.wav`.

---

## ⛓️ IoT + Blockchain Demo

```powershell
cd d:\PRACTICA_5\integration_examples

python iot_blockchain_example.py
```

Verás simulación completa de IoT → IA → Blockchain → Smart Contract.

---

## 📊 Ver Informe de Negocio

```powershell
# Simplemente abre el archivo:
start d:\PRACTICA_5\business_analysis\BUSINESS_PLAN.md

# O en editor Visual Studio Code:
code d:\PRACTICA_5\business_analysis\BUSINESS_PLAN.md
```

---

## 🔧 Troubleshooting Rápido

| Error | Solución |
|-------|----------|
| "Connection refused" | ¿Está Práctica 4 ejecutándose? Ver Paso 1 |
| "API Key inválida" | Verifica `.env` API_KEY = `changeme-secret-key` |
| "Port 8000 in use" | Cambia puerto: `uvicorn app:app --port 8001` |
| "Rate limit exceeded" | Espera 1 minuto, máximo 10 req/min |
| "No module requests" | `pip install requests` |

---

## 📁 Archivos Clave

```
d:\PRACTICA_5\
├── web_client/
│   └── index.html          👈 Abre aquí en navegador
├── python_client/
│   └── ai_client.py        👈 Ejecuta para test
├── integration_examples/
│   ├── discord_bot.py      👈 Discord
│   ├── telegram_bot.py     👈 Telegram
│   ├── tts_integration.py  👈 Audio
│   └── iot_blockchain_example.py  👈 IoT + Blockchain
├── business_analysis/
│   └── BUSINESS_PLAN.md    👈 Informe completo
└── README.md               👈 Documentación
```

---

## ✅ Checklist de Validación

- [ ] Práctica 4 ejecutándose (puerto 8000)
- [ ] Cliente Web abre (port 8080)
- [ ] Health check muestra ✅
- [ ] Texto generado correctamente
- [ ] Cliente Python genera resultados
- [ ] Bots responden (si configuraste tokens)
- [ ] TTS genera archivos de audio
- [ ] IoT demo muestra blockchain records

---

## 📞 Ayuda Rápida

### Ver logs en tiempo real
```powershell
# Terminal 1 (API)
# Verás: "Generación completada | strategy=sampling..."
```

### Cambiar parámetros desde web
1. Temperatura: Slider 0.1 - 2.0
2. Estrategia: Dropdown (greedy, sampling, top_k)
3. N palabras: Input 1-200

### Exportar resultados
```powershell
# Cliente Python guarda JSON automáticamente
# Busca: d:\PRACTICA_5\python_client\generation_result_*.json
```

---

## 🎓 Próximos Pasos

1. ✅ Haz funcionar todo (checklist arriba)
2. 📝 Lee BUSINESS_PLAN.md completamente
3. 🔧 Personaliza web_client/app.js con tu branding
4. 🚀 Deploya a servidor real (Heroku, Azure, aws)
5. 📊 Agregó métricas y analytics
6. 💰 Implementa pagos (Stripe)
7. 🌍 Multiidioma

---

**¡Listo!** Ahora tienes un sistema completo de IA integrado con web, bots, y análisis de negocio.

**Tiempo total de setup:** 15 minutos  
**Líneas de código funcional:** ~2,000+  
**Casos de uso implementados:** 5+

🎉 **¡Felicidades! Has completado Práctica 5.**
