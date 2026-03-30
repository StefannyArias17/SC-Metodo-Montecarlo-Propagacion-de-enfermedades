import math


class PruebaChiCuadrado:
    """
    Validación de aleatoriedad mediante prueba Chi-Cuadrado.

    Divide el intervalo [0, 1) en k intervalos iguales y compara las
    frecuencias observadas contra las esperadas en la distribución uniforme.
    Usa distribución chi-cuadrado con k-1 grados de libertad y α = 0.05.
    """

    def prueba_chi_cuadrado(self, numeros_aleatorios, k=1000, alpha=0.05, return_detalle=False):
        """
        Ejecuta la prueba Chi-Cuadrado sobre una secuencia.

        Parameters
        ----------
        numeros_aleatorios : list[float]
            Secuencia U(0,1) a validar.
        k : int, optional
            Número de intervalos para dividir [0, 1). Por defecto 1000.
        alpha : float, optional
            Nivel de significancia. Por defecto 0.05.

        Returns
        -------
        bool | dict
            True/False si return_detalle=False.
            Diccionario con métricas de la prueba si return_detalle=True.
        """
        n = len(numeros_aleatorios)
        if n == 0:
            print("No se pueden realizar pruebas con una lista vacía.")
            if return_detalle:
                return {
                    "chi_calculado": 0.0,
                    "chi_critico": 0.0,
                    "aceptada": False,
                    "frecuencias_observadas": [],
                    "frecuencias_esperadas": [],
                }
            return False

        if k <= 1:
            print("k debe ser mayor que 1.")
            if return_detalle:
                return {
                    "chi_calculado": 0.0,
                    "chi_critico": 0.0,
                    "aceptada": False,
                    "frecuencias_observadas": [],
                    "frecuencias_esperadas": [],
                }
            return False

        frecuencia_esperada = n / k
        if frecuencia_esperada == 0:
            print("Frecuencia esperada inválida.")
            if return_detalle:
                return {
                    "chi_calculado": 0.0,
                    "chi_critico": 0.0,
                    "aceptada": False,
                    "frecuencias_observadas": [],
                    "frecuencias_esperadas": [],
                }
            return False

        frecuencias_observadas = self._histograma_manual(numeros_aleatorios, k)

        chi_cuadrado_calculado = 0.0
        for fo in frecuencias_observadas:
            chi_cuadrado_calculado += (fo - frecuencia_esperada) ** 2 / frecuencia_esperada

        if not (0.0 < alpha < 1.0):
            raise ValueError("alpha debe estar en (0,1).")

        grados_libertad = k - 1
        chi_cuadrado_teorico = self._chi2_ppf_aprox(1.0 - alpha, grados_libertad)
        frecuencias_esperadas = [frecuencia_esperada] * k
        aceptada = chi_cuadrado_calculado < chi_cuadrado_teorico

        if return_detalle:
            return {
                "chi_calculado": float(chi_cuadrado_calculado),
                "chi_critico": float(chi_cuadrado_teorico),
                "aceptada": bool(aceptada),
                "frecuencias_observadas": [int(v) for v in frecuencias_observadas],
                "frecuencias_esperadas": [float(v) for v in frecuencias_esperadas],
            }

        if aceptada:
            print("Prueba de chi-cuadrado: Aceptada")
            print(f"  Chi-cuadrado calculado: {chi_cuadrado_calculado:.8f}")
            print(f"  Chi-cuadrado teórico: {chi_cuadrado_teorico:.8f}")
            return True
        else:
            print("Prueba de chi-cuadrado: Rechazada")
            print(f"  Chi-cuadrado calculado: {chi_cuadrado_calculado:.8f}")
            print(f"  Chi-cuadrado teórico: {chi_cuadrado_teorico:.8f}")
            return False

    def _histograma_manual(self, datos, k):
        frecuencias = [0] * k

        for u in datos:
            if not (0.0 <= u <= 1.0):
                raise ValueError(f"Valor fuera de [0,1]: {u}")

            idx = int(u * k)
            if idx == k:
                idx = k - 1
            frecuencias[idx] += 1

        return frecuencias

    def _chi2_ppf_aprox(self, p, grados_libertad):
        """
        Aproxima el cuantil de chi-cuadrado usando transformación de
        Wilson-Hilferty:
            X ≈ ν * (1 - 2/(9ν) + z*sqrt(2/(9ν)))^3
        donde z es el cuantil normal estándar en p.
        """
        if not (0.0 < p < 1.0):
            raise ValueError("p debe estar en (0,1).")
        if grados_libertad <= 0:
            raise ValueError("grados_libertad debe ser > 0.")

        nu = float(grados_libertad)
        z = self._normal_inv_cdf(p)
        a = 2.0 / (9.0 * nu)
        x = nu * (1.0 - a + z * math.sqrt(a)) ** 3
        return max(0.0, x)

    def _normal_inv_cdf(self, p):
        """
        Inversa de la CDF normal estándar usando aproximación racional
        de Acklam (implementación manual).
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
