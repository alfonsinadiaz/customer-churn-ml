# Checklist de entrega final

## En el repositorio

- [x] Código de entrenamiento y API.
- [x] Datos históricos referenciados con DVC.
- [x] Experimentos y Model Registry documentados.
- [x] Tests automáticos con `pytest`.
- [x] Dockerfile y Compose local.
- [x] Workflow con tests, build y publicación a GHCR.
- [x] Compose de producción con tag explícito.
- [x] Logs JSON, `request_id`, latencia y versión del modelo.
- [x] `/health`, `/model` y `/predict`.
- [x] Script y documentación de drift.
- [x] README y runbook.

## Evidencias que requieren servicios externos

- [ ] Subir el objeto histórico faltante al remote DVC con una cuenta autorizada y verificar `dvc pull` desde un clon limpio.
- [ ] Merge del cambio final a `main` con workflow verde.
- [ ] Imagen visible en GHCR con tag `v1.0.0`.
- [ ] Despliegue verificado en un segundo host Linux.
- [ ] Captura o registro de `/health`, `/model`, `/predict` y logs del host.
- [ ] Release/tag final `v1.0.0` creado después de la verificación.
- [ ] Video de 12 a 15 minutos con participación de todo el equipo.
- [ ] Link del video agregado a la entrega.

No marcar un punto externo como cumplido sólo porque exista la configuración. La evidencia debe corresponder a una ejecución real.
