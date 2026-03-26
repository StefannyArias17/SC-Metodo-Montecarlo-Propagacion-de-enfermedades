from collections import Counter

from scipy.stats import chi2  # type: ignore


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
        poker_numeros = [f"{n:.5f}"[2:] for n in numeros_aleatorios]

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

        chi2_calculado = 0
        for categoria in probabilidades:
            oi = frecuencias[categoria]
            ei = n * probabilidades[categoria]

            # Fórmula: (Ei - Oi)^2 / Ei
            chi2_calculado += ((ei - oi) ** 2) / ei

        alpha = 0.05 

        # Grados de libertad = número de categorías - 1
        grados_libertad = len(probabilidades) - 1
        chi2_teorico = chi2.ppf(1 - alpha, grados_libertad)

        if chi2_calculado < chi2_teorico:
            print("Prueba de Poker: Aceptada")
            print(f"  Chi-cuadrado calculado: {chi2_calculado:.4f}")
            print(
                f"  Chi-cuadrado teórico {(1 - alpha) * 100:.1f}%: {chi2_teorico:.4f}"
            )
            return True
        else:
            print("Prueba de Poker: Rechazada")
            print(f"  Chi-cuadrado calculado: {chi2_calculado:.4f}")
            print(
                f"  Chi-cuadrado teórico {(1 - alpha) * 100:.1f}%: {chi2_teorico:.4f}"
            )
            return False
