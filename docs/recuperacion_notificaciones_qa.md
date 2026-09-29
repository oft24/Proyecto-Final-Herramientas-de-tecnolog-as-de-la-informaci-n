# Recuperación de notificaciones en QA

El 29-09-2026 Kiro reportó registro/login correctos y checkout 503 por notificaciones en el SHA `fd03e547e0d899593963f1823c9341e1822f98a1`. La salida local del run confirma que luego se probó el reenvío con `order_id` vacío. Esos 405 no son una prueba válida de autorización ni justifican cambiar el endpoint, que sigue siendo `POST /pedidos/<order_id>/reenviar-confirmacion`.

## Diagnóstico y corrección de código

Compose monta un volumen en `/var/lib/dangoko`, pero la imagen anterior no creaba ese directorio con propietario `appuser`. El servicio no root podía estar vivo y responder salud aunque no pudiera escribir el JSONL. Este defecto de configuración está confirmado en código; **falta el traceback remoto para atribuirle con certeza el 503 observado**. Comprobar `PermissionError`, UID/GID y permisos del directorio/archivo; si la causa real es otra, reportarla.

La corrección crea el directorio con dueño appuser en la imagen, comprueba escritura del archivo en `/salud` sin añadir eventos y devuelve 503 si el almacenamiento no está disponible. También añade `restart: unless-stopped` a ambos servicios para recuperar el despliegue con Docker. Comprobar que el servicio Docker está habilitado al arranque. Un contenedor detenido manualmente puede requerir `compose up` nuevamente.

Los volúmenes existentes conservan sus permisos: reconstruir la imagen no los corrige. No borrar el volumen ni sus eventos para resolverlo. No usar `chmod 777` ni dejar la aplicación ejecutándose como root.

## Encargo operativo de Kiro

1. En QA `i-086d08e1bca370b0f`, conservar el error remoto y permisos sin secretos. Mantener Avance 2 en `/opt/dangoko/repo`, puerto 5000.
2. Consultar RDS para los usuarios de prueba 6/7 y el intervalo del run, recuperando solo ID público, propietario, clave S3 y cantidades. El checkout escribe en S3 y RDS antes de notificar: **un 503 de notificaciones puede haber dejado ambos registros**. Verificar las claves exactas en S3; no concluir que faltan porque el HTTP no las devolvió. No borrar ni reintentar a ciegas.
3. Recibir el nuevo SHA completo de Codex. Hacer fetch y checkout de ese SHA en QA, después de comprobar que no hay cambios versionados locales que se perderían. Ejecutar pipeline completo con Python 3.12 y conservar nuevos logs, sin sobrescribir la corrida verde anterior. Exigir exit 0 y PERMITIDO. Esta nueva versión necesita su propia evidencia verde QA antes de promoverse.
4. Construir los dos servicios y corregir únicamente el dueño del directorio/log en el volumen de **este proyecto**. Los comandos siguientes se ejecutan dentro de `/home/ec2-user/dangoko-final-qa`; usar sudo si la `.env` privada lo requiere:

```bash
sudo docker compose -p dangoko-final-qa build api notifications
sudo docker compose -p dangoko-final-qa run --rm --no-deps --user root --entrypoint sh notifications -c 'chown appuser:appuser /var/lib/dangoko && if [ -f /var/lib/dangoko/notifications.jsonl ]; then chown appuser:appuser /var/lib/dangoko/notifications.jsonl; fi'
sudo docker compose -p dangoko-final-qa up -d api notifications
sudo docker compose -p dangoko-final-qa ps
```

El contenedor temporal solo ajusta dueño del volumen; los servicios normales mantienen `USER appuser`. No usar `down -v` ni eliminar volúmenes. Mantener HOST_BIND=127.0.0.1 y HOST_PORT=5002. Verificar salud de notifications con `log_ready=true`, configuración de reinicio y usuario real de ambos contenedores. Esperar salud con timeout, no asumirla por `up -d`.

5. Repetir pruebas del encargo de operación con usuarios nuevos y sesiones separadas. El checkout debe devolver 200 con ID `BDK-` válido y clave de recibo. Si falla, detener la secuencia y diagnosticar registros parciales. **No ejecutar reenvíos con ID vacío, marcador literal o extraído de una respuesta de error**.
6. Probar dueño 202, ajeno 404 y anónimo 401 sobre ese mismo pedido; confirmar en el JSONL incremento de uno para dueño y cero para cada rechazo. Sin SMTP declarar `delivery=recorded`, no correo enviado. Verificar RDS y S3 para ese pedido.
7. Devolver SHA nuevo, pipeline QA, diagnósticos, HTTP, persistencia, conteos de eventos y estado de Avance 2. Detenerse antes de Producción para validación de Codex.

## Evidencias y límites

Validación local del 29-09-2026 con Python 3.13.3: `python -m unittest discover -s app/tests -p 'test_*.py'` terminó con exit 0 y 40 pruebas OK. El pipeline completo terminó con exit 0 y PERMITIDO: Bandit 3 avisos por debajo del umbral HIGH, pip-audit 0 avisos y CycloneDX 10 componentes. Las tres pruebas nuevas comprueban salud sin añadir eventos, rechazo de almacenamiento no escribible y ausencia de aceptación cuando falla escribir la notificación. El motor Docker local no estaba disponible y el contexto AWS de Codex seguía denegado por `voc-cancel-cred`; build y ejecución real deben verificarse en QA con Python 3.12 antes de promover.

Conservar el rojo histórico `a4af214`, el commit de autorización `56b06f5` y el nuevo verde QA que incluya esta corrección. El commit de autorización sigue siendo el principal para la captura 1.3; la captura 1.4 debe corresponder al SHA que finalmente vaya a Producción. Las pruebas locales no sustituyen build y ejecución Docker en QA.
