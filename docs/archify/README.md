# Arquitectura con Archify

![Dangoko generado con Archify](dangoko.png)

- [Diagrama interactivo HTML](dangoko.html): descargar y abrir en navegador; GitHub muestra el código HTML, no ejecuta el visor.
- [Fuente editable JSON](dangoko.architecture.json).
- [Resultado de validación](dangoko.finalize-summary.json).

Generado con [Archify](https://github.com/tt-a1i/archify), versión 3.0.1, revisión del generador `5ca9c1233b82fac6478158cc1ee2d00c42d3ab1b`. Licencia del generador: MIT. Las fuentes del diagrama apuntan al repositorio Dangoko en `1674cb1f4f51cdaadf24a647af37dadfbe64b311`, no a credenciales ni a archivos privados.

Validaciones automáticas de esquema, entrega, artefacto y navegador: correctas, sin diagnósticos. Se inspeccionó la captura clara de 2048×1320 publicada como vista previa. El visor conserva controles en inglés; el contenido describe el proyecto en español. No se requiere instalar Archify para abrir el HTML.

El diagrama resume el flujo lógico, no es un plano exhaustivo de subredes. En cada EC2 hay api y notifications; QA y Producción comparten RDS y S3 del laboratorio. El reenvío requiere sesión y propiedad del pedido. Resend es externo a AWS. El acceso documentado es por túnel SSM. No se añadieron balanceadores, colas ni servicios que no existen.

## Regenerar

Con Node.js 18 o posterior y el generador en la revisión indicada, desde la raíz de Dangoko:

```bash
node /ruta/archify/archify/bin/archify.mjs finalize architecture docs/archify/dangoko.architecture.json docs/archify/dangoko.html --repo-root . --quality showcase --json
```

Los archivos de comprobación contienen rutas locales de generación sin secretos y hashes para vincular fuente y HTML. La especificación fija el commit de referencia; actualizarlo explícitamente cuando cambie la arquitectura. El SVG anterior se conserva como antecedente y no se atribuye a Archify.
