"""
iot_blockchain_example.py - Ejemplo de convergencia IoT + Blockchain + IA
Práctica 5: Integración, Automatización y Modelos de Negocio

Caso de Uso: Planta Industrial con Monitoreo Inteligente

Flujo:
1. Sensores IoT envían datos de producción
2. IA analiza y genera informe en lenguaje natural
3. Informe se certifica en blockchain (inmutable)
4. Smart contract ejecuta acciones automáticas si es necesario
"""

import json
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict
import logging
import sys
from pathlib import Path

# Add python_client to path to import ai_client
PYTHON_CLIENT_PATH = Path(__file__).parent.parent / "python_client"
sys.path.insert(0, str(PYTHON_CLIENT_PATH))

from ai_client import TextGenerationClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Simulación de Datos IoT ───────────────────────────────────────────

@dataclass
class SensorReading:
    """Lectura de sensor IoT."""
    sensor_id: str
    timestamp: str
    temperature: float  # Celsius
    pressure: float     # Bar
    vibration: float    # mm/s
    production_units: int
    error_count: int

    def __repr__(self) -> str:
        return f"[{self.sensor_id}] T={self.temperature}°C P={self.pressure}bar V={self.vibration}mm/s"


class IoTSimulator:
    """Simula lecturas de sensores IoT."""

    @staticmethod
    def simulate_normal_operation() -> List[SensorReading]:
        """Operación normal de la planta."""
        return [
            SensorReading(
                sensor_id="HORNO-01",
                timestamp=datetime.now().isoformat(),
                temperature=320.5,
                pressure=2.3,
                vibration=1.2,
                production_units=450,
                error_count=0
            ),
            SensorReading(
                sensor_id="PRENSA-02",
                timestamp=datetime.now().isoformat(),
                temperature=280.0,
                pressure=3.1,
                vibration=0.8,
                production_units=320,
                error_count=0
            ),
        ]

    @staticmethod
    def simulate_anomaly() -> List[SensorReading]:
        """Anomalía detectada - sobrecalentamiento."""
        return [
            SensorReading(
                sensor_id="HORNO-01",
                timestamp=datetime.now().isoformat(),
                temperature=385.2,  # ⚠️ ALTO
                pressure=2.8,       # Presión aumentada
                vibration=2.5,      # Vibración anormal
                production_units=120,  # Producción baja
                error_count=5
            ),
        ]


# ─── Blockchain Simulation ────────────────────────────────────────────

@dataclass
class BlockchainRecord:
    """Registro inmutable en blockchain."""
    record_id: str
    timestamp: str
    report: str
    sensor_hash: str      # Hash de datos de sensores
    ai_model_version: str
    stake: str            # Blockchain ID (ej: "0x3a2f8c...")
    action_triggered: str

    def to_json(self) -> str:
        return json.dumps(self.__dict__, indent=2)

    def to_transaction(self) -> str:
        """Formato para enviar a blockchain (simulado)."""
        return f"""
Transacción de Blockchain
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
To: SmartContract (0x1234...5678)
Data: {self.to_json()}
Gas: 50000 wei
Value: 0 ETH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """


# ─── IA Integration ────────────────────────────────────────────────────




