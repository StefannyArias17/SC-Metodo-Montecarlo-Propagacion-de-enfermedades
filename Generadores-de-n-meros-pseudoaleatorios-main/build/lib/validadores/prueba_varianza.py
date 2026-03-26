from scipy.stats import chi2  # type: ignore


class PruebaVarianza:
    def prueba_varianza(self, numeros_aleatorios):
        """
        Prueba de varianza para números pseudoaleatorios [0,1].

        Se verifica si la varianza calculada está dentro del intervalo:
        LLR = chi2_alpha_2 / (12 * (n - 1))
        LSR = chi2_1_minus_alpha_2 / (12 * (n - 1))
        """
        n = len(numeros_aleatorios)
        alpha = 0.05  # Nivel de significancia (5%)

        # 1. Calcular Media y Varianza
        media_calculada = sum(numeros_aleatorios) / n
        varianza_calculada = sum(
            (x - media_calculada) ** 2 for x in numeros_aleatorios
        ) / (n - 1)

        # 2. Valores críticos de Chi-cuadrado / chi2.ppf usa la probabilidad acumulada a la izquierda
        chi2_alpha_2 = chi2.ppf(1 - alpha / 2, n - 1)
        chi2_1_minus_alpha_2 = chi2.ppf(alpha / 2, n - 1)

        # 3. Límites de Aceptación
        LLR = chi2_alpha_2 / (12 * (n - 1))
        LSR = chi2_1_minus_alpha_2 / (12 * (n - 1))

        # 4. Comparamos la varianza directamente contra los límites
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
