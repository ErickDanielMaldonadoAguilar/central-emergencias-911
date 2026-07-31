# Bitácora de decisiones técnicas

## Proyecto

Plataforma de Central de Emergencias en Tiempo Real.

## Responsable

Erick Daniel Maldonado Aguilar.

## Propósito de la bitácora

En este documento registraré las decisiones técnicas más importantes tomadas durante el desarrollo del proyecto. Para cada decisión explicaré la alternativa seleccionada, la opción descartada y la razón por la que consideré que la elección era adecuada.

No se documentarán como decisiones independientes los detalles pequeños de programación. Estos quedarán registrados mediante el historial de commits.

---

## 1. Organización general del proyecto

### Decisión

Utilizar un solo repositorio organizado por componentes.

### Alternativa considerada

Crear un repositorio diferente para el generador, los consumidores, la infraestructura y la visualización.

### Justificación

Decidí trabajar con un solo repositorio porque todos los componentes forman parte de una misma tubería de datos y deben demostrarse funcionando de manera integrada. Esto también facilita mantener un único README, revisar el historial de cambios y ejecutar el proyecto durante la defensa.

---

## 2. Tecnologías principales

### Decisión

Utilizar Python con FastAPI, Apache Kafka, MongoDB y Docker Compose.

### Alternativas consideradas

Se evaluó utilizar Node.js o Java para el backend, PostgreSQL o Cassandra para el almacenamiento y una instalación manual de los servicios.

### Justificación

Seleccioné Python y FastAPI porque ya tengo experiencia con estas herramientas y puedo concentrarme en el procesamiento de datos y Kafka. Elegí MongoDB porque los eventos se manejarán como documentos JSON. Docker Compose permitirá ejecutar los servicios de manera controlada y reproducible.

---

## 3. Alcance de la simulación

### Decisión

Simular una central para Tegucigalpa y Comayagüela dividida en seis distritos operativos académicos.

### Justificación

Elegí este alcance porque es un entorno cercano y manejable. Los distritos son simulados y no representan divisiones oficiales del Sistema Nacional de Emergencias 911.

---

## 4. Prioridad del proyecto

### Decisión

Mantener un frontend sencillo y concentrar el trabajo en la generación, Kafka, procesamiento, almacenamiento, pruebas y balance de carga.

### Justificación

El objetivo principal del proyecto es demostrar una solución Big Data integrada. Por esta razón se evitarán funciones adicionales que no aporten directamente a los requisitos o a la defensa.