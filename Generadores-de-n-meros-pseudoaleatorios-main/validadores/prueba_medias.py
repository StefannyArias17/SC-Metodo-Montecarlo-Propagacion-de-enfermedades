import math


class PruebaMedias:
    """
    Validación de aleatoriedad mediante prueba de Medias.

    Verifica si la media muestral está dentro del intervalo de confianza
    esperado para una distribución uniforme U(0,1) con media teórica 0.5.
    Usa distribución normal con α = 0.05 (95% confianza).
    """

    def prueba_medias(self, numeros_aleatorios):
        """
        Ejecuta prueba de Medias sobre una secuencia.

        Parameters
        ----------
        numeros_aleatorios : list[float]
            Secuencia U(0,1) a validar.

        Returns
        -------
        bool
            True si media está dentro del intervalo de aceptación, False en caso contrario.
        """
        n = len(numeros_aleatorios)
        if n == 0:
            print("No se pueden realizar pruebas con una lista vacía.")
            return False

        for u in numeros_aleatorios:
            if not (0.0 <= u <= 1.0):
                raise ValueError(f"Valor fuera de [0,1]: {u}")

        media_calculada = sum(numeros_aleatorios) / n
        media_teorica = 0.5
        alpha = 0.05

        # Cuantil Z_(1 - alpha/2) usando inversa normal manual.
        z_alpha_2 = self._normal_inv_cdf(1.0 - alpha / 2.0)

        desviacion = math.sqrt(1.0 / (12.0 * n))
        llr = media_teorica - z_alpha_2 * desviacion
        lsr = media_teorica + z_alpha_2 * desviacion

        if llr <= media_calculada <= lsr:
            print("Prueba de medias: Aceptada")
            print(f"  Media calculada: {media_calculada:.8f}")
            print(f"  Rango: [{llr:.8f}, {lsr:.8f}]")
            return True
        else:
            print("Prueba de medias: Rechazada")
            print(f"  Media calculada: {media_calculada:.8f}")
            print(f"  Rango: [{llr:.8f}, {lsr:.8f}]")
            return False

    def _normal_inv_cdf(self, p):
        """
        Inversa de la CDF normal estándar usando aproximación racional de Acklam.
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
