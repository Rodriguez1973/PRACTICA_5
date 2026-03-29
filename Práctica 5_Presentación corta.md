# Presentacion Corta - Practica 5
## Integracion, Automatizacion y Modelo de Negocio

## Diapositiva 1 - Problema y objetivo

1. La redaccion manual de contenido comercial consume mucho tiempo.
2. Objetivo: integrar IA generativa en un flujo real de negocio.
3. Resultado buscado: reducir tiempos y aumentar productividad.

## Diapositiva 2 - Solucion implementada

1. Interfaz web para generar texto.
2. Backend proxy seguro (la API key no se expone en frontend).
3. Consumo de API remota desplegada en Azure.
4. Salida opcional en voz (TTS).

## Diapositiva 3 - Arquitectura en 4 pasos

1. Usuario -> Web `/app`.
2. Web -> Backend `/generate-proxy`.
3. Backend -> API Azure `/generate`.
4. Backend limpia y devuelve texto final.

## Diapositiva 4 - Modelo de automatizacion

Proceso elegido:

1. Borradores de emails de marketing.
2. Descripciones de productos.
3. Publicaciones para redes sociales.

Impacto esperado:

1. Reduccion del tiempo de redaccion inicial entre 60% y 85%.

## Diapositiva 5 - Modelo de negocio

Opciones:

1. SaaS.
2. Pago por uso.
3. Freemium.

Propuesta:

1. Empezar con freemium para captar usuarios.
2. Escalar a planes SaaS Pro y Business.

## Diapositiva 6 - Estrategia corporativa

1. Piloto en un area concreta (4-6 semanas).
2. Medir KPIs: tiempo, calidad, tasa de aprobacion.
3. Escalado progresivo a mas equipos.
4. Ventaja: mas velocidad, menor coste, mayor consistencia.

## Diapositiva 7 - Convergencia tecnologica

IoT:

1. Datos de sensores -> IA genera informes operativos en lenguaje natural.

Blockchain:

1. Registro hash inmutable para certificar origen y momento del texto generado.

## Diapositiva 8 - Cierre

1. La IA integrada aporta valor real cuando se conecta a procesos concretos.
2. El proyecto ya es base funcional para evolucionar a producto.
3. Siguientes pasos: dashboard de metricas, integraciones CRM/CMS y piloto con cliente real.
4. Preguntas.
