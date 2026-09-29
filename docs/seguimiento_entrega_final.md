# Seguimiento de la Entrega Final

Esta lista separa la base heredada del Avance 2 de los siete pasos nuevos que exige la Entrega Final. Ningún resultado local sustituye una captura de QA o Producción. Actualizarla junto con el Word `entrega/Evidencias_EntregaFinal_en_progreso.docx` cuando exista evidencia verificable.

| Paso de la rúbrica | Estado al 29-09-2026 | Evidencia que falta |
|---|---|---|
| 1. Aplicar el parche de Marketplace en la EC2 de QA del Avance 2 | Pendiente | Código integrado sin corregir y prueba del endpoint en QA. |
| 2. Pipeline bloqueando ese parche | Pendiente | Corrida real completa en QA, control fallido y decisión final BLOQUEADO en `reportes/pipeline_bloqueado.*`. |
| 3. Clasificar hallazgo | Pendiente de prueba | `docs/clasificacion_hallazgo.md`: tipo/CWE, severidad con impacto y explotabilidad, falso positivo sí/no. |
| 4. Separar contención y prevención | Pendiente | `docs/respuesta_incidente.md` con acciones distintas y verificadas. |
| 5. Remediar la causa raíz | Pendiente | Diff y commit de autorización manteniendo el reenvío funcional; pruebas contra acceso a pedido ajeno. |
| 6. Pipeline permitiendo después del arreglo | Pendiente | Corrida real completa en QA, decisión final PERMITIDO en `reportes/pipeline_verde.*`. |
| 7. Promover a EC2 nueva de Producción | Pendiente | `docs/evidencia_produccion.md`, captura de instancia nueva, commit desplegado, aplicación y reenvío corregido funcionando. |

## Hallazgos preliminares del parche entregado

El endpoint `POST /pedidos/<int:pedido_id>/reenviar-confirmacion` obtiene un pedido por identificador y reenvía su confirmación sin verificar sesión ni propiedad. Esto sugiere una falla de autorización por objeto, pero la clasificación definitiva y el bloqueo del pipeline deben documentarse después de ejecutarlo en QA. Además, el parche usa imports de ejemplo (`app.db`, `app.notificaciones`) y un ID entero, mientras que Dangoko usa IDs de pedido tipo `BDK-...`; la integración debe adaptar estos puntos sin corregir aún la falla de autorización para la primera corrida roja. No se debe afirmar que la herramienta lo detectó antes de ver su salida real.

## Evidencia visual pendiente en el Word

1. Pipeline bloqueando en QA.
2. Hallazgo exacto en reporte de herramienta o prueba manual.
3. Diff/commit real de remediación.
4. Pipeline permitiendo en QA.
5. Misma instancia EC2 de QA del Avance 2.
6. Instancia EC2 nueva de Producción.
7. Aplicación corregida funcionando en Producción.

## Puertas de calidad

- Confirmar identidad de instancia y cuenta AWS antes de modificar QA; no copiar credenciales al repositorio.
- Integrar el parche en rama de trabajo o commit identificable y capturar el estado vulnerable antes de remediarlo.
- Si Bandit no detecta la autorización ausente, añadir una prueba de seguridad que falle por acceso a pedido ajeno y registrar honestamente la limitación del SAST.
- No desplegar en Producción hasta que el mismo commit corregido pase pruebas y pipeline en QA.
- Conservar en el Word solo hechos demostrados. Los campos pendientes se marcan como tales; no se inventan capturas ni resultados.