class AIAnalyzer:
    """Analiza datos de sensores y genera reportes en lenguaje natural."""

    def __init__(self, api_url: str = "http://localhost:8000", api_key: str = "%KhJh-yj44k[RMuJpy"):
        self.client = TextGenerationClient(base_url=api_url, api_key=api_key)

    def analyze_readings(self, readings: List[SensorReading]) -> str:
        """Analiza lecturas y genera reporte."""
        
        # Extraer datos relevantes
        summary = self._summarize_readings(readings)
        
        # Generar reporte con IA
        seed = f"Reporte de producción. {summary}"
        
        try:
            result = self.client.generate(
                seed=seed,
                n_words=60,
                strategy='sampling',
                temperature=0.8
            )
            return result.generated_text
        except Exception as e:
            logger.error(f"Error en generación IA: {e}")
            return f"Error: {e}"

    def detect_anomaly(self, readings: List[SensorReading]) -> Dict:
        """Detecta anomalías en lecturas."""
        anomalies = []

        for reading in readings:
            # Umbrales de seguridad
            if reading.temperature > 360:  # Muy caliente
                anomalies.append({
                    'type': 'CRITICAL',
                    'sensor': reading.sensor_id,
                    'issue': f'Temperatura peligrosa: {reading.temperature}°C',
                    'action': 'PAUSE_PRODUCTION'
                })
            elif reading.vibration > 2.0:  # Mucha vibración
                anomalies.append({
                    'type': 'WARNING',
                    'sensor': reading.sensor_id,
                    'issue': f'Vibración anormal: {reading.vibration}mm/s',
                    'action': 'SCHEDULE_MAINTENANCE'
                })
            elif reading.error_count > 3:
                anomalies.append({
                    'type': 'WARNING',
                    'sensor': reading.sensor_id,
                    'issue': f'Errores detectados: {reading.error_count}',
                    'action': 'ALERT_TECHNICIAN'
                })

        return {
            'has_anomalies': len(anomalies) > 0,
            'anomalies': anomalies,
            'severity': 'CRITICAL' if any(a['type'] == 'CRITICAL' for a in anomalies) else 'WARNING' if anomalies else 'OK'
        }

    @staticmethod
    def _summarize_readings(readings: List[SensorReading]) -> str:
        """Resumen de datos para seed."""
        summary_parts = []
        avg_temp = sum(r.temperature for r in readings) / len(readings)
        total_production = sum(r.production_units for r in readings)

        summary_parts.append(f"Temperatura promedio: {avg_temp:.1f}°C")
        summary_parts.append(f"Producción total: {total_production} unidades")
        return " ".join(summary_parts)


# ─── Smart Contract Simulator ──────────────────────────────────────────

class SmartContract:
    """Smart contract que ejecuta acciones basadas en análisis."""

    def __init__(self):
        self.actions_log = []

    def execute_action(self, anomaly_data: Dict, report: str) -> str:
        """Ejecuta acción según anomalía detectada."""
        
        if not anomaly_data['has_anomalies']:
            action = "CONTINUE_NORMAL_OPERATION"
            self.actions_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'message': "Sistema funcionando normalmente"
            })
            return action

        # Determinar acción
        severity = anomaly_data['severity']
        
        if severity == 'CRITICAL':
            action = "STOP_PRODUCTION"
            message = "Sistema pausado por anomalía crítica"
            # Aquí irían acciones reales: cerrar válvulas, apagar maquinaria, etc.
            
        else:  # WARNING
            action = "SEND_ALERT_TECHNICIAN"
            message = "Alerta enviada al equipo técnico"
            # Enviar SMS, email, notificación a aplicación

        self.actions_log.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'message': message,
            'anomalies': anomaly_data['anomalies']
        })

        return action

    def get_logs(self) -> str:
        return json.dumps(self.actions_log, indent=2, ensure_ascii=False)


# ─── Orquestación Completa ────────────────────────────────────────────

