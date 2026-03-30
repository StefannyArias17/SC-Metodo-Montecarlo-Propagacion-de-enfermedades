import math


class PruebaKolmogorovSmirnov:
    """
    Validación de aleatoriedad mediante prueba Kolmogorov-Smirnov.

    Compara la función de distribución acumulada empírica con la teórica
    de una distribución uniforme U(0,1) usando la mayor diferencia (D-max).
    """

    def prueba_kolmogorov_smirnov(self, numeros_aleatorios, alpha=0.05, return_detalle=False):
        """
        Ejecuta prueba Kolmogorov-Smirnov sobre una secuencia.

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
        if n == 0:
            print("No se pueden realizar pruebas con una lista vacía.")
            if return_detalle:
                return {
                    "d_max": 0.0,
                    "d_critico": 0.0,
                    "aceptada": False,
                }
            return False

        if not (0.0 < alpha < 1.0):
            raise ValueError("alpha debe estar en el intervalo (0,1).")

        datos_ordenados = sorted(numeros_aleatorios)

        for u in datos_ordenados:
            if not (0.0 <= u <= 1.0):
                raise ValueError(f"Valor fuera de [0,1]: {u}")

        d_mas = 0.0
        d_menos = 0.0

        for i, x_i in enumerate(datos_ordenados, start=1):
            f_emp_superior = i / n
            f_emp_inferior = (i - 1) / n
            f_teorica = x_i  # Para U(0,1), F(x)=x

            d_mas = max(d_mas, f_emp_superior - f_teorica)
            d_menos = max(d_menos, f_teorica - f_emp_inferior)

        d_max = max(d_mas, d_menos)
        d_critico = self._d_critico_aprox(alpha, n)

        aceptada = d_max < d_critico

        print(f"  D+ calculado: {d_mas:.5f}")
        print(f"  D- calculado: {d_menos:.5f}")
        print(f"  D-Max calculado: {d_max:.5f}")
        print(f"  D-Teórico (D-alfa): {d_critico:.5f}")
        print(f"  Resultado: {'Aceptada' if aceptada else 'Rechazada'}")

        if return_detalle:
            return {
                "d_mas": float(d_mas),
                "d_menos": float(d_menos),
                "d_max": float(d_max),
                "d_critico": float(d_critico),
                "aceptada": bool(aceptada),
            }

        return aceptada

    def _d_critico_aprox(self, alpha, n):
        """
        Valor crítico aproximado para KS bilateral.

        Basado en aproximación asintótica:
            P(D_n > d) ~ 2 * exp(-2 n d^2)

        Despejando para nivel alpha:
            d ~ sqrt(-0.5 * ln(alpha/2)) / sqrt(n)

        Con corrección de tamaño finito (Stephens):
            d ~ c(alpha) / (sqrt(n) + 0.12 + 0.11/sqrt(n))
        """
        c_alpha = math.sqrt(-0.5 * math.log(alpha / 2.0))
        raiz_n = math.sqrt(n)
        return c_alpha / (raiz_n + 0.12 + 0.11 / raiz_n)
