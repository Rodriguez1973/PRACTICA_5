"""
model.py - Arquitectura del modelo de lenguaje basado en LSTM
Práctica 4: Entrenamiento, Evaluación y Despliegue
"""

import tensorflow as tf
from tensorflow.keras import layers, Model
import json
import os


class LMConfig:
    """Configuración del modelo de lenguaje."""

    def __init__(
        self,
        vocab_size: int = 10000,
        embedding_dim: int = 256,
        lstm_units: int = 512,
        num_lstm_layers: int = 2,
        dropout_rate: float = 0.3,
        sequence_length: int = 50,
    ):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.lstm_units = lstm_units
        self.num_lstm_layers = num_lstm_layers
        self.dropout_rate = dropout_rate
        self.sequence_length = sequence_length

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, indent=2)

    @classmethod
    def load(cls, path: str) -> "LMConfig":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)


def build_language_model(config: LMConfig) -> Model:
    """
    Construye un modelo de lenguaje LSTM multi-capa.

    Arquitectura:
        Embedding → LSTM (x N capas con dropout) → Dense(softmax)

    Args:
        config: Objeto LMConfig con los hiperparámetros.

    Returns:
        Modelo Keras compilado.
    """
    inputs = layers.Input(shape=(config.sequence_length,), name="token_ids")

    # Capa de embedding: convierte IDs de token en vectores densos
    x = layers.Embedding(
        input_dim=config.vocab_size,
        output_dim=config.embedding_dim,
        mask_zero=True,
        name="embedding",
    )(inputs)

    # Capas LSTM apiladas. Para entrenamiento autoregresivo por token,
    # todas deben devolver secuencias: salida (batch, seq_len, vocab_size).
    for i in range(config.num_lstm_layers):
        return_sequences = True
        x = layers.LSTM(
            units=config.lstm_units,
            return_sequences=return_sequences,
            dropout=config.dropout_rate,
            recurrent_dropout=0.1,
            name=f"lstm_{i + 1}",
        )(x)
        if i < config.num_lstm_layers - 1:
            x = layers.LayerNormalization(name=f"layer_norm_{i + 1}")(x)

    x = layers.Dropout(config.dropout_rate, name="output_dropout")(x)

    # Capa de salida: distribución de probabilidad sobre el vocabulario
    outputs = layers.Dense(config.vocab_size, activation="softmax", name="output_probs")(x)

    model = Model(inputs=inputs, outputs=outputs, name="LSTMLanguageModel")
    return model


def compile_model(model: Model, learning_rate: float = 1e-3) -> Model:
    """Compila el modelo con optimizador Adam y pérdida de entropía cruzada."""
    optimizer = tf.keras.optimizers.Adam(
        learning_rate=learning_rate,
        clipnorm=1.0,  # Gradient clipping para estabilidad
    )
    model.compile(
        optimizer=optimizer,
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


if __name__ == "__main__":
    cfg = LMConfig()
    model = build_language_model(cfg)
    compile_model(model)
    model.summary()
    print(f"\nParámetros totales: {model.count_params():,}")
