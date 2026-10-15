# Tarea diaria: reel de noticias IA para @tobdev.ia

Instrucciones para el agente programado. Corre de lunes a viernes. Todo en español rioplatense, tono claro y profesional, sin exagerar.

## Configuración

| Clave | Valor |
|---|---|
| Repo | `tobiaszarlenga/tobdev-media` (público, GitHub Pages en `main` / raíz) |
| URL pública de videos | `https://tobiaszarlenga.github.io/tobdev-media/videos/<archivo>.mp4` |
| Metricool blogId | `7428605` (marca tobdev.ia, timezone `America/Buenos_Aires`) |
| Red | solo Instagram, tipo `REEL` |
| Hora de publicación | 19:00 hora Argentina del mismo día |
| MODO | `aprobacion` → `autoPublish: false` (Tob confirma desde la app de Metricool). Cambiar a `automatico` → `autoPublish: true` cuando Tob lo pida. |
| Tope mensual | 18 reels publicados por mes calendario (el plan gratis de Metricool permite 20; dejamos margen) |

## Pasos

1. **Repo.** Agregá el repo con acceso de escritura y clonalo. Leé `historial.json`.
2. **Tope.** Contá las entradas de `historial.json` del mes actual. Si hay 18 o más, no hagas nada más y terminá informando "tope mensual alcanzado".
3. **Noticia.** Buscá en la web noticias de las últimas 48 h sobre inteligencia artificial, agentes, automatización o software para empresas. Preferí fuentes primarias (blogs oficiales de Anthropic, OpenAI, Google, Microsoft, Meta, etc.) o medios serios. Elegí UNA que:
   - no esté en `historial.json` (compará tema y URL, no solo el título);
   - le sirva a un dueño de pyme o profesional (no papers ultra técnicos, no política, no rumores);
   - podés verificar leyendo la fuente con WebFetch.
   Si no hay ninguna que cumpla, no publiques y terminá informando el motivo. Mejor un día sin post que un post flojo o falso.
4. **Contenido.** Escribí `noticia.json` en la raíz del repo de trabajo (no lo commitees):
   ```json
   {
     "fecha": "16 OCT",
     "titulo": "30–75 caracteres, concreto, sin clickbait",
     "puntos": ["≤100 caracteres", "≤100 caracteres", "≤100 caracteres"],
     "negocio": "≤110 caracteres: qué significa para un negocio real",
     "fuente": "Medio u organización (ej. Anthropic, blog oficial)"
   }
   ```
   Reglas: solo datos que estén en la fuente; nada de cifras inventadas; sin emojis dentro del video; nombres propios bien escritos.
5. **Render.** Si falta numpy/scipy: `pip install --break-system-packages numpy scipy`. Después:
   ```bash
   python3 plantilla/make_reel.py noticia.json videos/AAAA-MM-DD.mp4
   ```
   Tarda ~1 minuto. Verificá con `ffprobe` que dure ~19,5 s y sea 1080x1920. Extraé un fotograma a los 6 s y mirálo (Read) para confirmar que el texto no se corta ni se superpone. Si algo falla, acortá los textos y volvé a renderizar (máximo 2 intentos). Si sigue fallando, no publiques e informá el error.
6. **Subir.** `git add videos/AAAA-MM-DD.mp4 && git commit && git push`. Esperá ~2 minutos a que GitHub Pages lo publique.
7. **Programar en Metricool** con `createScheduledPost`:
   - `blogId`: `7428605`; `date`: hoy 19:00 `-03:00`.
   - `info`:
     ```json
     {
       "autoPublish": false,
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
   {"fecha": "AAAA-MM-DD", "titulo": "...", "url_fuente": "...", "video": "videos/AAAA-MM-DD.mp4", "metricool": "<plannerUrl o id>"}
   ```
   Commit + push.
9. **Limpieza.** Metricool descarga el video y guarda su propia copia (la respuesta trae `media` en `static.metricool.com`), así que el MP4 ya no hace falta en el repo. Borrá con `git rm` los MP4 de `videos/` con más de 3 días para que el repo no crezca. Nunca toques `plantilla/` ni `historial.json` salvo para agregar entradas.
10. **Informe final** (2–4 líneas): título elegido, fuente, hora programada y link de Metricool, o el motivo por el que no se publicó.

## Prohibido

- Subir a este repo cualquier video o dato de clientes (es público).
- Publicar sin `isAiGenerated: true`.
- Temas políticos, de salud, finanzas especulativas o rumores sin fuente oficial.
- Cambiar `autoPublish` a `true` si MODO sigue en `aprobacion`.
