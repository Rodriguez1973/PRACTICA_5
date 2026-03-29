"""
train.py - Script de entrenamiento en la nube
Práctica 4: Entrenamiento, Evaluación y Despliegue

Uso:
    python train.py --data_path ./data/corpus.txt --epochs 20 --batch_size 64

Compatible con:
    - Google Colab (GPU/TPU)
    - AWS EC2 (GPU)
    - Azure ML / SageMaker (mediante variables de entorno)
"""

import argparse
import logging
import os
import time
from pathlib import Path

import numpy as np
import tensorflow as tf

from model import LMConfig, build_language_model, compile_model

# ── Configuración del logger ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Detección de hardware ─────────────────────────────────────────────────────

def detect_hardware() -> str:
    """Detecta y configura el hardware disponible (GPU/TPU/CPU)."""
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        log.info("GPU detectada: %s", [g.name for g in gpus])
        return "GPU"

    try:
        tpu = tf.distribute.cluster_resolver.TPUClusterResolver()
        tf.config.experimental_connect_to_cluster(tpu)
        tf.tpu.experimental.initialize_tpu_system(tpu)
        log.info("TPU detectada: %s", tpu.master())
        return "TPU"
    except Exception:
        log.info("Sin acelerador. Usando CPU.")
        return "CPU"


# ── Tokenización y preparación de datos ──────────────────────────────────────

class TextTokenizer:
    """Tokenizador a nivel de palabra con vocabulario fijo."""

    PAD, UNK, BOS, EOS = "<PAD>", "<UNK>", "<BOS>", "<EOS>"

    def __init__(self, vocab_size: int = 10000):
        self.vocab_size = vocab_size
        self.word2idx: dict[str, int] = {}
        self.idx2word: dict[int, str] = {}

    def fit(self, text: str):
        """Construye el vocabulario a partir del corpus."""
        from collections import Counter
        words = text.lower().split()
        freq = Counter(words)
        specials = [self.PAD, self.UNK, self.BOS, self.EOS]
        vocab = specials + [w for w, _ in freq.most_common(self.vocab_size - len(specials))]
        self.word2idx = {w: i for i, w in enumerate(vocab)}
        self.idx2word = {i: w for w, i in self.word2idx.items()}
        log.info("Vocabulario construido: %d tokens", len(self.word2idx))

    def encode(self, text: str) -> list[int]:
        unk = self.word2idx[self.UNK]
        return [self.word2idx.get(w, unk) for w in text.lower().split()]

    def decode(self, ids: list[int]) -> str:
        return " ".join(self.idx2word.get(i, self.UNK) for i in ids)

    def save(self, path: str):
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"word2idx": self.word2idx, "idx2word": {str(k): v for k, v in self.idx2word.items()}}, f)

    @classmethod
    def load(cls, path: str) -> "TextTokenizer":
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        tok = cls()
        tok.word2idx = data["word2idx"]
        tok.idx2word = {int(k): v for k, v in data["idx2word"].items()}
        tok.vocab_size = len(tok.word2idx)
        return tok


def make_dataset(
    token_ids: list[int],
    seq_len: int,
    batch_size: int,
    shuffle: bool = True,
) -> tf.data.Dataset:
    """
    Crea un tf.data.Dataset de pares (entrada, etiqueta).
    La etiqueta es la secuencia desplazada un paso hacia el futuro
    (predicción de la siguiente palabra).
    """
    total = tf.data.Dataset.from_tensor_slices(token_ids)
    sequences = total.batch(seq_len + 1, drop_remainder=True)

    def split_xy(seq):
        return seq[:-1], seq[1:]

    ds = sequences.map(split_xy, num_parallel_calls=tf.data.AUTOTUNE)
    if shuffle:
        ds = ds.shuffle(buffer_size=10_000)
    ds = ds.batch(batch_size, drop_remainder=True)
    ds = ds.prefetch(tf.data.AUTOTUNE)
    return ds


# ── Callbacks ─────────────────────────────────────────────────────────────────

def build_callbacks(checkpoint_dir: str, log_dir: str) -> list:
    """
    Define los callbacks de entrenamiento:
    - ModelCheckpoint: guarda el mejor modelo (checkpoint).
    - EarlyStopping: detiene si la pérdida no mejora.
    - TensorBoard: visualización de métricas en tiempo real.
    - ReduceLROnPlateau: reduce la tasa de aprendizaje si hay estancamiento.
    """
    os.makedirs(checkpoint_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    checkpoint_path = os.path.join(checkpoint_dir, "ckpt_epoch_{epoch:03d}_loss_{val_loss:.4f}.keras")

    callbacks = [
        # Guarda el mejor modelo según val_loss
        tf.keras.callbacks.ModelCheckpoint(
            filepath=checkpoint_path,
            monitor="val_loss",
            save_best_only=True,
            save_weights_only=False,
            verbose=1,
        ),
        # Detiene el entrenamiento si val_loss no mejora en 3 épocas
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=3,
            restore_best_weights=True,
            verbose=1,
        ),
        # Reduce LR si val_loss no mejora en 2 épocas
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=2,
            min_lr=1e-6,
            verbose=1,
        ),
        # Logs para TensorBoard (tensorboard --logdir ./logs)
        tf.keras.callbacks.TensorBoard(
            log_dir=log_dir,
            histogram_freq=1,
            update_freq="epoch",
        ),
        # Log personalizado por época
        LossLogger(),
    ]
    return callbacks


