from scipy.stats import chi2  # type: ignore


class PruebaVarianza:
    """
    Validación de aleatoriedad mediante prueba de Varianza.

    Verifica si la varianza muestral está dentro del intervalo de confianza
    esperado para una distribución uniforme U(0,1) con varianza teórica 1/12.
    Usa distribución chi-cuadrado con α = 0.05.
    """

    def prueba_varianza(self, numeros_aleatorios):
        """
        Ejecuta prueba de Varianza sobre una secuencia.

        Parameters
        ----------
        numeros_aleatorios : list[float]
            Secuencia U(0,1) a validar.

        Returns
        -------
        bool
            True si varianza está dentro del intervalo de aceptación, False en caso contrario.

        Notes
        -----
        Intervalo de aceptación:
        LLR = χ²_(α/2, n-1) / (12(n-1))
        LSR = χ²_(1-α/2, n-1) / (12(n-1))
        """
        n = len(numeros_aleatorios)
        alpha = 0.05  

        media_calculada = sum(numeros_aleatorios) / n
        varianza_calculada = sum(
            (x - media_calculada) ** 2 for x in numeros_aleatorios
        ) / (n - 1)

        chi2_alpha_2 = chi2.ppf(1 - alpha / 2, n - 1)
        chi2_1_minus_alpha_2 = chi2.ppf(alpha / 2, n - 1)

        LLR = chi2_alpha_2 / (12 * (n - 1))
        LSR = chi2_1_minus_alpha_2 / (12 * (n - 1))

        if LSR <= varianza_calculada <= LLR:
            print("Prueba de varianza: Aceptada")
            print(f"  Varianza calculada: {varianza_calculada:.8f}")
            print(f"  Rango: [{LSR:.8f}, {LLR:.8f}]")
            cumple = True
        else:
            print("Prueba de varianza: Rechazada")
            print(f"  Varianza calculada: {varianza_calculada:.8f}")
            print(f"  Rango: [{LSR:.8f}, {LLR:.8f}]")
            cumple = False

        return cumple
