# Central de Emergencias 911

Proyecto académico de Big Data que simula llamadas de emergencia y utiliza Apache Kafka, MongoDB y FastAPI.

El sistema permite:

- Generar llamadas individuales.
- Generar lotes de hasta 10,000 llamadas.
- Enviar los eventos a Kafka.
- Procesarlos y guardarlos en MongoDB.
- Consultar el balance de carga de los distritos en un dashboard.

> Todos los datos utilizados son simulados con fines académicos.

## Requisitos

Antes de ejecutar el proyecto se necesita:

- Python 3.11
- Docker Desktop
- Git
- Visual Studio Code

## 1. Descargar el proyecto

Clonar el repositorio o descargarlo desde GitHub.

Después, abrir la carpeta del proyecto en Visual Studio Code.

## 2. Crear el archivo de configuración

Desde la carpeta principal del proyecto, ejecutar:

```powershell
Copy-Item infraestructura\.env.example infraestructura\.env
```

Abrir el archivo:

```text
infraestructura/.env
```

Y colocar una contraseña local:

```env
MONGO_ROOT_USERNAME=central911_admin
MONGO_ROOT_PASSWORD=coloque_una_contrasena
MONGO_DATABASE=central911
```

## 3. Crear el entorno virtual

```powershell
python -m venv .venv
```

Activarlo:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Después volver a ejecutar:

```powershell
.\.venv\Scripts\Activate.ps1
```

Cuando esté activo debe aparecer:

```text
(.venv)
```

## 4. Instalar las dependencias

```powershell
python -m pip install -r requirements.txt
```

## 5. Encender Kafka y MongoDB

Primero abrir Docker Desktop y esperar a que esté funcionando.

Después ejecutar:

```powershell
docker compose --env-file infraestructura\.env -f infraestructura\docker-compose.yml up -d
```

Comprobar los contenedores:

```powershell
docker compose --env-file infraestructura\.env -f infraestructura\docker-compose.yml ps
```

Esperar hasta que Kafka y MongoDB aparezcan como `healthy`.

## 6. Crear el topic de Kafka

Ejecutar una sola vez:

```powershell
docker exec central911-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:19092 --create --if-not-exists --topic llamadas-emergencia --partitions 6 --replication-factor 3 --config min.insync.replicas=2
```

## 7. Ejecutar el consumidor

Abrir una terminal nueva, activar el entorno virtual y ejecutar:

```powershell
python -m scripts.consumir_eventos_mongodb
```

Esta terminal debe permanecer abierta mientras se generan llamadas.

## 8. Ejecutar el generador

Abrir otra terminal, activar el entorno virtual y ejecutar:

```powershell
python -m uvicorn generador.app.main:app --reload --port 8000
```

Abrir en el navegador:

```text
http://127.0.0.1:8000
```

Desde esta pantalla se pueden generar llamadas individuales o por lotes.

## 9. Ejecutar el dashboard

Abrir otra terminal, activar el entorno virtual y ejecutar:

```powershell
python -m uvicorn visualizacion.app.main:app --reload --port 8001
```

Abrir en el navegador:

```text
http://127.0.0.1:8001
```

El dashboard permite consultar el balance general y seleccionar cualquiera de los seis distritos.

## Orden recomendado para ejecutar

```text
1. Abrir Docker Desktop
2. Levantar Kafka y MongoDB
3. Ejecutar el consumidor
4. Ejecutar el generador
5. Ejecutar el dashboard
6. Generar llamadas desde la interfaz
```

## Prueba rápida

Para comprobar las funciones básicas:

```powershell
python -m pytest -q
```

Para probar la distribución de los distritos en Kafka:

```powershell
python -m scripts.probar_particiones_kafka
```

## Detener el proyecto

Cerrar los servidores con:

```text
Ctrl + C
```

Detener Kafka y MongoDB sin eliminar los datos:

```powershell
docker compose --env-file infraestructura\.env -f infraestructura\docker-compose.yml down
```

## Autor

Erick Daniel Maldonado Aguilar