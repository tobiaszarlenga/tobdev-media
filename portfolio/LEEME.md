# Portfolio de TobDev para los videos

**Antes de usar un proyecto, mirá `permiso` en `sitios.json`: solo `true` puede aparecer en un video.** Casa Pan y El Gordo Burger no son clientes (son demos): no se usan sin su autorización por escrito.

Capturas reales de proyectos de Tob para los videos del pilar `marca` (y para cualquier reel que muestre su trabajo). Todo lo que hay acá ya está publicado en su portfolio (tobiaszarlenga.github.io): páginas públicas y sistemas con **datos de demostración**. Nada de datos privados de clientes.

- `sitios.json`: un registro por proyecto, con nombre, rubro, ubicación, URL, tipo (`pagina`, `sistema` o `plataforma`), **descripción** (lo único que se puede afirmar en el video: no inventar resultados, cifras ni clientes), las capturas y, en las páginas, `toque_cta`: posición `[x, y]` (0 a 1) del botón principal en la captura `celular`, para animar un toque.
- `capturas/<sitio>/`: `escritorio.jpg` (1400 px, lo que se ve al abrir la página), `escritorio-completa.jpg` (página entera, para hacer scroll), `celular.jpg` (780 px) y `celular-completa.jpg`.
- `flujos/el-gordo-burger/`: el pedido real paso a paso (menú → agregar → carrito → datos → enviar), `flujo.json` con el toque de cada paso y el mensaje de WhatsApp que genera la página (cliente de prueba).
- `fotos/`: fotos con licencia libre y su crédito en `sitios.json`.

## Sumar o actualizar un sitio

Los sitios no se pueden abrir desde la nube (el proxy los bloquea), así que se capturan desde el repo de cada uno:

1. `add_repo` del repo del sitio (lectura) y clonarlo.
2. Sitios estáticos con Tailwind por CDN y Google Fonts (los de `sitios-clientes`): `herramientas/prep.py <carpeta del sitio> <nombre>` compila Tailwind v3 con la config del HTML y cambia las fuentes por Fontsource locales (antes: `npm i tailwindcss@3 @fontsource/<familia>` en la carpeta de trabajo). Después `herramientas/shoot.py <nombre>` saca las cuatro capturas con Playwright.
3. Apps (Next.js, Vite): `npm ci` y `npx next dev` (o `vite`) y la misma captura con Playwright. Si leen datos de una base real, **no se capturan** hasta tener datos de demo.
4. Convertir a JPG (1400 px escritorio, 780 px celular, páginas completas cortadas a 6000 px) y sumar el registro a `sitios.json` con la descripción del portfolio. `herramientas/boxes.py` calcula `toque_cta` y `herramientas/flow.py` muestra cómo grabar un flujo con clics.

Las rutas dentro de las herramientas apuntan a `/home/claude/work/shots`: ajustalas a tu carpeta de trabajo.
