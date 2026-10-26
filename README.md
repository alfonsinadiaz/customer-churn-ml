# Customer Churn - Primer Parcial

Proyecto de Laboratorio de Minería de Datos para analizar y predecir el abandono de clientes de una empresa de telecomunicaciones.

El notebook conserva el desarrollo exploratorio y el código reutilizable se encuentra refactorizado en `src/`. El entrenamiento también puede ejecutarse desde Python sin depender de la ejecución manual del notebook.

## Dataset

El notebook espera el archivo:

```text
data/raw/customer_churn_historical.csv
```

El dataset contiene:

- 7.043 clientes y 21 columnas.
- 1.857 casos de churn, equivalentes al 26,37 %.
- 26 valores faltantes en `TotalCharges`.
- 0 filas duplicadas.

`customerID` se excluye del entrenamiento porque identifica al cliente y no representa una característica útil para generalizar predicciones.

El CSV no se incluye directamente en Git. DVC lo referencia mediante `data/raw/customer_churn_historical.csv.dvc`.

## Análisis exploratorio

El EDA revisa dimensiones, tipos de datos, cardinalidad, valores faltantes, distribuciones y relaciones descriptivas con `Churn`.

Principales observaciones:

- Los contratos mes a mes presentan una tasa de churn de 38,73 %.
- Los contratos de dos años presentan una tasa de 8,97 %.
- Los clientes con fibra óptica presentan una tasa de 40,25 %.
- Los clientes que abandonan tienen menor antigüedad promedio: 29,28 meses frente a 37,28.
- El cargo mensual promedio es mayor entre quienes abandonan: 79,98 frente a 63,94.

Estas relaciones son descriptivas y no demuestran causalidad.

## Preparación de datos

La partición utiliza `train_test_split` con estratificación y `random_state=42`:

- Entrenamiento: 5.634 registros, 80 %.
- Test: 1.409 registros, 20 %.

El preprocesamiento se implementa con `Pipeline` y `ColumnTransformer`:

- Variables numéricas: imputación por mediana y estandarización.
- Variables categóricas: One-Hot Encoding con categorías desconocidas ignoradas.
- `SeniorCitizen`: conversión de 0/1 a No/Yes antes del modelado.

Los parámetros de imputación y escalado se ajustan sólo con los datos de entrenamiento.

## Modelos comparados

| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Dummy Classifier | 0,74 | 0,00 | 0,00 | 0,00 | 0,50 |
| Regresión Logística balanceada | 0,72 | 0,48 | 0,72 | 0,58 | 0,81 |
| Random Forest balanceado | 0,76 | 0,54 | 0,61 | 0,57 | 0,80 |

La Regresión Logística se selecciona como candidata inicial porque obtiene el mayor recall, el mayor F1 y el mayor ROC-AUC de los modelos predictivos evaluados. Detecta 269 casos de churn y deja 103 falsos negativos.

La selección corresponde a una primera iteración sobre una sola partición train/test. Todavía no se realizó validación cruzada ni ajuste del umbral.

## Instalación

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux o macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecución

Con el dataset disponible en `data/raw/`, el EDA resumido se ejecuta desde la raíz:

```bash
python -m scripts.eda
```

Para ejecutar las seis alternativas, evaluar el candidato sobre el test aislado y registrarlo:

```bash
python -m src.training.train --register-best
```

El pipeline seleccionado se guarda en `models/churn_pipeline.joblib`. Las métricas y la identificación del Run final se generan en `results/generated/`. Estos archivos pueden regenerarse y no se versionan en Git.

## MLflow y Model Registry

