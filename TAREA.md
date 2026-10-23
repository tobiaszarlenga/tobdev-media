# Tarea diaria: reel de @tobdev.ia

Instrucciones para el agente programado. Corre de lunes a viernes. Formato v2: reel narrado con voz IA, subtítulos palabra por palabra y escenas animadas distintas en cada reel (`plantilla/make_reel2.py`). La plantilla vieja `make_reel.py` queda solo de respaldo.

**Siempre se publica un reel.** El objetivo es que la cuenta crezca en seguidores y tenga movimiento. El tema sale del calendario de pilares de `CONTENIDO.md` (tips de Claude, noticias, historia, plata con IA); si no hay noticia, se usa otro pilar. "No encontré noticia" nunca es motivo para no publicar. Todo en español rioplatense, tono claro y profesional, sin exagerar.

## Configuración

| Clave | Valor |
|---|---|
| Repo | `tobiaszarlenga/tobdev-media` (público, GitHub Pages en `main` / raíz) |
| URL pública de videos | `https://raw.githubusercontent.com/tobiaszarlenga/tobdev-media/main/videos/<archivo>.mp4` (respaldo: GitHub Pages) |
| Metricool blogId | `7428605` (marca tobdev.ia, timezone `America/Buenos_Aires`) |
| Red | solo Instagram, tipo `REEL` |
| Hora de publicación | 19:00 hora Argentina del mismo día |
| MODO | `automatico` → `autoPublish: true`. Se programa a la mañana y se publica solo a las 19:00; Tob puede vetarlo borrándolo en Metricool antes. Si Tob pide `aprobacion`, usar `autoPublish: false`. |
| Voz | ElevenLabs, voz `tobias` (clon de Tob, acento argentino, voice_id `73bgA51zDDQKg9HmPZ8f`, modelo `eleven_v4`), generada con el conector de ElevenLabs en el paso 5. Si algo falla, el reel sale igual con Kokoro. |
| Tope mensual | 18 reels publicados por mes calendario (el plan gratis de Metricool permite 20; dejamos margen) |

## Pasos

1. **Repo.** Agregá el repo con acceso de escritura y clonalo. Leé `CONTENIDO.md`, `IDEAS.md` y `historial.json`.
2. **Tope.** Contá las entradas de `historial.json` del mes actual. Si hay 18 o más, no hagas nada más y terminá informando "tope mensual alcanzado".
3. **Tema del día.** Mirá qué día es (hora Argentina) y qué pilar toca según `CONTENIDO.md`.
   - **Días de noticia** (martes y jueves, o cualquier día si hay una noticia muy grande): buscá noticias de las últimas 48 h sobre IA, agentes, automatización o software. Preferí fuentes primarias (blogs oficiales de Anthropic, OpenAI, Google, Microsoft, Meta, etc.) o medios serios. Tiene que: no estar en `historial.json` (compará tema y URL), servirle a un negocio o a alguien que trabaja con IA (no papers ultra técnicos, no política, no rumores) y poder verificarse leyendo la fuente con WebFetch. Si no hay ninguna que cumpla, **no se saltea el día**: usá el pilar `uso`.
   - **Otros pilares**: tomá la idea siguiente de ese pilar en `IDEAS.md` y verificá todos los datos como dice `CONTENIDO.md` (doc oficial para tips; 2 fuentes serias para historia; nada de ingresos prometidos ni cifras sin fuente para negocio).
   - Si una idea no se puede verificar, pasá a la siguiente de la lista. Mejor otro tema que un dato falso.
