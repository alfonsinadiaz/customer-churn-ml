# Runbook de despliegue y operación

Este procedimiento está pensado para un host Linux distinto de la máquina de desarrollo. Requiere Docker Engine, Docker Compose v2 y acceso de red a GHCR y DagsHub.

## 1. Preparar el servidor

Crear una carpeta de trabajo y copiar allí `compose.prod.yaml`:

```bash
mkdir -p ~/customer-churn-ml
cd ~/customer-churn-ml
```

Crear `.env` en el servidor. No copiarlo al repositorio:

```dotenv
IMAGE_NAME=ghcr.io/alfonsinadiaz/customer-churn-ml
IMAGE_TAG=v1.0.0
API_PORT=8000
LOG_LEVEL=INFO
MODEL_URI=models:/customer-churn-candidate/1
MODEL_VERSION=registry-v1
MLFLOW_TRACKING_URI=https://dagshub.com/alfonsinadiaz/customer-churn-ml.mlflow
MLFLOW_TRACKING_USERNAME=<usuario-dagshub>
MLFLOW_TRACKING_PASSWORD=<token-dagshub>
```

Restringir la lectura del archivo:

```bash
chmod 600 .env
```

## 2. Iniciar el servicio

Si el paquete de GHCR es privado, iniciar sesión con un token que tenga `read:packages`:

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u <usuario-github> --password-stdin
```

Luego descargar e iniciar la versión explícita:

```bash
docker compose -f compose.prod.yaml pull
docker compose -f compose.prod.yaml up -d
docker compose -f compose.prod.yaml ps
```

La primera carga puede tardar mientras MLflow descarga el modelo. El healthcheck tiene 60 segundos de espera inicial.

## 3. Verificación posterior

```bash
curl --fail http://localhost:8000/health
curl http://localhost:8000/model
```

Probar una inferencia real desde `/docs` o con el ejemplo de `README.md`. Guardar como evidencia:

- hostname y fecha;
- tag de imagen desplegado;
- salida de `/health` y `/model`;
- respuesta de `/predict` con su `request_id`;
- línea de log que tenga el mismo `request_id`.

## 4. Logs y diagnóstico

Estado del contenedor:

```bash
docker compose -f compose.prod.yaml ps
docker inspect --format '{{json .State.Health}}' churn-api
```

Logs recientes o en vivo:

```bash
docker compose -f compose.prod.yaml logs --tail=200 churn-api
docker compose -f compose.prod.yaml logs -f churn-api
```

Los logs son JSON. Una request incluye `status_code`, `duration_ms`, `model_version` y `request_id`.

- Servicio caído: `ps` no muestra `Up` o `curl /health` no conecta.
- Modelo inaccesible: `/health` responde `503` y aparece `model_unavailable`.
- Errores de aplicación: buscar nivel `ERROR` o evento `request_failed`.
- Latencia: comparar `duration_ms` para `/predict`; una suba persistente requiere revisar CPU, memoria, red y descarga/carga del modelo.

Para seguir un caso informado por un usuario:

```bash
docker compose -f compose.prod.yaml logs churn-api | grep '<request_id>'
```

## 5. Actualizar una versión

Editar solamente `IMAGE_TAG` en `.env`, por ejemplo `v1.0.1`, y ejecutar:

```bash
docker compose -f compose.prod.yaml pull
docker compose -f compose.prod.yaml up -d
curl --fail http://localhost:8000/health
```

Comprobar que `/model` muestre la versión esperada y repetir una predicción. No borrar la imagen anterior hasta terminar la verificación.

## 6. Rollback

Restaurar el tag anterior en `.env` y recrear el servicio:

```bash
docker compose -f compose.prod.yaml pull
docker compose -f compose.prod.yaml up -d
curl --fail http://localhost:8000/health
```

Si el problema está en el modelo, restaurar `MODEL_URI` y `MODEL_VERSION` a la versión previa y volver a crear el contenedor.

## 7. Detener

```bash
docker compose -f compose.prod.yaml down
```

No usar `down -v`: este despliegue no necesita borrar volúmenes y una limpieza amplia complica el diagnóstico.

## 8. Seguridad mínima

- No imprimir ni versionar `.env`, tokens o contraseñas.
- Usar tokens de alcance mínimo y rotarlos si se exponen.
- Publicar el puerto sólo en la red necesaria; para Internet, colocar un proxy con TLS y autenticación.
- Conservar tags inmutables (`v1.0.0` o digest) para poder auditar y volver atrás.
