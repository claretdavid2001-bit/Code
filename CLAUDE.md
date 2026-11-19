# TFM — instrucciones del proyecto

## Datos del TFM (rellenar)
- Título: <PENDIENTE>
- Máster / Universidad: <PENDIENTE>
- Tutor/a: <PENDIENTE>
- Marco normativo principal: PGC (RD 1514/2007) / NIIF-UE / NIA-ES / LIS (Ley 27/2014) — <ajustar>
- Fecha de corte normativo: <PENDIENTE> (normativa vigente a esta fecha)
- Norma de citación: APA 7 — <ajustar a la guía de la universidad>
- Extensión máxima: <PENDIENTE> palabras

## Estructura de carpetas
- `tfm/` → texto del TFM (`.md` o `.docx`, un fichero por capítulo idealmente) y anexos (`.xlsx`).
- `revision/` → informes que generan los agentes. Es la "pizarra compartida": cada agente lee los informes de los demás.
- `tools/` → utilidades (conversión docx→md).

## Convenciones
- Español técnico, conciso. Importes en euros, separador de miles con punto, decimales con coma.
- Toda afirmación normativa cita norma y apartado (NRV x.y PGC, NIC xx párr. yy, NIA-ES xxx apdo. yy, art. xx LIS, consulta ICAC BOICAC nº / DGT V0000-00).
- Lo que dependa de juicio profesional se marca expresamente como tal.

## Sistema de agentes
Ver `.claude/agents/` y ejecutar `/revisar-tfm` (revisión completa) o `/revisar-tfm <capítulo>`.
