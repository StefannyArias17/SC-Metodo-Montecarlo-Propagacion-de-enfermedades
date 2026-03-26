"""
Script principal de EpiSim, aquí genera las 8 gráficas del análisis epidemiológico
 
Coordina la ejecución del modelo (episim_simulation.py) con la visualización
de resultados. Cada función graficar es responsable de una sola gráfica,
lo que hace fácil regenerar o modificar cualquiera de forma independiente.
 
Se puede ejecutar con parámetros por defecto o cargando un CSV externo:
    python episim.py
    python episim.py --config config_ejemplo.csv
"""
import os
import sys
import math
import time
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

import constants
from episim_simulation import EpiSim

os.makedirs("salidas", exist_ok=True)

COLORES = {"S": "#1976D2", "E": "#F57C00", "I": "#D32F2F", "R": "#388E3C"}

# UTILIDADES
def cargar_config(ruta: str):
    """
    Carga parámetros desde un archivo CSV y los sobreescribe en constants.
 
    El formato es nombre,valor por línea. Solo se sobreescriben los atributos que 
    ya existen en constants, así que no hay riesgo de inyectar variables extrañas.
 
    Parámetros:
        ruta (str) : ruta al archivo CSV de configuración
    """
    if not os.path.exists(ruta):
        print(f"[Config] Archivo no encontrado: {ruta}")
        return
    with open(ruta) as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            partes = linea.split(",")
            if len(partes) >= 2:
                nombre, valor = partes[0].strip(), partes[1].strip()
                if hasattr(constants, nombre):
                    tipo = type(getattr(constants, nombre))
                    setattr(constants, nombre, tipo(valor))
                    print(f"[Config] {nombre} = {valor}")


