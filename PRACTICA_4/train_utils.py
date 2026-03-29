# -*- coding: utf-8 -*-
"""
                 PRÁCTICA 4: Entrenamiento, Evaluación y Despliegue.
            Entrenamiento de Modelos de Lenguaje y Utilidades de Tokenización
                       Programación de Inteligencia Artificial

En este módulo se implementan utilidades para el entrenamiento de modelos de lenguaje, incluyendo un tokenizador personalizado y una función para crear datasets de TensorFlow a partir de secuencias de tokens. Estas herramientas son esenciales para preparar los datos y entrenar el modelo de generación de texto que se utilizará en la API.

DESARROLLADO POR:   José A. Rodríguez López
FECHA: 27 de Marzo, 2026
PROYECTO: Programación de Inteligencia Artificial
================================================================================
"""

import json # Librería para manejar archivos en formato JSON
from collections import Counter # Librería para contar la frecuencia de palabras
import tensorflow as tf # Librería principal para Deep Learning
import numpy as np # Librería para manejo de arrays y operaciones matemáticas

class TextTokenizer:
    """Tokenizador a nivel de palabra."""
    # Definir tokens especiales para el vocabulario
    PAD, UNK, BOS, EOS = "<PAD>", "<UNK>", "<BOS>", "<EOS>"

    # Inicializar el tokenizador con un tamaño de vocabulario máximo
    def __init__(self, vocab_size: int = 10000):
        self.vocab_size = vocab_size
        self.word2idx = {}
        self.idx2word = {}

    def fit(self, text: str):
        """Construye el vocabulario."""
        words = text.lower().split()
        freq = Counter(words)
        specials = [self.PAD, self.UNK, self.BOS, self.EOS]
        vocab = specials + [w for w, _ in freq.most_common(self.vocab_size - len(specials))]
        self.word2idx = {w: i for i, w in enumerate(vocab)}
        self.idx2word = {i: w for w, i in self.word2idx.items()}
        print(f"Vocabulario construido: {len(self.word2idx)} tokens")

    def encode(self, text: str):
        """Convierte texto a IDs de tokens, usando UNK para palabras fuera del vocabulario."""
        unk = self.word2idx[self.UNK]
        return [self.word2idx.get(w, unk) for w in text.lower().split()]

    def decode(self, ids):
        """Convierte IDs de tokens a texto, usando UNK para tokens desconocidos."""
        return " ".join(self.idx2word.get(i, self.UNK) for i in ids)

    def save(self, path: str):
        """Guarda el tokenizador en un archivo JSON."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"word2idx": self.word2idx, "idx2word": {str(k): v for k, v in self.idx2word.items()}}, f)

    @classmethod
    def load(cls, path: str):
        """Carga el tokenizador desde un archivo JSON."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        tok = cls()
        tok.word2idx = data["word2idx"]
        tok.idx2word = {int(k): v for k, v in data["idx2word"].items()}
        tok.vocab_size = len(tok.word2idx)
        return tok

def make_dataset(token_ids, seq_len, batch_size, shuffle=True):
    """Crea un tf.data.Dataset para entrenamiento."""
    total = tf.data.Dataset.from_tensor_slices(token_ids)
    sequences = total.batch(seq_len + 1, drop_remainder=True)

    def split_xy(seq):
        """Dado un tensor de forma (seq_len + 1,), devuelve (seq_len,) para X y (seq_len,) para Y."""
        return seq[:-1], seq[1:]

    # Aplicar la función de mapeo para dividir cada secuencia en entradas (X) y etiquetas (Y)
    ds = sequences.map(split_xy, num_parallel_calls=tf.data.AUTOTUNE)
    # Mezclar los datos si se especifica, con un buffer grande para asegurar buena aleatorización
    if shuffle:
        ds = ds.shuffle(buffer_size=10000)
    # Agrupar los datos en lotes de tamaño batch_size, descartando el último lote si no tiene el tamaño completo
    ds = ds.batch(batch_size, drop_remainder=True)
    ds = ds.prefetch(tf.data.AUTOTUNE)
    return ds
