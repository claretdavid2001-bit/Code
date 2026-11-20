"""Descarga de precios (Yahoo Finance) y conversión a EUR."""
from __future__ import annotations

import concurrent.futures as cf
import time

import numpy as np
import pandas as pd
import yfinance as yf

from .universo import es_usd


def descargar_precios(tickers: list[str], periodo: str = "3y") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (cierres ajustados, volúmenes) con columnas = tickers válidos."""
    raw = yf.download(tickers, period=periodo, interval="1d", auto_adjust=True,
                      progress=False, threads=True, group_by="column")
    close = raw["Close"].dropna(axis=1, thresh=200)
    vol = raw["Volume"].reindex(columns=close.columns)
    return close, vol


def eurusd(periodo: str = "3y") -> pd.Series:
    s = yf.download("EURUSD=X", period=periodo, interval="1d", auto_adjust=True, progress=False)["Close"]
    return s.squeeze().rename("EURUSD")


def rentabilidades_eur(close: pd.DataFrame, fx: pd.Series) -> pd.DataFrame:
    """Log-rentabilidades diarias en EUR (las de EE. UU. se convierten con EURUSD)."""
    lr = {}
    fx = fx.reindex(close.index).ffill()
    for t in close.columns:
        p = close[t].dropna()
        if es_usd(t):
            p = (p / fx.reindex(p.index)).dropna()
        lr[t] = np.log(p).diff()
    return pd.DataFrame(lr).dropna(how="all")


_CAMPOS = ["shortName", "sector", "industry", "marketCap", "currency", "trailingPE", "forwardPE",
           "priceToBook", "returnOnEquity", "profitMargins", "operatingMargins", "debtToEquity",
           "revenueGrowth", "earningsGrowth", "freeCashflow", "dividendYield", "payoutRatio",
           "beta", "recommendationMean", "targetMeanPrice", "currentPrice", "numberOfAnalystOpinions"]


def _info(t: str) -> dict:
    for intento in range(3):
        try:
            i = yf.Ticker(t).info or {}
            if i:
                return {"ticker": t, **{c: i.get(c) for c in _CAMPOS}}
        except Exception:
            time.sleep(1 + 2 * intento)
    return {"ticker": t}


def fundamentales(tickers: list[str]) -> pd.DataFrame:
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        filas = list(ex.map(_info, tickers))
    df = pd.DataFrame(filas).set_index("ticker")
    for c in df.columns:
        if c not in ("shortName", "sector", "industry", "currency"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df
