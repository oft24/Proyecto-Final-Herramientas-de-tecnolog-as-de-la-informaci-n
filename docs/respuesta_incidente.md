# Respuesta al hallazgo

## Contención inmediata

El checkout vulnerable a4af214 se mantuvo aislado para las pruebas del pipeline, sin levantarlo como servicio ni abrir un puerto. En QA se conservó el Avance 2 en su puerto 5000. El checkout de la Final usó otra carpeta y proyecto Compose; Producción recibió únicamente el código corregido.

Esta medida reduce exposición mientras se corrige, pero no arregla la causa. Ante un incidente real ya expuesto se deshabilitaría temporalmente el endpoint y se revisarían los eventos, sin confundir esa acción con la solución permanente.

## Prevención implementada

El endpoint exige sesión, consulta el pedido en RDS y compara orders.user_id con el usuario autenticado antes de notificar. Un pedido ajeno devuelve 404 para no revelar existencia; un anónimo recibe 401. El correo sale de la cuenta autenticada, no de parámetros del solicitante.

Las pruebas preservan propietario, usuario ajeno, anónimo, pedido de invitado, ID inexistente, origen cruzado y fallo de notificaciones. No se eliminó la función ni se bajaron los umbrales.

## Validación y promoción

[Rojo QA](../reportes/pipeline_bloqueado.txt): dos rechazos faltantes, exit 1. [Verde QA](../reportes/pipeline_verde.txt) y [cierre](../reportes/aws/cierre_qa.txt): SHA 80a4a3b antes/después, exit 0. [Producción](evidencia_produccion.md): mismo SHA y pruebas reales con conteo de eventos invariable tras rechazos.

SMTP se configuró después, sin modificación de código. [Correo real](correo_confirmacion.md): aceptación de la aplicación y entrega reportada por el proveedor. Las pruebas previas recorded siguen identificadas como registro, no como envío.

## Riesgos residuales

No hay limitación de frecuencia específica del reenvío, pruebas DAST completas ni escáner de imagen. S3/RDS no forman una transacción distribuida; puede quedar un recibo sin pedido si RDS falla. QA y Producción comparten RDS y bucket del laboratorio, aunque separan usuarios de prueba, contenedores y EC2. El SMTP de pruebas no permite enviar a cualquier cliente sin verificar dominio.
