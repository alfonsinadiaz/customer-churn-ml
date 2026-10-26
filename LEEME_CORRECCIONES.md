# Correcciones del segundo parcial

Esta copia incorpora las correcciones sobre main, commit original 1fa1ef7.

1. Descomprimir el ZIP. Conservar una copia del proyecto original.
2. Crear un entorno virtual y ejecutar `pip install -r requirements.txt`.
3. El paquete incluye el modelo recuperado de MLflow versión 4 y sus metadatos en models/ para facilitar la comprobación local. Ambos siguen ignorados por Git: no subirlos manualmente. La reproducción desde Git usa `python -m scripts.fetch_model`, como indica README.
4. Ejecutar `python -m pytest -q`.
5. Ejecutar `python -m uvicorn app.api_main:app --reload` y abrir http://localhost:8000/docs.
6. Usar examples/customer.json para una predicción.
7. Comprobar Docker según README. Docker no está instalado en el entorno de revisión, por lo que ese paso no fue ejecutado aquí.
8. Incorporar los archivos corregidos a una rama de su repositorio y revisar los cambios. No copiar entornos virtuales ni sobrescribir la carpeta .git.
9. Crear el tag entrega-2 únicamente sobre el commit finalmente comprobado. No fue creado ni publicado en esta revisión.

Verificación realizada: 23 pruebas automatizadas aprobadas con Python 3.12 y las dependencias indicadas. Prueba de API con TestClient, modelo real versión 4: /health correcto y /predict HTTP 200, probabilidad aproximada 0.93965, CHURN, HIGH.

Los tests automatizados usan datos sintéticos; la prueba adicional utiliza el artefacto de negocio recuperado de DagsHub. No se reentrenó ni se modificó el Registry. Quedan pendientes la ejecución real con Docker (Python 3.11 en la imagen) y la defensa/justificación de los umbrales por el equipo.

Cambios: esquemas Pydantic de entrada/salida, restricciones y categorías, carga al inicio, control de errores, versión desde metadatos con hash, script de recuperación, metadatos en entrenamiento, límites de riesgo coherentes, .dockerignore, Docker y Compose, dependencias, tests y documentación.

Se agregó .github/workflows/verificar-entrega-2.yml para comprobar en GitHub Actions las pruebas y el recorrido real de Docker Compose. Requiere publicar el código; esa ejecución todavía no ocurrió. Si DagsHub requiere autenticación, configurar los secretos MLFLOW_TRACKING_USERNAME y MLFLOW_TRACKING_PASSWORD en GitHub. Crear entrega-2 una vez que la comprobación sobre el commit presentado finalice correctamente.
