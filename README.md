# Plataforma de Central de Emergencias en Tiempo Real

Proyecto integrador desarrollado para la asignatura Big Data (IF350) de la Universidad Católica de Honduras.

## Descripción

El proyecto simula el flujo de llamadas recibidas por una central de emergencias. El sistema permitirá generar llamadas de manera individual y por lotes, enviarlas mediante Apache Kafka, procesarlas, almacenarlas en MongoDB y visualizar el balance de carga de cada distrito.

El balance de carga compara la cantidad de llamadas activas con las unidades disponibles para responder.

## Flujo general del sistema

Generador web → Apache Kafka → Consumidores → Procesamiento → MongoDB → Visualización

## Tecnologías seleccionadas

- Python 3.11
- FastAPI
- Apache Kafka en modo KRaft
- MongoDB
- Docker Desktop
- Docker Compose
- Visual Studio Code
- Git y GitHub

## Estado actual

El proyecto se encuentra en la fase inicial de organización y diseño del generador de datos.

## Fases del proyecto

1. Generación de datos.
2. Ingesta con Apache Kafka.
3. Procesamiento y almacenamiento.
4. Visualización, integración y pruebas.

## Ejecución

Las instrucciones completas de instalación y ejecución se agregarán conforme se implementen los componentes del sistema.

## Autor

Erick Daniel Maldonado Aguilar