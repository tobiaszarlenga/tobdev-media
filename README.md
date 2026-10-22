# tobdev-media

Medios públicos de [@tobdev.ia](https://instagram.com/tobdev.ia): plantilla y videos del reel diario (tips de Claude, noticias, historia y plata con IA).

- `CONTENIDO.md` — estrategia: pilares por día, verificación, ganchos y llamados a la acción.
- `IDEAS.md` — banco de temas por pilar.

- `plantilla/make_reel2.py` — generador del reel v2: voz IA (ElevenLabs o Kokoro), subtítulos palabra por palabra, 27 escenas animadas (mockups, cifras, fotos reales con crédito), 5 temas visuales (`noche`, `claro`, `grilla`, `neon`, `editorial`), transiciones barajadas por reel y música procedural en 4 estilos (HyperFrames + GSAP). El guion se escribe según `plantilla/ESCENAS.md`; ejemplos en `plantilla/ejemplo-*.json`. `--revisar` valida y avisa cuando un reel se parece demasiado a los anteriores.
- `plantilla/make_reel.py` — plantilla vieja de 19 s, solo de respaldo.
- `videos/` — MP4 servidos por GitHub Pages para que Metricool los publique. Se borran a los pocos días (Metricool guarda su copia).
- `historial.json` — lo ya publicado, para no repetir.
- `TAREA.md` — instrucciones del agente programado.

Solo contenido propio de tobdev. Nunca material de clientes: este repo es público.
