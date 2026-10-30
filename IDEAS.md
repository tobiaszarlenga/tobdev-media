# Banco de ideas

Ideas para los días sin noticia y para cada pilar. **Antes de usar cualquiera, verificá los datos** según `CONTENIDO.md` (las que dicen "verificar" tienen datos que todavía nadie confirmó). Marcá las usadas con `[x]` y la fecha. Cuando un pilar tenga menos de 3 ideas libres, agregá nuevas.

## tip (lunes) — Claude, Claude Code, API

- [x] CLAUDE.md y `/init`: dejarle escrito cómo es tu proyecto para no explicarlo en cada sesión (2026-10-19)
- [x] Modo plan: que primero arme el plan y recién después toque código (2026-10-26)
- [ ] `/clear` y `/compact`: no llenar el contexto con conversaciones viejas (verificar qué hace cada uno)
- [ ] Volver atrás: deshacer lo que hizo Claude Code en una sesión (verificar atajo o comando de rewind/checkpoints)
- [ ] Pegarle una captura de pantalla para que entienda el error o el diseño (verificar cómo se pega en la terminal)
- [ ] Skills: enseñarle un procedimiento una vez y que lo use siempre (verificar en la doc de skills)
- [ ] Hooks: bloquear acciones que nunca querés que haga, por ejemplo tocar un archivo (la doc menciona PreToolUse)
- [ ] Subagentes: dividir una tarea grande en partes (verificar en la doc)
- [ ] `CLAUDE.local.md`: preferencias tuyas que no se suben al repo (está en la doc de memoria)
- [ ] `.claude/rules/`: reglas que solo cargan para ciertos archivos (está en la doc de memoria)
- [ ] Modo no interactivo (`claude -p`) para usarlo en scripts (verificar)
- [ ] Proyectos en claude.ai: subir tus archivos una vez y que los use en cada chat (verificar en support.claude.com)

## historia (miércoles)

- [x] 1969: el primer mensaje de ARPANET iba a ser "LOGIN" y el sistema se colgó después de "LO" (2026-10-21)
- [x] 1947: el "primer bug" fue una polilla real pegada en el cuaderno del Harvard Mark II (2026-10-28)
- [ ] 1966: ELIZA, el primer chatbot, y la gente que se encariñó con un programa de pocas reglas (verificar)
- [ ] 1950: Turing propone el "juego de la imitación" (verificar)
- [ ] 1956: la conferencia de Dartmouth y el nacimiento del término "inteligencia artificial" (verificar)
- [ ] 1920: la palabra "robot" viene de una obra de teatro checa (R.U.R., Karel Čapek) (verificar)
- [ ] 1843: Ada Lovelace y el primer algoritmo pensado para una máquina (verificar)
- [ ] 1997: Deep Blue le gana a Kasparov (verificar)
- [ ] 2016: AlphaGo y la jugada 37 (verificar)
- [ ] 2017: "Attention Is All You Need", el paper de donde sale la T de GPT (verificar)
- [ ] 1991: la primera página web todavía está online (verificar)
- [ ] 2011: Watson gana Jeopardy! (verificar)

## negocio (viernes) — plata y casos con IA

- [x] Detrás de escena: este reel lo hace un agente de IA solo, todos los días (busca el tema, escribe el guion, pone la voz, edita y publica). Real: es este mismo sistema. (2026-10-20)
- [ ] Detrás de escena: cómo tobdev arma la landing de un comercio con agentes de IA (real: pipeline de tobdev; sin nombrar clientes)
- [x] 5 servicios con IA que le podés vender a un comercio de tu barrio (landing, turnos por WhatsApp, reels, presupuestos, respuestas a reseñas) (2026-10-23)
- [ ] Cobrar por mes en vez de una sola vez: por qué conviene cobrar una cuota por un servicio con IA
- [ ] El error de prometer de más: qué no hace la IA y conviene aclararlo antes de venderla
- [ ] Cómo conseguir el primer cliente: mostrarle una demo hecha con sus datos públicos (sin usar datos privados)
- [ ] Freelance con IA: hacer en una tarde lo que antes llevaba una semana, y qué hacer con ese tiempo

## marca (viernes, una semana sí y una no) — trabajos reales de TobDev

