# Prompts para Kiro: AWS de la Entrega Final

Este archivo es para el alumno y Codex. **No envíes todas las fases a la vez.** Copia el prompt de la fase 0, revisa su inventario con Codex y entrega la siguiente fase solo cuando se cumpla la condición de avance. Una pausa entre fases es una decisión técnica; Kiro no debe pedir «Continue» para cada comando rutinario. **Primero completa el trabajo y conserva logs verificables; el alumno hará las capturas desde Linux al final.** Codex dará los comandos exactos a partir de las rutas e IDs reales que reporte Kiro.

La rúbrica exige: pipeline rojo y hallazgo en la **EC2 QA del Avance 2**, commit de remediación, pipeline verde en esa misma QA, una **EC2 de Producción nueva** y la aplicación corregida funcionando en ella. Las capturas y resultados deben ser reales. Bandit, pip-audit y CycloneDX complementan la prueba de autorización: el hallazgo de negocio lo detectan las pruebas de acceso, no Bandit.

## Mapa conocido, sujeto a verificación por Kiro

| Uso | Identidad esperada | Regla |
| --- | --- | --- |
| Cuenta y región | `943135209242`, `us-west-2` | Si difieren, detenerse. |
| QA heredada | `dangoko-avance2-linux`, `i-086d08e1bca370b0f` | No sustituir por otra EC2 ni desmontar el Avance 2. La IP puede haber cambiado. |
| Aplicación anterior | `/opt/dangoko/repo`, puerto 5000 | No alterar ni usar como checkout vulnerable. |
| Bucket compartido | `dangoko-avance2-943135209242-us-west-2-mkt` | Confirmar privado, cifrado y permisos del perfil; no recrear ni vaciar. |
| RDS compartido | `dangoko-avance2-rds`, base `dangoko` | Confirmar PostgreSQL, cifrado y no público; no recrear ni borrar datos. |
| QA Final | `/home/ec2-user/dangoko-final-qa`, Compose `dangoko-final-qa`, `127.0.0.1:5002` | Checkout separado; nunca exponer el parche vulnerable como servicio. |
| Producción Final | **EC2 nueva** `dangoko-final-prod-linux`, Compose `dangoko-final-prod` | Crear solo tras QA verde; registrar su ID real. No reutilizar la IP/ID de QA. |
| Repositorio | `https://github.com/oft24/Proyecto-Final-Herramientas-de-tecnolog-as-de-la-informaci-n.git`, `main` | Confirmar `git rev-parse HEAD` y comunicar el SHA; Codex aprobará el SHA exacto para QA verde y Producción. |
| Parche vulnerable histórico | `a4af214` | Solo checkout temporal para pipeline rojo; no desplegarlo. |
| Remediación identificable | `56b06f5` | Capturar diff o historial antes/después. |

Se reutilizan bucket y RDS si las verificaciones confirman que siguen siendo los correctos; **no se inventa infraestructura adicional**. QA y Producción usarán datos de prueba distinguibles en los recursos compartidos. La presentación/video se hará después: no terminar Producción antes de obtener todas las capturas y grabaciones. Vigilar costos y pedir al alumno que decida cuándo detenerla o terminarla.

## Fase 0 — Inventario, solo lectura

Enviar a Kiro:

> Eres responsable únicamente de infraestructura, despliegue y verificaciones AWS de Dangoko Entrega Final. Codex se encarga del código, pipeline, documentos, Git y Word. Lee `docs/encargo_kiro_aws.md` del repositorio `https://github.com/oft24/Proyecto-Final-Herramientas-de-tecnolog-as-de-la-informaci-n.git`, rama `main`; informa el SHA observado para que Codex lo confirme. **En esta fase no cambies ningún recurso ni archivo** y no ejecutes todavía pipeline ni despliegue.
>
> Haz inventario read-only de la cuenta `943135209242` y `us-west-2`: confirma `sts get-caller-identity`; la EC2 QA `i-086d08e1bca370b0f` (nombre, estado, IP actual, tipo, AMI, AZ, subnet, VPC, SG, perfil IAM, disco y acceso SSM); y en la propia QA confirma ubicación de `/opt/dangoko/repo`, Docker/Compose, puerto 5000, servicios actuales y espacio libre sin imprimir `.env` ni secretos. Identifica si hay recursos **ya existentes de la Entrega Final** para no duplicarlos.
>
> Verifica el bucket `dangoko-avance2-943135209242-us-west-2-mkt`: región, bloqueo público, cifrado, política/permisos de la instancia y uso por la app (solo metadatos; no copies recibos). Verifica RDS `dangoko-avance2-rds`: estado, motor, endpoint privado, `PubliclyAccessible=false`, `StorageEncrypted=true`, VPC/subnets/SG y conectividad prevista desde QA. Confirma cómo podrá llegar una EC2 nueva a RDS y S3 con mínimo privilegio. Si la región, cuenta, IDs, rutas o recursos reales no coinciden, **detente y dime los valores reales; no adivines ni crees reemplazos**.
>
> Devuelve una tabla `recurso | valor esperado | valor observado | estado | evidencia/comando` y otra con `riesgo/bloqueo | consecuencia | decisión necesaria`. Propón AMI, tipo, subnet, SG y perfil para una EC2 nueva llamada `dangoko-final-prod-linux` con recursos compatibles con AWS Academy; distingue lo verificado de lo propuesto y di si el saldo/cuota es visible o no. No muestres credenciales, contraseñas, variables privadas, cookies ni datos de clientes. **Termina esta fase con el inventario; no avances a QA hasta que Codex lo revise.**

