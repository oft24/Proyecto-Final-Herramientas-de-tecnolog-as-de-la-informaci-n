# ADR 001 Decisiones técnicas de Dangoko Marketplace

Fecha: 17 de septiembre de 2026
Estado: aceptada

## Contexto

El proyecto parte de Bbldak, un catálogo Flask que ya se despliega en dangokobox.com. El Avance 2 exige una aplicación propia de tema Marketplace, dos contenedores propios, S3, RDS, identificación de usuario, IaC y un pipeline con una decisión final. El tiempo y la memoria de AWS Academy favorecen un MVP pequeño, con PostgreSQL y servicios Flask livianos.

## Decisiones

### 1. Framework del backend

**Elegí:** Flask.

**Por qué:** Bbldak ya está construido con Flask y sus plantillas, rutas y pruebas se pueden conservar. Esto reduce el cambio de superficie y permite concentrar el trabajo en autenticación, pedidos, persistencia y controles de seguridad.

**Qué descarté y por qué:** FastAPI. Sería una buena opción para una API nueva, pero migrar el catálogo completo aumentaría el riesgo de romper la experiencia visual y las pruebas existentes sin aportar valor proporcional al MVP.

### 2. Separación en servicios

**Elegí:** un contenedor `api`, un contenedor `notifications` y PostgreSQL local en Compose.

**Por qué:** el API valida y registra pedidos, mientras `notifications` representa el servicio independiente obligatorio del tema 3. La separación permite demostrar una llamada entre servicios y deja lista la sustitución de PostgreSQL local por RDS.

**Qué descarté y por qué:** meter la confirmación dentro del proceso Flask. Habría sido más corto, pero no cumpliría la pieza técnica distintiva ni demostraría desacoplamiento.

### 3. Almacenamiento

**Elegí:** S3 para recibos JSON privados y RDS PostgreSQL para usuarios, pedidos y partidas.

**Por qué:** S3 es adecuado para objetos que no necesitan consultas relacionales y RDS conserva integridad entre usuarios, pedidos e items. El recibo usa cifrado AES256 y el bucket bloquea todo acceso público.

**Qué descarté y por qué:** conservar pedidos solo en archivos locales o usar Supabase como base principal. Eso no demostraría el requisito de RDS y haría que los datos dependieran del filesystem efímero del contenedor.

## Consecuencias

Se conserva gran parte del frontend de Bbldak y se puede levantar todo con una sola orden de Compose. A cambio, el proyecto tiene dos configuraciones de base de datos que deben mantenerse coherentes: PostgreSQL local para pruebas y RDS para AWS. También se necesita configurar permisos AWS antes de que el flujo de S3 pueda operar en modo obligatorio.

## Actualización para la Entrega Final

El 29 de septiembre de 2026 se retiró el servicio PostgreSQL local del Compose principal. Los contenedores propios siguen siendo `api` y `notifications`; la persistencia de QA y Producción se realiza en RDS. Esta actualización responde a la evaluación del Avance 2 y evita una segunda base local que pueda confundir las evidencias. Las pruebas unitarias aíslan la capa de datos con dobles de prueba, mientras que las pruebas de integración se ejecutan contra RDS en AWS.
