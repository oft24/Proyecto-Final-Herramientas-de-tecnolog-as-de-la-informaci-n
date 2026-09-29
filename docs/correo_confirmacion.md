# Reenvío real de confirmación

La función nueva es POST /pedidos/<codigo-BDK>/reenviar-confirmacion. Exige sesión y pertenencia del pedido. Obtiene el destinatario de la cuenta autenticada.

El 29-09-2026 se configuró SMTP en Producción i-0f3fd952d3b7b73a1, sin cambiar el código 80a4a3b. Se recreó únicamente notifications para cargar la configuración privada.

| Comprobación | Resultado |
|---|---|
| Login | HTTP 200 |
| Checkout | HTTP 200, BDK-3E199EDDFD |
| Recibo | orders/cc829a69-e002-48f9-ae0f-12304f257459-37bc03f3.json |
| Reenvío propietario | HTTP 202, email_sent |
| Proveedor | Resend, last_event=delivered |
| ID proveedor | 01a0eeaa-6265-77ee-b3a2-f423ce8b4cc0 |
| Fecha UTC | 2026-09-29 19:35:39 |

[Respuesta de la aplicación](../reportes/aws/compra_correo.json) y [respuesta del proveedor](../reportes/aws/resend_entrega.json), con destinatario personal redactado.

## Configuración sin secretos

Host smtp.resend.com, puerto 587, STARTTLS, usuario resend. La clave se configura solo en .env privada con permisos 600, nunca en Git, reportes ni capturas. [Documentación SMTP](https://resend.com/docs/send-with-smtp).

Remitente de pruebas onboarding@resend.dev, limitado por Resend a la cuenta del proveedor. Un servicio para destinatarios arbitrarios necesita dominio verificado y remitente autorizado.

recorded significa registro; email_sent, aceptación SMTP; delivered, entrega reportada por el proveedor al servidor destinatario. Ninguno acredita lectura humana. El checkout registra el evento inicial; el reenvío explícito envía el correo.
