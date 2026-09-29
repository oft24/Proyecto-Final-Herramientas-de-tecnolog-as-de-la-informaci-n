# Evidencia de Producción

Estado documentado el 29-09-2026. La captura de la consola identifica una EC2 distinta de QA.

| Campo | Valor observado |
|---|---|
| Región | us-west-2, Oregón |
| QA | i-086d08e1bca370b0f, dangoko-avance2-linux |
| Producción nueva | i-0f3fd952d3b7b73a1, dangoko-final-prod-linux |
| SHA verde QA y desplegado | 80a4a3b408837feb08c4097849db1660b237a6f1 |
| Proyecto Compose | dangoko-final-prod |
| Servicios | api y notifications, appuser, sin PostgreSQL local |
| Acceso usado | Túnel SSM, PC localhost:5003 hacia EC2 puerto 5000 |
| RDS compartida | dangoko-avance2-rds, privada y cifrada |
| S3 compartido | dangoko-avance2-943135209242-us-west-2-mkt, privado, AES256 |

La URL localhost del navegador es el extremo local del túnel; la aplicación corre en EC2. No es el acceso público solicitado para la presentación posterior. Las IP públicas pueden cambiar al reiniciar el laboratorio.

## Pruebas de extremo a extremo

A las 17:15 UTC el registro respondió 201, login y /api/auth/me 200, checkout 200. Pedido BDK-4E6A7D2EDB, usuario 10, total 1120.00, producto 811140, cantidad 1. El recibo S3 devolvió tamaño 385 bytes y AES256.

El reenvío del dueño devolvió 202; usuario ajeno 404; anónimo 401. Los eventos pasaron de 0 a 1 y permanecieron en 1 tras ambos rechazos. En esa corrida delivery=recorded, porque todavía no había SMTP.

- [Log completo](../reportes/aws/pruebas_produccion.txt).
- [Consulta RDS complementaria](../reportes/aws/rds_produccion.txt). La sección vacía del primer log no es la evidencia de persistencia.
- [Nueva EC2](capturas/1_6-07.png), [QA diferenciada](capturas/1_5-06.png), [interfaz real](capturas/1_7-08.png).

## Correo posterior

A las 19:35 UTC se probó el reenvío de BDK-3E199EDDFD con SMTP configurado en Producción: HTTP 202, email_sent y delivered en Resend. [Detalle y límites](correo_confirmacion.md). No se cambió la aplicación para esa configuración.

## Límites y cierre

No se instaló el checkout vulnerable como servicio público. Las pruebas del vulnerable corrieron aisladas en QA. La revisión documental posterior no representa otro SHA desplegado. No publicar .env, tokens ni cookies, y no abrir RDS/S3 al público para la demostración.

La captura del correo recibido puede añadirse al Word. La presentación, acceso público controlado y la decisión de detener recursos al terminar requieren seguimiento del alumno.
