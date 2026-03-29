"""
telegram_bot.py - Bot de Telegram que usa la IA para generar texto
Práctica 5: Integración, Automatización y Modelos de Negocio

Instalación:
    pip install python-telegram-bot python-dotenv

Configuración:
    1. Crear archivo .env:
        TELEGRAM_TOKEN=tu_token_del_bot
        API_URL=http://localhost:8000
        API_KEY=tu_api_key

    2. Obtener token en @BotFather de Telegram
    3. Crear un grupo de prueba y agregar el bot

Uso:
    python telegram_bot.py
"""

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv
import logging
from ai_client import TextGenerationClient

# ─── Configuración de logging ──────────────────────────────────────────
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── Cargar variables de entorno ───────────────────────────────────────
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
API_URL = os.getenv('API_URL', 'http://localhost:8000')
API_KEY = os.getenv('API_KEY', '%KhJh-yj44k[RMuJpy')

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN no configurado en .env")

# ─── Crear cliente de IA ───────────────────────────────────────────────
ai_client = TextGenerationClient(base_url=API_URL, api_key=API_KEY)

# ─── Handlers ──────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start."""
    welcome_message = """
🤖 ¡Hola! Soy un bot generador de texto con IA.

*Cómo usarme:*
1. Envía `/generar tu texto aquí` para generar una continuación
2. Usa `/info` para ver información del bot
3. Usa `/help` para ver todos mis comandos

*Ejemplo:*
`/generar el científico descubrió un nuevo planeta`

¡Experimenta con diferentes textos y estrategias!
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /generar <texto>."""
    if not context.args:
        await update.message.reply_text(
            "❌ Debes proporcionar un texto.\n"
            "Uso: `/generar tu texto aquí`",
            parse_mode='Markdown'
        )
        return

    seed = ' '.join(context.args)
    if len(seed) > 500:
        await update.message.reply_text("❌ El texto es demasiado largo (máximo 500 caracteres).")
        return

    # Indicador de carga
    await update.message.chat.send_action("typing")

    try:
        result = ai_client.generate(
            seed=seed,
            n_words=50,
            strategy='sampling',
            temperature=1.0
        )

        response = f"""
🤖 *Generación de Texto*
━━━━━━━━━━━━━━━━━━━━━━
📝 *Seed:*
`{result.seed}`

✨ *Texto generado:*
```
{result.generated_text}
```

━━━━━━━━━━━━━━━━━━━━━━
⏱️ Tiempo: {result.elapsed_ms:.2f}ms
📊 Palabras: {result.n_words_generated}
        """

        await update.message.reply_text(response, parse_mode='Markdown')
        logger.info(f"✅ Generación exitosa para {update.effective_user.first_name}")

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /info."""
    try:
        health = ai_client.health_check()
        info_text = f"""
🤖 *Bot de Generación de Texto*
━━━━━━━━━━━━━━━━━━━━━━━━
*Estado API:*
{'✅ Conectado' if health['model_loaded'] else '❌ Desconectado'}

*Vocabulario:*
{health['vocab_size']} tokens

*Comandos:*
• `/generar` - Generar texto
• `/info` - Esta información
• `/help` - Ayuda detallada
        """
        await update.message.reply_text(info_text, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /help."""
    help_text = """
🤖 *Ayuda - Bot IA*
━━━━━━━━━━━━━━━━━━━━━━

*Comandos:*

`/generar <texto>`
Genera continuación usando IA LSTM

*Ejemplos:*
• `/generar el científico descubrió`
• `/generar en un futuro lejano`
• `/generar la inteligencia artificial`

*Parámetros:*
• Máximo 500 caracteres de entrada
• Genera hasta 50 palabras
• Estrategia: sampling (equilibrada)

*Requisitos:*
La API REST debe estar en ejecución
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja mensajes de texto normal."""
    # Ignorar mensajes que no son comandos
    if update.message.text.startswith('/'):
        return
    
    # Opcionalmente, responder a menciones
    pass

# ─── Main ──────────────────────────────────────────────────────────────

def main():
    """Inicia el bot."""
    logger.info("🚀 Iniciando bot de Telegram...")

    # Crear aplicación
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Agregar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("generar", generate_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Iniciar el bot
    logger.info("✅ Bot iniciado. Presiona Ctrl+C para detener.")
    application.run_polling()

if __name__ == "__main__":
    main()
