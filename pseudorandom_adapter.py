"""
Adaptador que conecta la biblioteca de generadores y validadores con Episim

Generador seleccionado: Congruencia Lineal (LCG)
    Parámetros: a=1664525, c=1013904223, m=2^32  (Numerical Recipes / ANSI C)
    Justificación: período completo 2^32 ≈ 4.3 x 10^9, supera el millón de
    números requerido con amplio margen

Pruebas ejecutadas:
    'Medias', 'Varianza', 'Chi Cuadrado', 'Kolmogorov Smirnov', 'Poker', 'Rachas'
"""

import sys
import os
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

"""
Agrega la carpeta de la biblioteca del Punto 3 al path de Python
Esto permite importar sus módulos
"""
_PSEUDORANDOM_LIBRARY  = os.path.join(os.path.dirname(__file__), "Generadores-de-n-meros-pseudoaleatorios-main")
if _PSEUDORANDOM_LIBRARY not in sys.path:
    sys.path.insert(0, _PSEUDORANDOM_LIBRARY)

"""
Importa lo que se necesita de la biblioteca del generdor
ValidacionService se importa directamente desde su módulo para evitar
cargar el __init__.py que viene con entorno GUI
"""
from generador_numeros.congruencia_lineal import GeneradorCongruenciaLineal

import importlib.util as _ilu

def _import_directo(nombre_modulo: str, ruta_relativa: str):
    ruta_abs = os.path.join(_PSEUDORANDOM_LIBRARY, ruta_relativa)
    spec = _ilu.spec_from_file_location(nombre_modulo, ruta_abs)
    mod  = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_vs_mod         = _import_directo("validacion_service_p3",
                                   "app_services/validacion_service.py")
ValidacionService = _vs_mod.ValidacionService

"""
Matriz s,x  — estructura de trazabilidad del generador
Documenta el estado completo del generador

Nota: la secuencia se llena directamente desde el pool generado,
no número a número, porque GeneradorCongruenciaLineal del Punto 3
produce toda la secuencia de una vez sin exponer un método next()
"""
class _MatrizEstado:
    """Registra el estado completo del generador para trazabilidad."""

    def __init__(self, semilla: int, parametros: dict):
        self.semilla_inicial = semilla
        self.parametros      = parametros.copy()
        self.secuencia       = []          # primeros 20 valores
        self.n_generados     = 0
        self.ultimo_x        = None

    def registrar(self, valor: float):
        self.n_generados += 1
        self.ultimo_x = valor
        if len(self.secuencia) < 20:
            self.secuencia.append(round(valor, 8))

    def resumen(self) -> str:
        lineas = [
            "=" * 52,
            "  MATRIZ s,x — Estado del Generador (Punto 3 · LCG)",
            "=" * 52,
            f"  Semilla inicial (s)  : {self.semilla_inicial}",
            f"  Parámetros           : {self.parametros}",
            f"  Números generados    : {self.n_generados:,}",
            f"  Último valor (x_n)   : {self.ultimo_x}",
            f"  Primeros 10 valores  : {self.secuencia[:10]}",
            "=" * 52,
        ]
        return "\n".join(lineas)

def generar_pool_global(semilla: int = 42, n: int = 1_000_000) -> list:
    """
    Genera un pool de n números U(0,1) usando el LCG del Punto 3.
    
    Parámetros:
        semilla (int) : semilla documentada (Matriz s,x)
        n       (int) : tamaño del pool (por defecto 1,000,000)

    Retorno:
        list[float]  → n valores en [0, 1)
    """
    # Generador de números pseudoaleatorios (Punto 3)
    gen_pseudoaleatorio = GeneradorCongruenciaLineal(semilla=semilla)

    # Matriz s,x para trazabilidad
    estado = _MatrizEstado(
        semilla=semilla,
        parametros={"a": gen_pseudoaleatorio.a, "c": gen_pseudoaleatorio.c, "m": gen_pseudoaleatorio.m,
                    "método": "Congruencia Lineal (Punto 3)"}
    )
    
    # Genera los n números de una sola vez por eficiencia
    pool = gen_pseudoaleatorio.siguiente_Ri_Congruencia_Lineal(n)

    # Registra los primeros 20 valores en la matriz s,x
    for v in pool[:20]:
        estado.registrar(v)
    # Completa el contador con el resto ya que solo se registran 20 por eficiencia
    estado.n_generados = n
    estado.ultimo_x    = pool[-1] if pool else None

    print(f"[Pool Global · Punto 3] Generados {n:,} números con LCG "
          f"(semilla={semilla})")
    print(estado.resumen())
    return pool

