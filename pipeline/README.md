# Pipeline de calidad

El pipeline ejecuta controles relacionados con los riesgos de esta aplicación y termina en una sola decisión. Instala las herramientas fijadas en `pipeline/requirements-tools.txt` y las dependencias de `app/requirements.txt` antes de correrlo:

```powershell
python pipeline/run_pipeline.py
```

Herramientas y artefactos:

- Bandit analiza el backend y el servicio de notificaciones. Bloquea hallazgos `HIGH`; deja todos los avisos en `reportes/bandit.json` para revisión.
- pip-audit consulta vulnerabilidades conocidas de las dependencias, incluidas las transitivas. Bloquea cualquier aviso único y guarda `reportes/pip_audit.json`.
- CycloneDX Python genera y valida `reportes/sbom_cyclonedx.json` desde `app/requirements.txt`.
- Las pruebas de regresión incluyen controles de autorización para la nueva funcionalidad de reenvío. Una prueba fallida bloquea el despliegue.

La evidencia roja de la Entrega Final debe salir de una corrida sobre el parche de Marketplace sin remediar. Bandit no identifica necesariamente errores de autorización: si no marca el parche, documenta el límite y muestra la prueba de autorización que lo detiene. La corrida verde se toma después de corregir el endpoint y ejecutar el mismo pipeline.
