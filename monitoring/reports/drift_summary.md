# Resumen de data drift

- Variables analizadas: 19
- Variables con drift: 2
- Proporción con drift: 10.5%
- Drift global: no

## Variables señaladas

| Variable | PSI | Umbral |
|---|---:|---:|
| MonthlyCharges | 0.4149 | 0.20 |
| tenure | 0.2952 | 0.20 |

## Interpretación

- `MonthlyCharges` cambió respecto del histórico. Como es una entrada directa del modelo, una nueva mezcla de cargos puede desplazar las probabilidades de churn.
- `tenure` también cambió. Esto puede indicar una proporción distinta de clientes nuevos y antiguos, segmentos que históricamente tienen riesgos diferentes.

## Acción propuesta

El resultado es una señal de cambio en los datos, no una prueba de pérdida de calidad. Se propone validar rangos y reglas de carga, comparar las distribuciones por segmento y revisar la distribución de probabilidades. Cuando haya etiquetas recientes, se calculan recall, F1 y ROC-AUC. Sólo si el cambio persiste y el desempeño cae se evalúa reentrenar y volver a validar; no se activa un reentrenamiento automático.
