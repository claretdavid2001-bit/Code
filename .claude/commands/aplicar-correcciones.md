---
description: Aplica al TFM los hallazgos aceptados del seguimiento y relanza la verificación
argument-hint: "[severidad mínima: Alta|Media|Baja] (por defecto Alta)"
---

1. Lee `revision/seguimiento_hallazgos.xlsx` y `revision/INFORME_INTEGRADO.md`. Toma los hallazgos con Estado ≠ "Descartado" y severidad ≥ $ARGUMENTS (por defecto Alta), excluyendo los marcados "Decisión del autor" sin comentario del autor.
2. Si el TFM está en `.docx`, NO lo sobrescribas: genera `tfm/_corregido/<nombre>.docx` con control de cambios (python-docx: inserciones/borrados como revisiones w:ins/w:del) para que el autor acepte o rechace en Word. Si está en `.md`, edita directamente (git guarda el histórico).
3. Marca en el xlsx los aplicados como "Resuelto" con comentario "Aplicado automáticamente — revisar".
4. Relanza solo los agentes afectados en modo verificación sobre las zonas modificadas (en paralelo) y comunica al usuario lo que queda abierto.
