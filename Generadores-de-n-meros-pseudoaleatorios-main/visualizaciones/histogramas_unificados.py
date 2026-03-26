"""Utilidades para visualizar histogramas de generadores y distribuciones."""

import matplotlib.pyplot as plt
import numpy as np
from distribuciones.normal import GeneradorDistribucionNormal
from distribuciones.uniforme import GeneradorDistribucionUniforme
from generador_numeros.congruencia_lineal import GeneradorCongruenciaLineal
from generador_numeros.congruencial_aditivo import GeneradorCongruencialAditivo
from generador_numeros.congruencial_multiplicativo import GeneradorCongruencialMultiplicativo
from generador_numeros.cuadrados_medios import GeneradorCuadradosMedios


def _imprimir_estadisticas(numeros, esperado_texto):
    """Imprime un resumen estadistico comun para cualquier muestra."""
    print("\n--- Estadisticas ---")
    print(f"Total de numeros: {len(numeros)}")
    print(f'Lista de numeros: {numeros[:10]}{"..." if len(numeros) > 10 else ""}')
    print(f"Minimo: {min(numeros):.8f}")
    print(f"Maximo: {max(numeros):.8f}")
    print(f"Media: {sum(numeros) / len(numeros):.8f}")
    print(f"Esperado: {esperado_texto}")


