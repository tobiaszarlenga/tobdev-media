# Guion del reel v2 (`make_reel2.py`)

El reel se arma desde `guion.json`: una lista de **beats**. Cada beat es una frase que dice la voz y la escena que se ve mientras la dice. La voz (ElevenLabs si el guion trae `elevenlabs` o `voz_archivo`; si no, Kokoro con acento rioplatense), los subtítulos palabra por palabra, la música, las transiciones y los tiempos salen solos del texto.

```json
{
  "etiqueta": "18 OCT",
  "fuente": "OpenAI · centro de ayuda",
  "acento": "#19C37D",
  "tema": "claro",
  "musica": "suave",
  "beats": [
    {"texto": "Escribís *una frase*, y {ChatGPT|chat yi pi ti} te arma la *presentación entera*.",
     "escena": {"tipo": "prompt", "texto": "Armame 6 diapositivas para presentarle el presupuesto a un cliente"}}
  ]
}
```

## Campos generales

| Campo | Qué es |
|---|---|
| `etiqueta` | Texto corto arriba a la derecha: la fecha (`18 OCT`) en noticias, serie y número en el resto (`TIP #2`, `HISTORIA #1`). `fecha` también funciona. |
| `fuente` | Medio u organización. Se muestra en el cierre. |
| `acento` | Color de acento de este reel (hex). Usá el color de marca de la empresa de la que se habla si es reconocible (Google `#4285F4`, OpenAI `#19C37D`, Anthropic `#D97757`, Microsoft `#00A4EF`, Meta `#0866FF`, Apple `#A1A1AA`, Mercado Libre `#FFE600`). Si no, alterná entre `#11BFD6`, `#F59E0B`, `#B48CFF`, `#FF6B6B`, `#22C55E`. No repitas el acento del reel anterior. |
| `tema` | **Look del reel**: `noche` (por defecto: aurora azul/violeta y piso de puntos), `claro` (papel cálido, texto oscuro, tipografía Poppins), `grilla` (plano técnico: cuadrícula, bordes rectos, línea de escaneo), `neon` (negro con brillo fuerte y franjas), `editorial` (serif Lora, reglas finas, papel oscuro). **No repitas el tema de los últimos 2 reels.** El cierre y la cabecera son siempre de TobDev. |
| `musica` | Estilo de la música procedural: `tech` (por defecto), `suave` (más lenta, sin batería), `urgente` (rápida, menor), `retro` (plucks cortos). Distinto al del reel anterior. |
| `transiciones` | Opcional. Lista de transiciones entre escenas (`zoom`, `rise`, `wipe`, `slide`, `iris`, `flip`, `push`, `swing`, `flash` (destello blanco, corte con golpe), `whip` (barrido rápido con desenfoque), `corte`) o un solo nombre para todas. Si no la ponés, el motor baraja el catálogo con la semilla del reel (nunca dos iguales seguidas). |
| `semilla` | Opcional. Entero que fija transiciones, deriva de cámara y variación de la música. Por defecto sale del texto del guion. |
| `voz` | `em_alex` (por defecto, masculina) o `ef_dora` (femenina). Solo para Kokoro. |
| `acento_voz` | `rio` (por defecto: "y" y "ll" como "sh") o `latam` (neutro). |
| `velocidad` | 1.1 por defecto. Entre 1.0 y 1.2. |
| `elevenlabs` | Opcional. `{"voice_id": "...", "model_id": "eleven_v4", "stability": 0.5}`: la voz se genera con la API de ElevenLabs y los subtítulos usan los tiempos por carácter que devuelve. Necesita acceso a `api.elevenlabs.io` (secreto de red del entorno o `ELEVENLABS_API_KEY`). Si falla, usa Kokoro con `voz` y avisa. El audio queda en caché (`~/.cache/reel-voz`) por texto + voz. |
| `voz_archivo` | Opcional. Ruta (relativa al guion) a una voz grabada aparte, por ejemplo de ElevenLabs. También acepta **una lista** de archivos (mp3, wav o el audio de un mp4) que se pegan en orden con 0,3 s entre medio: así el gancho lo dice el clip del avatar con su propio audio y el resto sale de otra toma (`["/tmp/avatar.mp4", "/tmp/voz-resto.mp3"]`). Se usa ese audio tal cual y los subtítulos y escenas se acomodan a sus tiempos (alineación automática contra una referencia Kokoro). El audio tiene que decir exactamente el texto del guion, con la pronunciación de `{Texto\|pronunciación}`. Necesita `librosa` (`pip install --break-system-packages librosa`). |

