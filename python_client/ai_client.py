"""
ai_client.py - Cliente Python para la API REST de generación de texto
Práctica 5: Integración, Automatización y Modelos de Negocio

Ejemplo de uso:
    client = TextGenerationClient("http://localhost:8000", "tu-api-key")
    result = client.generate("el científico descubrió", n_words=50)
    print(result['generated_text'])
"""

import requests
import json
from typing import Optional, Literal
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GenerationResult:
    """Resultado de una generación de texto."""
    seed: str
    generated_text: str
    strategy: str
    n_words_generated: int
    elapsed_ms: float
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            'seed': self.seed,
            'generated_text': self.generated_text,
            'strategy': self.strategy,
            'n_words_generated': self.n_words_generated,
            'elapsed_ms': self.elapsed_ms,
            'timestamp': self.timestamp,
        }

    def __str__(self) -> str:
        return f"""
╔═══════════════════════════════════════════════════════════════╗
║                    RESULTADO DE GENERACIÓN                     ║
╠═══════════════════════════════════════════════════════════════╣
Seed: {self.seed}
───────────────────────────────────────────────────────────────
Texto generado:
{self.generated_text}
───────────────────────────────────────────────────────────────
Estrategia: {self.strategy}
Palabras generadas: {self.n_words_generated}
Tiempo: {self.elapsed_ms:.2f} ms
╚═══════════════════════════════════════════════════════════════╝
"""


class TextGenerationClient:
    """Cliente para la API REST de generación de texto."""

    def __init__(
        self, 
        base_url: str = "http://localhost:8000",
        api_key: str = "%KhJh-yj44k[RMuJpy",
        timeout: int = 30,
    ):
        """
        Inicializa el cliente.

        Args:
            base_url: URL base de la API (ej: http://localhost:8000)
            api_key: Clave de autenticación de la API
            timeout: Tiempo de espera máximo en segundos
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
        })

    def health_check(self) -> dict:
        """
        Verifica el estado de la API.

        Returns:
            Diccionario con status del servicio

        Raises:
            requests.exceptions.RequestException: Error de conexión
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error en health check: {str(e)}")

    def generate(
        self,
        seed: str,
        n_words: int = 50,
        strategy: Literal["greedy", "sampling", "top_k"] = "sampling",
        temperature: float = 1.0,
        top_k: int = 40,
    ) -> GenerationResult:
        """
        Genera texto a partir de un seed.

        Args:
            seed: Texto inicial para la generación (1-500 caracteres)
            n_words: Número de palabras a generar (1-200)
            strategy: Estrategia de generación ("greedy", "sampling", "top_k")
            temperature: Temperatura para muestreo (0.1-2.0)
            top_k: K para top-k sampling (1-500)

        Returns:
            GenerationResult con el texto generado

        Raises:
            ValueError: Si los parámetros no son válidos
            requests.exceptions.RequestException: Error de conexión
        """
        # Validación de parámetros
        if not seed or len(seed) > 500:
            raise ValueError("Seed debe tener 1-500 caracteres")
        if not 1 <= n_words <= 200:
            raise ValueError("n_words debe estar entre 1 y 200")
        if strategy not in {"greedy", "sampling", "top_k"}:
            raise ValueError(f"Estrategia inválida: {strategy}")
        if not 0.1 <= temperature <= 2.0:
            raise ValueError("Temperatura debe estar entre 0.1 y 2.0")
        if not 1 <= top_k <= 500:
            raise ValueError("top_k debe estar entre 1 y 500")

        payload = {
            'seed': seed,
            'n_words': n_words,
            'strategy': strategy,
            'temperature': temperature,
            'top_k': top_k,
        }

        try:
            response = self.session.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return GenerationResult(**data)
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise Exception("API Key inválida")
            elif response.status_code == 429:
                raise Exception("Límite de tasa excedido. Intenta más tarde.")
            else:
                raise Exception(f"Error en generación: {response.json().get('detail', str(e))}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de conexión: {str(e)}")

    def batch_generate(
        self,
        seeds: list[str],
        **kwargs
    ) -> list[GenerationResult]:
        """
        Genera texto para múltiples seeds.

        Args:
            seeds: Lista de textos iniciales
            **kwargs: Parámetros adicionales para generate()

        Returns:
            Lista de GenerationResult
        """
        results = []
        for seed in seeds:
            result = self.generate(seed, **kwargs)
            results.append(result)
        return results

    def save_result(self, result: GenerationResult, filename: str) -> None:
        """
        Guarda un resultado en JSON.

        Args:
            result: GenerationResult a guardar
            filename: Ruta del archivo
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    def close(self) -> None:
        """Cierra la sesión HTTP."""
        self.session.close()


# ─── Ejemplo de uso ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("🤖 Cliente Python - Generador de Texto con IA")
    print("=" * 60)

    # Crear cliente
    client = TextGenerationClient(
        base_url="http://localhost:8000",
        api_key="changeme-secret-key"
    )

    try:
        # Health check
        print("\n📡 Verificando conexión...")
        health = client.health_check()
        print(f"✅ Estado: {health['status']}")
        print(f"   Modelo: {'Cargado ✓' if health['model_loaded'] else 'No disponible ✗'}")
        print(f"   Tokenizador: {'Cargado ✓' if health['tokenizer_loaded'] else 'No disponible ✗'}")
        print(f"   Vocabulario: {health['vocab_size']} tokens")

        # Ejemplos de generación
        examples = [
            ("el científico descubrió", 50, "sampling"),
            ("en un futuro lejano", 40, "top_k"),
            ("la inteligencia artificial", 60, "greedy"),
        ]

        print("\n✨ Generando ejemplos...")
        results = []
        for seed, n_words, strategy in examples:
            print(f"\n📝 Generando desde: '{seed}' ({strategy})")
            result = client.generate(
                seed=seed,
                n_words=n_words,
                strategy=strategy,
                temperature=1.0 if strategy != "greedy" else 0.7,
            )
            results.append(result)
            print(result)

        # Guardar resultados
        print("\n💾 Guardando resultados...")
        for i, result in enumerate(results):
            client.save_result(result, f"generation_result_{i+1}.json")
        print("✅ Resultados guardados en generation_result_*.json")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        client.close()
