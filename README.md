# TFM — sistema multiagente de revisión

Siete agentes de Claude Code que revisan el TFM y se pasan el trabajo a través de la carpeta `revision/` (pizarra compartida con formato de hallazgos común).

```
            ┌─ tfm-normativa   (PGC/NIIF/NIA-ES/LIS, vigencia, citas exactas)
            ├─ tfm-metodologia (objetivos ↔ conclusiones, estructura)
 Fase 1 ────┼─ tfm-bibliografia(citas ↔ referencias, fuentes, plagio)      → revision/01..05
 (paralelo) ├─ tfm-datos       (recálculo, asientos, Excel)
            └─ tfm-redaccion   (estilo, terminología, glosario)
                     │
 Fase 2 ──── tfm-tribunal (lee todo, ataca el fondo, rúbrica, preguntas defensa) → 06
                     │  discrepancias
 Fase 2b ─── réplica de los agentes cuestionados
                     │
 Fase 3 ──── tfm-integrador (deduplica, resuelve conflictos, prioriza)
              → INFORME_INTEGRADO.md + seguimiento_hallazgos.xlsx
```

## Uso
1. Rellena los `<PENDIENTE>` de `CLAUDE.md`.
2. Sube el TFM a `tfm/` (`.docx` o `.md`; anexos `.xlsx`). Opcional: guía de TFM de la universidad.
3. En Claude Code: `/revisar-tfm` (todo) o `/revisar-tfm cap3.docx`.
4. Marca estados en el Excel y ejecuta `/aplicar-correcciones Alta`.
5. Repite `/revisar-tfm`: la nueva ronda se compara con `revision/historico/`.

Agentes sueltos: "usa el agente tfm-tribunal sobre el capítulo 4".
