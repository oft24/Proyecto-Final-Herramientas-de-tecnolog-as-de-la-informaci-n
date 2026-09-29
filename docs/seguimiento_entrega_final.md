# Seguimiento de la Entrega Final — 29-09-2026

Los resultados locales demuestran la falla y su corrección. El 29-09-2026 Kiro reportó una corrida roja real en la EC2 QA; **el log original permanece allí y todavía faltan la corrida verde QA, las capturas y Producción**. El Word se actualizará con evidencia AWS, sin marcar pasos aún no ejecutados.

| Paso | Estado comprobado | Pendiente para la rúbrica |
|---|---|---|
| 1. Parche de Marketplace en la EC2 QA heredada | Kiro reportó checkout temporal `a4af214` en `/home/ec2-user/dangoko-pipeline-red` de la misma QA `i-086d08e1bca370b0f`, sin servicio vulnerable levantado; Avance 2 siguió en puerto 5000. | Tomar captura de identidad e integración desde QA al final. |
| 2. Pipeline que bloquea | Kiro reportó corrida QA de 29-09-2026 08:14:25 UTC: exit 1, 31 pruebas con dos fallas de autorización (`202` frente a `401`/`404`), `BLOQUEADO`; Bandit, pip-audit y CycloneDX pasaron. Log indicado en `/home/ec2-user/evidencias-final/pipeline_rojo_stdout.txt`; el rojo inicial por Python 3.9 **no** es evidencia válida. | Transferir el log QA original, confirmar metadata/exit code y tomar captura legible al final. |
| 3. Clasificación | `docs/clasificacion_hallazgo.md`: CWE-639, severidad media, impacto, reproducción y falso positivo descartado localmente. | Correlacionar con salida QA. |
| 4. Contención y prevención | `docs/respuesta_incidente.md`: Kiro reportó la revisión vulnerable solo en checkout de pruebas, sin servicio público; corrección de sesión/propiedad y pruebas locales. | Confirmar remediación funcional en QA. |
| 5. Remediación | Commit `56b06f5`: código corregido y pruebas locales del propietario/ajeno/anónimo/errores. | Validar extremo a extremo en QA. |
| 6. Pipeline que permite | Corrida final local: exit 0, `PERMITIDO`; 37 pruebas pasan, Bandit sin HIGH, pip-audit sin avisos y SBOM CycloneDX con 10 componentes. `reportes/pipeline_verde_local.txt` conserva el veredicto local. | Repetir en QA sobre el mismo SHA que vaya a Producción. |
| 7. Nueva EC2 Producción | `docs/evidencia_produccion.md` es plantilla pendiente, **no evidencia**. | Solo tras QA verde: crear EC2 nueva, desplegar, probar, tomar capturas. |

## Capturas aún por reunir en el Word

1. Pipeline rojo en QA con control y decisión visibles.
2. Hallazgo exacto de autorización en reporte/prueba QA.
3. Diff o commit de remediación identificable.
4. Pipeline verde en QA.
5. Identidad de la misma EC2 QA del Avance 2 (`i-086d08e1bca370b0f`).
6. EC2 nueva de Producción, con ID propio.
7. Aplicación corregida funcionando en esa EC2.

Kiro solo operará AWS y comunicará salidas/capturas; Codex mantiene código, reportes y Word. El video/presentación se atiende después. No se debe afirmar entrega de correo real sin `delivery=email_sent`, y aun ese estado solo confirma aceptación por SMTP, no recepción final.