Condición para fase 1: cuenta/región/QA/S3/RDS coinciden o Codex corrige el mapa con datos observados; sin bloqueos de acceso o presupuesto no resueltos.

## Fase 1 — Parche en QA y pipeline rojo

Enviar a Kiro solo después de revisar fase 0:

> Trabaja **únicamente** en la EC2 QA verificada `i-086d08e1bca370b0f`. No toques `/opt/dangoko/repo`, sus contenedores ni el puerto 5000. Clona el repositorio Final en `/home/ec2-user/dangoko-final-qa` (o informa la ruta real si la cuenta Linux difiere). Verifica remoto y SHA. Crea un checkout temporal aislado del commit vulnerable `a4af214` y prepara las dependencias del pipeline en un entorno virtual privado; no programes ni alteres tests, umbrales o reportes para fabricar un rojo. No ejecutes el checkout vulnerable como servicio ni abras puertos.
>
> En ese checkout, ejecuta el pipeline completo `python pipeline/run_pipeline.py`. Conserva **comando, SHA completo, fecha UTC, stdout, stderr y exit code** en archivos de evidencia fuera del checkout o en una ruta informada. El rojo correcto debe mostrar las pruebas de autorización del reenvío para usuario ajeno y anónimo (`202` observado contra `404`/`401` esperados), seguida de `DECISIÓN FINAL: BLOQUEADO`, con exit code distinto de cero. Conserva las rutas y comandos de lectura para tomar más tarde las capturas **1.1 pipeline bloqueando**, **1.2 hallazgo exacto** y **1.5 identidad de QA**; no hagas screenshots ahora. Bandit no tiene que reportar este hallazgo: si el bloqueo se debe solo a falta de herramientas, red, credenciales o un error ajeno, informa la causa y detente; no lo declares evidencia válida.
>
> Devuélveme `ID QA | ruta checkout | SHA | comando | exit code | pruebas fallidas | decisión final | rutas de logs | estado intacto del Avance 2`. No hagas commits ni push. No pases a la fase verde hasta que Codex confirme que el rojo es válido.

Condición para fase 2: falla de autorización auténtica reproducida en QA y bloqueo completo conservado; Avance 2 intacto.

## Fase 2 — Pipeline verde y funcionalidad corregida en QA

Enviar a Kiro solo después de revisar el rojo:

> Usa la misma EC2 QA. Antes de ejecutar, confirma con Codex el **SHA corregido completo** que se promoverá; fíjalo y no sigas `main` a ciegas. En un checkout separado del vulnerable, instala dependencias y ejecuta el mismo pipeline completo sin `--demo-red`. Conserva comando, SHA, fecha UTC, stdout, stderr y exit code. Exige exit 0 y `DECISIÓN FINAL: PERMITIDO`; incluye resultados de pruebas, Bandit, pip-audit y SBOM CycloneDX. Si falla por una nueva vulnerabilidad o servicio externo, devuelve el reporte; no cambies código, dependencias ni controles para forzar verde. Conserva la salida y comando de lectura para la captura posterior **1.4 pipeline permitiendo** y la referencia al diff/commit `56b06f5` para **1.3 remediación**; no hagas screenshots ahora.
>
> Solo tras el verde, despliega **ese mismo SHA** en la carpeta QA separada, Compose project `dangoko-final-qa`, `HOST_BIND=127.0.0.1`, `HOST_PORT=5002`, dos servicios propios `api` y `notifications`, sin PostgreSQL local. Crea `.env` privada con permisos 600, RDS y bucket verificados, `REQUIRE_RDS=true`, `REQUIRE_AWS=true`, secreto Flask aleatorio y perfil de instancia para AWS cuando sea posible. No imprimas `.env` ni uses secretos en logs o Git. Verifica `docker compose ps`, `/salud` HTTP 200 con RDS/S3 listos, registro/login de usuarios de prueba, checkout que crea fila en RDS y objeto `orders/` en S3, reenvío del propietario y rechazo `404` de usuario ajeno y `401` anónimo sin generar un segundo evento. Distingue `delivery=recorded` de `delivery=email_sent`; sin SMTP autorizado, no afirmes envío de correo. Usa identidades/datos de prueba nuevos; no borres datos existentes. Mantén intactos Avance 2 y puerto 5000.
>
> Devuélveme `SHA rojo | SHA verde | exit code | decisión | ID QA | servicios | /salud | registro/login | pedido RDS | recibo S3 | reenvío propietario | rechazo ajeno/anónimo | delivery | rutas de evidencia`. Sanitiza respuestas: no contraseñas, cookies, direcciones personales ni recibos completos. Si cualquier prueba falla, detente antes de Producción y manda la reproducción para que Codex arregle el código.

