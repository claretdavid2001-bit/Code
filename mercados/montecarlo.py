"""Simulación Monte Carlo: bootstrap por bloques con volatilidad filtrada (FHS-lite).

Por valor y horizonte se generan N trayectorias diarias (por defecto 10.000):
  1. Residuos históricos (3 años, en EUR) sin media -> conserva colas gruesas y asimetría.
  2. Re-escalado a la volatilidad actual (EWMA λ=0,94 / vol histórica) -> régimen actual.
  3. Remuestreo por bloques de 5 sesiones -> conserva agrupamiento de volatilidad.
  4. Deriva prudente: 30 % media histórica (topada ±40 % anual) + 70 % prior de mercado (7 % anual).
     Evita extrapolar rachas pasadas (sesgo de los ganadores recientes).

Juicio: las probabilidades dependen del modelo; no son frecuencias garantizadas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

PRIOR_ANUAL = 0.07
PESO_HIST = 0.30
TOPE_HIST = 0.40
BLOQUE = 5


def _deriva_diaria(r: np.ndarray) -> float:
    hist = np.clip(r.mean() * 252, -TOPE_HIST, TOPE_HIST)
    anual = PESO_HIST * hist + (1 - PESO_HIST) * PRIOR_ANUAL
    return anual / 252


def _vol_ewma(r: np.ndarray, lam: float = 0.94) -> float:
    v = r[:20].var()
    for x in r[20:]:
        v = lam * v + (1 - lam) * x * x
    return float(np.sqrt(v))


def simular(r: pd.Series, horizonte: int, objetivo: float, stop: float,
            n: int = 10_000, semilla: int = 42) -> dict:
    """objetivo y stop en tanto por uno (p.ej. 0.15 y -0.08). Devuelve métricas de la distribución."""
    r = r.dropna().to_numpy()[-756:]
    rng = np.random.default_rng(semilla)
    mu = _deriva_diaria(r)
    resid = r - r.mean()
    escala = np.clip(_vol_ewma(r) / r.std(), 0.5, 2.5)
    resid = resid * escala

    nb = int(np.ceil(horizonte / BLOQUE))
    ini = rng.integers(0, len(resid) - BLOQUE, size=(n, nb))
    idx = (ini[:, :, None] + np.arange(BLOQUE)).reshape(n, -1)[:, :horizonte]
    caminos = np.cumsum(resid[idx] + mu, axis=1)          # log-rentabilidad acumulada
    final = np.expm1(caminos[:, -1])

    lo, hi = np.log1p(stop), np.log1p(objetivo)
    t_obj = np.where((caminos >= hi).any(1), (caminos >= hi).argmax(1), horizonte + 1)
    t_stp = np.where((caminos <= lo).any(1), (caminos <= lo).argmax(1), horizonte + 1)
    p_obj = float(np.mean(t_obj < t_stp))
    p_stp = float(np.mean(t_stp < t_obj))
    resto = (t_obj > horizonte) & (t_stp > horizonte)
    e_resto = float(final[resto].mean()) if resto.any() else 0.0

    q5 = np.quantile(final, 0.05)
    return {
        "escenarios": n,
        "p_ganancia": float(np.mean(final > 0)),
        "p_objetivo": p_obj,
        "p_stop": p_stp,
        "p_ninguno": 1 - p_obj - p_stp,
        "ret_ninguno": e_resto,
        "ret_esperado": float(final.mean()),
        "p5": float(q5),
        "p50": float(np.median(final)),
        "p95": float(np.quantile(final, 0.95)),
        "cvar95": float(final[final <= q5].mean()),
        "esperanza_operativa": p_obj * objetivo + p_stp * stop + (1 - p_obj - p_stp) * e_resto,
        "vol_escala": float(escala),
    }
