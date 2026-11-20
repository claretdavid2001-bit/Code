"""Excel del informe: fórmulas vivas, Aptos, verde/negro, inputs en azul, hoja de cuadre."""
from __future__ import annotations

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.formatting.rule import CellIsRule
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName

F = "Aptos"
VERDE = "1E6B3A"
VERDE_CLARO = "E2EFDA"
NEGRO = Font(name=F, size=10, color="000000")
AZUL = Font(name=F, size=10, color="0000FF")
CAB = Font(name=F, size=10, bold=True, color="FFFFFF")
TIT = Font(name=F, size=14, bold=True, color=VERDE)
FILL_CAB = PatternFill("solid", fgColor=VERDE)
FILL_IN = PatternFill("solid", fgColor="FFF9E5")
FINO = Side(style="thin", color="BFBFBF")
BORDE = Border(bottom=FINO)
PCT, PCT0, EUR, NUM = "0.0%", "0%", '#,##0 "€";-#,##0 "€"', "#,##0.00"


def _cab(ws, fila, textos):
    for j, t in enumerate(textos, 1):
        c = ws.cell(fila, j, t)
        c.font, c.fill = CAB, FILL_CAB
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[fila].height = 30


def _nombre(wb, nombre, ref):
    wb.defined_names[nombre] = DefinedName(nombre, attr_text=ref)


