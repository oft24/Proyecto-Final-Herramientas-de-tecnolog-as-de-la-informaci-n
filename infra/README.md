# Terraform y alcance de la infraestructura

La consigna del Avance 2 exige archivos .tf que describan S3 y RDS y pasen el escaneo propio, incluso si los recursos se crearon por consola. Los archivos de esta carpeta conservan esa base.

## Código incluido

- `main.tf`: EC2 base, grupos de seguridad, bucket privado cifrado AES256, subredes RDS y PostgreSQL con almacenamiento cifrado y sin acceso público.
- `variables.tf`: parámetros de región, red, credenciales y capacidad. No contiene credenciales reales.
- `outputs.tf`: identificadores y endpoints no secretos.
- `.terraform.lock.hcl`: versiones y hashes del proveedor. Debe versionarse; no es una contraseña.

## Inventario de la Final observado el 29-09-2026

| Recurso | Identificador | Relación con esta configuración |
|---|---|---|
| QA | i-086d08e1bca370b0f | EC2 del Avance 2 reutilizada para QA |
| Producción | i-0f3fd952d3b7b73a1 | EC2 nueva creada en la operación AWS, no administrada por este estado Terraform |
| SG Producción | sg-0826360c49412a15e | Regla de aplicación separada, acceso mediante SSM |
| RDS | dangoko-avance2-rds | Recurso compartido existente, privado/cifrado |
| SG RDS | sg-073770a1042e0cb1d | Permite 5432 desde SG de aplicación; se agregó SG Producción |
| S3 | dangoko-avance2-943135209242-us-west-2-mkt | Recurso compartido existente, privado/AES256 |
| Región | us-west-2 | Oregón |

La configuración base **no es una representación completa importada del estado actual**: la EC2 nueva y su regla RDS se operaron fuera de Terraform. Tampoco hay evidencia aquí de un `terraform apply` exitoso. La documentación distingue descripción declarativa de recursos reales y gestión efectiva del estado.

## Uso seguro

No ejecutar `apply` ni `destroy` sobre AWS existente sin revisar el estado, importar los recursos que corresponda y aprobar un plan sin sustituciones inesperadas. Los nombres de la base son del Avance 2; un apply a ciegas puede entrar en conflicto con recursos compartidos.

Para validar sintaxis se puede usar `terraform init -backend=false` y `terraform validate`, con el proveedor disponible. `terraform fmt -check` revisa formato. El pipeline académico verifica propiedades específicas del texto de main.tf; no equivale a un plan de Terraform ni a un escáner IaC completo.

El valor `allowed_cidr` debe ser explícito y restringido. No usar 0.0.0.0/0 para abrir SSH o la aplicación durante esta entrega. Las credenciales se inyectan privadamente, nunca en .tf, .tfvars, reportes ni Git; el estado también puede contener secretos.
