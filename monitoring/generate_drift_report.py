"""Genera evidencia de data drift entre el histórico y un lote actual.

El identificador y el target no se comparan porque no son variables de entrada
del modelo. Se usa PSI con umbral 0.20 para que el criterio sea estable entre
columnas numéricas y categóricas.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE = PROJECT_ROOT / "data" / "raw" / "customer_churn_historical.csv"
DEFAULT_CURRENT = PROJECT_ROOT / "data" / "production" / "customer_churn_current.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "monitoring" / "reports"
EXCLUDED_COLUMNS = {"customerID", "Churn"}


def comparable_frames(reference_path: Path, current_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    reference = pd.read_csv(reference_path)
    current = pd.read_csv(current_path)
    common = [
        column
        for column in reference.columns
        if column in current.columns and column not in EXCLUDED_COLUMNS
    ]
    if not common:
        raise ValueError("No hay variables comparables entre ambos archivos")
    return reference[common].copy(), current[common].copy()


def extract_summary(snapshot: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "drift_detected": False,
        "drifted_columns_count": 0,
        "drifted_columns_share": 0.0,
        "columns": [],
    }
    metrics = snapshot.dict().get("metrics", [])
    for metric in metrics:
        name = metric.get("metric_name", metric.get("metric", ""))
        config = metric.get("config", {}) or {}
        value = metric.get("value")
        if "DriftedColumnsCount" in name and isinstance(value, dict):
            summary["drifted_columns_count"] = int(value.get("count", 0))
            summary["drifted_columns_share"] = float(value.get("share", 0.0))
            summary["drift_detected"] = summary["drifted_columns_share"] >= float(
                config.get("drift_share", 0.5)
            )
        elif "ValueDrift" in name:
            column = config.get("column", "unknown")
            if isinstance(column, dict):
                column = column.get("column_name", str(column))
            score = float(value) if value is not None else None
            threshold = float(config.get("threshold", 0.2))
            summary["columns"].append(
                {
                    "column": str(column),
                    "psi": score,
                    "threshold": threshold,
                    "drifted": score is not None and score > threshold,
                }
            )
    summary["columns"].sort(
        key=lambda item: item["psi"] if item["psi"] is not None else -1,
        reverse=True,
    )
    return summary


def write_markdown(summary: dict[str, Any], path: Path) -> None:
    drifted = [item for item in summary["columns"] if item["drifted"]]
    lines = [
        "# Resumen de data drift",
        "",
        f"- Variables analizadas: {len(summary['columns'])}",
        f"- Variables con drift: {summary['drifted_columns_count']}",
        f"- Proporción con drift: {summary['drifted_columns_share']:.1%}",
        f"- Drift global: {'sí' if summary['drift_detected'] else 'no'}",
        "",
        "## Variables señaladas",
        "",
    ]
    if drifted:
        lines.extend(["| Variable | PSI | Umbral |", "|---|---:|---:|"])
        lines.extend(
            f"| {item['column']} | {item['psi']:.4f} | {item['threshold']:.2f} |"
            for item in drifted
        )
    else:
        lines.append("Ninguna variable superó el umbral configurado.")
    drifted_names = {item["column"] for item in drifted}
    lines.extend(["", "## Interpretación", ""])
    if "MonthlyCharges" in drifted_names:
        lines.append(
            "- `MonthlyCharges` cambió respecto del histórico. Como es una entrada directa del modelo, una nueva mezcla de cargos puede desplazar las probabilidades de churn."
        )
    if "tenure" in drifted_names:
        lines.append(
            "- `tenure` también cambió. Esto puede indicar una proporción distinta de clientes nuevos y antiguos, segmentos que históricamente tienen riesgos diferentes."
        )
    if not drifted:
        lines.append("- El lote se mantiene dentro del criterio configurado para todas las variables.")
    lines.extend(
        [
            "",
            "## Acción propuesta",
            "",
            "El resultado es una señal de cambio en los datos, no una prueba de pérdida de calidad. Se propone validar rangos y reglas de carga, comparar las distribuciones por segmento y revisar la distribución de probabilidades. Cuando haya etiquetas recientes, se calculan recall, F1 y ROC-AUC. Sólo si el cambio persiste y el desempeño cae se evalúa reentrenar y volver a validar; no se activa un reentrenamiento automático.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def generate(reference_path: Path, current_path: Path, output_dir: Path) -> dict[str, Any]:
    reference, current = comparable_frames(reference_path, current_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    report = Report([DataDriftPreset(method="psi", threshold=0.20, drift_share=0.50)])
    snapshot = report.run(current, reference)
    snapshot.save_html(str(output_dir / "drift_report.html"))
    snapshot.save_json(str(output_dir / "drift_report.json"))

    summary = extract_summary(snapshot)
    summary.update(
        {
            "reference_rows": len(reference),
            "current_rows": len(current),
            "reference_path": reference_path.name,
            "current_path": current_path.name,
        }
    )
    (output_dir / "drift_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_markdown(summary, output_dir / "drift_summary.md")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera el reporte de data drift")
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--current", type=Path, default=DEFAULT_CURRENT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = generate(args.reference, args.current, args.output_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
