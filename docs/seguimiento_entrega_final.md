# Seguimiento de la Entrega Final — 29-09-2026

Los resultados locales demuestran la falla y su corrección, pero **no sustituyen** las corridas y capturas de QA ni Producción solicitadas en la rúbrica. El Word se actualizará con evidencia AWS, sin marcar pasos aún no ejecutados.

| Paso | Estado comprobado | Pendiente para la rúbrica |
|---|---|---|
| 1. Parche de Marketplace en la EC2 QA heredada | Endpoint inicial integrado en commit local `a4af214`; falla de autorización demostrada con pruebas locales. | Clonar en la misma EC2 QA, sin desplegar la revisión vulnerable. Capturar instancia e integración. |
| 2. Pipeline que bloquea | `reportes/pipeline_bloqueado_local.txt`: exit 1, dos pruebas de autorización fallan, `BLOQUEADO`. | Repetir en QA, guardar stdout/stderr/exit y captura legible. |
| 3. Clasificación | `docs/clasificacion_hallazgo.md`: CWE-639, severidad media, impacto, reproducción y falso positivo descartado localmente. | Correlacionar con salida QA. |
| 4. Contención y prevención | `docs/respuesta_incidente.md`: la revisión vulnerable no se ejecutó como servicio público; corrección de sesión/propiedad y pruebas locales. | Confirmar contención y resultado en QA. |
| 5. Remediación | Código corregido y tests locales del propietario/ajeno/anónimo/errores; commit final pendiente. | Registrar SHA remediado y validar extremo a extremo en QA. |
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