def _graficar_histogramas(
    numeros,
    titulo,
    bins=50,
    rango=None,
    xticks=None,
    x_label="Valor",
):
    """
    Dibuja dos histogramas de la misma secuencia:
    1. Escala normal
    2. Escala logaritmica

    Parameters
    ----------
    numeros : list[float]
        Secuencia de valores a visualizar.
    titulo : str
        Titulo general de la figura.
    bins : int, optional
        Numero de intervalos del histograma.
    rango : tuple[float, float] | None, optional
        Rango del eje X para ambos histogramas.
    xticks : list[float] | np.ndarray | None, optional
        Marcas del eje X.
    x_label : str, optional
        Etiqueta para el eje X.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    ax1.hist(
        numeros,
        bins=bins,
        range=rango,
        color="steelblue",
        edgecolor="black",
        alpha=0.75,
    )
    ax1.set_title("Vista Normal")
    ax1.set_xlabel(x_label)
    ax1.set_ylabel("Frecuencia")
    if xticks is not None:
        ax1.set_xticks(xticks)
    ax1.grid(axis="y", alpha=0.3)

    ax2.hist(
        numeros,
        bins=bins,
        range=rango,
        color="coral",
        edgecolor="black",
        alpha=0.75,
    )
    ax2.set_title("Escala Logaritmica")
    ax2.set_xlabel(x_label)
    ax2.set_ylabel("Frecuencia (log)")
    if xticks is not None:
        ax2.set_xticks(xticks)
    ax2.set_yscale("log")
    ax2.grid(axis="y", alpha=0.3, which="both")

    plt.suptitle(titulo, fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.show()


def _visualizar_muestra(
    numeros,
    titulo,
    esperado_texto,
    bins=50,
    rango=None,
    xticks=None,
    x_label="Valor",
):
    """Muestra estadísticas y dos histogramas para la misma muestra."""
    _imprimir_estadisticas(numeros, esperado_texto)
    _graficar_histogramas(
        numeros=numeros,
        titulo=titulo,
        bins=bins,
        rango=rango,
        xticks=xticks,
        x_label=x_label,
    )


def visualizar_histograma_cuadrados_medios(semilla, digitos, pasos, bins=50):
    """Grafica histogramas del método Cuadrados Medios.

    Parameters
    ----------
    semilla : int
    digitos : int
    pasos : int
    bins : int, optional
    """
    gen = GeneradorCuadradosMedios(semilla=semilla, digitos=digitos)
    numeros = gen.siguiente_Ri_Cuadrados_Medios(pasos)

    titulo = (
        "Histograma de Frecuencia - Cuadrados Medios\n"
        f"Semilla: {semilla}, Digitos: {digitos}, Muestras: {pasos}"
    )

    _visualizar_muestra(
        numeros=numeros,
        titulo=titulo,
        esperado_texto="uniforme [0,1): 0.5",
        bins=bins,
        rango=(0, 1),
        xticks=np.arange(0, 1.05, 0.1),
        x_label="Valor (R_i)",
    )


def visualizar_histograma_congruencia_lineal(semilla, pasos, bins=50):
    """Grafica histogramas del método Congruencia Lineal.

    Parameters
    ----------
    semilla : int
    pasos : int
    bins : int, optional
    """
    gen = GeneradorCongruenciaLineal(semilla=semilla)
    numeros = gen.siguiente_Ri_Congruencia_Lineal(pasos)

    titulo = (
        "Histograma de Frecuencia - Congruencia Lineal\n"
        f"Semilla: {semilla}, Muestras: {pasos}"
    )

    _visualizar_muestra(
        numeros=numeros,
        titulo=titulo,
        esperado_texto="uniforme [0,1): 0.5",
        bins=bins,
        rango=(0, 1),
        xticks=np.arange(0, 1.05, 0.1),
        x_label="Valor (R_i)",
    )


def visualizar_histograma_congruencial_multiplicativo(
    semilla, pasos, a=1664525, m=2**32, bins=50
):
    """Grafica histogramas del método Congruencial Multiplicativo.

    Parameters
    ----------
    semilla : int
    pasos : int
    a : int, optional
    m : int, optional
    bins : int, optional
    """
    gen = GeneradorCongruencialMultiplicativo(semilla=semilla, a=a, m=m)
    numeros = gen.siguiente_Ri_Congruencial_Multiplicativo(pasos)

    titulo = (
        "Histograma de Frecuencia - Congruencial Multiplicativo\n"
        f"Semilla: {semilla}, a: {a}, m: {m}, Muestras: {pasos}"
    )

    _visualizar_muestra(
        numeros=numeros,
        titulo=titulo,
        esperado_texto="uniforme [0,1): 0.5",
        bins=bins,
        rango=(0, 1),
        xticks=np.arange(0, 1.05, 0.1),
        x_label="Valor (R_i)",
    )


def visualizar_histograma_congruencial_aditivo(
    semillas_iniciales, pasos, m=2**32, bins=50
):
    """Grafica histogramas del método Congruencial Aditivo.

    Parameters
    ----------
    semillas_iniciales : list[int]
    pasos : int
    m : int, optional
    bins : int, optional
    """
    gen = GeneradorCongruencialAditivo(semillas_iniciales=semillas_iniciales, m=m)
    numeros = gen.siguiente_Ri_Congruencial_Aditivo(pasos)

    titulo = (
        "Histograma de Frecuencia - Congruencial Aditivo\n"
        f"Semillas: {semillas_iniciales}, m: {m}, Muestras: {pasos}"
    )

    _visualizar_muestra(
        numeros=numeros,
        titulo=titulo,
        esperado_texto="uniforme [0,1): 0.5",
        bins=bins,
        rango=(0, 1),
        xticks=np.arange(0, 1.05, 0.1),
        x_label="Valor (R_i)",
    )


def visualizar_histograma_distribucion_uniforme(
    semilla,
    pasos,
    a=0.0,
    b=1.0,
    bins=50,
):
    """Grafica histogramas para una distribución Uniforme U(a, b).

    Parameters
    ----------
    semilla : int
    pasos : int
    a : float, optional
    b : float, optional
    bins : int, optional
    """
    gen_base = GeneradorCongruenciaLineal(semilla=semilla)
    uniformes_base = gen_base.siguiente_Ri_Congruencia_Lineal(pasos)

    gen_uniforme = GeneradorDistribucionUniforme(a=a, b=b)
    numeros = gen_uniforme.generar(uniformes_base)

    titulo = (
        "Histograma de Frecuencia - Distribucion Uniforme\n"
        f"Semilla: {semilla}, a: {a}, b: {b}, Muestras: {pasos}"
    )

    _visualizar_muestra(
        numeros=numeros,
        titulo=titulo,
        esperado_texto=f"uniforme [{a}, {b}): {(a + b) / 2:.8f}",
        bins=bins,
        rango=(a, b),
        xticks=np.linspace(a, b, 11),
        x_label="Valor",
    )


def visualizar_histograma_distribucion_normal(
    semilla,
    pasos,
    mu=0.0,
    sigma=1.0,
    bins=50,
):
    """Grafica histogramas para una distribución Normal N(mu, sigma^2).

    Parameters
    ----------
    semilla : int
    pasos : int
    mu : float, optional
    sigma : float, optional
    bins : int, optional
    """
    gen_base = GeneradorCongruenciaLineal(semilla=semilla)
    uniformes_base = gen_base.siguiente_Ri_Congruencia_Lineal(pasos)

    # Box-Muller requiere valores estrictamente en (0, 1).
    epsilon = 1e-12
    uniformes_ajustados = [
        min(max(u, epsilon), 1.0 - epsilon) for u in uniformes_base
    ]

    gen_normal = GeneradorDistribucionNormal(mu=mu, sigma=sigma)
    numeros = gen_normal.generar(uniformes_ajustados)[:pasos]

    titulo = (
        "Histograma de Frecuencia - Distribucion Normal\n"
        f"Semilla: {semilla}, mu: {mu}, sigma: {sigma}, Muestras: {pasos}"
    )

    _visualizar_muestra(
        numeros=numeros,
        titulo=titulo,
        esperado_texto=f"normal: mu = {mu}, sigma = {sigma}",
        bins=bins,
        rango=None,
        xticks=None,
        x_label="Valor",
    )


__all__ = [
    "visualizar_histograma_cuadrados_medios",
    "visualizar_histograma_congruencia_lineal",
    "visualizar_histograma_congruencial_multiplicativo",
    "visualizar_histograma_congruencial_aditivo",
    "visualizar_histograma_distribucion_uniforme",
    "visualizar_histograma_distribucion_normal",
]
