# PRÁCTICA 5: Integración, automatización y modelo de negocio
## API de Generación de Texto con Proxy Seguro

---

## PORTADA

**Asignatura:** Programación de Inteligencia Artificial  
**Curso/Nivel:** Práctica 5  
**Período:** Marzo 2026  
**Autor:** José A. Rodríguez López  
**Centro:** Universidad / Centro Educativo  

---

## RESUMEN EJECUTIVO

Esta práctica desarrolla una aplicación web que genera texto mediante un proxy API. El sistema recibe parámetros del usuario, los envía a un servicio remoto, procesa el resultado y lo devuelve de forma limpia y coherente. El nivel de sofisticación radica en la validación exhaustiva, protección de credenciales y estrategia inteligente de ampliación de generación hasta obtener texto con cierre natural.

**Palabras clave:** FastAPI, proxy, generación de texto, integración web, IA remota, arquitectura cliente-servidor.

---

## TABLA DE CONTENIDOS

1. Introducción
2. Objetivos
3. Metodología
4. Descripción técnica del sistema
5. Resultados y validación
6. Conclusiones
7. Referencias

---

## 1. INTRODUCCIÓN

El objetivo central es integrar un servicio remoto de generación de texto mediante un proxy API que actúe como intermediario de seguridad. En lugar de exponer el navegador directamente a la API remota, se construye un servidor FastAPI que valida solicitudes, protege credenciales y mejora la calidad de las respuestas.

La arquitectura se organiza en dos capas conectadas:
- **Capa de aplicación:** servidor FastAPI que valida, procesa y coordina con el servicio remoto.
- **Capa de presentación:** interfaz web responsiva donde el usuario configura parámetros y consulta resultados.

Esta separación permite mantener control centralizado sobre seguridad, validación y normalización de datos.

### 1.1 Contexto del proyecto
Esta práctica forma parte de un itinerario de automatización e integración. El objetivo es demostrar cómo construir sistemas que comuniquen de forma segura y robusta con APIs remotas, aplicando validación de entrada, protección de credenciales y estrategias de mejora de calidad.

## 2. OBJETIVOS

### 2.1 Objetivo general
Desarrollar una aplicación web integrada que genere texto de forma segura y coherente mediante un proxy API que actúe como intermediario robusto con servicios remotos.

### 2.2 Objetivos específicos
- Implementar validación de entrada exhaustiva en el backend.
- Establecer comunicación segura y confiable con la API remota.
- Asegurar coherencia textual mediante ampliación incremental de generación hasta obtener cierre natural.
- Implementar medidas de seguridad HTTP (headers, protección de credenciales).
- Crear interfaz web responsiva que se adapte a múltiples dispositivos.
- Integrar funcionalidad de accesibilidad mediante síntesis de voz.
- Demostrar manejo robusto de errores y estados del sistema.

---

## 3. METODOLOGÍA

### 3.1 Enfoque arquitectónico
La solución se divide en dos componentes integrados:
- **Backend:** servidor FastAPI responsable de validación, procesamiento y orquestación con servicio remoto.
- **Frontend:** interfaz web con HTML semántico, CSS moderno y JavaScript para interacción.

### 3.2 Tecnologías y herramientas
- **Backend:** FastAPI (framework asincrónico), Pydantic (validación de datos), httpx (cliente HTTP asincrónico).
- **Frontend:** HTML5, CSS3 con Grid, JavaScript vanilla sin dependencias externas.
- **Comunicación:** REST con JSON, autenticación mediante X-API-Key en headers.

### 3.3 Fases de desarrollo
1. Diseño de modelos de validación con Pydantic.
2. Implementación de endpoints de salud y configuración.
3. Desarrollo del proxy con estrategia incremental de generación.
4. Construcción de interfaz responsiva con layout adaptable.
5. Integración de lógica JavaScript.
6. Validación y pruebas de flujos.

---

## 4. DESCRIPCIÓN TÉCNICA DEL SISTEMA

