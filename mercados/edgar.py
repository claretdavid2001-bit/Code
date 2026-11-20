"""Fundamentales oficiales de SEC EDGAR (XBRL companyfacts) y contraste con Yahoo Finance.

Fuente primaria: estados financieros presentados ante la SEC (10-K y 10-Q, US GAAP).
Solo cubre emisores que presentan en la SEC; los europeos siguen con Yahoo y revisión del analista.
Cálculo TTM: último ejercicio + acumulado del ejercicio en curso - mismo acumulado del ejercicio anterior.
"""
from __future__ import annotations

import datetime as dt
import time

import requests

UA = {"User-Agent": "RadarOportunidades research-bot admin@example.org"}
_cik_cache: dict[str, str] | None = None


def _get(url: str) -> dict | None:
    for i in range(3):
        try:
            r = requests.get(url, headers=UA, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(1 + 2 * i)
    return None


def cik(ticker: str) -> str | None:
    global _cik_cache
    if _cik_cache is None:
        d = _get("https://www.sec.gov/files/company_tickers.json") or {}
        _cik_cache = {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in d.values()}
    return _cik_cache.get(ticker.upper().replace(".", "-"))


def _d(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


FORMULARIOS = {"10-K", "10-Q", "10-K/A", "10-Q/A", "20-F", "40-F", "10-KT"}
MAX_ANTIGUEDAD = dt.timedelta(days=460)   # ~15 meses


def _hechos(facts: dict, conceptos: list[str], unidad: str = "USD") -> list[dict]:
    """Une los hechos de varios conceptos XBRL equivalentes (las empresas cambian de etiqueta con
    los años): por periodo, el primer concepto de la lista que lo tenga; dentro de él, la última
    presentación. Solo 10-K/10-Q. Devuelve [] si la serie resultante está desfasada (>15 meses)."""
    por_periodo: dict = {}
    for c in conceptos:
        for tax in ("us-gaap", "dei"):
            u = facts.get(tax, {}).get(c, {}).get("units", {}).get(unidad) or []
            propio: dict = {}
            for f in u:
                if tax == "us-gaap" and f.get("form") not in FORMULARIOS:
                    continue
                k = (f.get("start"), f["end"])
                if k not in propio or f["filed"] > propio[k]["filed"]:
                    propio[k] = f
            for k, f in propio.items():
                por_periodo.setdefault(k, f)
    if not por_periodo:
        return []
    fin = max(f["end"] for f in por_periodo.values())
    if _d(fin) < dt.date.today() - MAX_ANTIGUEDAD:
        return []
    return list(por_periodo.values())


def ttm(facts: dict, conceptos: list[str], unidad: str = "USD") -> tuple[float | None, str | None]:
    """(valor TTM, fecha de cierre) de un concepto de flujo."""
    h = [f for f in _hechos(facts, conceptos, unidad) if f.get("start")]
    if not h:
        return None, None
    dur = lambda f: (_d(f["end"]) - _d(f["start"])).days
    anuales = [f for f in h if 350 <= dur(f) <= 380]
    if not anuales:
        return None, None
    fy = max(anuales, key=lambda f: f["end"])
    ytd = [f for f in h if dur(f) < 350 and _d(f["start"]) > _d(fy["end"]) - dt.timedelta(days=10)
           and _d(f["end"]) > _d(fy["end"])]
    if not ytd:
        return fy["val"], fy["end"]
    act = max(ytd, key=lambda f: (f["end"], dur(f)))
    s0, e0 = _d(act["start"]) - dt.timedelta(days=365), _d(act["end"]) - dt.timedelta(days=365)
    prev = [f for f in h if abs((_d(f["start"]) - s0).days) <= 10 and abs((_d(f["end"]) - e0).days) <= 10]
    if not prev:
        return fy["val"], fy["end"]
    return fy["val"] + act["val"] - prev[0]["val"], act["end"]


def ultimo(facts: dict, conceptos: list[str], unidad: str = "USD") -> float | None:
    h = _hechos(facts, conceptos, unidad)
    return max(h, key=lambda f: f["end"])["val"] if h else None


def medio(facts: dict, conceptos: list[str], unidad: str = "USD") -> float | None:
    """Media del saldo de cierre y del de hace ~1 año (saldo medio, como en el ROE estándar)."""
    h = sorted(_hechos(facts, conceptos, unidad), key=lambda f: f["end"])
    if not h:
        return None
    ult = h[-1]
    ref = _d(ult["end"]) - dt.timedelta(days=365)
    previo = [f for f in h if abs((_d(f["end"]) - ref).days) <= 20]
    return (ult["val"] + previo[-1]["val"]) / 2 if previo else ult["val"]


INGRESOS = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet",
            "RevenuesNetOfInterestExpense", "RevenueFromContractWithCustomerIncludingAssessedTax"]


def fundamentales_sec(ticker: str, precio_usd: float) -> dict | None:
    c = cik(ticker)
    if not c:
        return None
    d = _get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{c}.json")
    time.sleep(0.15)   # límite SEC: 10 peticiones/s
    if not d:
        return None
    f = d.get("facts", {})
    ni, fecha = ttm(f, ["NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic"])
    eps, _ = ttm(f, ["EarningsPerShareDiluted", "EarningsPerShareBasic"], "USD/shares")
    rev, _ = ttm(f, INGRESOS)
    cfo, _ = ttm(f, ["NetCashProvidedByUsedInOperatingActivities"])
    capex, _ = ttm(f, ["PaymentsToAcquirePropertyPlantAndEquipment"])
    EQ = ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"]
    eq = ultimo(f, EQ)
    eq_medio = medio(f, EQ)
    acc = ultimo(f, ["EntityCommonStockSharesOutstanding"], "shares")
    mcap = precio_usd * acc if acc else None
    fcf = (cfo - (capex or 0)) if cfo is not None else None
    return {
        "cik": c, "fecha_ttm": fecha,
        "beneficio_neto_ttm": ni, "bpa_diluido_ttm": eps, "ingresos_ttm": rev, "fcf_ttm": fcf,
        "patrimonio": eq, "acciones": acc,
        "per_gaap": precio_usd / eps if eps and eps > 0 else None,
        "roe": ni / eq_medio if ni is not None and eq_medio and eq_medio > 0 else None,
        "margen_neto": ni / rev if ni is not None and rev else None,
        "fcf_yield": fcf / mcap if fcf is not None and mcap else None,
        "patrimonio_negativo": bool(eq is not None and eq <= 0),
        "dias_desfase": (dt.date.today() - _d(fecha)).days if fecha else None,
    }


TOL = {"PER (trailing vs GAAP)": 0.15, "ROE": 0.25, "Margen neto": 0.15}


def contrastar(yahoo: dict, sec: dict) -> tuple[list[str], list[str]]:
    """(discrepancias, avisos).
    discrepancias: Yahoo no cuadra con la SEC -> dato no fiable, bloquea la idea hasta revisión.
    avisos: el dato es correcto pero engaña (calidad del beneficio, patrimonio reducido)."""
    disc, avisos = [], []
    desfasado = (sec.get("dias_desfase") or 0) > 100   # SEC aún sin el último 10-Q
    pares = [("PER (trailing vs GAAP)", yahoo.get("trailingPE"), sec.get("per_gaap")),
             ("ROE", yahoo.get("returnOnEquity"), sec.get("roe")),
             ("Margen neto", yahoo.get("profitMargins"), sec.get("margen_neto"))]
    for nombre, y, s in pares:
        if y is None or s is None:
            continue
        tol = TOL[nombre] * (2 if desfasado else 1)
        if abs(y - s) / max(abs(s), 1e-9) > tol:
            disc.append(f"{nombre}: Yahoo {y:.2f} vs SEC {s:.2f}")
    fpe, gpe, eps = yahoo.get("forwardPE"), sec.get("per_gaap"), sec.get("bpa_diluido_ttm")
    if sec.get("patrimonio_negativo"):
        avisos.append("Patrimonio neto negativo: ROE y P/VC no significativos")
    elif (sec.get("roe") or 0) > 0.6:
        avisos.append(f"ROE {sec['roe']:.0%} inflado por patrimonio reducido (recompras/deterioros)")
    if fpe and fpe > 0 and eps is not None and eps <= 0:
        avisos.append(f"Pérdidas GAAP (BPA {eps:.2f}) pero PER adelantado {fpe:.1f}: valoración sobre beneficio ajustado")
    elif fpe and gpe and fpe < 0.5 * gpe:
        avisos.append(f"PER adelantado {fpe:.1f} vs PER GAAP {gpe:.1f}: revisar BPA ajustado o ejercicio de referencia")
    if desfasado:
        avisos.append(f"SEC con cierre {sec.get('fecha_ttm')}: último 10-Q aún no incorporado")
    return disc, avisos


def verificar(candidatos: list[dict]) -> None:
    """Añade a cada candidato de EE. UU. los datos SEC y el estado de verificación (in situ)."""
    cache: dict[str, dict | None] = {}
    for c in candidatos:
        t = c["ticker"]
        if c.get("mercado") != "EE. UU.":
            c.update(verificacion="SIN FUENTE OFICIAL", discrepancias=[], avisos_calidad=[], sec=None)
            continue
        if t not in cache:
            try:
                cache[t] = fundamentales_sec(t, c["precio"])
            except Exception:
                cache[t] = None
        sec = cache[t]
        if not sec:
            c.update(verificacion="SIN FUENTE OFICIAL", discrepancias=[], avisos_calidad=[], sec=None)
            continue
        disc, av = contrastar(c.get("fundamentales") or {}, sec)
        c.update(verificacion="DISCREPANCIA" if disc else "VERIFICADO SEC", discrepancias=disc,
                 avisos_calidad=av, sec=sec)
