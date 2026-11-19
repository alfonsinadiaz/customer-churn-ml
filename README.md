# Customer Churn ML

Proyecto integrador de Laboratorio de Minería de Datos. El objetivo es estimar la probabilidad de baja de clientes de una empresa de telecomunicaciones y dejar el proceso completo reproducible: datos con DVC, experimentos con MLflow, modelo registrado, API, contenedor, CI/CD y monitoreo de drift.

## Problema y datos

El histórico tiene 7.043 clientes y 21 columnas. La variable objetivo es `Churn`; `customerID` se conserva para identificar registros, pero se excluye del entrenamiento. La proporción de churn observada es 26,37 % y hay 26 valores faltantes en `TotalCharges`.

Algunas conclusiones del análisis exploratorio:

- Los contratos mes a mes tienen una tasa de churn mayor que los contratos largos.
- Los clientes que se van tienen, en promedio, menos antigüedad.
- Fibra óptica y cargos mensuales altos aparecen asociados a más bajas.

Son asociaciones descriptivas y no implican causalidad.

El archivo histórico no se guarda directamente en Git. Está referenciado por `data/raw/customer_churn_historical.csv.dvc` y, una vez que el objeto esté disponible en el remote, se recupera con:

```bash
dvc pull
```

El remote configurado es `https://dagshub.com/alfonsinadiaz/customer-churn-ml.dvc`, el mismo proyecto final que refleja este repositorio de GitHub. Para publicar o recuperar los datos se usan `dvc push` y `dvc pull`. Las credenciales de DagsHub se cargan localmente y nunca se suben al repositorio.

## Entrenamiento y selección

El preprocesamiento y el estimador forman un único `Pipeline` de scikit-learn. Las variables numéricas se imputan por mediana y se escalan; las categóricas se codifican con One Hot Encoding y toleran categorías nuevas.

Se comparan seis configuraciones: un baseline, tres regresiones logísticas y dos Random Forest. La selección usa validación y pondera recall, F1 y ROC-AUC. El candidato elegido se vuelve a entrenar con train + validation y se evalúa una sola vez sobre el test aislado.

La reproducción local del 17 de noviembre de 2026 seleccionó `logreg_c1_threshold035`. En el test aislado obtuvo:

| Accuracy | Precision | Recall | F1 | ROC-AUC |
|---:|---:|---:|---:|---:|
| 0,656 | 0,424 | 0,847 | 0,565 | 0,812 |

Se priorizó recall porque, para este caso, dejar pasar un cliente con riesgo de baja es más costoso que revisar un falso positivo. El umbral operativo es 0,35.

```bash
python scripts/train_api_model.py
```

El comando genera:

- `models/churn_pipeline.joblib`: pipeline que consume la API local.
- `models/version.txt`: versión legible del modelo.
- `results/generated/experiment_results.csv`: comparación de corridas.
- `results/generated/selected_model.json`: evidencia de selección y test.

Estos archivos son regenerables y no se versionan en Git.

## MLflow y Model Registry

Cada corrida guarda parámetros, métricas, artefactos, hash del dataset y commit de Git. Para trabajar localmente no hace falta configurar nada: MLflow usa `mlflow.db`.

```bash
python -m mlflow ui --backend-store-uri sqlite:///mlflow.db
```