### 4.1 Estructura de archivos
- `api_simple.py`: API principal, rutas HTTP, validaciones y lógica de proxy.
- `web/index.html`: estructura de la interfaz de usuario.
- `web/styles.css`: estilos visuales, distribución de paneles y comportamiento responsivo.
- `web/app.js`: interacción de la interfaz con el backend y manejo de estado.
- `web/circuito-bg.js`: fondo animado en canvas.
- `requirements.txt`: dependencias del entorno Python.

### 4.2 Configuración por entorno
El backend requiere dos variables de entorno:
- `REMOTE_API_BASE_URL`: dirección del servicio remoto.
- `REMOTE_API_KEY`: credencial de autenticación.

Si alguna está ausente, el servidor rechaza operaciones remotas y devuelve un error de configuración.

### 4.3 Seguridad y políticas HTTP
Cada respuesta del servidor incluye cabeceras de seguridad:
- `X-Content-Type-Options: nosniff` → previene interpretación errada de tipos MIME.
- `X-Frame-Options: DENY` → evita inyección en iframes.
- `X-XSS-Protection: 1; mode=block` → protección contra inyecciones XSS.
- `Cache-Control: no-store` → previene almacenamiento en caché.

También se habilita CORS para permitir comunicación del frontend con el backend.

### 4.4 Modelos y validación
Se utilizan modelos Pydantic:
- `GenerateRequest`
- `GenerateResponse`

Restricciones de validación:
- `seed`: 1 a 500 caracteres (texto inicial de generación).
- `n_words`: 1 a 200 (palabras mínimas solicitadas).
- `strategy`: `greedy`, `sampling` o `top_k` (método de selección).
- `temperature`: 0.1 a 2.0 (nivel de creatividad/aleatoriedad).
- `top_k`: 1 a 500 (opciones candidatas consideradas).

Solicitudes fuera de estos límites son rechazadas con respuesta de validación clara.

### 4.5 Endpoints disponibles
- `GET /`: información general de la API.
- `GET /app`: entrega la aplicación web.
- `GET /favicon.ico`: entrega el favicon.
- `GET /health`: salud del proxy y estado de configuración remota.
- `GET /web-config`: configuración mínima para inicializar el frontend.
- `GET /health-remote`: comprobación de conectividad con la API remota.
- `POST /generate-proxy`: generación de texto mediante proxy.

### 4.6 Lógica de generación (`POST /generate-proxy`)
El parámetro `n_words` define el mínimo inicial. El proxy implementa un algoritmo iterativo:

1. Realiza solicitud inicial a la API remota con `n_words`.
2. Si la respuesta no contiene punto (`.`), repite aumentando `n_words` en bloques de 20.
3. Continua iterando hasta encontrar punto o alcanzar límite de 200 palabras.
4. Cuando detecta punto, recorta al último punto encontrado.
5. Si no hay punto antes del límite, devuelve la mejor salida obtenida.
6. Acumula tiempo total de todos los intentos en `elapsed_ms`.

Esta estrategia asegura coherencia textual sin bloqueos indefinidos.

### 4.7 Postprocesamiento de texto
Antes de la respuesta, el sistema normaliza el texto:
- Elimina tokens especiales de la IA (`<UNK>`, `<PAD>`, `<BOS>`, `<EOS>`).
- Corrige espaciado antes de puntuación.
- Normaliza mayúsculas (inicio de texto y después de punto).
- Recorta al último punto si existe.

### 4.8 Manejo de errores
- Conectividad remota: `502` (fallo en comunicación con API remota).
- Configuración local: `500` (variables de entorno faltantes o inválidas).
- Validación de entrada: respuesta clara de Pydantic/FastAPI.

### 4.9 Estructura HTML del frontend (`web/index.html`)
La interfaz presenta:
- Título identificador del sistema.
- Formulario para semilla de texto y configuración de parámetros.
- Bloque de información del endpoint remoto.
- Área de salida para texto generado y tiempo de respuesta.
- Controles: generar, reproducir (voz), detener (voz).