class LossLogger(tf.keras.callbacks.Callback):
    """Imprime la perplejidad (exponencial de la pérdida) al final de cada época."""

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        train_ppl = np.exp(logs.get("loss", float("inf")))
        val_ppl = np.exp(logs.get("val_loss", float("inf")))
        log.info(
            "Época %3d | loss=%.4f (ppl=%.1f) | val_loss=%.4f (val_ppl=%.1f) | lr=%.2e",
            epoch + 1,
            logs.get("loss", 0),
            train_ppl,
            logs.get("val_loss", 0),
            val_ppl,
            float(tf.keras.backend.get_value(self.model.optimizer.learning_rate)),
        )


# ── Entrenamiento principal ───────────────────────────────────────────────────

def train(args):
    start = time.time()
    hw = detect_hardware()

    # Directorios de salida
    out_dir = Path(args.output_dir)
    checkpoint_dir = out_dir / "checkpoints"
    log_dir = out_dir / "logs"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Cargar corpus
    log.info("Cargando datos desde: %s", args.data_path)
    with open(args.data_path, "r", encoding="utf-8") as f:
        text = f.read()
    log.info("Corpus cargado: %d caracteres, ~%d palabras", len(text), len(text.split()))

    # 2. Tokenización
    tokenizer = TextTokenizer(vocab_size=args.vocab_size)
    tokenizer.fit(text)
    tokenizer.save(str(out_dir / "tokenizer.json"))

    token_ids = tokenizer.encode(text)
    log.info("Tokens totales: %d", len(token_ids))

    # 3. División train / validación (90% / 10%)
    split = int(0.9 * len(token_ids))
    train_ids, val_ids = token_ids[:split], token_ids[split:]

    train_ds = make_dataset(train_ids, args.seq_len, args.batch_size, shuffle=True)
    val_ds = make_dataset(val_ids, args.seq_len, args.batch_size, shuffle=False)

    # 4. Construir modelo
    config = LMConfig(
        vocab_size=len(tokenizer.word2idx),
        embedding_dim=args.embedding_dim,
        lstm_units=args.lstm_units,
        num_lstm_layers=args.num_layers,
        dropout_rate=args.dropout,
        sequence_length=args.seq_len,
    )
    config.save(str(out_dir / "model_config.json"))

    # Usar estrategia de distribución según hardware
    if hw == "TPU":
        strategy = tf.distribute.TPUStrategy()
    elif len(tf.config.list_physical_devices("GPU")) > 1:
        strategy = tf.distribute.MirroredStrategy()
    else:
        strategy = tf.distribute.get_strategy()

    with strategy.scope():
        if args.resume_from:
            log.info("Reanudando desde checkpoint: %s", args.resume_from)
            model = tf.keras.models.load_model(args.resume_from)
        else:
            model = build_language_model(config)
            compile_model(model, learning_rate=args.lr)

    model.summary(print_fn=log.info)

    # 5. Entrenamiento
    log.info("Iniciando entrenamiento por %d épocas en %s...", args.epochs, hw)
    callbacks = build_callbacks(str(checkpoint_dir), str(log_dir))

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs,
        callbacks=callbacks,
    )

    # 6. Guardar modelo final
    final_path = str(out_dir / "model_final.keras")
    model.save(final_path)
    log.info("Modelo final guardado en: %s", final_path)

    # 7. Resumen del entrenamiento
    elapsed = time.time() - start
    best_val_loss = min(history.history.get("val_loss", [float("inf")]))
    best_val_ppl = np.exp(best_val_loss)
    log.info(
        "Entrenamiento completado en %.1f min. Mejor val_loss=%.4f (ppl=%.1f)",
        elapsed / 60,
        best_val_loss,
        best_val_ppl,
    )
    return history


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Entrenamiento de modelo de lenguaje LSTM")
    p.add_argument("--data_path",     default="data/corpus.txt",  help="Ruta al corpus de texto")
    p.add_argument("--output_dir",    default="output",           help="Directorio de salida")
    p.add_argument("--vocab_size",    type=int,   default=10000,  help="Tamaño del vocabulario")
    p.add_argument("--seq_len",       type=int,   default=50,     help="Longitud de secuencia")
    p.add_argument("--embedding_dim", type=int,   default=256,    help="Dimensión de embedding")
    p.add_argument("--lstm_units",    type=int,   default=512,    help="Unidades por capa LSTM")
    p.add_argument("--num_layers",    type=int,   default=2,      help="Número de capas LSTM")
    p.add_argument("--dropout",       type=float, default=0.3,    help="Tasa de dropout")
    p.add_argument("--lr",            type=float, default=1e-3,   help="Tasa de aprendizaje")
    p.add_argument("--batch_size",    type=int,   default=64,     help="Tamaño de batch")
    p.add_argument("--epochs",        type=int,   default=20,     help="Número de épocas")
    p.add_argument("--resume_from",   default=None,               help="Checkpoint para reanudar")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train(args)