4. **Guion.** Leé `plantilla/ESCENAS.md` completo y escribí el guion en `guiones/AAAA-MM-DD.json` (se commitea junto con el video: sirve para rehacer el reel si hace falta). Resumen de lo que exige:
   - No pongas `elevenlabs` ni `voz_archivo`: la voz se agrega en el paso 5.
   - 8 a 12 beats, 40 a 55 s. El beat 1 es el gancho (fórmulas en `CONTENIDO.md`): tiene que frenar el scroll en el primer segundo, nunca "hoy les traigo".
   - `etiqueta`: la fecha (`20 OCT`) para noticias; serie y número para el resto (`TIP #2`, `HISTORIA #1`, `IA Y PLATA #1`, `IA EN TU NEGOCIO #1`).
   - El beat anterior al cierre o el cierre lleva el llamado a la acción del pilar (guardar, comentar o compartir), con voz.
   - **Que no se parezca al anterior.** Cada beat con una escena distinta a la anterior, al menos 5 tipos distintos por reel, al menos 2 tipos que no hayan aparecido en los últimos 3 reels (mirá `escenas` en `historial.json`; hay 27 tipos, incluidos `imagen`, `codigo`, `pasos`, `anillo`, `titular`, `cita`, `tabla`, `calendario` y `planes`), y no arrancar con el mismo tipo que el reel anterior.
   - `tema` (look): `noche`, `claro`, `grilla`, `neon` o `editorial`, distinto al de los últimos 2 reels (mirá `tema` en `historial.json`). Sugerencia por pilar: tips → `grilla` o `claro`; noticias → `noche` o `neon`; historia → `editorial`; negocio → `claro`. No es obligatorio: lo que importa es alternar.
   - `musica`: `tech`, `suave`, `urgente` o `retro`, distinta a la del reel anterior.
   - `acento`: color de la marca de la que se habla o uno de la lista de ESCENAS.md, distinto al del reel anterior.
   - Si el tema tiene una imagen real que lo cuenta mejor que un mockup (historia: una foto del ENIAC o de la polilla del Mark II; una noticia sobre un producto físico), usá la escena `imagen` con una foto de Unsplash o Pexels **con licencia libre y crédito** (por `url`), o una ilustración generada con el conector de ElevenLabs (`creative_generate_image`, bajada de `storage.googleapis.com`). Wikimedia no se puede bajar desde acá (rechaza robots): no lo intentes. Nunca Google Imágenes ni fotos de prensa. Si la descarga falla, cambiá la escena: no vale la pena trabarse.
   - Si ninguna escena ilustra bien una frase, podés crear una nueva en `plantilla/make_reel2.py` (máximo una por reel: HTML en `scene_html`, cues en `scene_params`, animación en el objeto `SC` del JS, CSS, `SCENE_TYPES`/`REQUIRED` y una fila en `ESCENAS.md`). Tiene que pasar `--revisar` y verse bien en la hoja de contacto; se commitea con el reel para que quede disponible.
   - Pronunciación con `{Texto|pron}` para siglas, marcas y palabras en inglés. Máximo 1–2 `*palabras clave*` por beat.
   - Solo datos verificados en las fuentes; nada de cifras inventadas. Los datos de los mockups (nombres, montos, empresas) son ficticios. Sin logos, sin emojis.
   - Voz de marca TobDev: español rioplatense con voseo, directo, técnico, **sin hype**. Nada de "revolucionario", "increíble", "cambia todo".
   - Último beat: `cierre`.
   La cabecera, el logo y el cierre son de TobDev y están fijos en la plantilla: no los toques. Fondo, superficies, tipografía y subtítulos cambian con `tema`. Hay guiones de ejemplo en `plantilla/ejemplo-guion.json` (noticia), `plantilla/ejemplo-tip.json` (tip) y `plantilla/ejemplo-claro.json` (tema claro con las escenas nuevas).
5. **Voz, revisar y renderizar.** Instalá lo que falte: `pip install --break-system-packages numpy scipy soundfile kokoro-onnx librosa`.
   **Voz (ElevenLabs).** Dejá el texto de los beats cerrado antes de este paso: si después lo cambiás, la voz hay que generarla de nuevo y gasta créditos otra vez (cambiar escenas no afecta).
   ```bash
   python3 plantilla/make_reel2.py guiones/AAAA-MM-DD.json videos/AAAA-MM-DD.mp4 --texto-voz
   ```
   Valida el guion e imprime el texto hablado entre `TEXTO_VOZ_INICIO` y `TEXTO_VOZ_FIN`. Cargá con ToolSearch `mcp__ElevenLabs__creative_generate_speech` y `mcp__ElevenLabs__creative_get_flow_run_status`, y generá la voz con: `prompt` = ese texto exacto (con sus saltos de línea), `voice_id` = `73bgA51zDDQKg9HmPZ8f`, `model_id` = `eleven_v4`, `generations_count` = 1. Consultá `creative_get_flow_run_status` esperando `poll_after_seconds` entre llamadas hasta `all_completed`, y bajá el `content_url` de la generación:
   ```bash
   curl -sS --max-time 120 -o /tmp/voz-AAAA-MM-DD.mp3 "<content_url>"
   ```
   Agregá al guion `"voz_archivo": "/tmp/voz-AAAA-MM-DD.mp3"`. Si falla cualquier cosa (conector, generación o descarga), **no reintentes** (cada intento gasta créditos): seguí sin `voz_archivo`, sale con Kokoro, y anotalo en el informe final.
   **Revisar y renderizar**, en dos pasos:
   ```bash
   python3 plantilla/make_reel2.py guiones/AAAA-MM-DD.json videos/AAAA-MM-DD.mp4 --revisar
   ```
   Valida el guion (`ERROR` frena: corregí y repetí; `AVISO`: corregilo si tiene sentido, en especial los de variedad: mismo tema, misma música, escenas repetidas), arma la voz y el HTML (menos de 2 minutos) e imprime `REVISAR <ruta>` (una o dos hojas de contacto con un fotograma por escena). También imprime `VOZ archivo` (voz de ElevenLabs alineada) o `VOZ kokoro`. Miralas con Read: texto cortado, superposiciones, algo fuera de pantalla, una escena vacía o una imagen que no es la que esperabas. Si hay que corregir, cambiá el guion (no el texto de los beats, que ya tiene voz) y repetí `--revisar` (máximo 2 veces).
   ```bash
   python3 plantilla/make_reel2.py guiones/AAAA-MM-DD.json videos/AAAA-MM-DD.mp4
   ```
   Reusa lo que armó `--revisar`, renderiza (4 a 6 minutos; correlo en primer plano con timeout de 10 minutos) y verifica duración y tamaño solo. Si imprime `OK`, listo: no hace falta mirar fotogramas del video final. Si falla dos veces, no publiques e informá el error.
