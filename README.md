# Dangoko Marketplace — Entrega Final

Aplicación de marketplace para productos asiáticos. El proyecto usa Flask, PostgreSQL, S3, Docker Compose y un servicio independiente de notificaciones. El flujo principal es: catálogo → carrito → pedido persistido en RDS → recibo privado en S3 → notificación.

La documentación académica está en [docs/README.md](docs/README.md). La aplicación vive en `app/`, la infraestructura como código en `infra/` y los controles del pipeline en `pipeline/`.

## Clonar el proyecto

```bash
git clone https://github.com/oft24/Proyecto-Final-Herramientas-de-tecnolog-as-de-la-informaci-n.git
cd Proyecto-Final-Herramientas-de-tecnolog-as-de-la-informaci-n
```

## Ejecutar con Docker y RDS

Nunca copies credenciales reales al repositorio. Crea el archivo local desde la plantilla y completa sus valores únicamente en tu máquina o en la EC2. `DB_HOST` debe ser el endpoint privado de RDS; Compose ya no arranca PostgreSQL local:

```bash
cp .env.example .env
chmod 600 .env
docker compose up --build -d --remove-orphans
curl http://127.0.0.1:5000/salud
docker compose ps
```

En PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up --build -d --remove-orphans
Invoke-WebRequest http://127.0.0.1:5000/salud
docker compose ps
```

## Variables mínimas para AWS

Configura `.env` en la EC2 con el endpoint de RDS, la base `dangoko`, el bucket privado y la región `us-west-2`. Para la exposición directa de AWS Academy por HTTP usa:

```dotenv
PREFERRED_URL_SCHEME=http
REQUIRE_AWS=true
REQUIRE_RDS=true
REQUIRE_NOTIFICATIONS=true
```

No subas `.env`, `terraform.tfvars`, tokens ni contraseñas. Usa `.env.example` como referencia.

## Preparar una EC2 para esta entrega

Esta es una copia con historial Git independiente. No cambies el remoto ni mezcles la carpeta del Avance 2. En una EC2 destinada a QA o Producción, clona este repositorio en una carpeta nueva y crea allí su propio `.env` privado. En QA usa `HOST_BIND=127.0.0.1` y `HOST_PORT=5002` para no ocupar el puerto 5000 del Avance 2 ni exponer QA públicamente; en Producción usa el enlace y puerto permitidos por su grupo de seguridad:

```bash
git clone https://github.com/oft24/Proyecto-Final-Herramientas-de-tecnolog-as-de-la-informaci-n.git
cd Proyecto-Final-Herramientas-de-tecnolog-as-de-la-informaci-n
cp .env.example .env
# Completa DB_HOST, DB_PASSWORD, S3_BUCKET y FLASK_SECRET_KEY sin mostrarlos en logs.
# Para QA, fija HOST_BIND=127.0.0.1 y HOST_PORT=5002 en .env.
chmod 600 .env
docker compose build --no-cache api
docker compose up -d --force-recreate --remove-orphans api notifications
sleep 15
curl -i http://127.0.0.1:5000/salud
docker compose ps
```

Antes de usar una instancia que ya tenga otro despliegue, comprueba puertos y volúmenes para no interrumpir el Avance 2. No hagas el despliegue de la Entrega Final hasta completar las pruebas de QA.

## Cuenta y pedidos

La interfaz incluye registro e inicio de sesión visuales. Sus endpoints son:

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

El checkout crea el pedido en RDS antes de notificar. Si falla la creación en RDS, responde `503` y no se envía ninguna notificación ni se presenta una confirmación exitosa. WhatsApp no se abre automáticamente. Un usuario autenticado puede solicitar el reenvío **solo de un pedido propio** mediante `POST /pedidos/<codigo-BDK>/reenviar-confirmacion`; un usuario ajeno recibe `404` y uno anónimo `401`. Los pedidos antiguos sin código público persistido y los pedidos de invitado no pueden reenviarse desde esta ruta.

El servicio de notificaciones registra un evento en todos los casos aceptados. Sin `SMTP_HOST` responde `delivery=recorded`, que **no significa correo entregado**. Con SMTP autorizado y configurado envía un correo de texto y responde `delivery=email_sent` cuando la biblioteca de correo confirma el envío al servidor SMTP. Esto tampoco certifica la entrega final al buzón.

## Estado de la Entrega Final

Esta copia incluye la base del Avance 2 y la mejora del pipeline solicitada en la retroalimentación: Bandit, pip-audit, CycloneDX y Compose conectado a RDS. El parche se probó localmente en estado vulnerable (commit `a4af214`, pipeline bloqueado) y después se corrigió la autorización (pipeline local permitido). **Faltan las corridas equivalentes en QA, el despliegue del código corregido y la nueva EC2 de Producción.** Los reportes locales no sustituyen las capturas AWS de la rúbrica. El encargo de infraestructura, sin programación de la aplicación, está en [docs/encargo_kiro_aws.md](docs/encargo_kiro_aws.md).

## Validación de entrega

Instala las herramientas del pipeline en un entorno aislado y las dependencias de la aplicación:

```bash
python -m venv .venv
# Activa .venv según tu sistema antes de continuar.
python -m pip install -r app/requirements.txt -r pipeline/requirements-tools.txt
```

El pipeline ejecuta las pruebas, Bandit, pip-audit y CycloneDX. Se bloquea si una herramienta falla, hay un hallazgo HIGH de Bandit o alguna dependencia tiene una vulnerabilidad conocida. La corrida roja de la Entrega Final debe corresponder al parche real y su prueba de autorización, no al modo de demostración del Avance 2.

```bash
PYTHONPATH=app python -m pytest -q
python pipeline/run_pipeline.py
```

En PowerShell, establece `PYTHONPATH` con `$env:PYTHONPATH='app'` antes de llamar a `python -m pytest -q`.
