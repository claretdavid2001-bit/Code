# Radar de oportunidades

Sistema diario de análisis de acciones (IBEX 35, Euro Stoxx 50 y S&P 500) con un motor cuantitativo y cinco agentes especializados.

**Página del informe:** https://claude.ai/artifact/XTDVNKHjZtnA92MN4S63Jg

## Flujo diario (`/radar`)
1. **Motor** (`python3 -m mercados.motor`): descarga 3 años de precios y los fundamentales de unos 540 valores, puntúa por horizonte (corto: 15 sesiones; medio: 63; largo: 252) y pasa los 25 mejores de cada horizonte a Monte Carlo, con **10.000 escenarios por valor y horizonte** (750.000 al día).
2. **Agentes** (`.claude/agents/`):
   - `analista-tecnico`: tendencia, momentum, soportes y resistencias; ajusta el stop y el objetivo.
   - `analista-fundamental`: calidad y valoración relativa al sector; detecta datos erróneos y trampas de valor.
   - `analista-noticias-macro`: noticias de 72 h, fechas de resultados, OPA y agenda del BCE y la Fed.
   - `gestor-riesgos`: veta por eventos binarios, concentración, correlación y divisa.
   - `director-inversiones`: veredicto COMPRAR, VIGILAR o DESCARTAR, con convicción de 1 a 5 y un porqué breve.
3. **Salidas** (`salidas/<fecha>/`): `candidatos.json`, `veredictos.json`, `informe.xlsx` (fórmulas vivas y hoja de cuadre) e `informe.html`. Se publica en la URL fija.

## Monte Carlo (`mercados/montecarlo.py`)
- Bootstrap por bloques de 5 sesiones sobre las rentabilidades reales en EUR (las de EE. UU. se convierten con EUR/USD). Conserva las colas gruesas y el agrupamiento de volatilidad.
- Re-escalado a la volatilidad actual (EWMA con λ 0,94).
- Deriva prudente: 70 % de prior de mercado (7 % anual) y 30 % de media histórica, topada en ±40 %.
- Métricas: P(ganancia), P(objetivo antes que stop), P(stop antes), esperanza, P5, P50, P95 y CVaR95.

## Perfil moderado (`mercados/motor.py`)
Riesgo del 1 % del capital por idea y tope del 5 % por posición. Filtros: P(ganancia) ≥ 50 %, P(stop) ≤ 40 % y esperanza > 0.

## Limitaciones (importante)
- Las probabilidades salen de un **modelo**: suponen que la distribución de los últimos 3 años sigue siendo válida. No recogen saltos sin precedente (resultados, OPA, regulación); de eso se ocupan los agentes de noticias y de riesgos.
- Los datos de Yahoo Finance contienen errores (PER, ROE); el analista fundamental los marca.
- No es asesoramiento financiero. Tras unas semanas de histórico en `salidas/`, conviene medir la calibración: si las ideas con un 60 % de probabilidad aciertan de verdad alrededor del 60 %.
