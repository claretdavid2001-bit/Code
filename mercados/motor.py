"""Motor cuantitativo diario: cribado -> Monte Carlo -> ranking por horizonte.

Uso:  python -m mercados.motor [--n 10000] [--top 25] [--salida salidas]
Genera salidas/<fecha>/candidatos.json y salidas/<fecha>/informe.xlsx
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

from . import datos, edgar, montecarlo
from .indicadores import tabla_indicadores, z
from .universo import UNIVERSO, mercado

# Perfil moderado
RIESGO_OPERACION = 0.01   # pérdida máx. por idea si salta el stop (1 % del capital)
TOPE_POSICION = 0.05      # máx. 5 % del capital por idea
P_GANANCIA_MIN = 0.50
P_STOP_MAX = 0.40

HORIZONTES = {
    "corto": {"etiqueta": "Corto (3 semanas)", "dias": 15},
    "medio": {"etiqueta": "Medio (3 meses)", "dias": 63},
    "largo": {"etiqueta": "Largo (12 meses)", "dias": 252},
}


def niveles(h: str, fila: pd.Series) -> tuple[float, float]:
    """(objetivo, stop) en tanto por uno, escalados a la volatilidad del valor en el horizonte. Ratio beneficio/riesgo 1,5:1."""
    sig = fila.vol_anual * np.sqrt(HORIZONTES[h]["dias"] / 252)
    lim = {"corto": (0.03, 0.08), "medio": (0.06, 0.15), "largo": (0.15, 0.30)}[h]
    stop = -float(np.clip(0.8 * sig, *lim))
    return 1.5 * -stop, stop


def puntuar(ind: pd.DataFrame, fund: pd.DataFrame) -> dict[str, pd.Series]:
    s = {}
    rebote = ((ind.rsi14.between(40, 65)) & (ind.rsi14 > ind.rsi14_prev)).astype(float)
    corto = (0.30 * z(ind.ret_1m) + 0.20 * z(ind.vol_rel) + 0.50 * ind.max_20d + 0.50 * rebote
             + 0.30 * (ind.dist_sma50 > 0) - 0.20 * z(ind.vol_anual))
    s["corto"] = corto[(ind.rsi14 < 75) & (ind.dist_sma200 > 0)]

    medio = (0.40 * z(ind.mom_12_1) + 0.30 * z(ind.ret_6m) + 0.50 * ind.tendencia
             - 0.20 * z(ind.vol_anual) + 0.20 * z(ind.drawdown_1a))
    s["medio"] = medio[(ind.ret_1m < 0.25) & (ind.tendencia == 1)]

    f = fund.reindex(ind.index)
    pe = f.forwardPE.where(f.forwardPE > 0)
    fcf_y = f.freeCashflow / f.marketCap
    upside = f.targetMeanPrice / f.currentPrice - 1
    sect = f.sector.fillna("NA")
    zs = lambda x: x.groupby(sect).transform(lambda g: (g - g.mean()) / g.std() if g.count() > 2 else g * 0).clip(-3, 3).fillna(0)
    largo = (0.20 * zs(-pe) + 0.20 * zs(fcf_y) + 0.15 * z(f.returnOnEquity) + 0.10 * z(f.profitMargins)
             + 0.10 * z(f.revenueGrowth) - 0.10 * z(f.debtToEquity) + 0.10 * z(upside)
             + 0.15 * z(ind.mom_12_1) - 0.10 * z(ind.vol_anual))
    s["largo"] = largo[pe.notna() & (f.marketCap > 5e9)]
    return s


def ejecutar(n: int = 10_000, top: int = 25, salida: str = "salidas") -> Path:
    hoy = dt.date.today().isoformat()
    out = Path(salida) / hoy
    out.mkdir(parents=True, exist_ok=True)

    close, vol = datos.descargar_precios(UNIVERSO)
    fx = datos.eurusd()
    lr = datos.rentabilidades_eur(close, fx)
    ind = tabla_indicadores(close, vol, lr)
    fund = datos.fundamentales(list(close.columns))
    scores = puntuar(ind, fund)

    resultado = {"fecha": hoy, "fecha_datos": str(close.index[-1].date()), "universo_valido": int(close.shape[1]),
                 "escenarios_por_valor": n, "parametros": {
                     "riesgo_operacion": RIESGO_OPERACION, "tope_posicion": TOPE_POSICION,
                     "p_ganancia_min": P_GANANCIA_MIN, "p_stop_max": P_STOP_MAX,
                     "deriva_prior_anual": montecarlo.PRIOR_ANUAL, "peso_media_historica": montecarlo.PESO_HIST},
                 "horizontes": {}}
    total_esc = 0
    for h, cfg in HORIZONTES.items():
        cand = scores[h].sort_values(ascending=False).head(top)
        filas = []
        for t, sc in cand.items():
            i = ind.loc[t]
            obj, stp = niveles(h, i)
            m = montecarlo.simular(lr[t], cfg["dias"], obj, stp, n=n, semilla=zlib.crc32(f"{t}|{h}".encode()))
            total_esc += n
            fi = fund.loc[t] if t in fund.index else pd.Series(dtype=object)
            filas.append({
                "ticker": t, "nombre": fi.get("shortName") or t, "mercado": mercado(t),
                "sector": fi.get("sector"), "precio": round(float(i.precio), 4), "divisa": fi.get("currency"),
                "puntuacion_factores": float(sc), "objetivo_pct": obj, "stop_pct": stp,
                "precio_objetivo": float(i.precio * (1 + obj)), "precio_stop": float(i.precio * (1 + stp)),
                "peso_sugerido": float(min(TOPE_POSICION, RIESGO_OPERACION / -stp)),
                "indicadores": {k: (None if pd.isna(v) else float(v)) for k, v in i.items()},
                "fundamentales": {k: (None if pd.isna(v) else (float(v) if isinstance(v, (int, float, np.number)) else v))
                                  for k, v in fi.items()},
                **m,
            })
        edgar.verificar(filas)
        df = pd.DataFrame(filas)
        df["rentab_riesgo"] = df.esperanza_operativa / df.cvar95.abs()
        df["puntuacion_final"] = 0.5 * z(df.puntuacion_factores) + 0.5 * z(df.rentab_riesgo)
        df["apto_perfil"] = ((df.p_ganancia >= P_GANANCIA_MIN) & (df.p_stop <= P_STOP_MAX)
                             & (df.esperanza_operativa > 0) & (df.verificacion != "DISCREPANCIA"))
        df = df.sort_values(["apto_perfil", "puntuacion_final"], ascending=False)
        resultado["horizontes"][h] = {"etiqueta": cfg["etiqueta"], "dias": cfg["dias"],
                                      "candidatos": json.loads(df.to_json(orient="records"))}
    resultado["escenarios_totales"] = total_esc

    # Contexto de mercado para el agente macro
    resultado["mercado"] = {
        "amplitud_sobre_sma200": float((ind.dist_sma200 > 0).mean()),
        "ret_1m_mediano": float(ind.ret_1m.median()),
        "vol_mediana": float(ind.vol_anual.median()),
        "eurusd": float(fx.iloc[-1]),
        "cobertura_fundamentales": float(fund.attrs.get("cobertura", 1.0)),
        "sin_fundamentales": fund.attrs.get("sin_datos", []),
    }
    (out / "candidatos.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1, default=str))
    from .excel import generar_excel
    generar_excel(resultado, out / "informe.xlsx")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10_000)
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--salida", default="salidas")
    a = ap.parse_args()
    print(ejecutar(a.n, a.top, a.salida))
