import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import chi2, norm

from visualizaciones.graficas_de_validacion import (
    graficar_kolmogorov_smirnov,
    graficar_prueba_chi_cuadrado,
    graficar_prueba_poker,
    graficar_prueba_rachas,
    graficar_prueba_medias,
    graficar_prueba_varianza,
)


class GraficosService:
    """
    Servicio para generar y mostrar gráficos de validación estadística.

    Proporciona métodos para graficar histogramas y pruebas de validación
    de secuencias pseudoaleatorias (Histograma, Kolmogorov-Smirnov, Poker,
    Rachas, Chi-Cuadrado, Medias y Varianza).

    Notes
    -----
    - Todos los métodos son estáticos, no requiere instanciación.
    - Transforma automáticamente distribuciones a U(0,1) para validación.
    - Usa matplotlib para visualización.
    - Soporta filtrado por método de generación en gráficos multivariados.
    """
    @staticmethod
    def _obtener_rango_histograma(seq, metodo, params_dist):
        """
        Calcula el rango apropiado para el histograma según la distribución.

        Parameters
        ----------
        seq : list[float]
            Secuencia a graficar (se usa solo para contexto).
        metodo : str or None
            Nombre de la distribución.
        params_dist : dict
            Parámetros de distribución (a, b, mu, sigma).

        Returns
        -------
        tuple[float, float] or None
            Tupla (min, max) para el rango del histograma.
            None si no se puede determinar.
        """
        if metodo == "Distribucion Uniforme":
            a = float(params_dist.get("a", 0.0))
            b = float(params_dist.get("b", 1.0))
            return (a, b)

        if metodo == "Distribucion Normal":
            mu = float(params_dist.get("mu", 0.0))
            sigma = float(params_dist.get("sigma", 1.0))
            if sigma > 0:
                return (mu - 4 * sigma, mu + 4 * sigma)
            return None

        return (0, 1)

    @staticmethod
    def _calcular_intervalos_frecuencias(seq, cantidad_intervalos=30):
        """Calcula limites y frecuencias usando min/max y ancho fijo."""
        minimo = min(seq)
        maximo = max(seq)

        if minimo == maximo:
            intervalos = [minimo for _ in range(cantidad_intervalos)]
            frecuencias = [len(seq)] + [0] * (cantidad_intervalos - 1)
            return intervalos, frecuencias

        ancho_intervalo = (maximo - minimo) / cantidad_intervalos
        intervalos = [minimo]
        for _ in range(1, cantidad_intervalos):
            intervalos.append(intervalos[-1] + ancho_intervalo)

        frecuencias = [0] * cantidad_intervalos
        for valor in seq:
            indice = int((valor - minimo) / ancho_intervalo)
            if indice < 0:
                indice = 0
            elif indice >= cantidad_intervalos:
                indice = cantidad_intervalos - 1
            frecuencias[indice] += 1

        return intervalos, frecuencias

    @staticmethod
    def mostrar(
        tipo,
        corrida,
        seq,
        secuencias,
        metodo=None,
        params_dist=None,
        corridas_info=None,
    ):
        """
        Muestra un gráfico según el tipo de validación solicitado.

        Genera histogramas o gráficos de pruebas de validación estadística.
        Para pruebas multivariadas (Medias, Varianza) procesa todas las
        secuencias proporcionadas.

        Parameters
        ----------
        tipo : str
            Tipo de gráfico. Valores válidos: 'Histograma', 'Kolmogorov Smirnov',
            'Poker', 'Rachas', 'Chi Cuadrado', 'Medias', 'Varianza'.
        corrida : str
            Nombre/descripción de la corrida actual (para título).
        seq : list[float]
            Secuencia a graficar (para Histograma).
        secuencias : dict[str, list[float]]
            Diccionario con todas las secuencias (para Medias, Varianza).
        metodo : str, optional
            Nombre de la distribución para transformación.
        params_dist : dict, optional
            Parámetros de distribución por defecto {a: 0, b: 1, mu: 0, sigma: 1}.
        corridas_info : dict, optional
            Información sobre cada corrida (método usado) para filtrado.

        Returns
        -------
        None
            Muestra el gráfico usando matplotlib.pyplot.show().
        """
        if params_dist is None:
            params_dist = {"a": 0.0, "b": 1.0, "mu": 0.0, "sigma": 1.0}

        if tipo == "Histograma":
            if metodo == "Distribucion Normal":
                intervalos, frecuencias = GraficosService._calcular_intervalos_frecuencias(
                    seq,
                    cantidad_intervalos=30,
                )
                ancho_intervalo = 1.0
                if len(intervalos) > 1:
                    ancho_intervalo = intervalos[1] - intervalos[0]

                plt.figure(figsize=(9, 5))
                plt.bar(
                    intervalos,
                    frecuencias,
                    width=ancho_intervalo,
                    align="edge",
                    color="steelblue",
                    edgecolor="black",
                )
                plt.title(f"Histograma - {corrida}")
                plt.xlabel("Ri")
                plt.ylabel("Frecuencia")
                plt.grid(alpha=0.3)
                plt.tight_layout()
                plt.show()
            else:
                rango = GraficosService._obtener_rango_histograma(seq, metodo, params_dist)
                plt.figure(figsize=(9, 5))
                plt.hist(seq, bins=30, range=rango, color="steelblue", edgecolor="black")
                plt.title(f"Histograma - {corrida}")
                plt.xlabel("Ri")
                plt.ylabel("Frecuencia")
                plt.grid(alpha=0.3)
                plt.tight_layout()
                plt.show()
            return

        seq_validacion = seq

        if tipo == "Kolmogorov Smirnov":
            graficar_kolmogorov_smirnov(seq_validacion)
            return

        if tipo == "Poker":
            graficar_prueba_poker(seq_validacion)
            return

        if tipo == "Rachas":
            graficar_prueba_rachas(seq_validacion)
            return

        if tipo == "Chi Cuadrado":
            graficar_prueba_chi_cuadrado(seq_validacion, k=10, alpha=0.05)
            return

        if tipo == "Medias":
            GraficosService._graficar_medias(
                secuencias=secuencias,
                corridas_info=corridas_info,
                params_dist=params_dist,
                metodo_objetivo=metodo,
            )
            return

        if tipo == "Varianza":
            GraficosService._graficar_varianza(
                secuencias=secuencias,
                corridas_info=corridas_info,
                params_dist=params_dist,
                metodo_objetivo=metodo,
            )

    @staticmethod
    def _graficar_medias(
        secuencias,
        corridas_info=None,
        params_dist=None,
        metodo_objetivo=None,
    ):
        """
        Grafica medias muestrales con intervalos de confianza.

        Calcula la media y error estándar para cada secuencia, filtra por
        método si se especifica, y muestra un gráfico con barras de error.

        Parameters
        ----------
        secuencias : dict[str, list[float]]
            Diccionario de secuencias indexadas por clave de corrida.
        corridas_info : dict, optional
            Información de cada corrida (método usado).
        params_dist : dict, optional
            Parámetros de distribución para transformación.
        metodo_objetivo : str, optional
            Si se establece, solo grafica secuencias de este método.

        Returns
        -------
        None
            Muestra el gráfico usando visualizaciones.graficar_prueba_medias().

        Raises
        ------
        ValueError
            Si no hay corridas con datos suficientes.
        """
        if not secuencias:
            raise ValueError("No hay corridas disponibles para graficar medias.")

        alpha = 0.05
        z = float(norm.ppf(1 - alpha / 2))

        sample_means = []
        ci_lower = []
        ci_upper = []

        for corrida_key, seq_i in secuencias.items():
            metodo_i = None
            if corridas_info and corrida_key in corridas_info:
                metodo_i = corridas_info[corrida_key][0]

            if metodo_objetivo is not None and metodo_i != metodo_objetivo:
                continue

            seq_validacion_i = seq_i

            n_i = len(seq_validacion_i)
            if n_i < 2:
                continue

            media_i = float(np.mean(seq_validacion_i))
            error_i = z * ((1 / (12 * n_i)) ** 0.5)

            sample_means.append(media_i)
            ci_lower.append(media_i - error_i)
            ci_upper.append(media_i + error_i)

        if not sample_means:
            raise ValueError("No hay corridas con datos suficientes para graficar medias.")

        graficar_prueba_medias(
            sample_means=sample_means,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            theoretical_mean=0.5,
            alpha=alpha,
        )

    @staticmethod
    def _graficar_varianza(
        secuencias,
        corridas_info=None,
        params_dist=None,
        metodo_objetivo=None,
    ):
        """
        Grafica varianzas muestrales con intervalos de confianza chi-cuadrado.

        Calcula la varianza muestral para cada secuencia y sus intervalos
        de confianza usando la distribución chi-cuadrado, filtra por método
        si se especifica.

        Parameters
        ----------
        secuencias : dict[str, list[float]]
            Diccionario de secuencias indexadas por clave de corrida.
        corridas_info : dict, optional
            Información de cada corrida (método usado).
        params_dist : dict, optional
            Parámetros de distribución para transformación.
        metodo_objetivo : str, optional
            Si se establece, solo grafica secuencias de este método.

        Returns
        -------
        None
            Muestra el gráfico usando visualizaciones.graficar_prueba_varianza().

        Raises
        ------
        ValueError
            Si no hay corridas con datos suficientes.
        """
        if not secuencias:
            raise ValueError("No hay corridas disponibles para graficar varianza.")

        alpha = 0.05
        var_teorica = 1 / 12

        sample_variances = []
        ci_lower = []
        ci_upper = []

        for corrida_key, seq_i in secuencias.items():
            metodo_i = None
            if corridas_info and corrida_key in corridas_info:
                metodo_i = corridas_info[corrida_key][0]

            if metodo_objetivo is not None and metodo_i != metodo_objetivo:
                continue

            seq_validacion_i = seq_i

            n_i = len(seq_validacion_i)
            if n_i < 2:
                continue

            s2 = float(np.var(seq_validacion_i, ddof=1))
            chi2_inf = float(chi2.ppf(alpha / 2, n_i - 1))
            chi2_sup = float(chi2.ppf(1 - alpha / 2, n_i - 1))

            li = (n_i - 1) * s2 / chi2_sup
            ls = (n_i - 1) * s2 / chi2_inf

            sample_variances.append(s2)
            ci_lower.append(li)
            ci_upper.append(ls)

        if not sample_variances:
            raise ValueError("No hay corridas con datos suficientes para graficar varianza.")

        graficar_prueba_varianza(
            sample_variances=sample_variances,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            theoretical_variance=var_teorica,
            alpha=alpha,
        )
