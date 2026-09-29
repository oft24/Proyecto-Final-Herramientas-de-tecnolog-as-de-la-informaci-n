# Dangoko Marketplace Entrega Final

Esta aplicación parte del catálogo mayorista de Bbldak y lo adapta a un marketplace pequeño para dangokobox.com. Un visitante puede consultar el catálogo, crear una cuenta, iniciar sesión y generar un pedido de cotización. El pedido se guarda en RDS, su recibo JSON se almacena en un bucket privado de S3 y un servicio independiente registra la notificación de confirmación.

Alumno: Luis Antonio Hernández Vázquez. Matrícula: 3101149. Tema elegido: 3, Marketplace. Repositorio de la Entrega Final: `https://github.com/oft24/Proyecto-Final-Herramientas-de-tecnolog-as-de-la-informaci-n.git`.

## Cómo se levanta en desarrollo

```powershell
Copy-Item .env.example .env
# Configura el endpoint de RDS y las demás variables privadas en .env.
docker compose up --build
```

La aplicación queda en `http://localhost:5000`. El endpoint de salud es `GET /salud`. El servicio de notificaciones vive en `http://notifications:5001` dentro de Compose. Tanto en QA como en Producción se usa RDS; para ejecutar el checkout desde una máquina local se requiere conectividad privada a esa base.

## Flujo principal

1. El frontend muestra el catálogo heredado de Bbldak.
2. `POST /api/auth/register` y `POST /api/auth/login` identifican al usuario mediante una sesión Flask.
3. `POST /api/checkout` valida productos, cantidades y consentimiento.
4. El API guarda el pedido y sus partidas en RDS PostgreSQL.
5. El API escribe un recibo privado en S3 con cifrado AES256.
6. El API llama a `notifications` por HTTP. Ese contenedor registra la confirmación en un archivo de eventos.

## Servicios de AWS

| Servicio | Uso | Controles definidos |
|---|---|---|
| S3 | Recibos JSON de los pedidos | Bloqueo total de acceso público, cifrado AES256 y versionado |
| RDS PostgreSQL | Usuarios, pedidos y partidas | Cifrado de almacenamiento, `publicly_accessible = false`, subredes privadas y grupo de seguridad que solo permite tráfico desde la aplicación |

Terraform deja la configuración en `infra/`. Los valores sensibles se proporcionan por variables o por el entorno de AWS Academy; no se guardan en Git.

## Variables importantes

En el despliegue real se deben establecer `DB_HOST` con el endpoint de RDS, `DB_SSLMODE=require`, `S3_BUCKET`, `AWS_REGION`, `FLASK_SECRET_KEY`, las credenciales de AWS mediante el mecanismo seguro disponible y `REQUIRE_RDS=true`, `REQUIRE_AWS=true`. El Compose principal usa RDS y ya no contiene PostgreSQL local.

## Pipeline

```powershell
python pipeline/run_pipeline.py
```

El pipeline ejecuta pruebas de sintaxis y regresión, Bandit, pip-audit, higiene de secretos, controles de IaC, endurecimiento del Dockerfile y generación de SBOM con CycloneDX Python. Todas las etapas alimentan un único veredicto. Para la Entrega Final, la corrida roja debe surgir de la falla real en el parche y la verde del código remediado:

```powershell
python -m pip install -r app/requirements.txt -r pipeline/requirements-tools.txt
python pipeline/run_pipeline.py
```

## Estado de entrega

Esta es la base para la Entrega Final, derivada del Avance 2 y con el pipeline mejorado. Los recursos y resultados del Avance 2 son antecedentes, no evidencias de QA ni Producción para esta entrega. Aún faltan integrar el parche funcional, demostrar una corrida roja real y su remediación verde, desplegar y probar los ambientes requeridos, y reunir las capturas y el video finales.
