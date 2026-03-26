from scipy.stats import norm  # type: ignore


class PruebaMedias:
    """
    Validación de aleatoriedad mediante prueba de Medias.

    Verifica si la media muestral está dentro del intervalo de confianza
    esperado para una distribución uniforme U(0,1) con media teórica 0.5.
    Usa distribución normal con α = 0.05 (95% confianza).
    """

    def prueba_medias(self, numeros_aleatorios):
        """
        Ejecuta prueba de Medias sobre una secuencia.

        Parameters
        ----------
        numeros_aleatorios : list[float]
            Secuencia U(0,1) a validar.

        Returns
        -------
        bool
            True si media está dentro del intervalo de aceptación, False en caso contrario.

        Notes
        -----
        Intervalo de aceptación:
        LLR = 0.5 - Z_α/2 * √(1/12n)
        LSR = 0.5 + Z_α/2 * √(1/12n)
        """
        n = len(numeros_aleatorios)
        media_calculada = sum(numeros_aleatorios) / n
        media_teorica = 0.5

        alpha = 0.05 

        
        Z_alpha_2 = norm.ppf(1 - alpha / 2) 

        # Límites
        desviacion = (1 / (12 * n)) ** 0.5
        LLR = media_teorica - Z_alpha_2 * desviacion
        LSR = media_teorica + Z_alpha_2 * desviacion

        if LLR <= media_calculada <= LSR:
            print("Prueba de medias: Aceptada")
            print(f"  Media calculada: {media_calculada:.8f}")
            print(f"  Rango: [{LLR:.8f}, {LSR:.8f}]")
            return True
        else:
            print("Prueba de medias: Rechazada")
            print(f"  Media calculada: {media_calculada:.8f}")
            print(f"  Rango: [{LLR:.8f}, {LSR:.8f}]")
            return False
