#!/usr/bin/env python3
"""Monta la web “¿Existe realmente el cambio climático?” a partir de src/ y de los datos de datos/."""
import csv
import hashlib
import json
import re
import shutil
from pathlib import Path

RAIZ = Path(__file__).parent
SRC = RAIZ / "src"
DATOS = RAIZ / "datos"
SITIO = RAIZ / "site"

EQUIPO = "Marcos Ramos, Gonzalo Redondo, Jaime Ramos y Victor Cerveros"

REPARTO = [
    ("1", "Marcos Ramos", "Definición e indicador de temperatura", [("definicion", "1. Definición"), ("ind-temperatura", "Indicador 1")]),
    ("2", "Gonzalo Redondo", "Indicadores de CO₂ y glaciares", [("ind-co2", "Indicador 2"), ("ind-glaciares", "Indicador 3")]),
    ("3", "Jaime Ramos", "Análisis crítico", [("analisis", "3. Análisis crítico")]),
    ("4", "Victor Cerveros", "Dos posturas y conclusión", [("posturas", "4. Dos posturas"), ("conclusion", "5. Conclusión")]),
]

PAGINAS = [
    ("index.html", "¿Existe realmente el cambio climático?",
     "Trabajo de Sostenibilidad (UD2): datos de temperatura, CO₂ y glaciares, cómo se verifican, consenso científico, dos posturas y conclusión."),
]

UNSPLASH = "https://images.unsplash.com/"
FOTOS = {
    "glaciar": ("photo-1704746375104-2f9bae4a3fc7", "Ella Deane",
                "https://unsplash.com/photos/a-large-glacier-with-a-mountain-in-the-background-o7BLOcV6RyA",
                "Un gran glaciar con una montaña al fondo, en Kenai Fjords (Alaska).", "Evidencias"),
    "periodicos": ("photo-1573812195421-50a396d17893", "Utsav Srestha",
                   "https://unsplash.com/photos/pile-of-newspapers-HeNrEdA4Zp4",
                   "Una pila de periódicos.", "Análisis crítico"),
}

FUENTES = ("https://fonts.googleapis.com/css2?family=Hanken+Grotesk:ital,wght@0,400..700;1,400"
           "&amp;family=Newsreader:opsz,wght@6..72,500..700&amp;display=swap")

PLANTILLA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo}</title>
<meta name="description" content="{descripcion}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="{fuentes}" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="{fuentes}"></noscript>
<link rel="stylesheet" href="assets/estilos.css?v={v}">
</head>
<body>
<a class="saltar" href="#contenido">Saltar al contenido</a>
<nav class="barra" aria-label="{etiqueta_nav}">
  <div class="barra__dentro">
    <a class="barra__titulo" href="index.html">Cambio climático</a>
    <ol class="barra__lista">
{nav}
    </ol>
    {extra_nav}
  </div>
</nav>
<main id="contenido">
{cuerpo}
<footer class="pie">
  <p>Trabajo de clase de {equipo}. Sostenibilidad, UD2. Gráficos y franjas de elaboración propia con datos públicos de NASA, NOAA, WGMS y EPA; fotos de Unsplash.</p>
