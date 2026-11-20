---
description: Ejecuta el Radar de oportunidades diario (motor cuantitativo + 5 agentes) y publica la página
---
Ejecuta el informe diario del Radar de oportunidades. Responde siempre en español.

1. **Dependencias.** `pip install -q -r requirements.txt`
2. **Motor cuantitativo.** `python3 -m mercados.motor --n 10000 --top 25` (unos 3 minutos). Anota la carpeta `salidas/<fecha>` que imprime. Si falla la descarga de datos, para y avisa.
3. **Análisis en paralelo.** Lanza en un mismo mensaje estos subagentes, pasándoles la ruta de `candidatos.json`:
   - `analista-tecnico` con el horizonte `corto`
   - `analista-tecnico` con el horizonte `medio`
   - `analista-fundamental` con los horizontes `largo` y `medio`
   - `analista-noticias-macro` con la unión de los 6 primeros candidatos aptos de cada horizonte
4. **Riesgos.** Lanza `gestor-riesgos` con las salidas anteriores, incluidas las fechas de resultados.
5. **Decisión.** Lanza `director-inversiones` con todo lo anterior. Debe escribir `salidas/<fecha>/veredictos.json`.
6. **Página.** `python3 -m mercados.pagina salidas/<fecha>`. Genera `publicado/radar.html`.
7. **Publicación.** Lee el artefacto con la herramienta Artifact (`action: "read"`, URL en `RADAR_URL.txt`) y después publica `publicado/radar.html` en esa misma URL.
8. **Registro.** Haz commit de `salidas/<fecha>/` y `publicado/radar.html` con el mensaje "Radar <fecha>" y súbelo a la rama de trabajo. El histórico permite medir después el acierto real de las probabilidades.
9. **Respuesta final.** Como máximo 8 líneas: las ideas COMPRAR de cada horizonte con su ticker, la probabilidad de ganancia y el motivo en 10 palabras, y el enlace.