Formatos y escenas en `plantilla/ESCENAS.md` → "Estilo marca". Proyectos y lo que se puede decir de cada uno: `portfolio/sitios.json`. Rotá formato y proyecto protagonista (no el mismo dos veces seguidas). **Solo proyectos con `"permiso": true` en `sitios.json`**: si una idea nombra uno que no lo tiene, salteala.

- [x] Problema → marca → trabajos: "Tu negocio no debería depender de seis apps y una planilla rota" (`guiones/marca-sistemas.json`, lo subió Tob a mano) (2026-10-25)
- [x] Suspenso: "Este cursor está a punto de hacer clic" (`guiones/marca-clic.json`, lo subió Tob a mano) (2026-10-25)
- [x] Caso real: "Este pedido llegó completo" con El Gordo Burger (`guiones/marca-pedido.json`, lo subió Tob a mano) (2026-10-25)
- [x] Oferta: "Mirá tu página web antes de pagarla" (demo gratis en 24 h, desde $175.000, hosting incluido; `boceto` → sitios → `numero`) (`guiones/marca-demo.json`, 2026-10-30, lo sube Tob a mano)
- [ ] Caso real: Liga Infantil YB, los veedores cargan el resultado y la tabla de posiciones se arma sola (sitio duo con escritorio → posiciones)
- [ ] Caso real: Certificador de Obras, el medidor dicta "revoque al 70" desde el celular y se carga aunque no haya señal (sitio con `celular-medir`, chips "Carga por voz" / "Funciona sin señal")
- [ ] Suspenso: un dedo a punto de tocar "Inscribí tu equipo" (Torneo JOGO) y la inscripción que llega por WhatsApp
- [ ] Problema → trabajos: "Tu negocio vive en Instagram y nadie encuentra el precio" → carrusel de páginas con carta, catálogo y botón de WhatsApp (Casa Pan, El Gordo Burger, D12tinto, Malala)
- [ ] Problema → marca: "Tu obra se sigue en un Excel que solo entiende una persona" → Certificador (planilla → logo → sitio)
- [ ] Rubros: "¿Tenés una ortopedia, un laboratorio o una marca de ropa?" → un sitio por rubro con scroll (Férulas Tuc, Infinity Labs, D12tinto)

## ensayo (miércoles por medio) — ideas con nombre propio, formato ensayo (ver CONTENIDO.md)

- [x] El valle inquietante (Mori, 1970) y el riesgo de usar la IA para todo (MIT "Your Brain on ChatGPT"; Microsoft Research, CHI 2025) (2026-10-29, `guiones/2026-10-29-valle.json`, lo sube Tob a mano)
- [ ] Efecto ELIZA (1966): por qué le atribuimos entendimiento a un programa que solo devuelve patrones, y qué pasa cuando le contamos la vida a un chatbot (verificar: Weizenbaum, y un estudio reciente sobre vínculos con chatbots)
- [ ] Sesgo de automatización: cuando la máquina sugiere, dejamos de mirar (verificar: estudios en aviación o medicina; ejemplo de GPS)
- [ ] La paradoja de la automatización (Bainbridge, 1983): cuanto más automatizás, más importante es el humano que queda (verificar)
- [ ] Ley de Goodhart: cuando la métrica se vuelve el objetivo, deja de servir (y qué pasa con los textos "optimizados" por IA) (verificar)
- [ ] Efecto Google (Sparrow, 2011): recordamos dónde está la información, no la información; ¿qué pasa ahora con la IA? (verificar)
- [ ] Sesgo de fluidez: lo que suena bien nos parece verdadero, y la IA siempre suena bien (verificar: estudios de fluidez de procesamiento)

## uso (martes o jueves sin noticia) — IA en tu negocio

- [x] Contestar consultas de WhatsApp fuera de horario (2026-10-29, `guiones/2026-10-29-turnos-whatsapp.json`, lo sube Tob a mano)
- [ ] Armar presupuestos en minutos a partir de una lista de precios
- [ ] Responder reseñas de Google con el tono del negocio
- [ ] Resumir audios largos de clientes o proveedores
- [ ] Escribir descripciones de productos para la tienda online
- [ ] Ordenar facturas y gastos del mes
- [ ] Detectar las preguntas que más te hacen y armar las respuestas frecuentes
