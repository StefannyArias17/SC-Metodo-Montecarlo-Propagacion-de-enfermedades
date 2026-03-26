import math

from scipy.stats import norm  # type: ignore


class PruebaRachas:
    def prueba_rachas(self, numeros_aleatorios, alpha=0.05):
        # Datos para la prueba de rachas
        mediana_teorica = 0.5
        probabilidad_acumulada = 1 - alpha / 2
        z_teorico = norm.ppf(probabilidad_acumulada)

        rango_Min = z_teorico * -1
        rango_Max = z_teorico

        n = len(numeros_aleatorios)

        # Contar rachas, 1 --> + y 0 --> -
        signos = [1 if num >= mediana_teorica else 0 for num in numeros_aleatorios]

        rachas_totales = 1
        for i in range(1, len(signos)):
            if signos[i] != signos[i - 1]:
                rachas_totales += 1

        n_pos = sum(signos)
        n_neg = n - n_pos

        numerador = 2 * n_pos * n_neg

        media_rachas = (numerador / n) + 1
        varianza_rachas = (numerador * (numerador - n)) / ((n**2) * (n - 1))

        z_estadistico = (rachas_totales - media_rachas) / math.sqrt(varianza_rachas)

        if rango_Min <= z_estadistico <= rango_Max:
            print("Prueba de Rachas: Aceptada")
            print(f"  Z estadístico: {z_estadistico:.4f}")
            print(f"  Rango aceptable: [{rango_Min:.4f}, {rango_Max:.4f}]")
            print(f"Total muestras: {n_pos + n_neg}")
            return True
        else:
            print("Prueba de Rachas: Rechazada")
            print(f"  Z estadístico: {z_estadistico:.4f}")
            print(f"  Rango aceptable: [{rango_Min:.4f}, {rango_Max:.4f}]")
            print(f"Total muestras: {n_pos + n_neg}")
            return False
