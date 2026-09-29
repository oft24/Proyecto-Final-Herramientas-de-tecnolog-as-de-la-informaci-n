# Respuesta al hallazgo de reenvío

## Contención inmediata

El estado vulnerable se dejó únicamente como commit de prueba local `a4af214`; **no se desplegó como servicio público**. La corrida roja local se hizo con pruebas y sin levantar ese checkout. La instrucción de QA es ejecutar esa versión solo como pipeline en un checkout aislado, sin contenedor ni puerto abierto. Todavía falta confirmar en AWS que esa contención se respetó. No se rotaron credenciales ni se modificaron datos de clientes porque la prueba local utilizó dobles de base de datos y notificación.

## Prevención y corrección

La ruta corregida exige sesión, obtiene el pedido por código persistido en RDS, compara `orders.user_id` con el usuario autenticado **antes** de solicitar la notificación y responde `404` al pedido ajeno para no revelar su existencia. El destino del reenvío se toma del correo de la cuenta autenticada, no de un valor enviado por el cliente ni de un correo antiguo del pedido. Las pruebas abarcan propietario, usuario ajeno, anónimo, pedido de invitado, ID inexistente, origen cruzado y falla del servicio de notificaciones.

El servicio de notificaciones informa `delivery=recorded` si solo registró el evento y `delivery=email_sent` únicamente si se configuró SMTP y `send_message` terminó sin error. Sin SMTP no se debe afirmar que salió un email real. La corrida verde local está en `reportes/pipeline_verde_local.txt`; la corrida verde en QA, el despliegue y la prueba de extremo a extremo siguen pendientes.