Por defecto, las corridas se guardan en `sqlite:///mlflow.db`. La interfaz local se abre con:

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
```

El entrenamiento registra seis alternativas razonadas:

| Run | Familia | Cambio evaluado |
|---|---|---|
| `dummy_prior` | Baseline | Referencia sin capacidad predictiva |
| `logreg_c0.5` | Lineal | Regularización `C=0.5` |
| `logreg_c1` | Lineal | Regularización `C=1.0` |
| `logreg_c1_threshold035` | Lineal | Umbral de decisión 0.35 |
| `random_forest_depth5` | Árbol | Profundidad máxima 5 |
| `random_forest_depth10` | Árbol | Profundidad máxima 10 |

Cada Run guarda parámetros, métricas, hash del dataset, commit Git, archivo JSON y pipeline completo. Una séptima corrida entrena el candidato seleccionado con train y validation, lo evalúa una sola vez sobre test y origina la versión del Model Registry.

La validación seleccionó `logreg_c1_threshold035`. En el test aislado obtuvo recall `0,847`, F1 `0,565` y ROC-AUC `0,812`.

Para registrar el mismo flujo en DagsHub se definen localmente las siguientes variables, sin guardar el token en Git:

```text
MLFLOW_TRACKING_URI=https://dagshub.com/giselle.san/entregaPrimerParcial.mlflow
MLFLOW_TRACKING_USERNAME=giselle.san
MLFLOW_TRACKING_PASSWORD=TOKEN_PERSONAL
```

La ejecución remota verificada el 21 de septiembre de 2026 registró `customer-churn-candidate` versión 4. La corrida final de origen es [`cbc3cc5511bf4a5fae054191f097fe76`](https://dagshub.com/giselle.san/entregaPrimerParcial.mlflow/#/experiments/0/runs/cbc3cc5511bf4a5fae054191f097fe76) y conserva como origen el commit `f629724`. Las seis corridas pueden compararse en el [experimento de DagsHub MLflow](https://dagshub.com/giselle.san/entregaPrimerParcial.mlflow/#/experiments/0).

Las pruebas se ejecutan con:

```bash
pytest
```

El notebook sigue disponible en `notebooks/01_eda_y_modelos.ipynb`. Debe iniciarse desde la carpeta `notebooks/` para que su ruta `../data/raw/customer_churn_historical.csv` encuentre el archivo.

## DVC

La versión local de DVC ya está inicializada y el CSV está rastreado. Para comprobar el estado:

```bash
dvc status
```

El remote utiliza el proyecto de DagsHub que ya existía y su URL ya está guardada en `.dvc/config`:

<https://dagshub.com/giselle.san/entregaPrimerParcial>

Cada integrante debe guardar su propio usuario y token mediante configuración local. `.dvc/config.local` está ignorado por Git y los tokens no deben incluirse en el repositorio. Después puede recuperar o subir los datos con:

```bash
dvc pull
dvc push
```

En esta copia el remote ya está configurado y `dvc push` fue comprobado el 21 de septiembre de 2026. Cada integrante utiliza sus propias credenciales para ejecutar `dvc pull` o `dvc push`.

## Estructura actual

```text
customer-churn-ml/
├── data/raw/
│   └── customer_churn_historical.csv.dvc
├── notebooks/
│   └── 01_eda_y_modelos.ipynb
├── scripts/
│   └── eda.py
├── src/
│   ├── data/load_data.py
│   ├── evaluation/metrics.py
│   ├── features/preprocessing.py
│   └── training/train.py
├── tests/
│   ├── test_metrics.py
│   ├── test_preprocessing.py
│   └── test_training.py
├── .dvc/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Estado frente a los requisitos del parcial

| Requisito | Estado actual |
|---|---|
| Repositorio GitHub con README y dependencias | Cumplido |
| EDA de dimensiones, tipos, faltantes, target y calidad | Cumplido |
| Partición reproducible y test separado | Cumplido |
| Pipeline de preprocesamiento con scikit-learn | Cumplido |
| Baseline, modelo lineal y modelo de árboles | Cumplido |
| Entrenamiento ejecutable desde Python fuera del notebook | Cumplido |
| Pruebas de métricas, preprocesamiento y alternativas | Cumplido: 3 pruebas |
| Dataset rastreado localmente con DVC | Cumplido |
| Remote DVC apuntando al DagsHub existente | Configurado |
| Autenticación vigente y comprobación de `dvc push` | Cumplido |
| Seis corridas relevantes en MLflow | Cumplido en DagsHub |
| Modelo candidato en Model Registry | Cumplido: versión 4, Run `cbc3cc5511bf4a5fae054191f097fe76` |
| Tag Git `entrega-1` sobre el commit presentado | Cumplido en la versión final |
| Reproducción completa desde una segunda copia | Comprobada: clone, DVC pull, EDA, pruebas y entrenamiento |

La segunda copia utilizó una credencial local de DagsHub que se retiró al finalizar la prueba. Cada integrante debe utilizar su propio token; ninguna credencial forma parte de Git.

## Repositorio

<https://github.com/alfonsinadiaz/customer-churn-ml>


## Segundo parcial: ejecución reproducible

Dependencias ajustadas: scikit-learn 1.9.0 coincide con el artefacto registrado recuperado; MLflow 3.17.2 queda fijado para evitar cambios de versión mayor o menor inadvertidos.