"""
VALIDAR GENERADOR  — Probador General
"""
# Lista con los nombres exactos que ValidacionService del Punto 3 reconoce internamente.
_PRUEBAS_GENERADOR = [
    "Medias",
    "Varianza",
    "Chi Cuadrado",
    "Kolmogorov Smirnov",
    "Poker",
    "Rachas",
]

# Diccionario que traduce los nombres del generador a los de Episim (posibilidad de cambiar de validador)
_CLAVE_MAP = {
    "Medias":              "medias",
    "Varianza":            "varianza",
    "Chi Cuadrado":        "chi2",
    "Kolmogorov Smirnov":  "ks",
    "Poker":               "poker",
    "Rachas":              "rachas",
}


def validar_generador(numeros: list, alpha: float = 0.05,
                      verbose: bool = True) -> dict:
    """
    Ejecuta las 6 pruebas estadísticas del Punto 3 sobre la secuencia.
    
    Parámetros:
        numeros (list[float]) : secuencia a validar
        alpha   (float)       : nivel de significancia
            alpha no es usado directamente por el generador actual, se conserva para
            evitar cambios riesgosos ahora o en el futuro en episim_simulation.py
        verbose (bool)        : imprimir resumen en consola

    Retorno:
        resultados (dict)     : resultados de las pruebas
    """
    
    # Limitar la muestra a 10000 para eficiencia ya que KS y Rachas son computacionalmente costososs
    muestra = numeros[:10_000] if len(numeros) > 10_000 else numeros

    # Ejecuta todas las pruebas usando la librería actual
    resultados_pruebas: list[tuple[str, bool, str]] = ValidacionService.ejecutar_pruebas(
        muestra,
        pruebas_activas=_PRUEBAS_GENERADOR,
        metodo=None,                        # Sin transformaciones porque la secuencia ya está en U(0,1)
        params_dist=None,                   # Sin parametros porque no se usa el método de transformación
    )

    # Convierte la lista de tuplas en el dict que EpiSim espera (transformación debida a cambio de validadores)
    resultados = {}
    for (nombre_prueba, paso, detalle) in resultados_pruebas:
        clave = _CLAVE_MAP.get(nombre_prueba, nombre_prueba.lower())
        resultados[clave] = {
            "prueba"      : nombre_prueba,
            "aprueba_H0"  : paso,
            "conclusion"  : "APRUEBA" if paso else "RECHAZA",
            "detalle_p3"  : detalle,
        }

    # Si todas aprueban, todas = True
    todas = all(r["aprueba_H0"] for r in resultados.values())
    # Resultado general de aprobación
    resultados["todas_aprueban"] = todas

    # Imprime los resultados
    if verbose:
        print("\n" + "=" * 58)
        print("  PROBADOR GENERAL (Punto 3) — Resultados de Validación")
        print("=" * 58)
        print(f"  {'Prueba':<26} {'Resultado':<12} {'Detalle'}")
        print("-" * 58)
        orden = ["Medias", "Varianza", "Chi Cuadrado",
                 "Kolmogorov Smirnov", "Poker", "Rachas"]
        for nombre in orden:
            clave = _CLAVE_MAP.get(nombre, nombre.lower())
            if clave not in resultados:
                continue
            r = resultados[clave]
            icono = "✓" if r["aprueba_H0"] else "✗"
            det = r.get("detalle_p3", "")[:25]
            print(f"  {nombre:<26} {icono} {r['conclusion']:<10}  {det}")
        print("-" * 58)
        estado_txt = "✓ GENERADOR VÁLIDO" if todas else "✗ GENERADOR NO VÁLIDO"
        print(f"  Estado general: {estado_txt}")
        print("=" * 58 + "\n")

    return resultados

