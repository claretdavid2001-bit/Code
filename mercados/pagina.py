"""Genera la página HTML del informe a partir de candidatos.json (+ veredictos.json de los agentes).

Uso: python -m mercados.pagina salidas/<fecha>   -> salidas/<fecha>/informe.html y publicado/radar.html
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = Path(__file__).parent


def generar(carpeta: str | Path) -> Path:
    carpeta = Path(carpeta)
    d = json.loads((carpeta / "candidatos.json").read_text())
    v = carpeta / "veredictos.json"
    d["veredictos"] = json.loads(v.read_text()) if v.exists() else {}
    # Aligerar: solo lo que la página usa
    for h in d["horizontes"].values():
        for c in h["candidatos"]:
            c.pop("indicadores", None)
            c.pop("fundamentales", None)
    datos = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")
    html = (BASE / "plantilla.html").read_text().replace("__DATOS__", datos)
    out = carpeta / "informe.html"
    out.write_text(html)
    pub = BASE.parent / "publicado"
    pub.mkdir(exist_ok=True)
    (pub / "radar.html").write_text(html)
    return out


if __name__ == "__main__":
    print(generar(sys.argv[1]))
