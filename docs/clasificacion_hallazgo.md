# Clasificación del hallazgo: reenvío de pedido ajeno

## Resultado comprobado localmente

El parche inicial del Marketplace añadió `POST /pedidos/<pedido_id>/reenviar-confirmacion` sin verificar la sesión ni que el pedido perteneciera al solicitante. En el commit `a4af214`, las pruebas `test_other_user_cannot_resend_order` y `test_anonymous_user_cannot_resend_order` obtuvieron `202` donde exigían `404` y `401`. La corrida completa en `reportes/pipeline_bloqueado_local.txt` terminó con código de salida 1 y `DECISIÓN FINAL: BLOQUEADO`. **Esto es evidencia local; falta reproducirla en la EC2 QA.**

## Tipo, impacto y severidad

- Tipo: control de acceso roto a nivel de objeto, [CWE-639](https://cwe.mitre.org/data/definitions/639.html), equivalente al riesgo [OWASP API1:2023 Broken Object Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/).
- Severidad valorada: **media**. Con un identificador de pedido conocido, una persona sin permiso podía activar un nuevo evento de confirmación para una compra ajena y repetir la acción. La respuesta no entregaba el contenido del pedido al atacante; el código BDK aleatorio reduce la facilidad de descubrir pedidos al azar, pero no protege cuando el ID se comparte o filtra.
- Condición de reproducción: crear pedido del usuario A, iniciar sesión como usuario B (o salir de sesión), invocar el endpoint con el código público de A y observar el `202` indebido. La corrección debe devolver `404` a B, `401` al anónimo y **no crear evento**.

No es un falso positivo: el test ejercita la ruta HTTP y comprueba el efecto de notificación. Bandit no señaló esta autorización de negocio; fue la regresión de acceso la que bloqueó el pipeline. Los avisos medios de Bandit se conservan para revisión, pero no se presentan como origen de este hallazgo. La ejecución remediada local pasa la prueba; la verificación QA queda pendiente.
