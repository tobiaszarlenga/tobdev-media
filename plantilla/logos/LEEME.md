# Logos de marcas

Para identificar a la empresa de la que habla un reel (uso editorial, como hace cualquier medio). Nunca para sugerir que la marca patrocina o aprueba el contenido.

- `marcas.json`: clave → nombre, color de marca, si el SVG ya trae sus colores (`multi`) y `viewBox`. `_alias` mapea otros nombres (`chatgpt` → `openai`).
- Origen: [Simple Icons](https://simpleicons.org) (datos CC0; Walmart, Amazon y LinkedIn salen de la versión 10, que todavía los tenía) y [LobeHub Icons](https://github.com/lobehub/lobe-icons) (MIT) para las marcas de IA con color. Microsoft (cuatro cuadrados) y la chispa de Walmart dibujados a mano; `fondo` cambia el color de la ficha (Walmart va sobre azul).
- Las marcas son de sus dueños.

Para sumar una marca: `npm install simple-icons @lobehub/icons-static-svg` en una carpeta temporal, copiar el SVG acá y agregar la entrada a `marcas.json` (color en hex de la propia librería).