## Marcado dentro de `texto`

- `*palabras*` → palabras clave: recuadro de selección en el color de acento. **Máximo 1 o 2 por beat**; si todo está destacado, nada lo está.
- `{Texto|pronunciación}` → se ve "Texto" y la voz dice "pronunciación". Obligatorio para siglas, marcas y palabras en inglés:
  `{ChatGPT|chat yi pi ti}`, `{OpenAI|open ei ai}`, `{IA|inteligencia artificial}` (**nunca** `i a`: la voz de ElevenLabs lo junta y suena "i"), `{PDF|pe de efe}`, `{Google|gugol}`, `{Microsoft|maicrosoft}`, `{Gemini|yémini}`, `{Claude|clod}`, `{WhatsApp|guasap}`, `{iPhone|ai fon}`, `{app|ap}`, `{@tobdev.ia|tob dev}` (en pantalla se ve el usuario completo). Los números escribilos en palabras dentro de la pronunciación si son largos: `{2.000 millones|dos mil millones}`.
- La puntuación manda las pausas: coma = pausa corta, punto = pausa larga. Frases cortas.

## Reglas del guion

1. **8 a 12 beats, 40 a 55 segundos** en total (unas 110–140 palabras).
2. **Beat 1 = gancho**: el resultado o la acción concreta, nunca "Hoy les traigo una noticia". Ej.: "Escribís una frase, y ChatGPT te arma la presentación entera."
3. Orden sugerido: gancho → qué es (con la empresa) → cómo funciona (2–3 beats) → límite o dato real (planes, precio, países) → `frase` "¿Y para tu negocio?" → usos concretos → advertencia honesta si corresponde → `cierre`.
4. **Variedad (lo que más se nota)**: cada beat cambia de escena, nunca dos beats seguidos usan el mismo `tipo`, **al menos 5 tipos distintos** por reel y **al menos 2 tipos que no hayan aparecido en los últimos 3 reels** (mirá `escenas` en `historial.json`; `--revisar` te dice cuáles están libres). No arranques con el mismo tipo que el reel anterior, cambiá `tema`, `musica` y `acento` respecto del anterior. Si una idea pide una escena que no existe, se crea (ver `TAREA.md` / la skill).
5. Cada escena tiene que ser la **imagen literal** de lo que dice la frase (si dice "en minutos", `reloj`; si dice "le escribís", `prompt` o `celular`; si da una cifra, `numero` o `anillo`; si muestra algo real, `imagen`).
6. Datos de la noticia: solo los que están en la fuente. Datos dentro de los mockups (nombres, montos, empresas): **inventados y verosímiles** ("Constructora Demo", "Sofi"). Las empresas reales de la noticia van con **su logo** (`marcas`, o `logo` en `titular`, `impacto`, `chips` y `comparacion`): uso editorial para identificarlas, nunca como si patrocinaran el video. Las empresas inventadas de los mockups, sin logo.
7. Ver `CONTENIDO.md` para ganchos y llamados a la acción por pilar.
8. Voz TobDev: rioplatense con voseo, directo, sin hype (nada de "revolucionario", "increíble", "cambia todo"). Sin emojis.
9. El último beat siempre es `cierre`, con "Seguí a {@tobdev.ia|tob dev}" y el remate del pilar (por ejemplo, "para más tips de {Claude|clod}").

## Escenas (`escena.tipo`)

`en` = palabra del texto del beat en la que aparece ese elemento (sincroniza la animación con la voz). Si no la ponés, se reparte parejo. Ninguna escena arranca vacía: el marco (ventana, tarjeta, teléfono) se ve desde el primer cuadro y las listas aparecen apagadas y se encienden cuando la voz las nombra; los números cuentan desde que empieza la escena y aterrizan cuando se dicen.