"""
GRAFICACIÓN DE LAS VALIDACIONES
"""
def graficar_validacion(numeros: list, resultados: dict,
                        ruta_salida: str = "validacion.png"):
    """
    Genera un panel de 6 gráficas de validación y lo guarda en ruta_salida

    Usa los datos de la secuencia y los resultados del Probador General para
    construir las visualizaciones

    Parámetros:
        numeros      (list[float]) : secuencia original (pool global)
        resultados   (dict)        : salida de validar_generador()
        ruta_salida  (str)         : ruta del archivo PNG a guardar
    """
    # Las gráficas muestran exactamente los mismos datos que se validaron estadísticamente
    muestra = numeros[:10_000] if len(numeros) > 10_000 else numeros
    n = len(muestra)

    fig = plt.figure(figsize=(16, 10))
    fig.suptitle(
        "Probador General (Punto 3) — Panel de Validación Estadística\n"
        "Generador: Congruencia Lineal · a=1664525, c=1013904223, m=2³²",
        fontsize=13, fontweight="bold", y=0.99
    )
    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.50, wspace=0.38)

    # 1. Histograma general (Prueba de Medias)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.hist(muestra, bins=30, color="steelblue", edgecolor="white", alpha=0.85)
    media_obs = sum(muestra) / n
    ax1.axvline(0.5,       color="red",    linestyle="--", lw=1.5, label="μ teórica=0.5")
    ax1.axvline(media_obs, color="orange", linestyle="-",  lw=1.5,
                label=f"μ obs={media_obs:.4f}")
    r_med = resultados.get("medias", {})
    ax1.set_title(f"Distribución general\n(Medias: {r_med.get('conclusion','—')})",
                  fontsize=9)
    ax1.set_xlabel("Valor"); ax1.set_ylabel("Frecuencia")
    ax1.legend(fontsize=7)

    # 2. Varianza
    ax2 = fig.add_subplot(gs[0, 1])
    var_obs = sum((x - media_obs)**2 for x in muestra) / (n - 1)
    var_teo = 1.0 / 12.0
    r_var   = resultados.get("varianza", {})
    ax2.bar(["Varianza\nObservada", "Varianza\nTeórica"],
            [var_obs, var_teo],
            color=["steelblue", "salmon"], edgecolor="white")
    ax2.set_title(f"Prueba de Varianza\n{r_var.get('conclusion','—')}", fontsize=9)
    ax2.set_ylabel("Valor")
    for i, v in enumerate([var_obs, var_teo]):
        ax2.text(i, v + 0.0003, f"{v:.5f}", ha="center", fontsize=8)

    # 3. Chi-cuadrado (frecuencias obs vs esperadas)
    ax3 = fig.add_subplot(gs[0, 2])
    k = 10
    esp = n / k
    obs_chi = [0] * k
    for x in muestra:
        idx = min(int(x * k), k - 1)
        obs_chi[idx] += 1
    r_chi2 = resultados.get("chi2", {})
    ax3.bar(range(k), obs_chi, color="steelblue", alpha=0.7, label="Observado")
    ax3.axhline(esp, color="red", linestyle="--", lw=1.5,
                label=f"Esperado≈{esp:.0f}")
    ax3.set_title(f"Chi-cuadrado Uniformidad\n{r_chi2.get('conclusion','—')}",
                  fontsize=9)
    ax3.set_xlabel("Intervalo"); ax3.set_ylabel("Frecuencia")
    ax3.legend(fontsize=7)

    # 4. Kolmogorov-Smirnov (FEC vs teórica)
    ax4 = fig.add_subplot(gs[1, 0])
    sorted_m = sorted(muestra)
    paso = max(1, n // 500)
    fx = sorted_m[::paso]
    fy = [(i + 1) / n for i in range(n)][::paso]
    ax4.plot(fx, fy, color="steelblue", lw=1, label="F_n (empírica)")
    ax4.plot([0, 1], [0, 1], "r--", lw=1.5, label="U(0,1) teórica")
    r_ks = resultados.get("ks", {})
    ax4.set_title(f"Kolmogorov-Smirnov\n{r_ks.get('conclusion','—')}", fontsize=9)
    ax4.set_xlabel("x"); ax4.set_ylabel("F(x)")
    ax4.legend(fontsize=7)

    # 5. Póker (categorías)
    ax5 = fig.add_subplot(gs[1, 1])
    cats = ["Todos\ndist.", "Un\npar", "Dos\npares",
            "Tercia", "Full", "Póker\n4ig.", "Quintilla"]
    p_teo = [0.30240, 0.50400, 0.10800, 0.07200, 0.00900, 0.00450, 0.00010]
    d_pk = 5
    n_gr = n // d_pk
    from collections import Counter
    obs_pk = [0] * 7
    cat_keys = ["Todos_distintos","Un_par","Dos_pares","Tercia",
                "Full","Poker_4iguales","Quintilla"]
    def _clasicar(g):
        c = Counter(int(x * 10) % 10 for x in g)
        f = sorted(c.values(), reverse=True)
        if   f[0]==5: return 6
        elif f[0]==4: return 5
        elif f[0]==3 and len(f)>1 and f[1]==2: return 4
        elif f[0]==3: return 3
        elif f[0]==2 and len(f)>1 and f[1]==2: return 2
        elif f[0]==2: return 1
        else: return 0
    for i in range(n_gr):
        g = muestra[i*d_pk:(i+1)*d_pk]
        obs_pk[_clasicar(g)] += 1
    esp_pk = [n_gr * p for p in p_teo]
    x_pos = list(range(7))
    ax5.bar([x - 0.2 for x in x_pos], obs_pk, width=0.4,
            color="steelblue", alpha=0.8, label="Observado")
    ax5.bar([x + 0.2 for x in x_pos], esp_pk, width=0.4,
            color="salmon", alpha=0.8, label="Esperado")
    ax5.set_xticks(x_pos); ax5.set_xticklabels(cats, fontsize=7)
    r_pk = resultados.get("poker", {})
    ax5.set_title(f"Prueba de Póker\n{r_pk.get('conclusion','—')}", fontsize=9)
    ax5.legend(fontsize=7)

    # 6. Rachas
    ax6 = fig.add_subplot(gs[1, 2])
    rachas = 1
    for i in range(1, n):
        if i > 1:
            if (muestra[i] > muestra[i-1]) != (muestra[i-1] > muestra[i-2]):
                rachas += 1
        else:
            if muestra[i] != muestra[i-1]:
                rachas += 1
    rachas_esp = (2 * n - 1) / 3
    r_rc = resultados.get("rachas", {})
    ax6.bar(["Rachas\nObservadas", "Rachas\nEsperadas"],
            [rachas, rachas_esp],
            color=["steelblue", "salmon"], edgecolor="white")
    ax6.set_title(f"Prueba de Rachas\n{r_rc.get('conclusion','—')}", fontsize=9)
    ax6.set_ylabel("Número de rachas")

    plt.savefig(ruta_salida, dpi=130, bbox_inches="tight")
    plt.close()
    print(f"[Validación · Punto 3] Gráfica guardada: {ruta_salida}")