Condición para fase 3: pipeline verde real y pruebas funcionales QA completas sobre el SHA que se promoverá.

## Fase 3 — EC2 nueva y promoción a Producción

Enviar a Kiro solo después de revisar el verde y la prueba QA:

> Ahora crea **una EC2 nueva** en la cuenta `943135209242`, región `us-west-2`, nombre `dangoko-final-prod-linux`. Antes de crearla, verifica otra vez presupuesto/cuota y que no exista ya una EC2 Final de Producción; usa una AMI/tipo/subnet/volumen compatibles con Docker y el laboratorio, y reporta tu elección real. No sustituyas ni reutilices QA `i-086d08e1bca370b0f`. Aplica SG restrictivo, perfil IAM apropiado para SSM/S3 y acceso RDS 5432 **solo desde el SG de esta aplicación**. No hagas RDS o S3 públicos, no recrees ni borres el bucket/RDS compartidos y no abras SSH/5000 a `0.0.0.0/0`. Si para la captura se necesita acceso web, propone un túnel SSM o una regla temporal limitada a la IP del alumno; pide decisión antes de abrir exposición adicional.
>
> Clona el repositorio Final en una ruta propia de esa instancia y despliega **el SHA completo idéntico al de la corrida verde QA**, Compose `dangoko-final-prod`, `.env` privada 600, solo `api` y `notifications`, sin PostgreSQL local. Comprueba `docker compose ps`, `/salud`, registro/login, checkout, pedido RDS, recibo S3, reenvío autorizado, rechazo de ajeno/anónimo y estado `delivery` real. No mezcles los pedidos de prueba QA y Producción; utiliza usuarios identificables como prueba y no borres registros. Confirma que no se promovió `a4af214`.
>
> Devuélveme `cuenta | región | ID e IP real de nueva EC2 | AMI/tipo/AZ/subnet/SG/IAM | SHA QA verde | SHA Producción | servicios | códigos HTTP | S3/RDS | delivery | ruta/método de acceso posterior`. Prepara, pero **no tomes aún**, las capturas **1.6 EC2 nueva** y **1.7 aplicación corregida funcionando en esa EC2**: devuelve el método exacto para abrir la página real y mostrar identidad de Producción sin secretos. Si el estado es parcial, dilo; no afirmes éxito por un `/salud` aislado. No detengas ni termines Producción antes de tomar capturas y grabar el video pendiente.

Condición para fase 4: mismo SHA en verde QA y en Producción, pruebas funcionales completas y logs conservados; las capturas quedan pendientes.

## Fase 4 — Cierre de evidencia y costos

Enviar a Kiro cuando las fases anteriores estén verificadas:

> Entrega un informe final **sin inventar evidencia**. Para cada captura futura 1.1–1.7 indica instancia, ruta de log o pantalla exacta, **comando corto de solo lectura para reproducirla**, fecha UTC, ID y SHA cuando corresponda. Incluye rutas de stdout/stderr de pipeline rojo y verde, exit codes, controles que bloquearon/pasaron, prueba de `orders/` en S3 y fila en RDS (solo metadatos), y resultado real de notificación. Marca cada paso de la rúbrica como comprobado o pendiente con motivo. **No tomes screenshots ni fabriques imágenes**: el alumno hará todas las capturas al final desde la consola Linux y AWS; Codex preparará los comandos exactos y las integrará en el Word. Reporta estado y costo/saldo visible de ambas EC2; si el video aún no se grabó, avisa que Producción debe permanecer accesible o detenerse de forma recuperable según decisión del alumno. **No termines recursos ni borres evidencia sin autorización explícita.**

## Regla de coordinación

Kiro no decide correcciones de código ni redacta la autoevaluación. Si pide un dato que puede descubrir con consultas de solo lectura (IP, ruta, SG, endpoint, AMI, estado), que lo descubra y lo reporte. Si encuentra una diferencia material frente al mapa (otra cuenta, otra QA, bucket/RDS ausentes, permisos insuficientes, costo no aceptable o una prueba falsa), **se detiene y devuelve la observación exacta**, sin improvisar recursos ni pedir al alumno clics de «Continue» para preguntas rutinarias. Codex decide si se actualiza el código, se ajusta la fase o se solicita una elección al alumno.
