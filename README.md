# Customer Churn - Primer Parcial

Proyecto de Laboratorio de Minería de Datos para analizar y predecir el abandono de clientes de una empresa de telecomunicaciones.

La versión actual concentra el análisis exploratorio, el preprocesamiento y la comparación inicial de modelos en `notebooks/01_eda_y_modelos.ipynb`.

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

El CSV no se incluye actualmente en Git. Debe ubicarse manualmente en `data/raw/` antes de ejecutar el notebook.

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

1. Crear la carpeta `data/raw/`.
2. Copiar allí `customer_churn_historical.csv`.
3. Abrir `notebooks/01_eda_y_modelos.ipynb`.
4. Ejecutar las celdas en orden.

El notebook debe iniciarse desde la carpeta `notebooks/` para que la ruta `../data/raw/customer_churn_historical.csv` encuentre el archivo.

## Estructura actual

```text
customer-churn-ml/
├── notebooks/
│   └── 01_eda_y_modelos.ipynb
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
| Dataset bajo DVC con remoto en DagsHub | Pendiente |
| Seis corridas relevantes en MLflow | Pendiente |
| Modelo candidato en Model Registry | Pendiente |
| Entrenamiento ejecutable desde Python fuera del notebook | Pendiente |
| Tag Git `entrega-1` sobre el commit presentado | Pendiente |
| Reproducción completa desde una segunda copia | Pendiente |

Los puntos pendientes son necesarios para cumplir completamente la consigna y asegurar la trazabilidad entre dataset, código, corridas y modelo registrado.

## Repositorio

<https://github.com/alfonsinadiaz/customer-churn-ml>