| tipo | Para qué | Parámetros |
|---|---|---|
| `terminal` | Comandos en una terminal (Claude Code, scripts) | `titulo` (barra de la ventana, ej. "claude — ~/mi-tienda"), `lineas` [{`tipo`: "cmd" (se tipea) / "out" (respuesta) / "ok" (resultado con tilde), `texto`, `en`}] (1–6) |
| `codigo` | Un archivo con código o configuración (CLAUDE.md, un script, un JSON) | `archivo` (nombre de la pestaña), `lineas` [{`texto`, `en`, `marcar` (true resalta esa línea)}] (2–9), `marcar` (índice de una línea). Colorea solo: comentarios, strings, números, palabras clave |
| `linea_tiempo` | Historia: hitos con año | `hitos` [{`anio`, `texto` (admite `*destacado*`), `en`}] (2–4) |
| `pasos` | Un procedimiento en orden (1, 2, 3) | `pasos` [{`titulo` (admite `*destacado*`), `sub`, `en`}] (2–4) |
| `prompt` | Alguien le escribe a una IA | `texto` (lo que se tipea, ≤90 car.), `etiqueta` (def. "Tu mensaje"), `estado` (def. "Generando…") |
| `capas` | Varias pantallas/diapositivas/documentos apilados en 3D | `items` (3–5 títulos cortos), `en` (cuándo se ilumina la de arriba) |
| `flujo` | Entradas que se convierten en un resultado | `entradas` [{`texto`, `icono`, `en`}] (1–3), `salida`, `en` |
| `cursores` | Trabajo en equipo / edición en vivo / IA que corrige | `personas` (2 nombres), `comentario` (con @mención), `en_comentario`, `antes`, `despues` (título que cambia), `en_cambio`, `aplicado` |
| `chips` estilo `archivo` | Formatos, archivos, exportaciones | `estilo:"archivo"`, `items` [{`texto`, `sub` (extensión), `en`}] (2–4) |
| `chips` estilo `etiqueta` | Planes, países, integraciones, requisitos | `estilo:"etiqueta"`, `items` [{`texto`, `icono`, `en`}], `barra` opcional {`texto`, `valor` 0–1, `en`} |
| `impacto` | **Tipografía cinética**: las palabras del beat entran gigantes y en mayúsculas, golpe por golpe, con las `*claves*` sobre un bloque del color de acento y temblor de cámara. Ideal para el gancho o un remate corto. Oculta los subtítulos | `logo` (marca arriba del texto, opcional), `por_linea` (palabras por renglón, def. 2) |
| `marcas` | **Logos de las empresas** de la noticia: 1 (presentación grande), 2 (enfrentados con `VS`, `→`, `+` o `×`) o 3–4 (grilla) | `logos` [{`marca` (clave de `plantilla/logos/marcas.json`, ej. `walmart`, `amazon`, `openai`, `claude`, `gemini`, `meta`, `microsoft`, `mcp`), `texto` (nombre que se muestra), `estado` (pastilla abajo, ej. "Los bloquea"), `ok` (true verde / false rojo), `en`}], `union` (`vs`, `flecha`, `y`, `x`), `titulo` |
| `frase` | Frase fuerte en grande (oculta los subtítulos) | — usa el texto del beat. Ideal para "¿Y para tu negocio?" o el remate. ≤8 palabras |
| `cita` | Una frase textual de alguien (historia, declaraciones) | `texto` (la cita, ≤160 car.; si no lo ponés usa el texto del beat palabra por palabra), `autor`, `cargo` ("UCLA · 1969"), `en` (cuándo empieza a escribirse), `en_autor` |
| `titular` | Una noticia como tapa de diario | `titulo` (≤70 car., admite `*destacado*`), `bajada`, `medio` (fuente), `fecha`, `etiqueta` (def. "ÚLTIMO"), `en` (cuándo se subraya) |
| `lista` | Usos o beneficios | `items` [{`texto`, `en`}] (2–4), `titulo` opcional |
| `tabla` | Comparar planes, precios o características en filas | `titulo`, `columnas` (2–3 encabezados), `filas` [[...]] (2–5), `marcar` (índice de la fila que se resalta), `en` |
| `planes` | 2 o 3 planes o precios lado a lado | `planes` [{`nombre`, `precio`, `detalle`, `destacado` (true levanta la tarjeta), `tag` (def. "Recomendado"), `en`}] (2–3) |
| `reloj` | Tiempo ahorrado, plazos, velocidad | `antes`, `despues`, `en` |
| `calendario` | Fechas, frecuencia, plazos ("todos los lunes", "desde el 1 de noviembre") | `mes`, `anio`, `inicio` (día de la semana del 1: 0 lunes … 6 domingo), `cantidad` (días del mes), `marcas` [{`dia`, `texto` (corto), `en`}] (1–4) |
| `alerta` | Advertencia, riesgo, "revisá antes" | `titulo`, `filas` [[etiqueta, valor]] (2–5), `marcar` (índice de la fila que se resalta), `en` |
| `numero` | Una cifra o un año | `valor` (número), `prefijo`, `sufijo`, `decimales`, `desde`, `separador` (`false` para años: 1969 y no 1.969), `etiqueta` (admite `*destacado*`), `en` |
| `anillo` | Un porcentaje o una proporción | `valor` (0–100), `sufijo` (def. "%"), `etiqueta` (admite `*destacado*`), `en`, `desde`, `decimales` |
| `navegador` | Algo que pasa en una web o un agente que navega | `url` (inventada), `pestanas` (1–3), `titulo`, `en` (clic) |
| `celular` | Chat, WhatsApp, atención al cliente, app | `app`, `icono`, `mensajes` [{`de`:"yo"/"ia", `texto`, `en`}] (2–4) |
| `grafico` | Crecimiento, comparación de cifras | `titulo`, `barras` [{`label`, `valor`, `texto`}] (3–5), `marcar` (índice destacado, def. el último), `en` |
| `comparacion` | Antes vs. ahora, o dos opciones | `antes` {`titulo`, `items`, `en`, `icono`}, `despues` {`titulo`, `items`, `en`, `icono`} (la de arriba se ve apagada y la de abajo resaltada) |
| `particulas` | Muchas personas, usuarios o empresas | `valor`, `sufijo`, `etiqueta`, `en` |
| `imagen` | **Una foto o ilustración real** con movimiento lento de cámara (historia, productos, lugares, personas públicas) | `archivo` (ruta relativa al guion) **o** `url` (https; el motor la baja), `credito` (obligatorio salvo imagen propia o generada: "Foto: NASA · dominio público"), `titulo` (texto sobre la foto, admite `*destacado*`), `en`, `encuadre`: `cover` (def., llena la escena) o `tarjeta` (foto impresa inclinada con pie), `movimiento`: `acercar` / `alejar` / `derecha` / `izquierda` (def. por semilla) |
| `presentador` | **Tob hablando a cámara** (avatar con sincronización labial) a pantalla completa, con subtítulos abajo y su nombre. Pensado para el beat 1 (gancho) | `video` (mp4 9:16 del avatar), `nombre`, `cargo`, `marca` (pastilla arriba a la derecha, def. "EN VIVO"; `false` la saca), `video_desde` (segundo de `voz_archivo` donde empieza el audio del clip; def. 0). Necesita `voz_archivo` con el clip primero (ver abajo) |
| `cierre` | Marca TobDev + CTA + fuente | `sub`, `cta` opcionales |

