import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import chi2, norm
from app_services.validacion_service import ValidacionService

from visualizaciones.graficas_de_validacion import (
    graficar_kolmogorov_smirnov,
    graficar_prueba_chi_cuadrado,
    graficar_prueba_poker,
    graficar_prueba_rachas,
    graficar_prueba_medias,
    graficar_prueba_varianza,
)


class GraficosService:
    @staticmethod
    def _transformar_seq_para_validacion(seq, metodo, params_dist):
        return ValidacionService._transformar_para_validacion(
            seq,
            metodo=metodo,
            params_dist=params_dist,
        )

    @staticmethod
    def _obtener_rango_histograma(seq, metodo, params_dist):
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
    def mostrar(
        tipo,
        corrida,
        seq,
        secuencias,
        metodo=None,
        params_dist=None,
        corridas_info=None,
    ):
        if params_dist is None:
            params_dist = {"a": 0.0, "b": 1.0, "mu": 0.0, "sigma": 1.0}

        if tipo == "Histograma":
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

        seq_validacion = GraficosService._transformar_seq_para_validacion(
            seq,
            metodo=metodo,
            params_dist=params_dist,
        )

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
        if not secuencias:
            raise ValueError("No hay corridas disponibles para graficar medias.")

        if params_dist is None:
            params_dist = {"a": 0.0, "b": 1.0, "mu": 0.0, "sigma": 1.0}

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

            seq_validacion_i = GraficosService._transformar_seq_para_validacion(
                seq_i,
                metodo=metodo_i,
                params_dist=params_dist,
            )

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
        if not secuencias:
            raise ValueError("No hay corridas disponibles para graficar varianza.")

        if params_dist is None:
            params_dist = {"a": 0.0, "b": 1.0, "mu": 0.0, "sigma": 1.0}

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

            seq_validacion_i = GraficosService._transformar_seq_para_validacion(
                seq_i,
                metodo=metodo_i,
                params_dist=params_dist,
            )

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
