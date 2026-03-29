# Practica 5: Guia de ejecucion

## 1. Instalación

Desde PRACTICA_5:
1. pip install -r requirements.txt

## 2. Variables de entorno

En PowerShell, desde PRACTICA_5:

1. $env:REMOTE_API_BASE_URL="https://ca-practica4.wittycoast-99cc6956.westeurope.azurecontainerapps.io"
2. $env:REMOTE_API_KEY="%KhJh-yj44k[RMuJpy"

## 3. Arranque

Desde PRACTICA_5:

1. uvicorn api_simple:app --host 0.0.0.0 --port 8000 --reload

## 4. Verificaciones

1. http://localhost:8000/health
2. http://localhost:8000/health-remote
3. http://localhost:8000/docs
4. http://localhost:8000/app

## 5. Uso funcional

1. Abrir http://localhost:8000/app
2. Pulsar "Probar conexion remota"
3. Escribir semilla
4. Configurar parámetros
5. Pulsar "Generar texto"
6. Opcional: "Hablar resultado"