6. **Subir.** `git add videos/AAAA-MM-DD.mp4 guiones/AAAA-MM-DD.json && git commit && git push`. No hace falta esperar a GitHub Pages.
7. **Programar en Metricool** con `createScheduledPost`:
   - `blogId`: `7428605`; `date`: hoy 19:00 `-03:00`.
   - `info`:
     ```json
     {
       "autoPublish": true,
       "draft": false,
       "text": "<caption>",
       "firstCommentText": "",
       "media": ["https://raw.githubusercontent.com/tobiaszarlenga/tobdev-media/main/videos/AAAA-MM-DD.mp4"],
       "providers": [{"network": "instagram"}],
       "publicationDate": {"dateTime": "AAAA-MM-DDT19:00:00", "timezone": "America/Buenos_Aires"},
       "instagramData": {"type": "REEL", "showReelOnFeed": true, "isAiGenerated": true},
       "videoCoverMilliseconds": 3000
     }
     ```
   - Caption según `CONTENIDO.md`: primera línea = gancho (≤90 caracteres); 2–4 líneas con valor que no está en el video; la pregunta o el llamado a la acción del pilar; "Fuente: <fuente>" si hay; "Seguí a @tobdev.ia"; 4–6 hashtags del pilar. Máximo 1.200 caracteres.
   - La URL de `raw.githubusercontent.com` funciona apenas hacés push (GitHub Pages a veces tarda o no se actualiza). Si Metricool la rechaza, esperá 2 minutos y probá una vez con `https://tobiaszarlenga.github.io/tobdev-media/videos/AAAA-MM-DD.mp4`. Si también falla, informá el error textual.
8. **Historial.** Agregá a `historial.json` → `publicados`:
   ```json
   {"fecha": "AAAA-MM-DD", "pilar": "tip", "serie": "TIP #2", "titulo": "...", "url_fuente": "...", "video": "videos/AAAA-MM-DD.mp4", "metricool": "<plannerUrl o id>", "acento": "#hex", "tema": "claro", "musica": "suave", "escenas": ["titular", "codigo", "..."], "voz": "elevenlabs"}
   ```
   En `voz` va `elevenlabs` si usaste `voz_archivo` o `kokoro` si no. Si el tema salió de `IDEAS.md`, marcalo como usado (`[x]` y fecha). Commit + push.
9. **Limpieza.** Metricool descarga el video y guarda su propia copia (la respuesta trae `media` en `static.metricool.com`), así que el MP4 ya no hace falta en el repo. Borrá con `git rm` los MP4 de `videos/` con más de 3 días para que el repo no crezca. Nunca borres `guiones/` ni toques `plantilla/` ni `CONTENIDO.md`; en `historial.json` e `IDEAS.md` solo agregás entradas o marcás ideas usadas.
10. **Informe final** (2–4 líneas): pilar y serie, título, fuente, voz usada (si fue Kokoro de respaldo, el motivo), hora programada y link de Metricool. Si no se publicó, el motivo (solo puede ser un error técnico o el tope mensual).

## Para gastar menos y tardar menos

- **Sin subagentes.** Hacé todo en esta sesión: cada subagente arranca de cero y multiplica el consumo.
- Leé solo `TAREA.md`, `CONTENIDO.md`, `IDEAS.md`, `plantilla/ESCENAS.md` y `historial.json`, una vez cada uno. No abras `make_reel2.py` ni el resto de `plantilla/` salvo que el script dé un error que no se entienda o que vayas a crear una escena nueva (paso 4).
- Para elegir y verificar el tema: 2 a 5 búsquedas y WebFetch con un pedido concreto ("devolvé solo la fecha y el nombre de…"), no páginas enteras.
- Para revisar el video alcanza la hoja de contacto de `--revisar`. No extraigas fotogramas del video final.
- No esperes con `sleep` ni consultes el render en bucle: corré el comando en primer plano.

## Prohibido

- Subir a este repo cualquier video o dato de clientes (es público).
- Publicar sin `isAiGenerated: true`.
- Temas políticos, de salud, finanzas especulativas (cripto, apuestas, "ingresos pasivos"), promesas de ingresos o rumores sin fuente oficial.
- Programar para una hora ya pasada o para otro día: siempre hoy a las 19:00. Si ya son más de las 18:30, no publiques e informalo.
