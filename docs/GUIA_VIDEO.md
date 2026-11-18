# Guía para el video final

Duración objetivo: 13 a 14 minutos. Todos los integrantes deben hablar y la demo debe hacerse sobre el servicio desplegado en el segundo host Linux.

| Tiempo | Contenido | Evidencia en pantalla |
|---|---|---|
| 0:00–1:00 | Presentación, problema y objetivo | README y nombres del equipo |
| 1:00–2:30 | Datos, DVC y preparación | `.dvc`, pipeline y `dvc status` |
| 2:30–4:00 | Modelos, criterio y métricas | MLflow: comparación de corridas |
| 4:00–5:00 | Modelo elegido y Registry | versión registrada y run de origen |
| 5:00–6:30 | API y contenedor | endpoints, Dockerfile y healthcheck |
| 6:30–8:00 | CI/CD | workflow verde y paquete en GHCR con tag explícito |
| 8:00–10:30 | Demo real | `/health`, `/model` y `/predict` en el host Linux |
| 10:30–11:30 | Logs | buscar el `request_id` de la predicción y mostrar `duration_ms` |
| 11:30–13:00 | Drift | reporte Evidently, variables señaladas e interpretación |
| 13:00–14:00 | Limitaciones y cierre | decisiones pendientes y posibles mejoras |

## Antes de grabar

- Repartir las secciones para que todos participen.
- Cerrar pestañas, archivos y terminales que muestren tokens.
- Dejar preparado un JSON válido para `/predict`.
- Confirmar que el tag mostrado en GHCR coincide con el desplegado.
- Hacer una prueba completa y verificar que el `request_id` aparece en la respuesta y en los logs.
- No afirmar que el drift obliga a reentrenar: explicar la revisión propuesta.

## Frase simple para explicar la arquitectura

“Git versiona el código, DVC referencia los datos, MLflow registra las pruebas y el modelo, GitHub Actions valida y publica la imagen, y Docker Compose ejecuta esa versión en otro servidor. Evidently compara el lote actual con la referencia.”
