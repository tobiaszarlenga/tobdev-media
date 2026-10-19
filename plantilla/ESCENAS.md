# Guion del reel v2 (`make_reel2.py`)

El reel se arma desde `guion.json`: una lista de **beats**. Cada beat es una frase que dice la voz y la escena que se ve mientras la dice. La voz (Kokoro, acento rioplatense), los subtítulos palabra por palabra, la música, los efectos y los tiempos salen solos del texto.

```json
{
  "etiqueta": "18 OCT",
  "fuente": "OpenAI · centro de ayuda",
  "acento": "#19C37D",
  "voz": "em_alex",
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
| `acento` | Color de acento de esta noticia (hex). Usá el color de marca de la empresa de la que se habla si es reconocible (Google `#4285F4`, OpenAI `#19C37D`, Anthropic `#D97757`, Microsoft `#00A4EF`, Meta `#0866FF`, Apple `#A1A1AA`, Mercado Libre `#FFE600`). Si no, alterná entre `#11BFD6`, `#F59E0B`, `#B48CFF`, `#FF6B6B`, `#22C55E`. No repitas el acento del reel anterior. |
| `voz` | `em_alex` (por defecto, masculina) o `ef_dora` (femenina). |
| `acento_voz` | `rio` (por defecto: "y" y "ll" como "sh") o `latam` (neutro). |
| `velocidad` | 1.1 por defecto. Entre 1.0 y 1.2. |

## Marcado dentro de `texto`

- `*palabras*` → palabras clave: recuadro de selección en el color de acento. **Máximo 1 o 2 por beat**; si todo está destacado, nada lo está.
- `{Texto|pronunciación}` → se ve "Texto" y la voz dice "pronunciación". Obligatorio para siglas, marcas y palabras en inglés:
  `{ChatGPT|chat yi pi ti}`, `{OpenAI|open ei ai}`, `{IA|i a}`, `{PDF|pe de efe}`, `{Google|gugol}`, `{Microsoft|maicrosoft}`, `{Gemini|yémini}`, `{Claude|clod}`, `{WhatsApp|guasap}`, `{iPhone|ai fon}`, `{app|ap}`, `{@tobdev.ia|tob dev punto i a}`. Los números escribilos en palabras dentro de la pronunciación si son largos: `{2.000 millones|dos mil millones}`.
- La puntuación manda las pausas: coma = pausa corta, punto = pausa larga. Frases cortas.

## Reglas del guion

1. **8 a 12 beats, 40 a 55 segundos** en total (unas 110–140 palabras).
2. **Beat 1 = gancho**: el resultado o la acción concreta, nunca "Hoy les traigo una noticia". Ej.: "Escribís una frase, y ChatGPT te arma la presentación entera."
3. Orden sugerido: gancho → qué es (con la empresa) → cómo funciona (2–3 beats) → límite o dato real (planes, precio, países) → `frase` "¿Y para tu negocio?" → usos concretos → advertencia honesta si corresponde → `cierre`.
4. **Cada beat cambia de escena** y nunca dos beats seguidos usan el mismo `tipo`. Usá **al menos 5 tipos distintos** por reel. Revisá `escenas` de los últimos 3 reels en `historial.json` y no arranques con el mismo tipo que el reel anterior.
5. Cada escena tiene que ser la **imagen literal** de lo que dice la frase (si dice "en minutos", `reloj`; si dice "le escribís", `prompt` o `celular`; si da una cifra, `numero`).
6. Datos de la noticia: solo los que están en la fuente. Datos dentro de los mockups (nombres, montos, empresas): **inventados y verosímiles** ("Constructora Demo", "Sofi"). Nunca logos: las marcas van como texto.
7. Ver `CONTENIDO.md` para ganchos y llamados a la acción por pilar.
8. Voz TobDev: rioplatense con voseo, directo, sin hype (nada de "revolucionario", "increíble", "cambia todo"). Sin emojis.
9. El último beat siempre es `cierre`, con "Seguí a {@tobdev.ia|tob dev punto i a}" y el remate del pilar (por ejemplo, "para más tips de {Claude|clod}").

## Escenas (`escena.tipo`)

`en` = palabra del texto del beat en la que aparece ese elemento (sincroniza la animación con la voz). Si no la ponés, se reparte parejo.

