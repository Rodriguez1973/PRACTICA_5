"""
tts_integration.py - Integración con Text-to-Speech (gTTS, pyttsx3, Azure)
Práctica 5: Integración, Automatización y Modelos de Negocio

Instalación:
    pip install gtts pyttsx3 python-dotenv

Ejemplo 1 - gTTS (Google Text-to-Speech):
    Requiere internet, voz natural, múltiples idiomas.

Ejemplo 2 - pyttsx3:
    Sin internet requerido, funciona offline con voces del sistema.

Ejemplo 3 - Azure Speech Services (opcional):
    Mejor calidad, requiere suscripción Azure.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

# Asegura que el script pueda importar el cliente al ejecutarse desde integration_examples/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python_client.ai_client import TextGenerationClient

# ─── Importes opcionales para TTS ──────────────────────────────────────
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# ─── Configuración ────────────────────────────────────────────────────
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = os.getenv('API_URL', 'http://localhost:8000')
API_KEY = os.getenv('API_KEY', '%KhJh-yj44k[RMuJpy')

# ─── Clientes ─────────────────────────────────────────────────────────
ai_client = TextGenerationClient(base_url=API_URL, api_key=API_KEY)


class TextToSpeechIntegration:
    """Integración con servicio de Text-to-Speech."""

    @staticmethod
    def convert_gtts(text: str, language: str = 'es', output_file: str = 'output.mp3') -> bool:
        """
        Convierte texto a voz usando Google Text-to-Speech.

        Args:
            text: Texto a convertir
            language: Código de idioma (ej: 'es' para español, 'en' para inglés)
            output_file: Ruta del archivo de salida

        Returns:
            True si es exitoso, False en caso contrario
        """
        if not GTTS_AVAILABLE:
            logger.error("❌ gTTS no está instalado. Instala con: pip install gtts")
            return False

        try:
            logger.info(f"🔊 Convirtiendo texto a voz (gTTS)...")
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(output_file)
            logger.info(f"✅ Audio guardado en: {output_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Error en gTTS: {e}")
            return False

    @staticmethod
    def convert_pyttsx3(text: str, output_file: str = 'output.wav', rate: int = 150) -> bool:
        """
        Convierte texto a voz usando pyttsx3 (offline).

        Args:
            text: Texto a convertir
            output_file: Ruta del archivo de salida
            rate: Velocidad de lectura (palabras por minuto)

        Returns:
            True si es exitoso, False en caso contrario
        """
        if not PYTTSX3_AVAILABLE:
            logger.error("❌ pyttsx3 no está instalado. Instala con: pip install pyttsx3")
            return False

        try:
            logger.info(f"🔊 Convirtiendo texto a voz (pyttsx3)...")
            engine = pyttsx3.init()
            engine.setProperty('rate', rate)
            engine.setProperty('volume', 0.9)

            # Listar voces disponibles
            voices = engine.getProperty('voices')
            logger.info(f"Voces disponibles: {len(voices)}")

            # Usar voz española si está disponible
            for voice in voices:
                if 'spanish' in voice.name.lower() or 'español' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    logger.info(f"✅ Usando voz: {voice.name}")
                    break

            engine.save_to_file(text, output_file)
            engine.runAndWait()
            logger.info(f"✅ Audio guardado en: {output_file}")
            return True

        except Exception as e:
            logger.error(f"❌ Error en pyttsx3: {e}")
            return False


# ─── Pipeline: Generar texto → Convertir a voz ─────────────────────

def generate_and_speak(seed: str, method: str = 'gtts', language: str = 'es') -> None:
    """
    Genera texto usando IA y lo convierte a voz.

    Args:
        seed: Texto inicial
        method: Método de TTS ('gtts' o 'pyttsx3')
        language: Idioma (para gTTS)
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Generando texto y convirtiendo a voz")
    logger.info(f"{'='*60}")

    try:
        # Paso 1: Generar texto
        logger.info(f"📝 Generando texto desde: '{seed}'")
        result = ai_client.generate(seed=seed, n_words=50)
        logger.info(f"✅ Texto generado ({result.n_words_generated} palabras)")

        # Paso 2: Convertir a voz
        full_text = result.generated_text
        output_file = f"speech_{result.strategy}.{'mp3' if method == 'gtts' else 'wav'}"

        if method == 'gtts':
            success = TextToSpeechIntegration.convert_gtts(
                text=full_text,
                language=language,
                output_file=output_file
            )
        else:
            success = TextToSpeechIntegration.convert_pyttsx3(
                text=full_text,
                output_file=output_file
            )

        if success:
            logger.info(f"\n✅ Pipeline completado:")
            logger.info(f"   - Texto generado ({result.n_words_generated} palabras)")
            logger.info(f"   - Audio generado: {output_file}")
            logger.info(f"   - Tiempo total: {result.elapsed_ms:.2f}ms (generación)")
        else:
            logger.error("❌ Error en la conversión de voz")

    except Exception as e:
        logger.error(f"❌ Error en pipeline: {e}")


# ─── Main: Ejemplos ────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("🎤 Integración Text-to-Speech con IA")
    print("=" * 60)

    # Ejemplos
    examples = [
        ("la inteligencia artificial", 'gtts'),
        ("en un futuro lejano", 'gtts' if GTTS_AVAILABLE else 'pyttsx3'),
        ("la inteligencia artificial", 'pyttsx3' if PYTTSX3_AVAILABLE else 'gtts'),
    ]

    for seed, method in examples:
        print(f"\n📚 Ejemplo: '{seed}' ({method})")
        print("-" * 60)

        # Verificar disponibilidad
        if method == 'gtts' and not GTTS_AVAILABLE:
            print(f"⚠️  gTTS no disponible. Instala: pip install gtts")
            continue
        elif method == 'pyttsx3' and not PYTTSX3_AVAILABLE:
            print(f"⚠️  pyttsx3 no disponible. Instala: pip install pyttsx3")
            continue

        generate_and_speak(seed, method=method, language='es')

    print(f"\n{'='*60}")
    print("✅ Generación completada. Revisa los archivos de audio.")
    print(f"{'='*60}")
