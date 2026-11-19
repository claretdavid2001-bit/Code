---
description: Revisión multiagente del TFM (5 revisores en paralelo → tribunal → integrador)
argument-hint: "[capítulo o fichero opcional, p. ej. cap3.md]"
---

Orquesta la revisión del TFM con los agentes de `.claude/agents/`. Alcance: $ARGUMENTS (si está vacío, TFM completo en `tfm/`).

## Fase 0 — Preparación
1. Si hay `.docx` en `tfm/`, ejecuta `bash tools/docx2md.sh`.
2. Si `tfm/` está vacío, detente y pide al usuario que suba el TFM.
3. Si ya existen informes en `revision/0*-*.md`, muévelos a `revision/historico/<fecha-hora>/` (incluido `INFORME_INTEGRADO.md` y el xlsx) para permitir comparar rondas.
4. Si `CLAUDE.md` tiene campos `<PENDIENTE>` relevantes (marco normativo, fecha de corte, norma de citación), avisa al usuario pero continúa con supuestos razonables declarados.

## Fase 1 — Revisión especializada (EN PARALELO, un único mensaje con 5 llamadas Agent)
Lanza a la vez, indicando a cada uno el alcance:
- `tfm-normativa` → `revision/01-normativa.md`
- `tfm-metodologia` → `revision/02-metodologia.md`
- `tfm-bibliografia` → `revision/03-bibliografia.md`
- `tfm-datos` → `revision/04-datos.md`
- `tfm-redaccion` → `revision/05-redaccion.md`

Espera a que terminen todos. Comprueba que existen los 5 ficheros; si falta alguno, relanza ese agente una vez.

## Fase 2 — Contraste (tribunal)
Lanza `tfm-tribunal`. Lee el TFM y los 5 informes, los cuestiona y escribe `revision/06-tribunal.md`.

## Fase 2b — Réplica (solo si hay "Discrepancias con fase 1")
Para cada agente cuestionado por el tribunal, relánzalo con la instrucción: "Lee la sección 'Discrepancias con fase 1' de revision/06-tribunal.md que afecta a tus IDs. Ratifica, corrige o retira cada hallazgo con motivación, y añade una sección 'Réplica al tribunal' al final de tu informe". Lanza las réplicas en paralelo.

## Fase 3 — Integración
Lanza `tfm-integrador` → `revision/INFORME_INTEGRADO.md` + `revision/seguimiento_hallazgos.xlsx`.

## Cierre
Muestra al usuario: nota estimada, top 10 acciones, decisiones pendientes del autor y rutas de los entregables. No modifiques el texto del TFM salvo que el usuario lo pida expresamente.
