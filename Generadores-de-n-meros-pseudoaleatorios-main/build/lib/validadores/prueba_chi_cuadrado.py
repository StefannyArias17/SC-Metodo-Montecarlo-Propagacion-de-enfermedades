import numpy as np
from scipy.stats import chi2  # type: ignore


class PruebaChiCuadrado:
    def prueba_chi_cuadrado(self, numeros_aleatorios, k=1000):
        n = len(numeros_aleatorios)
        if n == 0:
            print("No se pueden realizar pruebas con una lista vacía.")
            return False

        # 1. Dividir el rango [0, 1) en k intervalos iguales
        # 2. Contar cuántos números caen en cada intervalo
        frecuencias_observadas, _ = np.histogram(
            numeros_aleatorios, bins=k, range=(0, 1)
        )

        # 3. Calcular la frecuencia esperada (n/k para cada intervalo)
        frecuencia_esperada = n / k

        # 4. Calcular el estadístico de chi-cuadrado
        chi_cuadrado_calculado = sum(
            (fo - frecuencia_esperada) ** 2 / frecuencia_esperada
            for fo in frecuencias_observadas
        )

        # 5. Obtener el valor crítico de chi-cuadrado para k-1 grados de libertad y un nivel de significancia (alpha=0.05)

        alpha = 0.05
        grados_libertad = k - 1
        chi_cuadrado_teorico = chi2.ppf(1 - alpha, grados_libertad)

        # 6. Comparar el estadístico calculado con el valor teórico
        if chi_cuadrado_calculado < chi_cuadrado_teorico:
            print("Prueba de chi-cuadrado: Aceptada")
            print(f"  Chi-cuadrado calculado: {chi_cuadrado_calculado:.8f}")
            print(f"  Chi-cuadrado teórico: {chi_cuadrado_teorico:.8f}")
            return True
        else:
            print("Prueba de chi-cuadrado: Rechazada")
            print(f"  Chi-cuadrado calculado: {chi_cuadrado_calculado:.8f}")
            print(f"  Chi-cuadrado teórico: {chi_cuadrado_teorico:.8f}")
            return False
