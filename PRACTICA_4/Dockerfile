#                 PRÁCTICA 4: Entrenamiento, Evaluación y Despliegue.
#          Contenedor Docker para la API de Generación de Texto con FastAPI
#                       Programación de Inteligencia Artificial
#
# Dockerfile para construir una imagen que contenga la API de generación de 
# texto desarrollada en esta práctica. La imagen se basa en Python 3.13 y 
# expone el puerto 8000 para servir la API a través de uvicorn. Se incluyen las 
# dependencias necesarias, el código fuente de la API, y los artefactos del 
# modelo entrenado (modelo y tokenizador) para asegurar que la API funcione 
# correctamente al desplegarla en un contenedor Docker.
#
# DESARROLLADO POR:   José A. Rodríguez López
# FECHA: 27 de Marzo, 2026
# PROYECTO: Programación de Inteligencia Artificial
#===============================================================================

# Creación del contenedor
# docker build -t practica4-api .

# Ejecución del contenedor.
# docker run -p 8000:8000 -e API_KEY=%KhJh-yj44k[RMuJpy -e RATE_LIMIT=10 practica4-api

# Detención del contenedor.
# docker stop practica4-api

# Imagen base con Python 3.13 en variante ligera.
FROM python:3.13-slim

# Directorio de trabajo dentro del contenedor.
WORKDIR /app

# Actualizar pip a la última versión para evitar problemas de instalación.
RUN pip install --upgrade pip

# Copia e instala dependencias para aprovechar cache de capas.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el codigo de la API y utilidades necesarias.
COPY api_simple.py train_utils.py ./

# Crea la carpeta de artefactos y copia modelo/tokenizador en la ruta que usa la API.
RUN mkdir -p output
COPY modelo/model_final.keras ./output/model_final.keras
COPY tokenizer/tokenizer.json ./output/tokenizer.json

# Puerto donde uvicorn expone la API.
EXPOSE 8000

# Variables de entorno: API_KEY debe pasarse al ejecutar por seguridad.
# RATE_LIMIT es configurable en tiempo de ejecución.
ENV RATE_LIMIT=10

# Comando de inicio del servicio FastAPI.
CMD ["uvicorn", "api_simple:app", "--host", "0.0.0.0", "--port", "8000"]