def generar_excel(res: dict, ruta):
    wb = Workbook()

    # ---------- Supuestos ----------
    s = wb.active
    s.title = "Supuestos"
    s["A1"], s["A1"].font = "Supuestos e inputs (celdas azules editables)", TIT
    s["A2"] = f"Fecha informe: {res['fecha']} · Datos al cierre de {res['fecha_datos']} · {res['universo_valido']} valores · {res['escenarios_por_valor']:,} escenarios por valor y horizonte".replace(",", ".")
    s["A2"].font = NEGRO
    p = res["parametros"]
    inputs = [("Capital de la cartera (€)", 50000, EUR, "Capital"),
              ("Riesgo máx. por operación (% capital)", p["riesgo_operacion"], PCT, "RiesgoOp"),
              ("Tope por posición (% capital)", p["tope_posicion"], PCT, "TopePos"),
              ("Probabilidad de ganancia mínima", p["p_ganancia_min"], PCT0, "PGanMin"),
              ("Probabilidad de stop máxima", p["p_stop_max"], PCT0, "PStopMax"),
              ("Deriva prior de mercado (anual) [motor]", p["deriva_prior_anual"], PCT, None),
              ("Peso media histórica en la deriva [motor]", p["peso_media_historica"], PCT0, None)]
    _cab(s, 4, ["Concepto", "Valor"])
    for k, (txt, v, fmt, nm) in enumerate(inputs, 5):
        s.cell(k, 1, txt).font = NEGRO
        c = s.cell(k, 2, v)
        c.font, c.number_format = AZUL, fmt
        if nm:
            c.fill = FILL_IN
            _nombre(wb, nm, f"Supuestos!$B${k}")
    s["A13"] = "Nota: los inputs [motor] informan de la simulación; cambiarlos aquí no recalcula el Monte Carlo (se ejecuta en Python)."
    s["A13"].font = Font(name=F, size=9, italic=True)
    s.column_dimensions["A"].width = 48
    s.column_dimensions["B"].width = 16

    # ---------- Escenarios ----------
    e = wb.create_sheet("Escenarios")
    cols = ["Horizonte", "Ticker", "Nombre", "Mercado", "Precio", "Objetivo %", "Stop %", "P(objetivo)", "P(stop)",
            "P(ninguno)", "Ret. si ninguno", "Esperanza op.", "Esperanza (motor)", "P(ganancia)", "Ret. esperado",
            "P5", "P50", "P95", "CVaR 95 %", "Ratio B/R", "Peso sugerido", "Importe €", "Pérdida si stop €",
            "Apto perfil", "Ranking motor", "Verificación fuente", "Discrepancias / avisos", "PER GAAP (SEC)",
            "ROE (SEC)", "FCF yield (SEC)"]
    _cab(e, 1, cols)
    fila = 2
    filas_top = {h: [] for h in res["horizontes"]}
    for h, bloque in res["horizontes"].items():
        for rk, c in enumerate(bloque["candidatos"], 1):
            r = fila
            vals = [bloque["etiqueta"], c["ticker"], c["nombre"], c["mercado"], c["precio"], c["objetivo_pct"],
                    c["stop_pct"], c["p_objetivo"], c["p_stop"], f"=1-H{r}-I{r}", c["ret_ninguno"],
                    f"=H{r}*F{r}+I{r}*G{r}+J{r}*K{r}", c["esperanza_operativa"], c["p_ganancia"], c["ret_esperado"],
                    c["p5"], c["p50"], c["p95"], c["cvar95"], f"=F{r}/-G{r}", f"=MIN(TopePos,RiesgoOp/-G{r})",
                    f"=Capital*U{r}", f"=V{r}*G{r}",
                    f'=IF(AND(N{r}>=PGanMin,I{r}<=PStopMax,L{r}>0,Z{r}<>"DISCREPANCIA"),"SÍ","NO")', rk,
                    c.get("verificacion", "SIN FUENTE OFICIAL"),
                    " | ".join((c.get("discrepancias") or []) + (c.get("avisos_calidad") or [])) or None,
                    (c.get("sec") or {}).get("per_gaap"), (c.get("sec") or {}).get("roe"),
                    (c.get("sec") or {}).get("fcf_yield")]
            for j, v in enumerate(vals, 1):
                cell = e.cell(r, j, v)
                es_formula = isinstance(v, str) and v.startswith("=")
                cell.font = NEGRO if es_formula or j in (1, 3, 4, 26, 27) else AZUL
                cell.border = BORDE
            for j in (6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21):
                e.cell(r, j).number_format = PCT
            e.cell(r, 5).number_format = NUM
            e.cell(r, 20).number_format = "0.0x"
            e.cell(r, 28).number_format = "0.0x"
            e.cell(r, 29).number_format = PCT
            e.cell(r, 30).number_format = PCT
            e.cell(r, 22).number_format = EUR
            e.cell(r, 23).number_format = EUR
            if c.get("apto_perfil") and len(filas_top[h]) < 5:
                filas_top[h].append(r)
            fila += 1
    ult = fila - 1
    e.freeze_panes = "C2"
    for j, w in enumerate([18, 10, 26, 10, 10] + [11] * 20 + [18, 60, 11, 11, 11], 1):
        e.column_dimensions[get_column_letter(j)].width = w
    e.conditional_formatting.add(f"X2:X{ult}", CellIsRule(operator="equal", formula=['"SÍ"'],
                                                           fill=PatternFill("solid", fgColor=VERDE_CLARO)))
    e.auto_filter.ref = f"A1:AD{ult}"
    e.conditional_formatting.add(f"Z2:Z{ult}", CellIsRule(operator="equal", formula=['"DISCREPANCIA"'],
                                                           fill=PatternFill("solid", fgColor="F8CBAD")))

    # ---------- Resumen ----------
    rs = wb.create_sheet("Resumen", 0)
    rs["A1"], rs["A1"].font = "Mejores oportunidades del día (perfil moderado)", TIT
    rs["A2"] = "Vinculado a 'Escenarios' y 'Supuestos': cambia el capital o el riesgo y se recalcula."
    rs["A2"].font = Font(name=F, size=9, italic=True)
    cab = ["Horizonte", "Ticker", "Nombre", "Precio", "Objetivo %", "Stop %", "P(objetivo)", "P(stop)",
           "P(ganancia)", "Esperanza op.", "P5", "P95", "Peso", "Importe €", "Pérdida si stop €", "Verificación"]
    src = ["A", "B", "C", "E", "F", "G", "H", "I", "N", "L", "P", "R", "U", "V", "W", "Z"]
    _cab(rs, 4, cab)
    r = 5
    for h, filas in filas_top.items():
        for fr in filas:
            for j, col in enumerate(src, 1):
                c = rs.cell(r, j, f"=Escenarios!{col}{fr}")
                c.font, c.border = NEGRO, BORDE
                c.number_format = {4: NUM, 14: EUR, 15: EUR, 16: "General"}.get(j, PCT if j >= 5 else "General")
            r += 1
    fin_res = r - 1
    rs.cell(r + 1, 13, "Total").font = Font(name=F, size=10, bold=True)
    for j, col in ((13, "M"), (14, "N"), (15, "O")):
        c = rs.cell(r + 1, j, f"=SUM({col}5:{col}{fin_res})")
        c.font, c.number_format = Font(name=F, size=10, bold=True), (PCT if j == 13 else EUR)
    tot_row = r + 1
    for j, w in enumerate([18, 10, 28, 10] + [11] * 11 + [20], 1):
        rs.column_dimensions[get_column_letter(j)].width = w
    rs.freeze_panes = "D5"

    # ---------- Cuadre ----------
    q = wb.create_sheet("Cuadre")
    q["A1"], q["A1"].font = "Hoja de cuadre y controles", TIT
    _cab(q, 3, ["Control", "Valor", "Esperado", "Diferencia", "Estado"])
    n_top = sum(len(v) for v in filas_top.values())
    controles = [
        ("Probabilidades suman 1 (nº filas con descuadre)", f"=SUMPRODUCT(--(ABS(Escenarios!H2:H{ult}+Escenarios!I2:I{ult}+Escenarios!J2:J{ult}-1)>0.000001))", 0),
        ("Probabilidades en [0,1] (nº fuera de rango)", f"=COUNTIF(Escenarios!H2:J{ult},\"<0\")+COUNTIF(Escenarios!H2:J{ult},\">1\")", 0),
        ("Esperanza Excel vs motor (suma |dif.|)", f"=SUMPRODUCT(ABS(Escenarios!L2:L{ult}-Escenarios!M2:M{ult}))", 0),
        ("Posiciones por encima del tope", f"=COUNTIF(Escenarios!U2:U{ult},\">\"&TopePos+0.000001)", 0),
        ("Nº ideas en Resumen = aptas vinculadas", f"=COUNTA(Resumen!B5:B{max(fin_res, 5)})", n_top),
        ("Ideas en Resumen no aptas (perfil)", f"=COUNTIF(Resumen!A5:O{max(fin_res, 5)},\"NO\")", 0),
        ("Inversión total Resumen ≤ capital (exceso €)", f"=MAX(0,Resumen!N{tot_row}-Capital)", 0),
        ("Pérdida total si saltan todos los stops ≤ 10 % capital (exceso €)", f"=MAX(0,-Resumen!O{tot_row}-0.1*Capital)", 0),
        ("Ideas en Resumen con DISCREPANCIA Yahoo vs SEC", f"=COUNTIF(Resumen!P5:P{max(fin_res, 5)},\"DISCREPANCIA\")", 0),
        ("Ideas aptas en Escenarios con DISCREPANCIA", f"=COUNTIFS(Escenarios!X2:X{ult},\"SÍ\",Escenarios!Z2:Z{ult},\"DISCREPANCIA\")", 0),
    ]
    for k, (txt, f, esp) in enumerate(controles, 4):
        q.cell(k, 1, txt).font = NEGRO
        q.cell(k, 2, f).font = NEGRO
        q.cell(k, 3, esp).font = AZUL
        q.cell(k, 4, f"=B{k}-C{k}").font = NEGRO
        q.cell(k, 5, f'=IF(ABS(D{k})<0.0001,"OK","REVISAR")').font = NEGRO
        for j in (2, 3, 4):
            q.cell(k, j).number_format = "#,##0.000000" if k == 6 else "#,##0"
    fin = 3 + len(controles)
    q.cell(fin + 2, 1, "ESTADO GLOBAL").font = Font(name=F, size=11, bold=True)
    q.cell(fin + 2, 5, f'=IF(COUNTIF(E4:E{fin},"OK")={len(controles)},"OK","REVISAR")').font = Font(name=F, size=11, bold=True)
    verde = PatternFill("solid", fgColor=VERDE_CLARO)
    rojo = PatternFill("solid", fgColor="F8CBAD")
    q.conditional_formatting.add(f"E4:E{fin + 2}", CellIsRule(operator="equal", formula=['"OK"'], fill=verde))
    q.conditional_formatting.add(f"E4:E{fin + 2}", CellIsRule(operator="equal", formula=['"REVISAR"'], fill=rojo))
    q.column_dimensions["A"].width = 62
    for c in "BCDE":
        q.column_dimensions[c].width = 14

    for ws in wb.worksheets:
        ws.sheet_view.showGridLines = False
    wb.save(ruta)
