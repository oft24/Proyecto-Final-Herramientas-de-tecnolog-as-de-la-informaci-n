# Declaración de uso de inteligencia artificial

> Antecedente histórico del Avance 2 y preparación inicial. El estado actualizado y la declaración de la Final están en [declaracion_ia.md](declaracion_ia.md); los pendientes descritos abajo corresponden a esa etapa, no al cierre actual.

Usé Codex como apoyo para leer las instrucciones, revisar Bbldak, proponer la separación de servicios y escribir una primera versión del código. La responsabilidad de entender, probar y corregir cada parte sigue siendo del alumno.

## Qué generé con ayuda de IA

| Parte | Herramienta | Qué le pedí | Qué debo verificar o cambiar yo |
|---|---|---|---|
| Adaptación del backend | Codex | Convertir el checkout en un flujo de marketplace con usuarios, pedidos y notificaciones | Probar registro, login, pedido y errores con datos propios |
| Docker Compose | Codex | Separar API y notificaciones; conectar el API con RDS para la Entrega Final | Confirmar nombres, puertos, variables y acceso real a RDS |
| Terraform | Codex | Describir S3 privado y RDS PostgreSQL sin acceso público | Completar VPC, subredes, grupo de seguridad y límites de AWS Academy |
| Pipeline y documentación | Codex | Incorporar Bandit, pip-audit y CycloneDX tras la retroalimentación del Avance 2 | Ejecutar el pipeline en QA, conservar las corridas reales roja y verde y explicar las decisiones |

## Qué hice sin IA

Elegí reutilizar Bbldak como base, seleccioné el tema Marketplace, decidí que la pieza distintiva sería el servicio de notificaciones y debo validar personalmente la cuenta AWS, las variables, los resultados del pipeline y las capturas de entrega.

## Algo que la IA me dio mal y tuve que corregir

La primera integración dejó una inconsistencia entre el identificador público del pedido y el UUID usado en la base de datos, además de una referencia incorrecta al producto al insertar las partidas. Se corrigió separando `public_order_id`, `order_id` y `product_id`, y revisando el contrato de cada función. Debo confirmar este caso con una prueba real antes de entregar.

En el Avance 2 también quedó débil el pipeline: el bloqueo rojo se demostró con un archivo temporal y el SBOM lo producía un script propio. La retroalimentación pidió herramientas estándar. En esta Entrega Final se reemplazó esa demostración por Bandit, pip-audit y CycloneDX; el hallazgo del parche deberá probarse con una corrida real en QA.