### 4.10 Estilos CSS (`web/styles.css`)
Diseño visual e implementación:
- Paleta de colores definida mediante variables CSS en español.
- Layout en dos columnas en desktop (formulario e información remota a la izquierda, salida a la derecha).
- Disposición de una columna en dispositivos móviles.
- Paneles con sombras y bordes redondeados.
- Fondo con gradientes radiales y animación complementaria en canvas.

### 4.11 Lógica JavaScript (`web/app.js`)
Gestiona la interacción del usuario:
- Al cargar, consulta configuración del backend y muestra endpoint remoto.
- Prueba conectividad remota cuando el usuario lo solicita.
- Envía solicitudes de generación al proxy con validación local.
- Presenta texto generado, tiempo acumulado y estado operativo.
- Maneja errores con mensajes informativos al usuario.
- Integra Text-to-Speech (español) para lectura del resultado.

## 5. RESULTADOS Y VALIDACIÓN

### 5.1 Flujo funcional de extremo a extremo
Proceso completo de uso:
1. Acceso a `http://localhost:8000/app`.
2. Frontend consulta configuración del backend.
3. Usuario configura semilla de texto y parámetros de generación.
4. Envío de solicitud al endpoint `/generate-proxy`.
5. Backend valida entrada y consulta API remota.
6. Si falta punto, proxy amplia iterativamente hasta obtenerlo o alcanzar límite.
7. Postprocesamiento y normalización del texto.
8. Frontend recibe resultado con tiempo acumulado.
9. Usuario puede reproducir el texto mediante voz (opcional).

### 5.2 Dependencias requeridas
Definidas en `requirements.txt`:
- `fastapi`
- `uvicorn`
- `pydantic`
- `httpx`

### 5.3 Instrucciones de ejecución local
1. Configurar variables de entorno:
   - `REMOTE_API_BASE_URL`
   - `REMOTE_API_KEY`
2. Iniciar servidor:
   - `uvicorn api_simple:app --host 0.0.0.0 --port 8000 --reload`
3. Abrir en navegador:
   - `http://localhost:8000/app`

## 6. CONCLUSIONES

### 6.1 Conclusión técnica
En resumen, armamos un sistema que:
- Funciona como guardaespaldas de servicios remotos (los protege y valida todo).
- Valida entradas, protege credenciales y mejora la calidad del resultado.
- Usa un algoritmo ingeniero que amplia la generación de texto hasta encontrar un punto, sin quedarse esperando para siempre.

### 6.2 Logros alcanzados
- ✓ Integración segura con API remota mediante proxy intermediario.
- ✓ Validación robusta de entrada con Pydantic.
- ✓ Algoritmo inteligente de generación incremental hasta punto.
- ✓ Interfaz responsiva y accesible (Text-to-Speech).
- ✓ Manejo adecuado de errores y tiempos de espera.
- ✓ Desacoplamiento de credenciales (no expuestas en frontend).

### 6.3 Mejoras futuras
- Guardar resultados en caché para no repetir consultas.
- Deixar que veas un historial de lo que generaste.
- Agregar opciones para resumir textos o analizar sentimiento.
- Registrar logs y métricas (quién genera qué, cuándo).
- Controlar que un usuario no nos bombardee con solicitudes (rate limiting).

---

## 7. REFERENCIAS

[1] Starlette Foundation. (2024). FastAPI - Modern, fast web framework for building APIs with Python. https://fastapi.tiangolo.com/

[2] Kluyver, T., Ragan-Kelley, B., et al. (2016). Jupyter Notebooks - A publishing format for reproducible computational workflows. In Proceedings of the 2016 International Conference on Computational Science (ICCS), pp. 87-90.

[3] Mozilla Developer Network. (2024). Fetch API - JavaScript documentation. https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API

[4] Python Enhancement Proposal 8. (2013). Style Guide for Python Code (PEP 8). Python Software Foundation.

[5] OWASP Foundation. (2024). OWASP Top 10 - Security Best Practices for Web Applications. https://owasp.org/www-project-top-ten/

---

**Documento generado:** 29 de Marzo, 2026  
**Versión:** 1.0  
**Autor:** José A. Rodríguez López  
**Asignatura:** Programación de Inteligencia Artificial
