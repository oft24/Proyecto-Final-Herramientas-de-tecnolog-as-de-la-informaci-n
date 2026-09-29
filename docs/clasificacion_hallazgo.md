# Clasificación del hallazgo de autorización

## Reproducción confirmada

El parche inicial añadió POST /pedidos/<pedido_id>/reenviar-confirmacion sin exigir sesión ni verificar pertenencia. En el checkout a4af214, test_anonymous_user_cannot_resend_order recibió 202 en vez de 401 y test_other_user_cannot_resend_order recibió 202 en vez de 404.

[Rojo QA completo](../reportes/pipeline_bloqueado.txt) y [metadata](../reportes/pipeline_bloqueado_metadata.txt): Python 3.12.14, 31 pruebas, dos fallas, BLOQUEADO, pipeline_rc=1. Son pruebas con Flask test client y dependencias aisladas, no un ataque a datos de clientes.

## Tipo e impacto

Control de acceso roto a nivel de objeto, [CWE-639](https://cwe.mitre.org/data/definitions/639.html). Con un código conocido, un usuario no autorizado podía activar la confirmación de una compra ajena. Esto permite abuso del flujo y mensajes no solicitados.

**Severidad: media**, valoración contextual del proyecto, no puntuación CVSS calculada. La respuesta no entregaba el contenido del pedido al atacante. La aleatoriedad del código BDK reduce descubrimiento al azar, pero no autoriza el acceso cuando se conoce o comparte el ID.

## Falso positivo y controles

No es falso positivo: la prueba ejercita la ruta y obtiene aceptación indebida. Lo detectaron las pruebas de autorización, no Bandit. El análisis estático no demuestra la relación de negocio usuario-pedido. Se conservaron tres avisos de Bandit bajo el umbral HIGH; no se ocultaron para obtener verde.

La corrección exige sesión y pertenencia antes de notificar. Los resultados reales en [QA](../reportes/aws/pruebas_qa.txt) y [Producción](../reportes/aws/pruebas_produccion.txt) confirman dueño 202, ajeno 404 y anónimo 401, sin nuevos eventos por los rechazos.

[Commit de remediación](https://github.com/oft24/Proyecto-Final-Herramientas-de-tecnolog-as-de-la-informaci-n/commit/56b06f53487f5112d3d996162af672efc7e5d72e). El verde QA y la promoción corresponden al SHA posterior 80a4a3b, que también arregló la escritura del volumen de notificaciones.
