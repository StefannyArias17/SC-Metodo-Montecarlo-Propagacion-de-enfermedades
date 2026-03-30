from collections import Counter
import math

class PruebaPoker:
    """
    Validación de aleatoriedad mediante prueba de Poker.

    Clasifica los primeros 5 dígitos decimales de cada número en categorías
    poker (Quintilla, Póker, Full, Tercia, Dos Pares, Un Par, Todos Diferentes)
    y compara las frecuencias observadas contra las esperadas usando chi-cuadrado.
    """

    def clasificar_categoria(self, digitos):
        """
        Clasifica 5 dígitos en una categoría poker.

        Parameters
        ----------
        digitos : str
            String de 5 dígitos.

        Returns
        -------
        str
            Categoría poker: 'Todos Diferentes', 'Un Par', 'Dos Pares',
            'Tercia', 'Full House', 'Póker', 'Quintilla'.
        """
        distintos = len(set(digitos))

        if distintos == 5:
            return "Todos Diferentes"
        if distintos == 1:
            return "Quintilla"

        conteos = sorted(Counter(digitos).values(), reverse=True)

        if distintos == 4:
            return "Un Par"
        if distintos == 3:
            return "Tercia" if conteos[0] == 3 else "Dos Pares"
        if distintos == 2:
            return "Póker" if conteos[0] == 4 else "Full House"

        raise ValueError(f"No se pudo clasificar la cadena de dígitos: {digitos}")

    def prueba_poker(self, numeros_aleatorios):
        """
        Ejecuta prueba de Poker sobre una secuencia.

        Parameters
        ----------
        numeros_aleatorios : list[float]
            Secuencia U(0,1) a validar.

        Returns
        -------
        bool
            True si chi-cuadrado calculado < chi-cuadrado teórico, False en caso contrario.
        """
        n = len(numeros_aleatorios)
        if n == 0:
            print("No se pueden realizar pruebas con una lista vacía.")
            return False

        for u in numeros_aleatorios:
            if not (0.0 <= u <= 1.0):
                raise ValueError(f"Valor fuera de [0,1]: {u}")

        poker_numeros = [f"{u:.5f}"[2:] for u in numeros_aleatorios]

        frecuencias = {
            "Todos Diferentes": 0,
            "Un Par": 0,
            "Dos Pares": 0,
            "Tercia": 0,
            "Full House": 0,
            "Póker": 0,
            "Quintilla": 0,
        }

        for num in poker_numeros:
            categoria = self.clasificar_categoria(num)
            frecuencias[categoria] += 1

        probabilidades = {
            "Todos Diferentes": 0.30240,
            "Un Par": 0.50400,
            "Dos Pares": 0.10800,
            "Tercia": 0.07200,
            "Full House": 0.00900,
            "Póker": 0.00450,
            "Quintilla": 0.00010,
        }

        chi2_calculado = 0.0
        for categoria in probabilidades:
            oi = frecuencias[categoria]
            ei = n * probabilidades[categoria]
            chi2_calculado += ((ei - oi) ** 2) / ei

        alpha = 0.05
        grados_libertad = len(probabilidades) - 1  # 6
        chi2_teorico = self._chi2_ppf_aprox(1.0 - alpha, grados_libertad)

        if chi2_calculado < chi2_teorico:
            print("Prueba de Poker: Aceptada")
            print(f"  Chi-cuadrado calculado: {chi2_calculado:.4f}")
            print(f"  Chi-cuadrado teórico {(1 - alpha) * 100:.1f}%: {chi2_teorico:.4f}")
            return True
        else:
            print("Prueba de Poker: Rechazada")
            print(f"  Chi-cuadrado calculado: {chi2_calculado:.4f}")
            print(f"  Chi-cuadrado teórico {(1 - alpha) * 100:.1f}%: {chi2_teorico:.4f}")
            return False

    def _chi2_ppf_aprox(self, p, grados_libertad):
        """
        Aproximación de la función ppf de chi-cuadrado.

        Parameters
        ----------
        p : float
            Probabilidad.
        grados_libertad : int
            Grados de libertad.

        Returns
        -------
        float
            Valor aproximado de la función ppf.
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
        Aproximación de la función inv_cdf de la distribución normal.

        Parameters
        ----------
        p : float
            Probabilidad.

        Returns
        -------
        float
            Valor aproximado de la función inv_cdf.
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
