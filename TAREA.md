# Tarea diaria: reel de noticias IA para @tobdev.ia

Instrucciones para el agente programado. Corre de lunes a viernes. Formato v2: reel narrado con voz IA, subtítulos palabra por palabra y escenas animadas distintas en cada reel (`plantilla/make_reel2.py`). La plantilla vieja `make_reel.py` queda solo de respaldo. Todo en español rioplatense, tono claro y profesional, sin exagerar.

## Configuración

| Clave | Valor |
|---|---|
| Repo | `tobiaszarlenga/tobdev-media` (público, GitHub Pages en `main` / raíz) |
| URL pública de videos | `https://tobiaszarlenga.github.io/tobdev-media/videos/<archivo>.mp4` |
| Metricool blogId | `7428605` (marca tobdev.ia, timezone `America/Buenos_Aires`) |
| Red | solo Instagram, tipo `REEL` |
| Hora de publicación | 19:00 hora Argentina del mismo día |
| MODO | `automatico` → `autoPublish: true`. Se programa a la mañana y se publica solo a las 19:00; Tob puede vetarlo borrándolo en Metricool antes. Si Tob pide `aprobacion`, usar `autoPublish: false`. |
| Tope mensual | 18 reels publicados por mes calendario (el plan gratis de Metricool permite 20; dejamos margen) |

## Pasos

1. **Repo.** Agregá el repo con acceso de escritura y clonalo. Leé `historial.json`.
2. **Tope.** Contá las entradas de `historial.json` del mes actual. Si hay 18 o más, no hagas nada más y terminá informando "tope mensual alcanzado".
3. **Noticia.** Buscá en la web noticias de las últimas 48 h sobre inteligencia artificial, agentes, automatización o software para empresas. Preferí fuentes primarias (blogs oficiales de Anthropic, OpenAI, Google, Microsoft, Meta, etc.) o medios serios. Elegí UNA que:
   - no esté en `historial.json` (compará tema y URL, no solo el título);
   - le sirva a un dueño de pyme o profesional (no papers ultra técnicos, no política, no rumores);
   - podés verificar leyendo la fuente con WebFetch.
   Si no hay ninguna que cumpla, no publiques y terminá informando el motivo. Mejor un día sin post que un post flojo o falso.
4. **Guion.** Leé `plantilla/ESCENAS.md` completo y escribí `guion.json` en la raíz del repo de trabajo (no lo commitees). Resumen de lo que exige:
   - 8 a 12 beats, 40 a 55 s. El beat 1 es el gancho: el resultado o la acción concreta, nunca "hoy les traigo".
   - Cada beat con una escena distinta a la anterior, al menos 5 tipos distintos por reel, y no arrancar con el mismo tipo que el reel anterior (mirá `escenas` en `historial.json`).
   - `acento`: color de la marca de la que se habla o uno de la lista de ESCENAS.md, distinto al del reel anterior.
   - Pronunciación con `{Texto|pron}` para siglas, marcas y palabras en inglés. Máximo 1–2 `*palabras clave*` por beat.
   - Solo datos que estén en la fuente; nada de cifras inventadas sobre la noticia. Los datos de los mockups (nombres, montos, empresas) son ficticios. Sin logos, sin emojis.
   - Voz de marca TobDev: español rioplatense con voseo, directo, técnico, **sin hype**. Nada de "revolucionario", "increíble", "cambia todo".
   - Último beat: `cierre`.
   El diseño base (fondo, fuentes, logo, cierre) está fijo en la plantilla según el sistema de diseño de TobDev: no lo toques. Hay un guion de ejemplo en `plantilla/ejemplo-guion.json`.
5. **Render.** Instalá lo que falte: `pip install --break-system-packages numpy scipy soundfile kokoro-onnx`. Después:
   ```bash
   python3 plantilla/make_reel2.py guion.json videos/AAAA-MM-DD.mp4
   ```
   Tarda 8 a 10 minutos. Verificá con `ffprobe` que dure entre 35 y 60 s y sea 1080x1920. Extraé 4 fotogramas (al 15 %, 40 %, 65 % y 85 % de la duración) y miralos con Read: texto cortado, superposiciones, algo fuera de pantalla o una escena vacía. Si algo falla, corregí el guion (textos más cortos, otra escena) y volvé a renderizar (máximo 2 intentos). Si sigue fallando, no publiques e informá el error.
6. **Subir.** `git add videos/AAAA-MM-DD.mp4 && git commit && git push`. Esperá ~2 minutos a que GitHub Pages lo publique.
7. **Programar en Metricool** con `createScheduledPost`:
   - `blogId`: `7428605`; `date`: hoy 19:00 `-03:00`.
   - `info`:
     ```json
     {
       "autoPublish": true,
       "draft": false,
       "text": "<caption>",
       "firstCommentText": "",
       "media": ["https://tobiaszarlenga.github.io/tobdev-media/videos/AAAA-MM-DD.mp4"],
       "providers": [{"network": "instagram"}],
       "publicationDate": {"dateTime": "AAAA-MM-DDT19:00:00", "timezone": "America/Buenos_Aires"},
       "instagramData": {"type": "REEL", "showReelOnFeed": true, "isAiGenerated": true},
       "videoCoverMilliseconds": 3000
     }
     ```
   - Caption: primera línea gancho (≤90 caracteres), 2–3 líneas explicando, una línea "¿Y para tu negocio?" con la bajada, "Fuente: <medio>", cierre "Seguí a @tobdev.ia para más IA aplicada a negocios" y 4–6 hashtags (#inteligenciaartificial #IA #automatizacion #pymes + 1–2 del tema). Máximo 1.200 caracteres.
   - Si Metricool rechaza la URL, probá una vez con `https://raw.githubusercontent.com/tobiaszarlenga/tobdev-media/main/videos/AAAA-MM-DD.mp4`. Si también falla, informá el error textual.
8. **Historial.** Agregá a `historial.json` → `publicados`:
   ```json
   {"fecha": "AAAA-MM-DD", "titulo": "...", "url_fuente": "...", "video": "videos/AAAA-MM-DD.mp4", "metricool": "<plannerUrl o id>", "acento": "#hex", "escenas": ["prompt", "capas", "..."]}
   ```
   Commit + push.
9. **Limpieza.** Metricool descarga el video y guarda su propia copia (la respuesta trae `media` en `static.metricool.com`), así que el MP4 ya no hace falta en el repo. Borrá con `git rm` los MP4 de `videos/` con más de 3 días para que el repo no crezca. Nunca toques `plantilla/` ni `historial.json` salvo para agregar entradas.
10. **Informe final** (2–4 líneas): título elegido, fuente, hora programada y link de Metricool, o el motivo por el que no se publicó.

## Prohibido

- Subir a este repo cualquier video o dato de clientes (es público).
- Publicar sin `isAiGenerated: true`.
- Temas políticos, de salud, finanzas especulativas o rumores sin fuente oficial.
- Programar para una hora ya pasada o para otro día: siempre hoy a las 19:00. Si ya son más de las 18:30, no publiques e informalo.
