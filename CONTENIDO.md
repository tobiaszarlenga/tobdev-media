# Estrategia de contenido de @tobdev.ia

Objetivo: **que la cuenta crezca en seguidores y tenga movimiento** (vistas, guardados, compartidos, comentarios). Siempre sale un reel de lunes a viernes. Si no hay una noticia que valga la pena, se usa otro pilar: nunca hay un día sin publicar por falta de tema.

## Pilares y calendario

| Día | Pilar | Etiqueta arriba a la derecha | De qué se trata |
|---|---|---|---|
| Lunes | `tip` | `TIP #N` | Un truco concreto de Claude, Claude Code o la API: cómo se usa y para qué sirve. |
| Martes | `noticia` | fecha (`20 OCT`) | Lo más relevante de IA de las últimas 48 h para negocios o para gente que trabaja con IA. |
| Miércoles | `historia` | `HISTORIA #N` | Historia y curiosidades de la tecnología y la IA que llamen la atención. |
| Jueves | `noticia` | fecha | Igual que el martes. |
| Viernes | `negocio` | `IA Y PLATA #N` | Cómo ganar plata o ahorrar con IA: servicios que se pueden vender, casos reales, detrás de escena de tobdev. |

Reglas del calendario:
- **Martes y jueves sin noticia buena** (verificable, de las últimas 48 h, útil, no repetida): se usa el pilar `uso` (`IA EN TU NEGOCIO #N`): una tarea concreta de un negocio que se resuelve con IA y cómo hacerlo.
- **Noticia muy grande cualquier día** (lanzamiento de un modelo o producto que usa mucha gente, de Anthropic, OpenAI, Google, Microsoft, Meta o Apple): puede reemplazar el pilar del día. Máximo 3 noticias por semana.
- No repetir el mismo pilar dos días seguidos, salvo noticia muy grande.
- `N` es el número dentro de la serie: contá en `historial.json` cuántos hay de ese pilar y sumá 1. Las series numeradas hacen que la gente siga la cuenta para ver la próxima.

## Cómo elegir el tema de cada pilar

1. Mirá `IDEAS.md`: tomá la primera idea del pilar que no esté marcada como usada. Podés elegir otra de la lista si hoy hay un motivo (algo relacionado salió en las noticias).
2. Si no queda ninguna, buscá una nueva con el mismo criterio y agregá 3 más a la lista para los días siguientes.
3. Al publicar, marcá la idea como usada en `IDEAS.md` (`- [x] ... (AAAA-MM-DD)`).
4. Nunca repitas un tema que ya esté en `historial.json`.

## Verificación (no se negocia)

- **Tips**: cada dato tiene que estar en la documentación oficial (`code.claude.com/docs`, `docs.claude.com`, `support.claude.com`) leída hoy con WebFetch. Comandos, atajos y nombres de archivos, exactos. Si la doc cambió y el tip ya no aplica, elegí otro.
- **Historia**: fechas, nombres y cifras confirmados en al menos 2 fuentes serias (Wikipedia + museo, universidad, paper original o medio reconocido). Si las fuentes no coinciden, contá solo lo que coincide o elegí otro tema. Nada de anécdotas dudosas presentadas como hechos: si es una leyenda, se dice que es una leyenda.
- **Negocio / plata**: ejemplos realistas y concretos. **Nunca prometer ingresos ni inventar cifras** ("ganá USD 5.000 por mes"). Si se da un número, tiene fuente. Nada de esquemas, cripto, apuestas ni "ingresos pasivos". Lo que se muestra se tiene que poder hacer de verdad. Los casos de tobdev son reales (pipeline de landings, este reel automático); no inventar clientes ni resultados.
- **Noticias**: igual que siempre: fuente primaria o medio serio, leída con WebFetch, nada de rumores.
- **Uso**: tareas reales de un negocio (turnos, presupuestos, WhatsApp, reseñas, stock); las herramientas que se nombran tienen que existir y hacer eso. Sin precios salvo que estén verificados hoy.

## Lo que hace crecer la cuenta

- **Gancho en el primer segundo**: el primer beat tiene que frenar el scroll. Fórmulas que funcionan:
  - Error común: "Si usás Claude Code así, estás perdiendo tiempo."
  - Dato sorprendente: "El primer mensaje entre dos computadoras se colgó a la segunda letra."
  - Resultado: "Escribís una frase y te arma la presentación entera."
  - Contradicción: "La IA más usada del mundo no la hizo ninguna de las empresas que pensás." (solo si es verdad)
  - Nunca: "Hoy les traigo…", "¿Sabías que…?" como arranque flojo, ni preguntas genéricas.
- **Un reel = una idea.** Mejor un tip bien explicado que tres a medias.
- **Llamado a la acción según el pilar** (va en el beat de cierre, con voz, distinto cada día):
  - `tip`: guardar ("Guardalo para cuando lo necesites").
  - `historia`: comentar ("¿Lo sabías? Contámelo en los comentarios").
  - `negocio`: compartir ("Mandáselo a quien siempre dice que quiere emprender").
  - `noticia` y `uso`: comentar u opinar ("¿Lo usarías en tu negocio?").
  - Nunca prometer mandar algo por mensaje directo si comentan: no hay nada que lo mande.
- **Caption**: primera línea = el gancho (≤90 caracteres). Después 2–4 líneas que amplían (valor que no está en el video, así lo guardan). Cerrar con la pregunta o el llamado a la acción del pilar, la fuente si hay, "Seguí a @tobdev.ia" y 4–6 hashtags del pilar.
- **Hashtags por pilar** (más 1–2 del tema):
  - `tip`: #claudecode #claude #ia #programacion #productividad
  - `noticia` / `uso`: #inteligenciaartificial #IA #automatizacion #pymes
  - `historia`: #historiadelatecnologia #inteligenciaartificial #curiosidades #tecnologia
  - `negocio`: #emprender #inteligenciaartificial #negociosdigitales #freelance