La API requiere un pipeline y un archivo JSON asociado. La versión devuelta sale de los metadatos cuyo hash se comprueba al iniciar; no se fija en el código. Una ausencia o alteración del modelo impide el arranque.

### Preparar el modelo registrado

Instalar `requirements.txt` en un entorno virtual. Definir las variables de `.env.example` en la terminal (el archivo `.env` no se carga automáticamente). No guardar tokens en Git.

Linux/macOS:

```bash
export MLFLOW_TRACKING_URI=https://dagshub.com/giselle.san/entregaPrimerParcial.mlflow
export MODEL_NAME=customer-churn-candidate
export MODEL_VERSION=4
# Definir MLFLOW_TRACKING_USERNAME y MLFLOW_TRACKING_PASSWORD si el servidor requiere autenticación.
python -m scripts.fetch_model
```

PowerShell:

```powershell
$env:MLFLOW_TRACKING_URI="https://dagshub.com/giselle.san/entregaPrimerParcial.mlflow"
$env:MODEL_NAME="customer-churn-candidate"
$env:MODEL_VERSION="4"
python -m scripts.fetch_model
```

Este comando requiere acceso al Registry y genera `models/churn_pipeline.joblib` y `models/churn_pipeline.json`, con Run, commit, hash del dataset, hash del artefacto y umbrales. El hash comprueba correspondencia local; el origen registrado se obtiene de MLflow. Descargar únicamente modelos de un origen confiable.

Alternativa: recuperar el dataset con `dvc pull` y ejecutar `python -m src.training.train --register-best`. Esto crea un nuevo entrenamiento y, si se registra, una nueva versión: no garantiza recuperar la versión 4. Sin `--register-best`, la API identifica el artefacto como `local-<hash>`.

### Verificar y ejecutar

```bash
python -m pytest -q
python -m uvicorn app.api_main:app --host 0.0.0.0 --port 8000
```

Swagger: http://localhost:8000/docs. Estado: `GET /health`. Inferencia: `POST /predict`. El cuerpo debe contener las 19 características del cliente; se puede usar `examples/customer.json` con Swagger o:

```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" --data-binary @examples/customer.json
```

La respuesta incluye `prediction`, `probability` (entre 0 y 1), `risk_level` y `model_version`, con esquemas Pydantic de entrada y salida. Campos faltantes, categorías desconocidas, negativos o campos extra producen HTTP 422. Un error interno de inferencia devuelve HTTP 500 sin exponer detalles internos. La indisponibilidad del modelo produce HTTP 503 cuando el servicio está activo; normalmente la falta del modelo impide iniciar.

El umbral de clasificación se recupera de los parámetros del Run. LOW queda por debajo de ese umbral; MEDIUM desde el umbral hasta 0.70, y HIGH desde 0.70. Se alinea LOW con NO_CHURN para evitar resultados contradictorios. El corte 0.70 es una regla operativa provisional para priorizar contactos, no un umbral óptimo demostrado. El equipo debe justificarlo con capacidad de atención, costos y evaluación de calibración antes de un uso comercial. El umbral 0.35 del candidato original favorece recall ante el costo de omitir clientes que abandonan.

### Docker y Compose

Preparar primero ambos archivos del modelo. Se incorporan a la imagen; las credenciales de recuperación no se copian. Un cambio de modelo exige reconstruir la imagen.

```bash
docker build -t churn-api .
docker compose up --build -d
docker compose ps
docker compose logs
docker compose down
```

Se publica el puerto 8000 y se consulta `/health` como healthcheck. El Dockerfile comprueba la presencia de ambos artefactos durante la construcción; el arranque verifica su hash.

### Alcance de las pruebas y evidencia pendiente

La suite usa un pipeline real entrenado con datos sintéticos temporales para verificar carga, inferencia, contratos, categorías, valores negativos, campos faltantes, errores y umbrales. No mide la calidad del modelo de negocio ni certifica acceso a DagsHub. Antes de entregar, ejecutar la recuperación de la versión real y la demostración Docker completa en otra computadora, conservar su evidencia y contrastar la versión/Run con el Registry.

Después de verificar la solución, crear y publicar el tag sobre el commit evaluado:

```bash
git add .
git commit -m "Completa API, validación y reproducción del segundo parcial"
git tag entrega-2
git push origin HEAD
git push origin entrega-2
```

No crear el tag sobre una versión sin verificar. CI/CD, GHCR, deployment externo y drift corresponden a la entrega final.
