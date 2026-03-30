import math


class PruebaRachas:
    """
    Validación de aleatoriedad mediante prueba de Rachas.

    Cuenta el número de cambios de signo (rachas) respecto a la mediana (0.5)
    y compara la estadística Z calculada con el rango de aceptación.
    Detecta patrones no aleatorios en la secuencia.
    """

    def prueba_rachas(self, numeros_aleatorios, alpha=0.05, return_detalle=False):
        """
        Ejecuta prueba de Rachas sobre una secuencia.

        Parameters
        ----------
        numeros_aleatorios : list[float]
            Secuencia U(0,1) a validar.
        alpha : float, optional
            Nivel de significancia. Por defecto 0.05.

        Returns
        -------
        bool | dict
            True/False si return_detalle=False.
            Diccionario con métricas de la prueba si return_detalle=True.
        """
        n = len(numeros_aleatorios)
        if n < 2:
            print("Se requieren al menos 2 datos para prueba de rachas.")
            if return_detalle:
                return {
                    "rachas_observadas": 0,
                    "rachas_esperadas": 0.0,
                    "rachas_min": 0.0,
                    "rachas_max": 0.0,
                    "z_estadistico": 0.0,
                    "aceptada": False,
                }
            return False

        if not (0.0 < alpha < 1.0):
            raise ValueError("alpha debe estar en (0,1).")

        for u in numeros_aleatorios:
            if not (0.0 <= u <= 1.0):
                raise ValueError(f"Valor fuera de [0,1]: {u}")

        mediana_teorica = 0.5
        signos = [1 if num >= mediana_teorica else 0 for num in numeros_aleatorios]

        n_pos = sum(signos)
        n_neg = n - n_pos

        # Si todos quedan del mismo lado de la mediana, no hay varianza de rachas.
        if n_pos == 0 or n_neg == 0:
            print("Prueba de Rachas: Rechazada")
            print("  Todos los valores quedaron del mismo lado de 0.5.")
            print(f"Total muestras: {n}")
            if return_detalle:
                return {
                    "rachas_observadas": 1,
                    "rachas_esperadas": 0.0,
                    "rachas_min": 0.0,
                    "rachas_max": 0.0,
                    "z_estadistico": 0.0,
                    "aceptada": False,
                }
            return False

        rachas_totales = 1
        for i in range(1, n):
            if signos[i] != signos[i - 1]:
                rachas_totales += 1

        numerador = 2 * n_pos * n_neg
        media_rachas = (numerador / n) + 1
        varianza_rachas = (numerador * (numerador - n)) / ((n**2) * (n - 1))

        if varianza_rachas <= 0:
            print("Prueba de Rachas: Rechazada")
            print("  Varianza de rachas no positiva.")
            print(f"Total muestras: {n}")
            if return_detalle:
                return {
                    "rachas_observadas": int(rachas_totales),
                    "rachas_esperadas": float(media_rachas),
                    "rachas_min": float(media_rachas),
                    "rachas_max": float(media_rachas),
                    "z_estadistico": 0.0,
                    "aceptada": False,
                }
            return False

        z_estadistico = (rachas_totales - media_rachas) / math.sqrt(varianza_rachas)

        z_teorico = self._normal_inv_cdf(1.0 - alpha / 2.0)
        rango_min = -z_teorico
        rango_max = z_teorico
        rachas_min = media_rachas + rango_min * math.sqrt(varianza_rachas)
        rachas_max = media_rachas + rango_max * math.sqrt(varianza_rachas)
        aceptada = rango_min <= z_estadistico <= rango_max

        if return_detalle:
            return {
                "rachas_observadas": int(rachas_totales),
                "rachas_esperadas": float(media_rachas),
                "rachas_min": float(rachas_min),
                "rachas_max": float(rachas_max),
                "z_estadistico": float(z_estadistico),
                "aceptada": bool(aceptada),
            }

        if aceptada:
            print("Prueba de Rachas: Aceptada")
            print(f"  Z estadístico: {z_estadistico:.4f}")
            print(f"  Rango aceptable: [{rango_min:.4f}, {rango_max:.4f}]")
            print(f"Total muestras: {n}")
            return True
        else:
            print("Prueba de Rachas: Rechazada")
            print(f"  Z estadístico: {z_estadistico:.4f}")
            print(f"  Rango aceptable: [{rango_min:.4f}, {rango_max:.4f}]")
            print(f"Total muestras: {n}")
            return False

    def _normal_inv_cdf(self, p):
        """
        Inversa de CDF normal estándar (aproximación racional de Acklam).
        """
        if not (0.0 < p < 1.0):
            raise ValueError("p debe estar en (0,1).")

        a1 = -3.969683028665376e01
        a2 = 2.209460984245205e02
        a3 = -2.759285104469687e02
        a4 = 1.383577518672690e02
        a5 = -3.066479806614716e01
        a6 = 2.506628277459239e00

        b1 = -5.447609879822406e01
        b2 = 1.615858368580409e02
        b3 = -1.556989798598866e02
        b4 = 6.680131188771972e01
        b5 = -1.328068155288572e01

        c1 = -7.784894002430293e-03
        c2 = -3.223964580411365e-01
        c3 = -2.400758277161838e00
        c4 = -2.549732539343734e00
        c5 = 4.374664141464968e00
        c6 = 2.938163982698783e00

        d1 = 7.784695709041462e-03
        d2 = 3.224671290700398e-01
        d3 = 2.445134137142996e00
        d4 = 3.754408661907416e00

        plow = 0.02425
        phigh = 1.0 - plow

        if p < plow:
            q = math.sqrt(-2.0 * math.log(p))
            return (
                (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6)
                / ((((d1 * q + d2) * q + d3) * q + d4) * q + 1.0)
            )

        if p <= phigh:
            q = p - 0.5
            r = q * q
            return (
                (((((a1 * r + a2) * r + a3) * r + a4) * r + a5) * r + a6) * q
                / (((((b1 * r + b2) * r + b3) * r + b4) * r + b5) * r + 1.0)
            )

        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -(
            (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6)
            / ((((d1 * q + d2) * q + d3) * q + d4) * q + 1.0)
        )
