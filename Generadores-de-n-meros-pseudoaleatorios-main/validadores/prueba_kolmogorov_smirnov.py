import math

from scipy.stats import ksone 


class PruebaKolmogorovSmirnov:
    """
    Validación de aleatoriedad mediante prueba Kolmogorov-Smirnov.

    Compara la función de distribución acumulada empírica con la teórica
    de una distribución uniforme U(0,1) usando la mayor diferencia (D-max).
    """

    def prueba_kolmogorov_smirnov(self, numeros_aleatorios, alpha=0.05):
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
        bool
            True si D-max < D-crítico, False en caso contrario.
        """
        n = len(numeros_aleatorios)
        datos_ordenados = sorted(numeros_aleatorios)

        d_max = 0
        for i in range(1, n + 1):
           
            f_observada = i / n
            f_teorica = datos_ordenados[i - 1]
           
            distancia = abs(f_observada - f_teorica)

            if distancia > d_max:
                d_max = distancia

       
        if n > 50:
            d_critico = 1.36 / math.sqrt(n)
        else:
            
            d_critico = ksone.ppf(1 - alpha / 2, n)


        aceptada = d_max < d_critico

        print(f"  D-Max calculado: {d_max:.5f}")
        print(f"  D-Teórico (D-alfa): {d_critico:.5f}")
        print(f"  Resultado: {'Aceptada' if aceptada else 'Rechazada'}")

        return aceptada