Logos disponibles (80, en `plantilla/logos/marcas.json`, se suman más según `plantilla/logos/LEEME.md`): IA (`openai`/`chatgpt`, `claude`, `anthropic`, `gemini`, `google`, `meta`, `microsoft`, `copilot`, `mcp`, `deepseek`, `mistral`, `perplexity`, `grok`, `nvidia`, `huggingface`, `cursor`, `elevenlabs`…), comercio (`walmart`, `amazon`, `mercadopago`, `shopify`, `stripe`, `paypal`) y apps (`whatsapp`, `instagram`, `youtube`, `tiktok`, `x`, `linkedin`, `gmail`, `notion`…). `titular`, `impacto`, `chips` (`items[].logo`) y `comparacion` (`antes.logo`, `despues.logo`) también aceptan `logo`.

Iconos disponibles: `archivo`, `chat`, `lista`, `check`, `alerta`, `candado`, `rayo`, `usuario`, `enviar`, `flecha`, `bajar`, `lupa`, `chip`, `globo`, `escudo`, `grafico`, `reloj`, `estrella`, `codigo`, `dinero`.

### Avatar de Tob (`presentador`)

1. Conector de ElevenLabs (`elevenlabs_personalizado`): `creative_create_flow`, después `creative_add_flow_asset_node` con la selfie de Tob (asset `eK9ZCRnHQXw5gyFeUr7h`, en el auto, 9:16; hay otras fotos suyas en el workspace).
2. `creative_generate_speech` con el texto hablado **solo del beat 1** (primera línea de `--texto-voz`), voz `tobias`, `eleven_v4`, 1 toma, en el mismo flujo. El resto de las líneas va en otra generación.
3. `creative_add_flow_node` tipo `avatar`, modelo `heygen-avatar4`, `{"aspect_ratio": "9:16", "talking_style": "stable"}`, `connect_from` = [foto, voz del gancho]. `creative_run_flow_nodes` (primero con `estimate_only`). Tarda ~2 min.
4. Bajar el `content_url` del mp4 y en el guion: `"video": "/tmp/avatar.mp4"` y `"voz_archivo": ["/tmp/avatar.mp4", "/tmp/voz-resto.mp3"]`. El motor alinea solo labios, voz y subtítulos (probado: arranca exacto).

