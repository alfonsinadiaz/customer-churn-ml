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

Para entrenar los tres modelos, guardar las métricas y exportar el candidato:

```bash
python -m src.training.train
```

El pipeline seleccionado se guarda en `models/churn_pipeline.joblib` y las métricas en `results/generated/model_metrics.csv`. Ambos son archivos generados y no se versionan en Git.

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

En esta copia el remote ya está configurado. Para subir o recuperar el CSV sólo hay que actualizar el token local y ejecutar `dvc push` o `dvc pull`.

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
│   └── test_preprocessing.py
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
| Pruebas de métricas y preprocesamiento | Cumplido |
| Dataset rastreado localmente con DVC | Cumplido |
| Remote DVC apuntando al DagsHub existente | Configurado |
| Autenticación vigente y comprobación de `dvc push` | Pendiente: renovar token local |
| Seis corridas relevantes en MLflow | Pendiente |
| Modelo candidato en Model Registry | Pendiente |
| Tag Git `entrega-1` sobre el commit presentado | Pendiente |
| Reproducción completa desde una segunda copia | Pendiente |

Los puntos pendientes son necesarios para cumplir completamente la consigna y asegurar la trazabilidad entre dataset, código, corridas y modelo registrado.

## Repositorio

<https://github.com/alfonsinadiaz/customer-churn-ml>
