"""Entrena el modelo de churn y lo guarda para que la API lo cargue.

Ejecuta el entrenamiento existente de ``src.training.train`` y escribe un
archivo ``version.txt`` junto al pipeline para que la API pueda reportar la
versión del modelo sin depender de MLflow.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.training.train import run_experiments, DEFAULT_DATA, DEFAULT_MODEL, DEFAULT_RESULTS


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VERSION_PATH = PROJECT_ROOT / "models" / "version.txt"


def main() -> None:
    results = run_experiments(
        data_path=DEFAULT_DATA,
        model_path=DEFAULT_MODEL,
        results_path=DEFAULT_RESULTS,
        experiment="customer-churn-entrega-2",
        register_best=False,
    )

    best = results.sort_values("recall", ascending=False).iloc[0]
    version = f"{best['run_name']}-{best['recall']:.3f}"

    VERSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    VERSION_PATH.write_text(version, encoding="utf-8")

    evidence_path = DEFAULT_RESULTS.parent / "selected_model.json"
    if evidence_path.exists():
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        evidence["api_model_version"] = version
        with evidence_path.open("w", encoding="utf-8") as file:
            json.dump(evidence, file, indent=2)

    print(f"\nModelo guardado en: {DEFAULT_MODEL}")
    print(f"Version guardada en: {VERSION_PATH} ({version})")


if __name__ == "__main__":
    main()