class IndustrialAIOrchestrator:
    """Orquesta el flujo completo: IoT → IA → Blockchain → Smart Contract."""

    def __init__(self, api_url: str = "http://localhost:8000", api_key: str = "%KhJh-yj44k[RMuJpy"):
        self.iot = IoTSimulator()
        self.ai = AIAnalyzer(api_url, api_key)
        self.blockchain = []
        self.contract = SmartContract()

    def run_normal_operation(self) -> None:
        """Ejecuta un ciclo de operación normal."""
        logger.info("\n" + "="*70)
        logger.info("CICLO: OPERACIÓN NORMAL")
        logger.info("="*70)
        self._process_cycle(self.iot.simulate_normal_operation())

    def run_anomaly_cycle(self) -> None:
        """Ejecuta un ciclo con anomalía detectada."""
        logger.info("\n" + "="*70)
        logger.info("CICLO: ANOMALÍA DETECTADA ⚠️")
        logger.info("="*70)
        self._process_cycle(self.iot.simulate_anomaly())

    def _process_cycle(self, readings: List[SensorReading]) -> None:
        """Procesa un ciclo completo."""
        
        # Paso 1: Lectura de sensores
        logger.info("\n📊 PASO 1: Lectura de Sensores IoT")
        logger.info("─" * 70)
        for reading in readings:
            logger.info(f"  {reading}")

        # Paso 2: Detección de anomalías
        logger.info("\n🔍 PASO 2: Análisis de Anomalías")
        logger.info("─" * 70)
        anomaly_data = self.ai.detect_anomaly(readings)
        if anomaly_data['has_anomalies']:
            logger.warning(f"  ⚠️ ANOMALÍAS DETECTADAS: {anomaly_data['severity']}")
            for a in anomaly_data['anomalies']:
                logger.warning(f"     - {a['sensor']}: {a['issue']}")
        else:
            logger.info("  ✅ Sin anomalías. Sistema normal.")

        # Paso 3: Análisis IA
        logger.info("\n🤖 PASO 3: Análisis IA (Generación de Reportes)")
        logger.info("─" * 70)
        report = self.ai.analyze_readings(readings)
        logger.info(f"  Reporte generado:\n  {report[:200]}...")

        # Paso 4: Certificación en Blockchain
        logger.info("\n⛓️ PASO 4: Certificación En Blockchain")
        logger.info("─" * 70)
        import hashlib
        sensor_hash = hashlib.sha256(
            json.dumps([r.__dict__ for r in readings], default=str).encode()
        ).hexdigest()[:16]
        
        blockchain_record = BlockchainRecord(
            record_id=hashlib.sha256(
                f"{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12],
            timestamp=datetime.now().isoformat(),
            report=report,
            sensor_hash=sensor_hash,
            ai_model_version="LSTM-v1.0",
            stake=f"0x{sensor_hash}",
            action_triggered="PENDING"
        )
        logger.info(f"  Record ID: {blockchain_record.record_id}")
        logger.info(f"  Hash: {blockchain_record.stake}")
        logger.info(f"  ✅ Registrado en blockchain (inmutable)")
        self.blockchain.append(blockchain_record)

        # Paso 5: Ejecución de Smart Contract
        logger.info("\n📋 PASO 5: Ejecución de Smart Contract")
        logger.info("─" * 70)
        action = self.contract.execute_action(anomaly_data, report)
        logger.info(f"  Acción ejecutada: {action}")
        logger.info(f"  ✅ Smart contract completado")

        logger.info("\n" + "="*70)
        logger.info(f"CICLO COMPLETADO | Timestamp: {datetime.now().isoformat()}")
        logger.info("="*70)

    def print_blockchain_summary(self) -> None:
        """Muestra resumen de blockchain."""
        logger.info("\n" + "="*70)
        logger.info("BLOCKCHAIN SUMMARY")
        logger.info("="*70)
        logger.info(f"Total records: {len(self.blockchain)}")
        for i, record in enumerate(self.blockchain, 1):
            logger.info(f"\n  Record {i}:")
            logger.info(f"    ID: {record.record_id}")
            logger.info(f"    Timestamp: {record.timestamp}")
            logger.info(f"    Hash: {record.stake}")

    def print_contract_logs(self) -> None:
        """Muestra logs de smart contract."""
        logger.info("\n" + "="*70)
        logger.info("CONTRACT LOGS")
        logger.info("="*70)
        logger.info(self.contract.get_logs())


# ─── Main ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "█"*70)
    print("█  IoT + Blockchain + IA Integration Demo                       █")
    print("█  Caso de Uso: Monitoreo Industrial Inteligente                 █")
    print("█"*70)

    orchestrator = IndustrialAIOrchestrator()

    # Ciclo 1: Operación normal
    orchestrator.run_normal_operation()

    # Ciclo 2: Anomalía
    orchestrator.run_anomaly_cycle()

    # Resumen
    orchestrator.print_blockchain_summary()
    orchestrator.print_contract_logs()

    print("\n✅ Demo completada")