El tracking remoto y el Model Registry pertenecen al proyecto final [`alfonsinadiaz/customer-churn-ml`](https://dagshub.com/alfonsinadiaz/customer-churn-ml). Para registrar el modelo se completan localmente las credenciales indicadas en `.env.example` y se ejecuta:

```bash
python -m src.training.train --register-best --experiment customer-churn-final
```

La primera ejecución en este Registry crea `customer-churn-candidate`, versión 1. Si DagsHub asigna otra versión, se actualizan `MODEL_URI` y `MODEL_VERSION` con el valor informado por la corrida.

## Instalación y pruebas

Se recomienda Python 3.11.

```bash
python -m venv .venv
```

En Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
```

En Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
```

Los tests cubren preparación de datos, métricas, entrenamiento y los contratos principales de la API. Un `503` en `/predict` ya no se acepta como resultado válido de una prueba de inferencia.

## API

Para desarrollo local primero se genera el modelo y luego se inicia FastAPI:

```bash
python scripts/train_api_model.py
python -m uvicorn app.api_main:app --host 0.0.0.0 --port 8000
```

Documentación interactiva: `http://localhost:8000/docs`.

| Método | Ruta | Uso |
|---|---|---|
| GET | `/health` | Estado de la API y carga del modelo |
| GET | `/model` | Versión y origen del modelo |
| POST | `/predict` | Predicción individual de churn |

Ejemplo abreviado:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: demo-final-001" \
  -d '{"gender":"Female","SeniorCitizen":"No","Partner":"Yes","Dependents":"No","tenure":12,"PhoneService":"Yes","MultipleLines":"No","InternetService":"Fiber optic","OnlineSecurity":"No","OnlineBackup":"Yes","DeviceProtection":"No","TechSupport":"No","StreamingTV":"Yes","StreamingMovies":"Yes","Contract":"Month-to-month","PaperlessBilling":"Yes","PaymentMethod":"Electronic check","MonthlyCharges":89.5,"TotalCharges":1074.0}'
```

La respuesta incluye predicción, probabilidad, nivel de riesgo, versión de modelo y `request_id`.

El contrato de entrada restringe las variables categóricas a los valores observados durante el entrenamiento. `TotalCharges` puede enviarse como `null`; el pipeline aplica la misma imputación por mediana utilizada en entrenamiento.

## Docker

La imagen usa un usuario sin privilegios, expone un healthcheck y sólo instala dependencias de inferencia desde `requirements-api.txt`.

Desarrollo local, con el modelo montado desde `./models`:

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f churn-api
```

Producción usa `compose.prod.yaml`, una imagen versionada de GHCR y el modelo del Registry. Las instrucciones completas de instalación, actualización, diagnóstico y rollback están en [RUNBOOK.md](RUNBOOK.md).

## CI/CD y versionado

`.github/workflows/ci-cd.yml` se ejecuta en cada pull request, push a `main` y tag `v*`:

1. Descarga el código e instala Python 3.11.
2. Instala dependencias y ejecuta `pytest` como condición obligatoria.
3. Construye la imagen Docker.
4. En `main` y tags, publica en `ghcr.io/alfonsinadiaz/customer-churn-ml`.

Cada imagen recibe un tag por commit (`sha-...`). Un tag Git como `v1.0.0` también publica `v1.0.0`, `1.0.0` y `latest`. El despliegue documentado fija `v1.0.0`; no depende de `latest`.

La release final se crea solamente después de que el workflow esté verde y se haya verificado el despliegue en el segundo host Linux:

```bash
git tag -a v1.0.0 -m "Entrega final"
git push origin v1.0.0
```

## Logging y observabilidad

La API escribe logs JSON en stdout. Registra inicio, errores y cada request con:

- `request_id`, método, ruta y código HTTP;
- tiempo de proceso en milisegundos;
- versión del modelo usado.

`/health` devuelve `503` si el modelo local o el Registry no están disponibles. En Docker se revisa con `docker compose ps`, `curl /health` y `docker compose logs`. El runbook explica cómo detectar caída, errores y aumento de latencia.

## Data drift

El monitoreo compara el histórico con `customer_churn_current.csv` mediante Evidently. Excluye `customerID` y `Churn`, usa PSI con umbral 0,20 y considera drift global si cambia al menos la mitad de las variables.

```bash
python monitoring/generate_drift_report.py \
  --reference data/raw/customer_churn_historical.csv \
  --current data/production/customer_churn_current.csv
```

La salida visual y el resumen quedan en `monitoring/reports/`. El drift inicia una revisión de datos y contexto; no dispara reentrenamiento automático.

## Estructura

```text
app/                  API, esquemas, carga del modelo y logging
data/                 punteros DVC y lotes locales ignorados por Git
monitoring/           generación y evidencia de data drift
scripts/              EDA y entrenamiento para la API
src/                  carga, features, evaluación y entrenamiento
tests/                pruebas automáticas
.github/workflows/    CI/CD y publicación en GHCR
compose.prod.yaml     despliegue desde una imagen versionada
RUNBOOK.md            operación del servicio en Linux
```

## Limitaciones

- La selección usa una partición fija; no se implementó validación cruzada.
- La probabilidad no está calibrada para interpretarse como riesgo financiero.
- El lote actual no incluye `Churn`, por lo que permite medir drift de entrada pero no desempeño real reciente.
- Las categorías y patrones corresponden a este dataset de telecomunicaciones; no se debe extrapolar el modelo a otra población sin validación.
- Retrain y promoción de una nueva versión requieren revisión humana.
- Los artefactos de scikit-learn usan serialización basada en pickle; sólo se cargan modelos generados por este proyecto o recuperados del Registry autorizado.

## Material de entrega

- Código y documentación: este repositorio.
- Tracking y Registry: DagsHub/MLflow enlazado arriba.
- Imagen: `ghcr.io/alfonsinadiaz/customer-churn-ml:<versión>` después del workflow de release.
- Operación: [RUNBOOK.md](RUNBOOK.md).
- Evidencia de drift: `monitoring/reports/`.
- Guion y control final: `docs/GUIA_VIDEO.md` y `docs/CHECKLIST_ENTREGA_FINAL.md`.
