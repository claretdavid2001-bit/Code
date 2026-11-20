"""Indicadores técnicos y de momentum sobre el universo completo (cálculo vectorizado)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def rsi(close: pd.DataFrame, n: int = 14) -> pd.DataFrame:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def tabla_indicadores(close: pd.DataFrame, vol: pd.DataFrame, lr_eur: pd.DataFrame) -> pd.DataFrame:
    c = close.ffill()
    ult = c.iloc[-1]
    sma20, sma50, sma200 = (c.rolling(n).mean().iloc[-1] for n in (20, 50, 200))
    r = rsi(c)
    vol_d = lr_eur.iloc[-63:].std()
    t = pd.DataFrame({
        "precio": ult,
        "ret_1s": c.iloc[-1] / c.iloc[-6] - 1,
        "ret_1m": c.iloc[-1] / c.iloc[-22] - 1,
        "ret_3m": c.iloc[-1] / c.iloc[-64] - 1,
        "ret_6m": c.iloc[-1] / c.iloc[-127] - 1,
        "mom_12_1": c.iloc[-22] / c.iloc[-253] - 1,       # momentum 12m excluyendo último mes
        "dist_sma20": ult / sma20 - 1,
        "dist_sma50": ult / sma50 - 1,
        "dist_sma200": ult / sma200 - 1,
        "tendencia": (sma50 > sma200).astype(int),
        "rsi14": r.iloc[-1],
        "rsi14_prev": r.iloc[-4],
        "max_20d": (ult >= c.iloc[-21:-1].max()).astype(int),
        "vol_rel": vol.iloc[-5:].mean() / vol.iloc[-60:].mean(),
        "vol_anual": vol_d * np.sqrt(252),
        "drawdown_1a": ult / c.iloc[-252:].max() - 1,
        "atr_pct": (c.diff().abs().rolling(14).mean().iloc[-1]) / ult,
    })
    return t.replace([np.inf, -np.inf], np.nan)


def z(s: pd.Series) -> pd.Series:
    """z-score winsorizado a ±3."""
    s = s.astype(float)
    return ((s - s.mean()) / s.std()).clip(-3, 3).fillna(0)