Costo de referencia (23/10/2026): ~3.600 créditos por un gancho de 5 s (US$ 0,73), contra ~730 de la voz de todo el reel. Con la cara de Tob: solo con su consentimiento (ya lo dio) y siempre `isAiGenerated: true`. Con terceros: nunca sin consentimiento escrito.

### Imágenes: de dónde sacarlas

Solo imágenes que se puedan usar en una cuenta comercial. **No** capturas de Google Imágenes ni fotos de prensa sin licencia.

1. **Unsplash / Pexels** (`images.unsplash.com`, `images.pexels.com`): fotos genéricas (oficinas, comercios, teclados, hardware). Crédito: "Foto: <autor> · Unsplash". Funcionan por `url` desde el agente.
2. **Wikimedia Commons** (`upload.wikimedia.org`): fotos históricas de dominio público o CC (ARPANET, ENIAC, Turing, la polilla del Mark II). Crédito: "Foto: <autor> · Wikimedia Commons · <licencia>". **Wikimedia rechaza las descargas automáticas desde la nube (429, política de robots)**: no sirve por `url` desde el agente. Para usar una, Tob la baja y la adjunta (`archivo`), o se usa otra fuente.
3. **Generada con IA** con el conector de ElevenLabs (`creative_generate_image`, 9:16 o 4:5, estilo fotográfico sobrio; sin logos ni personas reales). Crédito: "Ilustración generada con IA". Para avatares o personas reales, nunca.
4. **Propia** de Tob (capturas del pipeline, fotos del local): adjunta en el chat o en el repo, `archivo`.

El dominio de donde se baja la imagen tiene que estar permitido en claude.ai → Ajustes → Capacidades (desde el 23/10: Unsplash, Pexels y `storage.googleapis.com` están permitidos). Si la descarga falla, `--revisar` corta con `ERROR` y hay que adjuntar la imagen como `archivo` o cambiar la escena. Nunca publiques un reel con una `imagen` que no viste en la hoja de contacto.

## Render

```bash
pip install --break-system-packages numpy scipy soundfile kokoro-onnx librosa
python3 plantilla/make_reel2.py guion.json videos/AAAA-MM-DD.mp4 --revisar   # valida, voz, HTML y hoja de contacto (<2 min)
python3 plantilla/make_reel2.py guion.json videos/AAAA-MM-DD.mp4             # render final (4–6 min) y verificación
```

- `--revisar` valida el guion antes de gastar tiempo: `ERROR` (escena inexistente, falta un parámetro, falta el cierre, llaves o asteriscos sin cerrar, tema/transición/música inexistentes, imagen que no se pudo bajar) frena; `AVISO` (palabras en inglés o siglas sin pronunciación, escenas repetidas seguidas, pocos tipos, mismo arranque, acento, tema o música que el reel anterior, menos de 2 escenas nuevas respecto de los últimos 3 reels) avisa. Después imprime `REVISAR <ruta>`: una imagen con un fotograma por escena.
- El segundo comando reusa la voz y el HTML si el guion no cambió (si cambiaste algo, vuelve a armar todo), renderiza con 2 procesos en paralelo y verifica duración y tamaño (`OK`).
- La primera vez baja el modelo de voz (~350 MB) desde GitHub a `~/.cache/kokoro`.
- `--texto-voz` valida el guion e imprime el texto hablado (con las pronunciaciones) para generar la voz afuera, por ejemplo con el conector de ElevenLabs, y usarla con `voz_archivo`.
- `--solo-html` arma voz y HTML sin hoja de contacto ni render. La carpeta de trabajo queda en `/tmp/reel2-<hash>` (o en `$REEL_WORK`).
- Fuentes incluidas (todas con licencia libre): FreeSans (GNU), JetBrains Mono (OFL), Poppins (OFL, tema `claro`), Lora (OFL, tema `editorial`).