</footer>
</main>
<div class="globo" role="status" aria-live="polite" hidden></div>
<script src="assets/sitio.js?v={v}" defer></script>
</body>
</html>
"""

# ---------- Datos ----------

def leer_datos():
    temp = {int(r["Year"]): float(r["Mean"]) for r in csv.DictReader(open(DATOS / "annual.csv")) if r["Source"] == "GISTEMP"}
    temp = {a: v for a, v in temp.items() if a <= 2025}  # solo años completos
    co2 = {int(r["Year"]): float(r["Mean"]) for r in csv.DictReader(open(DATOS / "co2-annmean-mlo.csv"))}
    gla = {int(r["Year"]): float(r["Mean cumulative mass balance"]) for r in csv.DictReader(open(DATOS / "glaciers.csv"))}
    return dict(sorted(temp.items())), dict(sorted(co2.items())), dict(sorted(gla.items()))


def num(v: float, dec: int = 1, signo: bool = False) -> str:
    s = f"{v:+.{dec}f}" if signo else f"{v:.{dec}f}"
    return s.replace("-", "−").replace(".", ",")


# Escala divergente (de RdBu): azul frío, gris neutro en el cero, rojo cálido
RDBU = ["#053061", "#2166ac", "#4393c3", "#92c5de", "#d1e5f0", "#f4f4f4", "#fddbc7", "#f4a582", "#d6604d", "#b2182b", "#67001f"]


def color_anomalia(v: float, tope: float = 1.3) -> str:
    t = max(-1.0, min(1.0, v / tope))
    pos = (t + 1) / 2 * (len(RDBU) - 1)
    i = min(int(pos), len(RDBU) - 2)
    f = pos - i
    a, b = RDBU[i], RDBU[i + 1]
    mezcla = [round(int(a[k:k + 2], 16) * (1 - f) + int(b[k:k + 2], 16) * f) for k in (1, 3, 5)]
    return "#" + "".join(f"{c:02x}" for c in mezcla)


def franjas(temp: dict) -> str:
    rects = "".join(f'<rect x="{i}" y="0" width="1.02" height="1" fill="{color_anomalia(v)}"/>' for i, v in enumerate(temp.values()))
    a0, a1 = min(temp), max(temp)
    return (f'<figure class="franjas"><svg viewBox="0 0 {len(temp)} 1" preserveAspectRatio="none" role="img" '
            f'aria-label="Franjas de temperatura global de {a0} a {a1}: azules al principio y cada vez más rojas al final.">{rects}</svg>'
            f'<figcaption><span>{a0}</span>Cada franja es un año: azul, más frío que la media de 1951-1980; rojo, más cálido. Datos de la NASA.<span>{a1}</span></figcaption></figure>')


# ---------- Gráficos en SVG ----------

AN, AL = 960, 380
M = {"i": 58, "d": 70, "s": 18, "b": 36}


def escala(d0, d1, r0, r1):
    return lambda v: r0 + (v - d0) / (d1 - d0) * (r1 - r0)


def ejes(x, y, anios, marcas_y, fmt_y, marcas_x):
    g = []
    for v in marcas_y:
        yy = y(v)
        g.append(f'<line class="g__rejilla{" g__cero" if v == 0 else ""}" x1="{M["i"]}" x2="{AN - M["d"]}" y1="{yy:.1f}" y2="{yy:.1f}"/>'
                 f'<text class="g__ey" x="{M["i"] - 8}" y="{yy + 4:.1f}">{fmt_y(v)}</text>')
    for a in marcas_x:
        g.append(f'<text class="g__ex" x="{x(a):.1f}" y="{AL - 10}">{a}</text>')
    return "".join(g)


def grafico_temperatura(temp):
    anios = list(temp)
    ancho = (AN - M["i"] - M["d"]) / len(anios)
    x = lambda a: M["i"] + (a - anios[0]) * ancho + ancho / 2
    y = escala(-0.6, 1.4, AL - M["b"], M["s"])
    barras = []
    for a, v in temp.items():
        y0, y1 = sorted((y(0), y(v)))
        barras.append(f'<rect x="{x(a) - ancho / 2 + 0.6:.2f}" y="{y0:.2f}" width="{max(ancho - 1.2, 1):.2f}" height="{max(y1 - y0, 0.8):.2f}" rx="1" fill="{color_anomalia(v)}"/>')
    ult = anios[-2]  # 2024, el récord
    etiqueta = (f'<text class="g__dato" x="{x(ult) + 8:.1f}" y="{y(temp[ult]) - 6:.1f}">{ult}: récord</text>')
    cuerpo = ejes(x, y, anios, [-0.5, 0, 0.5, 1.0], lambda v: num(v, 1, True) + " °C" if v else "0", [1880, 1900, 1920, 1940, 1960, 1980, 2000, 2020])
    return svg("temperatura", cuerpo + "".join(barras) + etiqueta,
               f"Gráfico de barras de la anomalía de temperatura global de {anios[0]} a {anios[-1]} respecto a 1951-1980. "
               f"Hasta los años 70 oscila alrededor de cero; después sube hasta el récord de {num(temp[ult], 1, True)} °C en {ult}.",
               {"x": anios, "y": [round(v, 2) for v in temp.values()], "u": "°C", "s": True, "tipo": "barras",
                "i": M["i"], "d": M["d"], "an": AN})


def grafico_linea(nombre, datos, d0, d1, marcas, fmt, unidad, marcas_x, clase, desc, dec=1, signo=False, inicio=True):
    anios = list(datos)
    x = escala(anios[0], anios[-1], M["i"] + 4, AN - M["d"])
    y = escala(d0, d1, AL - M["b"], M["s"])
    puntos = " ".join(f"{x(a):.1f},{y(v):.1f}" for a, v in datos.items())
    a0, a1 = anios[0], anios[-1]
    extremos = (f'<circle class="g__punto {clase}" cx="{x(a0):.1f}" cy="{y(datos[a0]):.1f}" r="4"/>'
                f'<circle class="g__punto {clase}" cx="{x(a1):.1f}" cy="{y(datos[a1]):.1f}" r="4"/>'
                f'<text class="g__dato" x="{x(a1) + 8:.1f}" y="{y(datos[a1]) + 4:.1f}">{num(datos[a1], dec, signo)}</text>'
                + (f'<text class="g__dato g__dato--suave" x="{x(a0) + 2:.1f}" y="{y(datos[a0]) - 14:.1f}">{num(datos[a0], dec, signo)} en {a0}</text>' if inicio else ""))
    cuerpo = ejes(x, y, anios, marcas, fmt, marcas_x) + f'<polyline class="g__linea {clase}" points="{puntos}"/>' + extremos
    return svg(nombre, cuerpo, desc, {"x": anios, "y": [round(v, 2) for v in datos.values()], "u": unidad, "s": signo,
                                       "tipo": "linea", "i": M["i"] + 4, "d": M["d"], "an": AN})


def svg(nombre, cuerpo, desc, datos):
    return (f'<figure class="grafico" data-grafico=\'{json.dumps(datos, ensure_ascii=False)}\'>'
            f'<svg class="g" viewBox="0 0 {AN} {AL}" role="img" aria-label="{desc}">{cuerpo}'
            f'<line class="g__guia" x1="0" x2="0" y1="{M["s"]}" y2="{AL - M["b"]}" hidden/></svg></figure>')


def tabla_decadas(datos, unidad, dec=2, signo=False, titulo=""):
    filas = "".join(f"<tr><th scope=\"row\">{a}</th><td>{num(v, dec, signo)} {unidad}</td></tr>"
                    for a, v in datos.items() if a % 10 == 0 or a == max(datos))
    return (f'<details class="datos-tabla"><summary>Ver los datos {titulo}</summary>'
            f'<table><thead><tr><th scope="col">Año</th><th scope="col">Valor</th></tr></thead><tbody>{filas}</tbody></table></details>')


# ---------- Piezas de texto ----------

def foto(clave, pie):
    ident, autor, pagina, alt, _ = FOTOS[clave]
    urls = [(f"{UNSPLASH}{ident}?auto=format&amp;fit=crop&amp;w={a}&amp;h={a * 9 // 16}&amp;q=70", a) for a in (720, 1440)]
    srcset = ", ".join(f"{u} {a}w" for u, a in urls)
    return (f'<figure class="foto"><img data-foto src="{urls[-1][0]}" srcset="{srcset}" sizes="(max-width: 66rem) 94vw, 62rem" '
            f'width="1440" height="810" alt="{alt}" loading="lazy" decoding="async">'
            f'<figcaption>{pie}. <span>Foto: <a href="{pagina}">{autor}</a>, Unsplash.</span></figcaption></figure>')


def encargo(nombre, corto=False):
    n = next(r[0] for r in REPARTO if r[1] == nombre)
    if corto:
        return f'<strong>{nombre}</strong>'
    return f'Se encarga <strong>{nombre}</strong>'


def reparto():
    filas = []
    for n, nombre, parte, secc in REPARTO:
        enlaces = ", ".join('<a href="#%s">%s</a>' % (i, t) for i, t in secc)
        filas.append(f'<tr><th scope="row">{nombre}</th><td>{parte}</td><td>{enlaces}</td></tr>')
    return ('<div class="tabla"><table><thead><tr><th scope="col">Integrante</th><th scope="col">Parte</th><th scope="col">Secciones</th>'
            '</tr></thead><tbody>' + "".join(filas) + "</tbody></table></div>")


def creditos():
    filas = "".join(f'<li>{autor}. <a href="{pagina}">{alt.rstrip(".")}</a>. Unsplash, licencia libre.</li>' for _, autor, pagina, alt, _ in FOTOS.values())
    return '<h3 class="h-sub">Fotografías</h3><ul class="refs refs--fotos">' + filas + "</ul>"


def navegacion(cuerpo):
    filas = []
    for ident, nombre in re.findall(r'<(?:section|header) class="[^"]*" id="([^"]+)" data-etapa="([^"]+)"', cuerpo):
        if ident == "inicio":
            continue
        filas.append(f'      <li><a href="#{ident}">{nombre}</a></li>')
    return "\n".join(filas)


def apilable(html: str) -> str:
    """Añade a cada celda el nombre de su columna (data-et) para apilar las tablas en el móvil."""
    def tabla(m):
        t = m.group(0)
        cab = re.search(r"<thead>(.*?)</thead>", t, re.S)
        if not cab:
            return t
        nombres = [re.sub(r"<[^>]+>", "", re.sub(r'<span class="(?:supuesto|estimacion)">(.*?)</span>', r"(\1)", c)).strip()
                   for c in re.findall(r"<th[^>]*>(.*?)</th>", cab.group(1), re.S)]
        def fila(fm):
            celdas = list(re.finditer(r"<(td|th)(\s[^>]*)?>", fm.group(0)))
            out, ultimo = [], 0
            for i, c in enumerate(celdas):
                out.append(fm.group(0)[ultimo:c.start()])
                etiqueta = nombres[i] if i < len(nombres) else ""
                out.append(f'<{c.group(1)}{c.group(2) or ""} data-et="{etiqueta}">')
                ultimo = c.end()
            out.append(fm.group(0)[ultimo:])
            return "".join(out)
        cuerpo = re.search(r"<tbody>.*?</tbody>", t, re.S)
        return t[:cuerpo.start()] + re.sub(r"<tr[^>]*>.*?</tr>", fila, cuerpo.group(0), flags=re.S) + t[cuerpo.end():]
    return re.sub(r"<table>.*?</table>", tabla, html, flags=re.S)


def version():
    h = hashlib.sha1()
    for nombre in ("estilos.css", "sitio.js"):
        h.update((SITIO / "assets" / nombre).read_bytes())
    return h.hexdigest()[:8]


def main():
    temp, co2, gla = leer_datos()
    piezas = {
        "franjas": franjas(temp),
        "grafico:temperatura": grafico_temperatura(temp) + tabla_decadas(temp, "°C", 1, True, "de temperatura por décadas"),
        "grafico:co2": grafico_linea("co2", co2, 300, 440, [300, 340, 380, 420], lambda v: f"{v}", "ppm", [1960, 1970, 1980, 1990, 2000, 2010, 2020],
                                     "g--co2", f"Línea de la concentración media anual de CO₂ en Mauna Loa de 1959 a 2025: sube sin pausa de {num(co2[1959])} a {num(co2[2025])} partes por millón.", 1)
                       + tabla_decadas(co2, "ppm", 1, False, "de CO₂ por décadas"),
        "grafico:glaciares": grafico_linea("glaciares", gla, -32, 2, [0, -10, -20, -30], lambda v: num(v, 0) + " m" if v else "0", "m", [1960, 1970, 1980, 1990, 2000, 2010, 2020],
                                           "g--gla", f"Línea del balance de masa acumulado de los glaciares de referencia de 1956 a 2023: baja de forma continua hasta {num(gla[2023])} metros de agua equivalente.", 1, True, False)
                             + tabla_decadas(gla, "m de agua equivalente", 1, True, "de los glaciares por décadas"),
    }
    v = version()
    for archivo, titulo, descripcion in PAGINAS:
        cuerpo = (SRC / archivo).read_text(encoding="utf-8")
        for clave, html in piezas.items():
            cuerpo = cuerpo.replace("{{" + clave + "}}", html)
        cuerpo = re.sub(r"\{\{foto:([a-z]+)\|([^}]+)\}\}", lambda m: foto(m.group(1), m.group(2)), cuerpo)
        cuerpo = re.sub(r"\{\{encargo-corto:([^}]+)\}\}", lambda m: encargo(m.group(1), True), cuerpo)
        cuerpo = re.sub(r"\{\{encargo:([^}]+)\}\}", lambda m: encargo(m.group(1)), cuerpo)
        cuerpo = cuerpo.replace("{{reparto}}", reparto()).replace("{{creditos}}", creditos())
        cuerpo = re.sub(r"(\d) %", r"\1&nbsp;%", cuerpo)
        cuerpo = re.sub(r"(\d) °C", r"\1&nbsp;°C", cuerpo)
        cuerpo = apilable(cuerpo)
        if archivo == "index.html":
            extra, etiqueta = "", "Apartados del trabajo"
        else:
            extra, etiqueta = '<a class="barra__guion" href="index.html">Volver</a>', "Partes del guion"
        html = PLANTILLA.format(titulo=titulo, descripcion=descripcion, fuentes=FUENTES, v=v, nav=navegacion(cuerpo),
                                extra_nav=extra, etiqueta_nav=etiqueta, cuerpo=cuerpo.rstrip(), equipo=EQUIPO)
        (SITIO / archivo).write_text(html, encoding="utf-8")
        print("ok", archivo, len(html))
    # Datos descargables, con nombre claro y sus columnas originales
    (SITIO / "datos").mkdir(exist_ok=True)
    with open(SITIO / "datos" / "temperatura-gistemp.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["anio", "anomalia_c_respecto_1951_1980"]); w.writerows(temp.items())
    shutil.copy(DATOS / "co2-annmean-mlo.csv", SITIO / "datos" / "co2-mauna-loa.csv")
    shutil.copy(DATOS / "glaciers.csv", SITIO / "datos" / "glaciares-referencia.csv")
    (SITIO / ".nojekyll").write_text("", encoding="utf-8")


if __name__ == "__main__":
    main()
