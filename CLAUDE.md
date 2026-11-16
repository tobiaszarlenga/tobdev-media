# tobdev-media

Videos de TobDev. El flujo de cualquier reel es la skill `videos-tobdev` + `plantilla/make_reel2.py` (guion JSON → MP4). El reel diario sigue `TAREA.md`.

## Skills de HyperFrames (`.claude/skills/`)

El motor renderiza con HyperFrames, así que sus skills oficiales sirven de referencia. **No reemplazan al motor**: los reels se siguen armando con `make_reel2.py`.

- `hyperframes-registry`: unos 450 bloques listos (transiciones, títulos, tipografía animada, subtítulos, gráficos, 3D, movimientos de cámara, grano, glitch). Antes de dibujar un efecto a mano, buscarlo acá y adaptarlo como escena `ilustracion` o como escena nueva del motor.
- `style-sampling`: estilos probados (Collage Explainer, Animated Science Explainer, 3D True Crime, etc.) para formatos nuevos.
- `reverse-any-video`: para analizar un reel de referencia que pase Tob (estructura y ritmo). Nunca copiar marca, textos ni personajes.
- `media-use`: música, efectos de sonido, íconos y tratamiento de imágenes con herramientas locales gratis.
- `hyperframes` y `hyperframes-cli`: reglas de render (seek-safe, sin `Math.random()`, etc.) y comandos de la CLI.

Telemetría: antes de usar la CLI de HyperFrames, `export HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1`. El motor fija `hyperframes@0.8.157`; las skills apuntan a la 0.9.x: si un bloque no anda, adaptarlo a mano.
