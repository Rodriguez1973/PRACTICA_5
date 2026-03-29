# -*- coding: utf-8 -*-
"""
                 PRÁCTICA 4: Entrenamiento, Evaluación y Despliegue.
                         Script principal para la práctica 4
                       Programación de Inteligencia Artificial

Modelo de lenguaje para la práctica 4.

DESARROLLADO POR:   José A. Rodríguez López
FECHA: 27 de Marzo, 2026
PROYECTO: Programación de Inteligencia Artificial
================================================================================
"""

import tensorflow as tf # Librería principal para Deep Learning
from tensorflow.keras import layers, Model # Librería para construir modelos con Keras
import json # Librería para manejar archivos en formato JSON

class LMConfig:
    """Configuración del modelo de lenguaje."""

    def __init__(
        self,
        vocab_size=10000, # Tamaño del vocabulario (número de tokens únicos)
        embedding_dim=384, # Dimensión de los vectores de embedding para cada token
        lstm_units=640, # Número de unidades en cada capa
        num_lstm_layers=3, # Número de capas en el modelo
        dropout_rate=0.25, # Tasa de dropout para regularización
        sequence_length=50, # Longitud de las secuencias de entrada para el modelo
    ):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.lstm_units = lstm_units
        self.num_lstm_layers = num_lstm_layers
        self.dropout_rate = dropout_rate
        self.sequence_length = sequence_length

    # Métodos para guardar y cargar la configuración en formato JSON
    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, indent=2)

    # Cargar la configuración desde un archivo JSON
    @classmethod
    def load(cls, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

# Funciones para construir y compilar el modelo de lenguaje
def build_language_model(config: LMConfig) -> Model:
    """Construye un modelo de lenguaje LSTM multi-capa."""
    inputs = layers.Input(shape=(config.sequence_length,), name="token_ids")

    # Capa de embedding para convertir IDs de tokens en vectores densos
    x = layers.Embedding(
        input_dim=config.vocab_size,
        output_dim=config.embedding_dim,
        mask_zero=True,
        name="embedding",
    )(inputs)

    # Mantener secuencia completa para predecir el siguiente token en cada paso.
    for i in range(config.num_lstm_layers):
        x = layers.LSTM(
            units=config.lstm_units,
            return_sequences=True,
            dropout=config.dropout_rate,
            recurrent_dropout=0.0,
            name=f"lstm_{i + 1}",
        )(x)
        if i < config.num_lstm_layers - 1:
            x = layers.LayerNormalization(name=f"layer_norm_{i + 1}")(x)

    # Capa de salida con softmax para predecir la probabilidad de cada token en el vocabulario
    x = layers.Dropout(config.dropout_rate, name="output_dropout")(x)
    outputs = layers.Dense(config.vocab_size, activation="softmax", name="output_probs")(x)

    # Crear el modelo Keras con las entradas y salidas definidas
    model = Model(inputs=inputs, outputs=outputs, name="LSTMLanguageModel")
    return model


def compile_model(model: Model, learning_rate: float = 5e-4) -> Model:
    """Compila el modelo."""
    optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate, clipnorm=1.0)
    model.compile(optimizer=optimizer, loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model
