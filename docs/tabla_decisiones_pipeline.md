# Tabla de decisiones de mi pipeline

Este pipeline termina en un solo veredicto. Una etapa fallida hace que la decisión sea `BLOQUEADO`, aunque las demás etapas pasen.

## Riesgos que introduce mi aplicación

| # | Riesgo concreto | Control | Por qué ese control |
|---|---|---|---|
| 1 | El catálogo recibe credenciales de AWS, RDS o Flask dentro del repositorio | Higiene de secretos | El API necesita acceso a S3 y RDS, por lo que una filtración permitiría leer recibos o modificar datos. |
| 2 | El bucket de recibos queda público o los pedidos de RDS quedan expuestos a Internet | Escaneo de IaC | El almacenamiento contiene datos de clientes y pedidos. El bloqueo público de S3 y `publicly_accessible = false` son propiedades verificables del código. |
| 3 | Una imagen Docker ejecuta la aplicación como root o sin comprobación de vida | Escaneo del Dockerfile | Un contenedor de API expuesto necesita reducir el impacto de una vulnerabilidad y permitir que Compose detecte un servicio no saludable. |
| 4 | Un cambio rompe el backend de catálogo o el flujo de pedido | Pruebas de sintaxis | La aplicación conserva mucho código heredado; compilar todos los módulos detecta errores baratos antes de construir o desplegar. |
| 5 | Se entrega el código sin inventario de dependencias | SBOM CycloneDX | Flask, boto3 y psycopg llegan desde terceros. El SBOM deja identificadas las versiones que deben revisarse. |
| 6 | Se introducen patrones inseguros en el backend | Bandit | Una herramienta SAST externa revisa el código Python y reporta sus avisos con archivo y línea. |
| 7 | Se fijan versiones con vulnerabilidades conocidas | pip-audit | Una herramienta SCA contrasta dependencias directas y transitivas con avisos publicados. |
| 8 | Un usuario reenvía la confirmación de un pedido ajeno | Prueba de autorización | Bandit no demuestra pertenencia entre usuario y pedido; un caso de regresión debe rechazar ese acceso. |

## Mis etapas y sus umbrales

| Etapa | Herramienta | Qué revisa | Umbral que bloquea | Por qué ese umbral |
|---|---|---|---|---|
| Pruebas de sintaxis y regresión | `compileall` + `unittest` | Módulos Python y pruebas del catálogo | Cualquier error de compilación o prueba fallida | Un módulo que no puede compilar o un flujo heredado que deja de funcionar no puede formar parte de una imagen funcional. |
| Higiene de secretos | `pipeline/run_pipeline.py` | Asignaciones no vacías de claves, contraseñas o llaves privadas | Cero hallazgos | Un solo secreto expuesto es suficiente para detener la entrega y rotarlo. |
| Infraestructura como código | `pipeline/run_pipeline.py` | Bloqueo público y cifrado de S3, cifrado y privacidad de RDS | Cualquier propiedad de seguridad ausente | Estos controles protegen directamente los datos de pedidos y son obligatorios en la consigna. |
| Docker endurecido | `pipeline/run_pipeline.py` | Imagen versionada, usuario no root y `HEALTHCHECK` | Cualquier control ausente | Son requisitos explícitos y reducen riesgos operativos básicos. |
| SAST | Bandit 1.9.4 | Backend y servicio de notificaciones | Cualquier aviso `HIGH` | La alta severidad exige detener el despliegue y revisar el código. Los avisos medios siguen visibles en `reportes/bandit.json`. |
| SCA | pip-audit 2.10.1 | Dependencias Python directas y transitivas | Cualquier vulnerabilidad conocida | Se actualizan los paquetes afectados antes de promover una imagen. El reporte queda en `reportes/pip_audit.json`. |
| Autorización | `unittest` | Acceso al reenvío de confirmación por propietario | Cualquier prueba fallida | Un ID de pedido conocido no autoriza a otro usuario a reenviar su confirmación. |
| SBOM | CycloneDX Python 7.4.0 | Dependencias fijadas en `app/requirements.txt` | Error de generación, validación o inventario vacío | El SBOM proviene de una herramienta estándar y permite identificar versiones. |

## Lo que decidí no cubrir

| Riesgo que dejo fuera | Por qué lo dejo fuera | Qué haría con más tiempo |
|---|---|---|
| Pruebas dinámicas completas contra el contenedor | Primero se necesita estabilizar el MVP y contar con un entorno AWS levantado | Agregaría DAST autenticado y pruebas de contrato entre API y notificaciones. |
| Escaneo de vulnerabilidades de imagen con Trivy | Depende de tener el binario o la imagen de Trivy disponible en el entorno de ejecución | Añadiría Trivy con bloqueo en HIGH/CRITICAL y conservaría el reporte como evidencia. |
| Rotación automática de secretos | AWS Academy y el tiempo del avance no justifican implementar un gestor de secretos completo | Migraría credenciales a Secrets Manager y asignaría permisos mínimos por rol. |
