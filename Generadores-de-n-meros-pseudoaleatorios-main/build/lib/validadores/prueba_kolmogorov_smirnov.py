import math

from scipy.stats import ksone  # type: ignore


class PruebaKolmogorovSmirnov:
    def prueba_kolmogorov_smirnov(self, numeros_aleatorios, alpha=0.05):
        n = len(numeros_aleatorios)
        datos_ordenados = sorted(numeros_aleatorios)

        d_max = 0
        for i in range(1, n + 1):
            # Frecuencia acumulada real
            f_observada = i / n
            # Frecuencia acumulada teórica para distribución uniforme
            f_teorica = datos_ordenados[i - 1]

            # Calculamos la diferencia absoluta
            distancia = abs(f_observada - f_teorica)

            if distancia > d_max:
                d_max = distancia

        # 3. Obtener el Valor Crítico (D-Alfa)
        # Para n > 50, se suele usar la aproximación: 1.36 / sqrt(n) para alpha=0.05
        if n > 50:
            d_critico = 1.36 / math.sqrt(n)
        else:
            # Para muestras pequeñas, usamos el valor de la distribución ksone (Kolmogorov-Smirnov)
            d_critico = ksone.ppf(1 - alpha / 2, n)

        # 4. Verificación
        aceptada = d_max < d_critico

        print(f"  D-Max calculado: {d_max:.5f}")
        print(f"  D-Teórico (D-alfa): {d_critico:.5f}")
        print(f"  Resultado: {'Aceptada' if aceptada else 'Rechazada'}")

        return aceptada