def suavizar(lista: list, ventana: int = 12) -> list:
    """
    Aplica una media móvil centrada para suavizar curvas estocásticas ruidosas.
 
    Parámetros:
        lista   (list) : valores a suavizar
        ventana (int)  : mitad del ancho de la ventana (default 12 días)
 
    Retorna:
        list con los valores suavizados
    """
    result = []
    for i in range(len(lista)):
        ini = max(0, i - ventana // 2)
        fin = min(len(lista), i + ventana // 2 + 1)
        result.append(sum(lista[ini:fin]) / (fin - ini))
    return result


def save(fig, nombre: str, out_dir: str = "salidas"):
    """Guarda la figura en out_dir e imprime la ruta por consola."""
    ruta = os.path.join(out_dir, nombre)
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [+] {ruta}")


# MODELO SEIR DETERMINÍSTICO, el relacionado a la "Referencia bibliográfica"
def seir_teorico(beta: float = 0.2714, sigma: float = 0.2857,
                 gamma: float = 0.0952) -> dict:
    """
    Resuelve el SEIR determinístico por el método de Euler y devuelve las curvas.
 
    Los parámetros por defecto son los valores efectivos derivados analíticamente
    del mecanismo estocástico del modelo:
        β_eff = E[contactos/día] × E[p_trans] = 0.5427 × 0.5 = 0.2714
        σ_eff = 1 / E[σ_inv] = 1 / 3.5 = 0.2857
        γ_eff = 1 / E[γ_inv] = 1 / 10.5 = 0.0952
        R0 = β_eff / γ_eff ≈ 2.85
 
    Se usa en la gráfica 08 para comparar el resultado estocástico contra
    el modelo continuo teórico (criterio de empate bibliográfico).
 
    Parámetros:
        beta  (float) : tasa de transmisión efectiva
        sigma (float) : tasa de progresión E → I (1/periodo de incubación)
        gamma (float) : tasa de recuperación I → R (1/periodo infeccioso)
 
    Retorna:
        dict con listas "S", "E", "I", "R", "dias" de longitud DAYS
    """
    N = constants.N_POPULATION; I0 = constants.I0_INFECTED
    dias = constants.DAYS
    S, E, I, R = float(N - I0), 0.0, float(I0), 0.0
    out = {k: [] for k in ["S", "E", "I", "R", "dias"]}
    out["dias"] = list(range(1, dias + 1))
    for _ in range(dias):
        dS = -beta * S * I / N
        dE =  beta * S * I / N - sigma * E
        dI =  sigma * E - gamma * I
        dR =  gamma * I
        S = max(0., S + dS); E = max(0., E + dE)
        I = max(0., I + dI); R = max(0., R + dR)
        out["S"].append(S); out["E"].append(E)
        out["I"].append(I); out["R"].append(R)
    return out

def analisis_convergencia(sim: EpiSim) -> list:
    """
    Calcula el pico medio y su error estándar para distintas cantidades de simulaciones.
 
    Sirve para demostrar que el estimador converge al aumentar las réplicas,
    lo que valida estadísticamente el tamaño de muestra elegido.
 
    Parámetros:
        sim (EpiSim) : modelo ya ejecutado
 
    Retorna:
        list de dicts con claves "simulaciones", "pico_medio" y "error_std"
    """
    picos  = sim.sin_vacunacion.stats["picos"]["raw"]
    puntos = [10, 50, 100, 250, 500, min(1000, len(picos))]
    tabla  = []
    for m in puntos:
        sub = picos[:m]
        mu  = sum(sub) / m
        sd  = (sum((x - mu)**2 for x in sub) / max(1, m - 1))**0.5
        ee  = sd / math.sqrt(m)
        tabla.append({"simulaciones": m, "pico_medio": round(mu, 1),
                      "error_std": round(ee, 2)})
    return tabla

# GRÁFICAS
def graficar_curvas_seir(sim: EpiSim, teorico: dict, out_dir: str):
    """
    Genera la gráfica 02: 02_curvas_seir.png promedio con banda de confianza al 95%.
 
    Muestra un panel por escenario (sin/con vacunación). Las curvas se suavizan
    con media móvil para reducir el ruido estocástico y facilitar la lectura.
    La banda IC 95% se grafica solo para I, que es el compartimento más relevante.
 
    Parámetros:
        sim     (EpiSim) : modelo ya ejecutado
        teorico (dict)   : salida de seir_teorico() (aunque no se usa aquí, se pasa por consistencia)
        out_dir (str)    : carpeta de salida
    """
    N = constants.N_POPULATION; dias = constants.DAYS
    t = list(range(1, dias + 1))
    n = len(sim.sin_vacunacion.resultados)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle(
        f"EpiSim SEIR — Curvas Epidémicas Promedio ± IC 95%\n"
        f"{n:,} simulaciones · N = {N:,} individuos · {dias} días",
        fontsize=13, fontweight="bold"
    )

    for ax, (esc, etiq) in zip(axes, [
        (sim.sin_vacunacion, "Sin Vacunación"),
        (sim.con_vacunacion, "Con Vacunación"),
    ]):
        pS  = suavizar([v/N*100 for v in esc.prom_S])
        pE  = suavizar([v/N*100 for v in esc.prom_E])
        pI  = suavizar([v/N*100 for v in esc.prom_I])
        pR  = suavizar([v/N*100 for v in esc.prom_R])
        loI = suavizar([v/N*100 for v in esc.lo_I])
        hiI = suavizar([v/N*100 for v in esc.hi_I])

        ax.plot(t, pS, color=COLORES["S"], lw=2.0, label="S — Susceptibles")
        ax.plot(t, pE, color=COLORES["E"], lw=1.8, label="E — Expuestos")
        ax.plot(t, pI, color=COLORES["I"], lw=2.8, label="I — Infectados")
        ax.plot(t, pR, color=COLORES["R"], lw=2.0, label="R — Recuperados")
        ax.fill_between(t, loI, hiI, color=COLORES["I"], alpha=0.18,
                        label="IC 95% (I)")

        # Anotación del pico para identificar el día y la magnitud de inmediato
        pico_pct = max(pI); dp = pI.index(pico_pct) + 1
        ax.annotate(
            f"Pico I: {pico_pct:.1f}%\n(Día {dp})",
            xy=(dp, pico_pct),
            xytext=(min(dp + 30, dias - 40), min(pico_pct + 6, 98)),
            arrowprops=dict(arrowstyle="->", color="darkred", lw=1.5),
            fontsize=9, color="darkred",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff9c4",
                      edgecolor="darkred")
        )

        ax.set_title(f"Escenario: {etiq}", fontweight="bold")
        ax.set_xlabel("Día"); ax.set_ylabel("Población (%)")
        ax.legend(fontsize=8); ax.grid(alpha=0.3)
        ax.set_xlim(1, dias); ax.set_ylim(-2, 105)

    plt.tight_layout()
    save(fig, "02_curvas_seir.png", out_dir)


def graficar_trayectorias(sim: EpiSim, out_dir: str):
    """
    Genera la gráfica 03: trayectorias individuales de I(t) nombrada como 03_trayectorias.png .
 
    Muestra hasta 40 simulaciones superpuestas en transparencia para visualizar
    la variabilidad estocástica entre corridas. Encima se dibuja el promedio
    y la banda IC 95%.
 
    Parámetros:
        sim     (EpiSim) : modelo ya ejecutado
        out_dir (str)    : carpeta de salida
    """
    N = constants.N_POPULATION; dias = constants.DAYS
    t = list(range(1, dias + 1))

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle(
        "Trayectorias Individuales de Infectados I(t)\n"
        "Variabilidad estocástica entre simulaciones independientes",
        fontsize=13, fontweight="bold"
    )

    for ax, (esc, col, etiq) in zip(axes, [
        (sim.sin_vacunacion, "#D32F2F", "Sin Vacunación"),
        (sim.con_vacunacion, "#1976D2", "Con Vacunación"),
    ]):
        # Se grafican 40 trayectorias muestreadas uniformemente del total
        paso = max(1, len(esc.resultados) // 40)
        for i in range(0, min(40 * paso, len(esc.resultados)), paso):
            ax.plot(t, [v/N*100 for v in esc.resultados[i].curva_I],
                    color=col, alpha=0.15, lw=0.8)
        ax.plot(t, suavizar([v/N*100 for v in esc.prom_I]),
                color="black", lw=2.8, label="Promedio", zorder=10)
        ax.fill_between(
            t,
            suavizar([v/N*100 for v in esc.lo_I]),
            suavizar([v/N*100 for v in esc.hi_I]),
            color=col, alpha=0.25, label="IC 95%"
        )
        s = esc.stats
        ax.text(0.98, 0.97,
                f"μ pico = {s['picos']['media']:.0f} ± {s['picos']['desv_std']:.0f}",
                transform=ax.transAxes, ha="right", va="top", fontsize=9,
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
        ax.set_title(f"Infectados I(t) — {etiq}", fontweight="bold")
        ax.set_xlabel("Día"); ax.set_ylabel("Infectados activos (%)")
        ax.legend(fontsize=9); ax.grid(alpha=0.3); ax.set_xlim(1, dias)

    plt.tight_layout()
    save(fig, "03_trayectorias.png", out_dir)

def graficar_comparacion(sim: EpiSim, out_dir: str):
    """
    Genera la gráfica 04: impacto de la vacunación sobre la epidemia nombrada como 04_comparacion.png .
 
    Panel izquierdo: curvas I(t) superpuestas de ambos escenarios con sus IC 95%
    y la reducción porcentual del pico.
    Panel derecho: barras comparativas de las tres métricas principales
    normalizadas al 100% para que sean comparables en escala.
 
    Parámetros:
        sim     (EpiSim) : modelo ya ejecutado
        out_dir (str)    : carpeta de salida
    """
    N = constants.N_POPULATION; dias = constants.DAYS
    t = list(range(1, dias + 1))
    sv = sim.sin_vacunacion; cv = sim.con_vacunacion

    fig = plt.figure(figsize=(16, 6), layout="constrained")
    gs  = gridspec.GridSpec(1, 3, figure=fig, wspace=0.35)
    fig.suptitle("Impacto de la Vacunación sobre la Epidemia\n"
                 "(parámetros epidemiológicos pareados — mismo β, σ, γ por par)",
                 fontsize=13, fontweight="bold")

    ax1   = fig.add_subplot(gs[0, :2])
    pI_sv = suavizar([v/N*100 for v in sv.prom_I])
    pI_cv = suavizar([v/N*100 for v in cv.prom_I])
    lo_sv = suavizar([v/N*100 for v in sv.lo_I])
    hi_sv = suavizar([v/N*100 for v in sv.hi_I])
    lo_cv = suavizar([v/N*100 for v in cv.lo_I])
    hi_cv = suavizar([v/N*100 for v in cv.hi_I])

    ax1.plot(t, pI_sv, "#D32F2F", lw=2.8, label="Sin vacunación")
    ax1.fill_between(t, lo_sv, hi_sv, color="#D32F2F", alpha=0.15)
    ax1.plot(t, pI_cv, "#1976D2", lw=2.8, label="Con vacunación")
    ax1.fill_between(t, lo_cv, hi_cv, color="#1976D2", alpha=0.15)

    pk_sv = max(pI_sv); pk_cv = max(pI_cv)
    red   = (pk_sv - pk_cv) / pk_sv * 100 if pk_sv > 0 else 0
    ax1.text(0.97, 0.96, f"Reducción pico I: {red:.1f}%",
             transform=ax1.transAxes, ha="right", va="top", fontsize=11,
             bbox=dict(boxstyle="round", facecolor="#e8f5e9", edgecolor="#388E3C"))
    ax1.set_xlabel("Día"); ax1.set_ylabel("Infectados activos I (%)")
    ax1.set_title("Infectados activos I(t): Sin vs Con Vacunación",
                  fontweight="bold")
    ax1.legend(fontsize=9); ax1.grid(alpha=0.3); ax1.set_xlim(1, dias)

    # Barras normalizadas para comparar magnitudes en distintas unidades
    ax2  = fig.add_subplot(gs[0, 2])
    mets = ["Pico I\n(personas)", "Total\ninfectados", "Día\ndel pico"]
    sv_v = [sv.stats["picos"]["media"], sv.stats["totales"]["media"],
            sv.stats["dias_p"]["media"]]
    cv_v = [cv.stats["picos"]["media"], cv.stats["totales"]["media"],
            cv.stats["dias_p"]["media"]]
    max_v = [max(s, c) for s, c in zip(sv_v, cv_v)]
    sv_n  = [v/m*100 for v, m in zip(sv_v, max_v)]
    cv_n  = [v/m*100 for v, m in zip(cv_v, max_v)]
    xp = list(range(3)); w = 0.32
    b1 = ax2.bar([x-w/2 for x in xp], sv_n, w, color="#D32F2F",
                 alpha=0.85, label="Sin vac.")
    b2 = ax2.bar([x+w/2 for x in xp], cv_n, w, color="#1976D2",
                 alpha=0.85, label="Con vac.")
    for b, v in zip(b1, sv_v):
        ax2.text(b.get_x()+b.get_width()/2, b.get_height()+1.5,
                 f"{v:.0f}", ha="center", va="bottom", fontsize=8,
                 color="#B71C1C")
    for b, v in zip(b2, cv_v):
        ax2.text(b.get_x()+b.get_width()/2, b.get_height()+1.5,
                 f"{v:.0f}", ha="center", va="bottom", fontsize=8,
                 color="#0D47A1")
    ax2.set_xticks(xp); ax2.set_xticklabels(mets, fontsize=9)
    ax2.set_ylabel("% respecto al máximo"); ax2.set_ylim(0, 120)
    ax2.set_title("Métricas comparadas\n(valores reales anotados)",
                  fontweight="bold")
    ax2.legend(fontsize=8); ax2.grid(alpha=0.3)

    save(fig, "04_comparacion.png", out_dir)


def graficar_histogramas(sim: EpiSim, out_dir: str):
    """
    Genera la gráfica 05: distribuciones de métricas clave + tablas descriptivas nombrada como
    05_histogramas.png .
 
    Fila superior: tres histogramas superpuestos (sin/con vacuna) para pico I,
    total de infectados y días hasta control.
    Fila inferior: tablas de estadísticas descriptivas por escenario + histograma
    bimodal que separa las simulaciones con extinción temprana de las epidemias
    completas cuando hay vacunación.
 
    La separación bimodal es importante porque mezclar extinción con epidemia
    completa distorsiona el promedio y la desviación estándar del escenario
    con vacunación.
 
    Parámetros:
        sim     (EpiSim) : modelo ya ejecutado
        out_dir (str)    : carpeta de salida
    """
    UMBRAL = 50  # pico ≤ 50 = extinción temprana
    N = constants.N_POPULATION
    n = len(sim.sin_vacunacion.resultados)
    sv = sim.sin_vacunacion; cv = sim.con_vacunacion

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle(
        f"Distribuciones de Métricas Epidémicas\n"
        f"Histogramas de {n:,} simulaciones Monte Carlo independientes",
        fontsize=13, fontweight="bold"
    )

    # Fila 0: histogramas superpuestos sin/con vacuna
    for col_i, (clave, titulo, xlabel) in enumerate([
        ("picos",    "Pico máximo de infectados I",   "Personas"),
        ("totales",  "Total de infectados acumulados", "Personas"),
        ("dias_c",   "Días hasta control epidémico",   "Día"),
    ]):
        ax = axes[0, col_i]
        for esc_stats, color, etiq in [
            (sv.stats, "#D32F2F", "Sin vac."),
            (cv.stats, "#1976D2", "Con vac."),
        ]:
            vals = esc_stats[clave]["raw"]
            mu   = sum(vals) / len(vals)
            sd   = (sum((x-mu)**2 for x in vals)/(len(vals)-1))**0.5
            ax.hist(vals, bins=min(30, max(5, len(set(vals)))),
                    color=color, alpha=0.55,
                    label=f"{etiq}\nμ={mu:.0f} ±{sd:.0f}")
        ax.set_title(titulo, fontweight="bold")
        ax.set_xlabel(xlabel); ax.set_ylabel("Frecuencia")
        ax.legend(fontsize=8); ax.grid(alpha=0.3)

    # Fila 1 col 0: tabla descriptiva Sin vacuna
    ax = axes[1, 0]
    s = sv.stats
    filas = [
        ["Métrica",    "Media",  "±Desv.", "Mediana", "Mín.",  "Máx."],
        ["Pico I",     f"{s['picos']['media']:.0f}",   f"{s['picos']['desv_std']:.0f}",
                       f"{s['picos']['mediana']:.0f}", f"{s['picos']['min']:.0f}",   f"{s['picos']['max']:.0f}"],
        ["Total inf.", f"{s['totales']['media']:.0f}", f"{s['totales']['desv_std']:.0f}",
                       f"{s['totales']['mediana']:.0f}",f"{s['totales']['min']:.0f}",f"{s['totales']['max']:.0f}"],
        ["Día pico",   f"{s['dias_p']['media']:.0f}",  f"{s['dias_p']['desv_std']:.0f}",
                       f"{s['dias_p']['mediana']:.0f}",f"{s['dias_p']['min']:.0f}",  f"{s['dias_p']['max']:.0f}"],
        ["Día ctrl",   f"{s['dias_c']['media']:.0f}",  f"{s['dias_c']['desv_std']:.0f}",
                       f"{s['dias_c']['mediana']:.0f}",f"{s['dias_c']['min']:.0f}",  f"{s['dias_c']['max']:.0f}"],
        ["β",          f"{s['betas']['media']:.3f}",   f"{s['betas']['desv_std']:.3f}",
                       f"{s['betas']['mediana']:.3f}", f"{s['betas']['min']:.3f}",   f"{s['betas']['max']:.3f}"],
        ["p efect.",   f"{s['p_efec']['media']:.3f}",  f"{s['p_efec']['desv_std']:.3f}",
                       f"{s['p_efec']['mediana']:.3f}",f"{s['p_efec']['min']:.3f}",  f"{s['p_efec']['max']:.3f}"],
    ]
    tbl = ax.table(cellText=filas[1:], colLabels=filas[0],
                   loc="center", cellLoc="center")
    tbl.auto_set_font_size(False); tbl.set_fontsize(9); tbl.scale(1, 1.6)
    for (row, col_), cell in tbl.get_celld().items():
        if row == 0:
            cell.set_facecolor("#D32F2F")
            cell.set_text_props(color="white", fontweight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#f5f5f5")
    ax.set_title("Estadísticas Descriptivas — Sin Vacunación", fontweight="bold")
    ax.axis("off")

    # Fila 1 col 1: tabla descriptiva Con vacuna con anotación de extinción
    ax = axes[1, 1]
    c = cv.stats
    picos_cv  = c["picos"]["raw"]
    n_extin   = sum(1 for p in picos_cv if p <= UMBRAL)
    pct_extin = 100 * n_extin / len(picos_cv)
    filas2 = [
        ["Métrica",    "Media",  "±Desv.", "Mediana", "Mín.",  "Máx."],
        ["Pico I",     f"{c['picos']['media']:.0f}",   f"{c['picos']['desv_std']:.0f}",
                       f"{c['picos']['mediana']:.0f}", f"{c['picos']['min']:.0f}",   f"{c['picos']['max']:.0f}"],
        ["Total inf.", f"{c['totales']['media']:.0f}", f"{c['totales']['desv_std']:.0f}",
                       f"{c['totales']['mediana']:.0f}",f"{c['totales']['min']:.0f}",f"{c['totales']['max']:.0f}"],
        ["Día pico",   f"{c['dias_p']['media']:.0f}",  f"{c['dias_p']['desv_std']:.0f}",
                       f"{c['dias_p']['mediana']:.0f}",f"{c['dias_p']['min']:.0f}",  f"{c['dias_p']['max']:.0f}"],
        ["Día ctrl",   f"{c['dias_c']['media']:.0f}",  f"{c['dias_c']['desv_std']:.0f}",
                       f"{c['dias_c']['mediana']:.0f}",f"{c['dias_c']['min']:.0f}",  f"{c['dias_c']['max']:.0f}"],
        ["β",          f"{c['betas']['media']:.3f}",   f"{c['betas']['desv_std']:.3f}",
                       f"{c['betas']['mediana']:.3f}", f"{c['betas']['min']:.3f}",   f"{c['betas']['max']:.3f}"],
        ["p efect.",   f"{c['p_efec']['media']:.3f}",  f"{c['p_efec']['desv_std']:.3f}",
                       f"{c['p_efec']['mediana']:.3f}",f"{c['p_efec']['min']:.3f}",  f"{c['p_efec']['max']:.3f}"],
    ]
    tbl2 = ax.table(cellText=filas2[1:], colLabels=filas2[0],
                    loc="center", cellLoc="center")
    tbl2.auto_set_font_size(False); tbl2.set_fontsize(9); tbl2.scale(1, 1.6)
    for (row, col_), cell in tbl2.get_celld().items():
        if row == 0:
            cell.set_facecolor("#1976D2")
            cell.set_text_props(color="white", fontweight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#f5f5f5")
    titulo_cv = (f"Estadísticas — Con Vacunación\n"
                 f"({n_extin} sims con extinción temprana = {pct_extin:.0f}%)")
    ax.set_title(titulo_cv, fontweight="bold")
    ax.axis("off")

    # Fila 1 col 2: bimodal — epidemia completa vs extinción temprana separadas
    ax = axes[1, 2]
    picos_epid  = [p for p in picos_cv if p >  UMBRAL]
    picos_extin = [p for p in picos_cv if p <= UMBRAL]
    if picos_epid:
        ax.hist(picos_epid, bins=30, color="#1976D2", alpha=0.75,
                label=f"Epidemia completa (n={len(picos_epid)})")
    if picos_extin:
        ax.hist(picos_extin, bins=15, color="#78909C", alpha=0.75,
                label=f"Extinción temprana (n={len(picos_extin)})")
    ax.axvline(UMBRAL, color="black", lw=1.5, linestyle="--",
               label=f"Umbral ={UMBRAL}")
    ax.set_title("Pico I — Con Vacunación\n(epidemia vs extinción separadas)",
                 fontweight="bold")
    ax.set_xlabel("Personas"); ax.set_ylabel("Frecuencia")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    ax.text(0.97, 0.60,
            "La extinción temprana ocurre\ncuando p_efectiva ≈ 0 por\n"
            "alta cobertura vacunal.\nEs un resultado válido del\nmodelo estocástico.",
            transform=ax.transAxes, ha="right", va="top", fontsize=7.5,
            bbox=dict(boxstyle="round", facecolor="#E3F2FD", edgecolor="#1976D2",
                      alpha=0.9))

    plt.tight_layout()
    save(fig, "05_histogramas.png", out_dir)



def graficar_sensibilidad(sensibilidad: dict, out_dir: str):
    """
    Genera la gráfica 06: análisis de sensibilidad con diagrama tornado nombrada como
    06_sensibilidad.png .
 
    Panel izquierdo: barras horizontales con el pico promedio para cada nivel
    de cada parámetro. Permite ver cómo evoluciona el pico al aumentar la intensidad.
    Panel derecho: diagrama tornado clásico ordenado por impacto (Δ rango).
    El parámetro con la barra más larga es el que más influye sobre la epidemia.
 
    Parámetros:
        sensibilidad (dict) : salida de EpiSim._analisis_sensibilidad()
        out_dir      (str)  : carpeta de salida
    """
    cols_s  = ["#E91E63", "#9C27B0", "#009688"]
    nombres = list(sensibilidad.keys())

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle(
        "Análisis de Sensibilidad — Parámetros Epidémicos\n"
        "Impacto de β, p_trans y tasa de vacunación sobre el pico de infectados",
        fontsize=13, fontweight="bold"
    )

    # Panel izquierdo: barras por nivel de parámetro
    ax = axes[0]
    for idx, (nom, datos) in enumerate(sensibilidad.items()):
        yp = [idx * 6 + i for i in range(len(datos["picos"]))]
        ax.barh(yp, datos["picos"], color=cols_s[idx], alpha=0.80,
                label=nom, height=0.8)
        for pos, (pk, et) in zip(yp, zip(datos["picos"], datos["etiquetas"])):
            ax.text(30, pos, et, va="center", fontsize=8)
            ax.text(pk + 50, pos, f"{pk:.0f}", va="center", fontsize=8,
                    fontweight="bold")
    ax.set_xlabel("Pico promedio de infectados (personas)")
    ax.set_title("Impacto por nivel de parámetro", fontweight="bold")
    ax.legend(fontsize=9, loc="lower right"); ax.grid(alpha=0.3); ax.set_yticks([])

    # Panel derecho: tornado, muestra directamente qué parámetro importa más
    ax2   = axes[1]
    rango = [sensibilidad[n]["rango"] for n in nombres]
    medio = [(max(sensibilidad[n]["picos"]) + min(sensibilidad[n]["picos"])) / 2
             for n in nombres]
    orden = sorted(range(len(rango)), key=lambda i: rango[i])
    for i, oi in enumerate(orden):
        ax2.barh(i, rango[oi], left=medio[oi] - rango[oi]/2,
                 height=0.5, color=cols_s[oi], alpha=0.85)
        ax2.text(medio[oi] + rango[oi]/2 + 50, i,
                 f"Δ = ±{rango[oi]:.0f}",
                 va="center", fontsize=10, fontweight="bold")
    ax2.set_yticks(range(len(orden)))
    ax2.set_yticklabels([nombres[oi] for oi in orden], fontsize=10)
    ax2.set_xlabel("Rango del pico I (personas)")
    ax2.set_title("Diagrama Tornado\n(barra más larga = mayor impacto)",
                  fontweight="bold")
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    save(fig, "06_sensibilidad.png", out_dir)


def graficar_convergencia(tabla: list, out_dir: str):
    """
    Genera la gráfica 07: convergencia del estimador Monte Carlo nombrada como
    07_convergencia.png .
 
    Muestra que al aumentar el número de simulaciones, el pico medio converge
    y el error estándar decrece como 1/√n, confirmando el Teorema Central
    del Límite. El panel log-log hace visible esa relación de forma directa.
 
    Parámetros:
        tabla   (list) : salida de analisis_convergencia()
        out_dir (str)  : carpeta de salida
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(
        "Convergencia del Pico de Infectados\n"
        "(Demostración del Teorema Central del Límite)",
        fontsize=13, fontweight="bold"
    )

    x  = [row["simulaciones"] for row in tabla]
    y  = [row["pico_medio"]   for row in tabla]
    ee = [row["error_std"]    for row in tabla]

    ax1.errorbar(x, y, yerr=ee, fmt="o-", color="steelblue",
                 linewidth=2, markersize=8, capsize=5, label="Pico I ± EE")
    ax1.set_xscale("log")
    ax1.set_xlabel("Número de simulaciones (escala log)")
    ax1.set_ylabel("Pico medio de infectados")
    ax1.set_title("Convergencia del estimador", fontweight="bold")
    ax1.grid(alpha=0.4); ax1.legend()
    for row in tabla:
        ax1.annotate(f"EE={row['error_std']:.1f}",
                     xy=(row["simulaciones"], row["pico_medio"]),
                     xytext=(5, 8), textcoords="offset points", fontsize=8)

    # Panel log-log del error estándar, la pendiente debería ser -0.5 si se cumple el TCL
    ax2.loglog(x[1:], ee[1:], "o-", color="coral", linewidth=2, markersize=8)
    ax2.set_xlabel("Número de simulaciones (escala log)")
    ax2.set_ylabel("Error estándar (escala log)")
    ax2.set_title("Reducción del EE (escala log-log)", fontweight="bold")
    ax2.grid(alpha=0.4, which="both")

    plt.tight_layout()
    save(fig, "07_convergencia.png", out_dir)

def graficar_empate_bibliografico(sim: EpiSim, teorico: dict, out_dir: str):
    """
    Genera la gráfica 08: criterio de empate estocástico vs determinístico
    es nombrada 08_empate_bibliografico.png .
 
    Compara el escenario SIN vacunación contra el SEIR determinístico calibrado
    con los parámetros efectivos del mecanismo estocástico.
    Un evaluador puede verificar que el modelo Monte Carlo reproduce el
    comportamiento esperado por la teoría epidemiológica clásica.
 
    Para I se usa IC 95% (percentiles). Para S, E, R se usa ±1σ diaria porque
    el IC 95% en esos compartimentos resulta en bandas muy amplias por la
    dispersión temporal de inicio de epidemia entre simulaciones.
 
    Parámetros:
        sim     (EpiSim) : modelo ya ejecutado
        teorico (dict)   : salida de seir_teorico()
        out_dir (str)    : carpeta de salida
    """
    N    = constants.N_POPULATION
    dias = constants.DAYS
    t    = list(range(1, dias + 1))
    sv   = sim.sin_vacunacion
    n    = len(sv.resultados)

    # Promedios suavizados (en %)
    promedios = {
        "S": suavizar([v/N*100 for v in sv.prom_S]),
        "E": suavizar([v/N*100 for v in sv.prom_E]),
        "I": suavizar([v/N*100 for v in sv.prom_I]),
        "R": suavizar([v/N*100 for v in sv.prom_R]),
    }

    # IC 95% para I
    lo_I = suavizar([v/N*100 for v in sv.lo_I])
    hi_I = suavizar([v/N*100 for v in sv.hi_I])

    # ±1σ diaria para S, E, R
    def banda_std(attr_curva):
        """±1σ diaria, más informativa que IC 95% para S/E/R con timing disperso."""
        lo_list, hi_list = [], []
        for d in range(dias):
            vals = [getattr(r, attr_curva)[d] / N * 100 for r in sv.resultados]
            mu   = sum(vals) / len(vals)
            sd   = (sum((x-mu)**2 for x in vals) / (len(vals)-1))**0.5
            lo_list.append(max(0., mu - sd))
            hi_list.append(min(100., mu + sd))
        return suavizar(lo_list), suavizar(hi_list)

    bandas = {
        "S": banda_std("curva_S"),
        "E": banda_std("curva_E"),
        "R": banda_std("curva_R"),
    }

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(
        "Criterio de Empate — Simulación Monte Carlo vs Modelo SEIR Teórico\n"
        "Escenario Sin Vacunación · β_eff=0.2714 · σ=0.2857 · γ=0.0952 · R0≈2.85\n"
        "(línea sólida = promedio simulado · línea punteada = SEIR determinístico)",
        fontsize=11, fontweight="bold"
    )

    config = [
        ("S", COLORES["S"], "Susceptibles",  "curva_S", "±1σ diaria"),
        ("E", COLORES["E"], "Expuestos",     "curva_E", "±1σ diaria"),
        ("I", COLORES["I"], "Infectados",    "curva_I", "IC 95%"),
        ("R", COLORES["R"], "Recuperados",   "curva_R", "±1σ diaria"),
    ]

    for ax, (comp, color, nombre, attr_curva, ic_label) in zip(axes.flat, config):
        prom = promedios[comp]
        teo  = [v/N*100 for v in teorico[comp]]
        lo, hi = (lo_I, hi_I) if comp == "I" else bandas[comp]

        ax.fill_between(t, lo, hi, color=color, alpha=0.20, label=ic_label)
        ax.plot(t, prom, color=color, lw=2.5,
                label=f"{comp} simulado (promedio)")
        ax.plot(t, teo,  color=color, lw=1.8, ls="--", alpha=0.85,
                label=f"{comp} teórico (SEIR det.)")

        # Anotaciones del pico solo en I para no saturar los otros paneles
        if comp == "I":
            pico_sim = max(prom); dp_sim = prom.index(pico_sim) + 1
            pico_teo = max(teo);  dp_teo = teo.index(pico_teo) + 1
            ax.annotate(
                f"Sim: {pico_sim:.1f}%\n(Día {dp_sim})",
                xy=(dp_sim, pico_sim),
                xytext=(min(dp_sim + 25, dias - 60), pico_sim + 3),
                arrowprops=dict(arrowstyle="->", color="darkred", lw=1.3),
                fontsize=8, color="darkred",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff9c4",
                          edgecolor="darkred")
            )
            ax.annotate(
                f"Teo: {pico_teo:.1f}%\n(Día {dp_teo})",
                xy=(dp_teo, pico_teo),
                xytext=(min(dp_teo + 25, dias - 60), pico_teo - 8),
                arrowprops=dict(arrowstyle="->", color="#555", lw=1.3),
                fontsize=8, color="#555",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#f0f0f0",
                          edgecolor="#555")
            )

        ax.set_title(f"{nombre} ({comp})", fontweight="bold", fontsize=11)
        ax.set_xlabel("Día de simulación")
        ax.set_ylabel("Población (%)")
        ax.legend(fontsize=8, loc="best")
        ax.grid(alpha=0.3)
        ax.set_xlim(0, dias); ax.set_ylim(-2, 105)

    plt.tight_layout()
    save(fig, "08_empate_bibliografico.png", out_dir)

def imprimir_tabla(sim: EpiSim):
    """
    Imprime en consola la tabla comparativa de estadísticas descriptivas.
 
    Muestra media ± desviación estándar y rango [min–max] para las cuatro
    métricas principales de cada escenario, junto con la reducción porcentual
    atribuida a la vacunación y los tiempos de CPU.
 
    Parámetros:
        sim (EpiSim) : modelo ya ejecutado
    """
    print("\n" + "="*72)
    print("  TABLA DE ESTADÍSTICAS DESCRIPTIVAS (1,000 simulaciones)")
    print("="*72)
    print(f"  {'Métrica':<35} {'Sin vacuna':>16} {'Con vacuna':>16}")
    print("-"*72)
    sv = sim.sin_vacunacion.stats
    cv = sim.con_vacunacion.stats
    for nombre, key in [("Pico infectados", "picos"),
                         ("Día del pico",    "dias_p"),
                         ("Total infectados","totales"),
                         ("Día de control",  "dias_c")]:
        s = sv[key]; c = cv[key]
        col_s = f"{s['media']:.0f} ± {s['desv_std']:.0f}"
        col_c = f"{c['media']:.0f} ± {c['desv_std']:.0f}"
        rng_s = f"[{s['min']:.0f}–{s['max']:.0f}]"
        rng_c = f"[{c['min']:.0f}–{c['max']:.0f}]"
        print(f"  {nombre+' (media ± std)':<35} {col_s:>16} {col_c:>16}")
        print(f"  {'  [min – max]':<35} {rng_s:>16} {rng_c:>16}")
        print("-"*72)

    sv_p = sv["picos"]["media"];   cv_p = cv["picos"]["media"]
    sv_t = sv["totales"]["media"]; cv_t = cv["totales"]["media"]
    if sv_p > 0:
        print(f"\n  Reducción pico  por vacunación : {(sv_p-cv_p)/sv_p*100:.1f}%")
    if sv_t > 0:
        print(f"  Reducción total por vacunación : {(sv_t-cv_t)/sv_t*100:.1f}%")
    print(f"\n  Tiempo sin vacunación          : {sim.sin_vacunacion.tiempo_s:.2f} s")
    print(f"  Tiempo con vacunación          : {sim.con_vacunacion.tiempo_s:.2f} s")
    print(f"  Tiempo total                   : {sim.tiempo_total_s} s")
    print("="*72)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EpiSim PLATINUM — SEIR Monte Carlo UPTC")
    parser.add_argument("--config", type=str, default=None,
                        help="Ruta a archivo CSV de configuración")
    args = parser.parse_args()

    if args.config:
        cargar_config(args.config)

    OUT_DIR = "salidas"

    sim = EpiSim()
    sim.execute()

    tabla_conv = analisis_convergencia(sim)
    teorico    = seir_teorico()

    print("\n  Generando gráficas...")
    sim.pool.guardar_validacion(os.path.join(OUT_DIR, "01_validacion_generador.png"))
    print(f"  [+] {OUT_DIR}/01_validacion_generador.png")

    graficar_curvas_seir(sim, teorico, OUT_DIR)
    graficar_trayectorias(sim, OUT_DIR)
    graficar_comparacion(sim, OUT_DIR)
    graficar_histogramas(sim, OUT_DIR)
    graficar_sensibilidad(sim.sensibilidad, OUT_DIR)
    graficar_convergencia(tabla_conv, OUT_DIR)
    graficar_empate_bibliografico(sim, teorico, OUT_DIR)

    imprimir_tabla(sim)