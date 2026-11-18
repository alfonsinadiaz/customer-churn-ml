# Lote actual

Ubicar en esta carpeta el archivo `customer_churn_current.csv` entregado por la materia. El CSV contiene datos de clientes, se ignora en Git y sólo se usa para generar la evidencia de drift.

```bash
python monitoring/generate_drift_report.py
```

El script compara las columnas de entrada comunes con el histórico recuperado por DVC.
