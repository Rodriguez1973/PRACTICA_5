"""
discord_bot.py - Bot de Discord que usa la IA para generar texto
Práctica 5: Integración, Automatización y Modelos de Negocio

Instalación:
    pip install discord.py python-dotenv

Configuración:
    1. Crear archivo .env:
        DISCORD_TOKEN=tu_token_del_bot
        API_URL=http://localhost:8000
        API_KEY=tu_api_key

    2. Crear un servidor de Discord de prueba
    3. Agregar el bot con permisos necesarios

Uso:
    python discord_bot.py
"""

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
from ai_client import TextGenerationClient

# ─── Configuración de logging ──────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Cargar variables de entorno ───────────────────────────────────────
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
API_URL = os.getenv('API_URL', 'http://localhost:8000')
API_KEY = os.getenv('API_KEY', '%KhJh-yj44k[RMuJpy')

if not DISCORD_TOKEN:
    raise ValueError("❌ DISCORD_TOKEN no configurado en .env")

# ─── Crear cliente de IA ───────────────────────────────────────────────
ai_client = TextGenerationClient(base_url=API_URL, api_key=API_KEY)

# ─── Configuración del bot ────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# ─── Event: Bot listo ──────────────────────────────────────────────────
@bot.event
async def on_ready():
    logger.info(f"🤖 Bot conectado como {bot.user}")
    try:
        health = ai_client.health_check()
        if health['model_loaded']:
            logger.info("✅ API de IA disponible")
        else:
            logger.warning("⚠️ Modelo no cargado en API")
    except Exception as e:
        logger.error(f"❌ Error al conectar con API: {e}")

# ─── Comando: generar texto ───────────────────────────────────────────
@bot.command(
    name='generar',
    help='Genera texto a partir de un seed. Uso: !generar "tu texto aquí"'
)
async def generate(ctx, *, seed: str = None):
    """Generar texto usando la IA."""
    if not seed:
        await ctx.send("❌ Debes proporcionar un texto inicial. Uso: `!generar el científico descubrió`")
        return

    if len(seed) > 500:
        await ctx.send("❌ El texto inicial es demasiado largo (máximo 500 caracteres).")
        return

    # Indicador de carga
    async with ctx.typing():
        try:
            result = ai_client.generate(
                seed=seed,
                n_words=50,
                strategy='sampling',
                temperature=1.0
            )

            # Formato del mensaje
            message = f"""
🤖 **Generación de Texto**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 **Seed:** `{result.seed}`

✨ **Texto generado:**
{result.generated_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏱️ Tiempo: {result.elapsed_ms:.2f}ms
📊 Estrategia: {result.strategy}
            """

            await ctx.send(message)
            logger.info(f"✅ Generación exitosa para usuario {ctx.author}")

        except Exception as e:
            logger.error(f"Error en generación: {e}")
            await ctx.send(f"❌ Error: {str(e)}")

# ─── Comando: info ────────────────────────────────────────────────────
@bot.command(name='info', help='Muestra información del bot')
async def info(ctx):
    """Muestra información del bot y estado de la API."""
    try:
        health = ai_client.health_check()
        embed = discord.Embed(
            title="🤖 Bot de Generación de Texto",
            description="Genera texto usando IA LSTM",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Estado API",
            value=f"✅ {health['status']}" if health['model_loaded'] else "❌ Modelo no disponible",
            inline=False
        )
        embed.add_field(
            name="Vocabulario",
            value=f"{health['vocab_size']} tokens",
            inline=True
        )
        embed.add_field(
            name="Comandos Disponibles",
            value="`!generar` - Generar texto\n`!info` - Este mensaje\n`!help` - Ayuda detallada",
            inline=False
        )

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Error al obtener información: {e}")

# ─── Comando: ayuda personalizada ──────────────────────────────────────
@bot.command(name='help', help='Muestra ayuda detallada')
async def help_command(ctx):
    """Muestra ayuda detallada sobre el bot."""
    help_text = """
🤖 **Bot de Generación de Texto con IA LSTM**

**Comandos disponibles:**

`!generar <texto>`
Genera continuación automática del texto.
Ejemplo: `!generar el científico descubrió`

`!info`
Muestra el estado del bot y la API.

`!help`
Muestra este mensaje.

**Parámetros configurable:**
- Número de palabras a generar: 50 (configurable en código)
- Estrategia: sampling (equilibrado entre determinismo y creatividad)
- Temperatura: 1.0 (neutra)

**Notas:**
- El texto inicial debe tener entre 1 y 500 caracteres
- Máximo 50 palabras generadas por comando
- La API debe estar en ejecución: `uvicorn app:app --host 0.0.0.0 --port 8000`
    """
    await ctx.send(help_text)

# ─── Main ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("🚀 Iniciando bot de Discord...")
    bot.run(DISCORD_TOKEN)