| tipo | Para qué | Parámetros |
|---|---|---|
| `terminal` | Comandos en una terminal (Claude Code, scripts) | `titulo` (barra de la ventana, ej. "claude — ~/mi-tienda"), `lineas` [{`tipo`: "cmd" (se tipea) / "out" (respuesta) / "ok" (resultado con tilde), `texto`, `en`}] (1–6) |
| `linea_tiempo` | Historia: hitos con año | `hitos` [{`anio`, `texto` (admite `*destacado*`), `en`}] (2–4) |
| `prompt` | Alguien le escribe a una IA | `texto` (lo que se tipea, ≤90 car.), `etiqueta` (def. "Tu mensaje"), `estado` (def. "Generando…") |
| `capas` | Varias pantallas/diapositivas/documentos apilados en 3D | `items` (3–5 títulos cortos), `en` (cuándo se ilumina la de arriba) |
| `flujo` | Entradas que se convierten en un resultado | `entradas` [{`texto`, `icono`, `en`}] (1–3), `salida`, `en` |
| `cursores` | Trabajo en equipo / edición en vivo / IA que corrige | `personas` (2 nombres), `comentario` (con @mención), `en_comentario`, `antes`, `despues` (título que cambia), `en_cambio`, `aplicado` |
| `chips` estilo `archivo` | Formatos, archivos, exportaciones | `estilo:"archivo"`, `items` [{`texto`, `sub` (extensión), `en`}] (2–4) |
| `chips` estilo `etiqueta` | Planes, países, integraciones, requisitos | `estilo:"etiqueta"`, `items` [{`texto`, `icono`, `en`}], `barra` opcional {`texto`, `valor` 0–1, `en`} |
| `frase` | Frase fuerte en grande (oculta los subtítulos) | — usa el texto del beat. Ideal para "¿Y para tu negocio?" o el remate. ≤8 palabras |
| `lista` | Usos o beneficios | `items` [{`texto`, `en`}] (2–4), `titulo` opcional |
| `reloj` | Tiempo ahorrado, plazos, velocidad | `antes`, `despues`, `en` |
| `alerta` | Advertencia, riesgo, "revisá antes" | `titulo`, `filas` [[etiqueta, valor]] (2–5), `marcar` (índice de la fila que se resalta), `en` |
| `numero` | Una cifra o un año | `valor` (número), `prefijo`, `sufijo`, `decimales`, `desde`, `separador` (`false` para años: 1969 y no 1.969), `etiqueta` (admite `*destacado*`), `en` |
| `navegador` | Algo que pasa en una web o un agente que navega | `url` (inventada), `pestanas` (1–3), `titulo`, `en` (clic) |
| `celular` | Chat, WhatsApp, atención al cliente, app | `app`, `icono`, `mensajes` [{`de`:"yo"/"ia", `texto`, `en`}] (2–4) |
| `grafico` | Crecimiento, comparación de cifras | `titulo`, `barras` [{`label`, `valor`, `texto`}] (3–5), `marcar` (índice destacado, def. el último), `en` |
| `comparacion` | Antes vs. ahora, o dos opciones | `antes` {`titulo`, `items`, `en`, `icono`}, `despues` {`titulo`, `items`, `en`, `icono`} (la de arriba se ve apagada y la de abajo resaltada) |
| `particulas` | Muchas personas, usuarios o empresas | `valor`, `sufijo`, `etiqueta`, `en` |
| `cierre` | Marca TobDev + CTA + fuente | `sub`, `cta` opcionales |

Iconos disponibles: `archivo`, `chat`, `lista`, `check`, `alerta`, `candado`, `rayo`, `usuario`, `enviar`, `flecha`, `bajar`, `lupa`, `chip`, `globo`, `escudo`, `grafico`, `reloj`, `estrella`, `codigo`, `dinero`.

## Render

```bash
pip install --break-system-packages numpy scipy soundfile kokoro-onnx
python3 plantilla/make_reel2.py guion.json videos/AAAA-MM-DD.mp4
```

Tarda 8 a 10 minutos (la primera vez baja el modelo de voz, ~350 MB, desde GitHub). Con `--solo-html` arma voz, audio y HTML sin renderizar; la carpeta de trabajo queda en la ruta que imprime `WORK` (o en `$REEL_WORK`) y ahí se puede correr `npx --yes hyperframes@0.8.157 snapshot --at 2,10,20` para revisar fotogramas antes del render.
