# Encargo a Kiro: únicamente infraestructura y despliegue AWS

Este documento fija el alcance total. Los prompts de `docs/prompts_kiro_aws_por_fases.md` delimitan qué fase está autorizada en cada mensaje: si recibes la fase 0, detente al entregar el inventario y espera la siguiente fase. La instrucción de avanzar sin «Continue» aplica dentro de una fase, no autoriza saltar sus condiciones de entrada.

Codex se encarga del código, pruebas locales, documentación y plantilla Word. **No programes, no modifiques archivos de la aplicación, tests, pipeline, Markdown ni Word, y no hagas commits ni push.** Ejecuta y documenta solamente las tareas de AWS descritas aquí. Si detectas un error de código, envía salida, SHA y pasos de reproducción; espera a que Codex entregue un nuevo commit antes de redeplegar.

Avanza de una fase a la siguiente sin pedirme que pulse «Continue» por rutina. Pregunta solo si hay una decisión material que no puedes tomar con esta instrucción (cuenta/credenciales incorrectas, presupuesto o riesgo de seguridad, servicio fallido, prueba roja que no bloquea o verde que no permite). Las aprobaciones propias de seguridad de Kiro siguen vigentes: no intentes evitarlas ni conviertas errores repetidos en un ciclo infinito.

Para minimizar aprobaciones repetidas, usa comandos cortos e idénticos cuando repitas una comprobación; no cambies por capricho el orden de argumentos, no encadenes comandos y no inventes variantes de PowerShell. Así el alumno puede confiar una comprobación de solo lectura concreta una sola vez. No solicites confianza global para `aws *`, `docker *` o `*`; pide aprobación para cambios de infraestructura.

## Identidad y límites

- Repositorio de la Final: `https://github.com/oft24/Proyecto-Final-Herramientas-de-tecnolog-as-de-la-informaci-n.git`, rama `main`. Codex comunicará el **SHA final corregido**. No uses un SHA anterior como Producción.
- Cuenta esperada `943135209242`, región `us-west-2`. Comprueba `aws sts get-caller-identity` y las instancias antes de actuar. Si las credenciales AWS Academy expiraron o la cuenta difiere, detente y solicita reconexión; no pidas ni muestres secretos en el chat.
- QA es **la misma EC2 del Avance 2**, ID `i-086d08e1bca370b0f`, nombre `dangoko-avance2-linux`. Identifícala por ID y región, no por IP. Conserva su despliegue anterior en `/opt/dangoko/repo` y su puerto 5000.
- Confirma el bucket privado cifrado `dangoko-avance2-943135209242-us-west-2-mkt` y RDS `dangoko-avance2-rds`. No los recrees, borres ni hagas pruebas destructivas.
- Clona la Final en otra carpeta, por ejemplo `/home/ec2-user/dangoko-final-qa`; usa Compose project `dangoko-final-qa`. Su `.env` privada debe tener permisos `600`, `HOST_BIND=127.0.0.1`, `HOST_PORT=5002`, endpoint privado RDS, bucket S3, `FLASK_SECRET_KEY` aleatoria y `REQUIRE_RDS=true`, `REQUIRE_AWS=true`. Obtén los valores sensibles del entorno autorizado, sin imprimirlos ni copiarlos a Git/SSM stdout. Prefiere el instance profile para S3.
- Si no hay SMTP autorizado/configurado, el reenvío **registra el evento** y responde `delivery=recorded`; eso no demuestra envío de email. Si hay SMTP permitido, configura sus variables privadas y verifica `delivery=email_sent`. No envíes pruebas a terceros reales.
- No abras el puerto QA 5002 al público. Usa `curl http://127.0.0.1:5002` dentro de la EC2 o un túnel seguro. No ejecutes ni expongas la revisión vulnerable de código como servicio.

## Orden obligatorio de trabajo

1. En QA, verifica cuenta, ID de instancia, SSM/SSH, disco, Docker/Compose, RDS y S3. Reporta estado exacto y SHA que se clonó. No reinicies la instancia a ciegas.
2. Clona el repo en la carpeta separada. Para la evidencia **roja**, crea un checkout temporal separado en el commit vulnerable `a4af214`; instala herramientas en un venv privado, ejecuta `python pipeline/run_pipeline.py` y conserva stdout, stderr, exit code y SHA. Debe mostrar la prueba de autorización fallida y `DECISIÓN FINAL: BLOQUEADO`. No levantes contenedores ni abras puertos desde ese checkout. Si la corrida no bloquea, informa la salida y detente.
3. En otro checkout del **SHA final corregido que comunique Codex**, ejecuta el mismo pipeline sin `--demo-red`, conserva stdout, stderr, exit code y SHA. Solo sigue si el exit code es 0 y aparece `DECISIÓN FINAL: PERMITIDO`. No confundas esta corrida QA con el reporte local del repositorio.
4. Despliega **solo el SHA corregido** en QA, Compose project `dangoko-final-qa`, con `HOST_BIND=127.0.0.1` y `HOST_PORT=5002`. Verifica `docker compose ps`, `/salud` 200 con RDS/S3 listos, registro/login, checkout real que genere pedido en RDS y recibo en S3, reenvío del propietario con su `delivery` real, y rechazo de usuario ajeno/anónimo sin un segundo evento. No imprimas passwords, cookies, correos reales ni recibos completos. Mantén el Avance 2 intacto.
5. Tras la corrida verde y la prueba QA, crea **una EC2 nueva** para Producción: nombre `dangoko-final-prod-linux`, misma cuenta y `us-west-2`, recursos compatibles con el presupuesto AWS Academy. Asegura SG restrictivo (RDS 5432 solo desde aplicación, no público), perfil IAM apropiado y volumen suficiente. Reporta ID/AMI/IP asignada; no supongas que la IP anterior de QA es la nueva.
6. Clona y despliega el **mismo SHA corregido** en Producción, con `.env` privada, Compose project `dangoko-final-prod` y sin PostgreSQL local. Verifica `docker compose ps`, `/salud`, registro/login, checkout, objeto S3, fila RDS, reenvío propietario y denegación de usuario ajeno. No copies la `.env` a reportes. Conserva la instancia prendida para las capturas; no detengas ni termines recursos sin permiso del alumno.

## Resultados que debes devolver a Codex

Envía un resumen pegable con cuenta/región verificadas, ID de QA, ID de Producción, SHA exactos, para cada corrida el comando, exit code, control que falló/pasó y decisión final, estado de Compose, códigos HTTP y resultado `delivery`, confirmación de RDS y S3, y rutas de archivos de salida **sanificados**. Conserva los logs completos y proporciona los comandos de solo lectura necesarios para mostrar más tarde: pipeline rojo QA, prueba/hallazgo, identidad EC2 QA, pipeline verde QA, EC2 nueva y app funcional en Producción. **No hagas capturas hasta completar y verificar ambas instancias**. Entonces prueba si tu sesión permite capturar pantallas reales; si puede, guarda PNG auténticos y entrega sus rutas. Si no, indica la limitación y deja los comandos para que el alumno y Codex las tomen. Declara cualquier paso pendiente; nunca inventes un resultado.

En SSM evita `docker compose exec -T` porque anteriormente bloqueó el agente. Usa Session Manager interactivo o comandos cortos con CommandId íntegro. La presentación/video se hará después; no es parte de este encargo.
