import numpy as np
from scipy.stats import chi2  # type: ignore


class PruebaChiCuadrado:
    """
    Validación de aleatoriedad mediante prueba Chi-Cuadrado.

    Divide el intervalo [0, 1) en k intervalos iguales y compara las
    frecuencias observadas contra las esperadas en la distribución uniforme.
    Usa distribución chi-cuadrado con k-1 grados de libertad y α = 0.05.
    """

    def prueba_chi_cuadrado(self, numeros_aleatorios, k=1000):
        """
        Ejecuta la prueba Chi-Cuadrado sobre una secuencia.

        Parameters
        ----------
        numeros_aleatorios : list[float]
            Secuencia U(0,1) a validar.
        k : int, optional
            Número de intervalos para dividir [0, 1). Por defecto 1000.

        Returns
        -------
        bool
            True si la prueba es aceptada, False si es rechazada.
        """
        n = len(numeros_aleatorios)
        if n == 0:
            print("No se pueden realizar pruebas con una lista vacía.")
            return False

                          
        frecuencias_observadas, _ = np.histogram(
            numeros_aleatorios, bins=k, range=(0, 1)
        )
         
        frecuencia_esperada = n / k

        chi_cuadrado_calculado = sum(
            (fo - frecuencia_esperada) ** 2 / frecuencia_esperada
            for fo in frecuencias_observadas
        )


        alpha = 0.05
        grados_libertad = k - 1
        chi_cuadrado_teorico = chi2.ppf(1 - alpha, grados_libertad)

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
