# Índice de la Entrega Final

Luis Antonio Hernández Vázquez · 3101149 · LSCA2314 · Tema 3 Marketplace.

| Paso de la rúbrica | Resultado comprobado | Evidencia |
|---|---|---|
| 1. Integrar en QA | Checkout vulnerable aislado a4af214, sin servicio público | [Metadata roja](../reportes/pipeline_bloqueado_metadata.txt) |
| 2. Bloquear | 31 pruebas, dos fallas, exit 1 | [Log rojo](../reportes/pipeline_bloqueado.txt) |
| 3. Clasificar | CWE-639, severidad media justificada | [Clasificación](clasificacion_hallazgo.md) |
| 4. Contener y prevenir | Aislamiento y control de sesión/propietario | [Respuesta](respuesta_incidente.md) |
| 5. Remediar | Commit 56b06f5; mejora operativa en 80a4a3b | [Módulo](../app/backend/reenviar_confirmacion.py), [pruebas](../app/tests/test_reenviar_confirmacion.py) |
| 6. Verde QA | SHA 80a4a3b, siete etapas OK, exit 0 | [Verde](../reportes/pipeline_verde.txt), [cierre](../reportes/aws/cierre_qa.txt) |
| 7. Nueva Producción | Mismo SHA, compra y autorización verificadas | [Producción](evidencia_produccion.md), [capturas](capturas/README.md) |

## Organización

- `app/`: frontend, backend, notificaciones y pruebas.
- `pipeline/`: orquestador y herramientas estándar fijadas.
- `infra/`: Terraform de la base y descripción del alcance actual.
- `reportes/`: corridas QA, verificaciones AWS y manifiesto de integridad; sufijos `_local` indican antecedentes.
- `docs/`: arquitectura, decisiones, clasificación, respuesta, evidencias y capturas.
- `entrega/`: instrucciones para la plataforma y borrador histórico identificado.

## Pendientes fuera del cierre técnico

El alumno debe revisar y subir su Word actualizado a la plataforma. La captura del correo recibido es complementaria y todavía no forma parte de las imágenes publicadas. No se fabricó una captura de Gmail. El Word guardado antes de configurar SMTP contiene una nota de correo pendiente que debe corregirse antes de subirlo.

La presentación es en vivo y de hasta diez minutos. Su consigna exige IP pública, no localhost. Falta preparar acceso controlado, comprobar instancias, grabar respaldo y ensayar. No se abrieron puertos en este cierre.

## Integridad y límites

[Validación local de este cierre](validacion_cierre.md): 40 pruebas, hashes/enlaces y Terraform validado, sin aplicar infraestructura.

Los resultados y fechas no se ajustaron artificialmente: la repetición roja v2 es posterior a la promoción, sobre el vulnerable aislado, para subsanar la captura errónea de exit code del wrapper anterior. [Cronología y discrepancias](../reportes/README.md). Los SHA256 y transformaciones constan en [el manifiesto](../reportes/manifest_evidencias.json).

Las pruebas corresponden al 29-09-2026. No garantizan disponibilidad actual ni ausencia futura de vulnerabilidades. El checkout registra pedidos de prueba/cotización; no cobra tarjetas.
