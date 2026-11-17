# Monitoreo de drift

El reporte compara las variables que consume el modelo entre el dataset histórico y el lote actual. `customerID` se excluye por ser un identificador y `Churn` porque el lote de producción todavía no tiene etiqueta.

```bash
python monitoring/generate_drift_report.py \
  --reference data/raw/customer_churn_historical.csv \
  --current data/production/customer_churn_current.csv
```

Los resultados quedan en `monitoring/reports/`:

- `drift_report.html`: reporte visual de Evidently.
- `drift_report.json`: salida completa para auditoría.
- `drift_summary.md` y `drift_summary.json`: resumen de variables señaladas y criterio de acción.

Se usa PSI con umbral 0,20 y se considera drift global si al menos la mitad de las variables lo supera. Es una alerta para investigar; por sí sola no dispara un reentrenamiento.
