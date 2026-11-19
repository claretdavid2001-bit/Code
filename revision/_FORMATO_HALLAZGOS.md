# Formato común de hallazgos (obligatorio para todos los agentes)

Cada agente escribe `revision/NN-<agente>.md` con esta estructura:

```markdown
# Informe <agente> — <fecha>
Alcance revisado: <ficheros / capítulos>
Resumen: <3-5 líneas>

| ID | Sev. | Ubicación | Hallazgo | Fundamento | Propuesta de corrección | Confianza |
|----|------|-----------|----------|------------|-------------------------|-----------|
| NOR-01 | Alta | cap2.md §2.3, párr. 4 | ... | NRV 9ª.2.1 PGC | Texto sustitutivo: "..." | Alta |
```

- **ID**: prefijo del agente (NOR, MET, BIB, DAT, RED, TRI) + número.
- **Severidad**:
  - **Alta**: error técnico/normativo, cifra que no cuadra, incoherencia objetivos–conclusiones, plagio/cita ausente. Puede suspender.
  - **Media**: debilita la calidad o la defensa (argumento incompleto, fuente secundaria donde debería ser primaria).
  - **Baja**: estilo, formato, erratas.
- **Ubicación**: fichero + apartado + párrafo/tabla, lo bastante precisa para localizarlo.
- **Propuesta**: siempre accionable; si es redacción, dar el texto alternativo.
- **Confianza**: Alta / Media / Baja. Si depende de juicio o de interpretación no pacífica, decirlo y marcar "Juicio".
- Sección final **"Para otros agentes"**: cuestiones detectadas fuera del propio ámbito (p. ej., el revisor de datos ve una cita mal → la deriva a BIB).
