# Evidencias del pipeline y de AWS

## Corridas oficiales

| Corrida | Entorno | SHA | Fecha UTC | Resultado |
|---|---|---|---|---|
| Roja v2 | QA i-086d08e1bca370b0f | a4af21417163f8e9811dc4633cace6eaf81bc587 | 2026-09-29 19:01:34 | BLOQUEADO, exit 1 |
| Verde v2 | Misma QA | 80a4a3b408837feb08c4097849db1660b237a6f1 | 2026-09-29 16:37:14 | PERMITIDO, exit 0 |

- [Rojo completo](pipeline_bloqueado.txt) y [metadata](pipeline_bloqueado_metadata.txt).
- [Verde completo](pipeline_verde.txt); [cierre QA](aws/cierre_qa.txt) registra SHA antes/después y exit code.
- Python 3.12.14. Sin `--demo-red` ni archivo plantado.
- El pipeline usa Flask test client con dependencias aisladas; las verificaciones HTTP contra servicios AWS se conservan por separado.

## Cronología y discrepancias

La [primera corrida roja](historico/pipeline_rojo_inicial.txt), con [metadata de las 08:14 UTC](historico/pipeline_rojo_inicial_metadata.txt), precedió al verde y detectó las dos fallas. Su wrapper registró exit 0 porque leyó el estado de `tee`. La repetición roja v2 a las 19:01 obtuvo directamente `pipeline_rc=1`. Su fecha posterior no significa que el vulnerable se desplegara en Producción.

La metadata verde de las 16:22 correspondía a una corrida anterior sin comprobación de SHA antes/después. Aquí se usa únicamente el verde de las 16:37, vinculado al cierre que comprueba 80a4a3b antes y después. [Vinculación conservada](aws/vinculacion_verde.txt). No se sustituyeron fechas.

En `aws/pruebas_qa.txt`, la primera extracción de /api/auth/me imprimió campos nulos al interpretar mal el objeto JSON. El cierre confirma authenticated=true y usuario 8. Las consultas RDS iniciales dejaron secciones vacías; `rds_qa.txt` y `rds_produccion.txt` contienen la comprobación complementaria. Se conservaron los errores de diagnóstico en los logs.

## Persistencia y correo

| Archivo | Evidencia |
|---|---|
| [QA](aws/pruebas_qa.txt) | Compra, S3 y autorización |
| [RDS QA](aws/rds_qa.txt) | BDK-D41BA639AE y partidas |
| [Producción](aws/pruebas_produccion.txt) | Compra, S3 y rechazos de acceso |
| [RDS Producción](aws/rds_produccion.txt) | BDK-4E6A7D2EDB y partidas |
| [Compra con correo](aws/compra_correo.json) | BDK-3E199EDDFD, email_sent |
| [Resend](aws/resend_entrega.json) | Estado delivered |

El [manifiesto](manifest_evidencias.json) identifica originales y copias mediante SHA256. Los logs del pipeline se copiaron byte a byte. Algunos registros PowerShell pasaron de UTF-16 a UTF-8 sin cambiar contenido. El correo personal se redactó en las dos evidencias JSON de SMTP. Los originales privados se conservaron fuera de Git.

`pipeline_*_local.txt`, `bandit.json`, `pip_audit.json` y `sbom_cyclonedx.json` son artefactos conservados de validación local, no exportaciones AWS. El verde QA acredita la ejecución de esas herramientas allí. El SBOM contiene diez requisitos directos, no un inventario completo del sistema operativo.
