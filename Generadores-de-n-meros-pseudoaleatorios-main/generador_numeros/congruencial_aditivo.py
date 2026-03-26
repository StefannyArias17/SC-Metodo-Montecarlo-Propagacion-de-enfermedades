class GeneradorCongruencialAditivo:
    """
    Generador de números pseudoaleatorios por el método congruencial aditivo.

    Este generador usa una recurrencia de orden 2 basada en suma modular:

        X_n = (X_{n-1} + X_{n-2}) mod m

    Luego cada valor entero X_i se normaliza a [0, 1) con:

        R_i = X_i / m

    Attributes
    ----------
    estado : list[int]
        Lista con el estado interno del generador.
        Incluye las semillas iniciales y todos los X_i generados.
    m : int
        Módulo usado en la operación de congruencia.

    Notes
    -----
    - Se requieren al menos 2 semillas iniciales.
    - El proceso es determinista:
      mismas semillas + mismo módulo => misma secuencia.
    - El periodo y la calidad estadística dependen de las semillas y de m.
    """

    def __init__(self, semillas_iniciales, m=2**32):
        """
        Inicializa el generador congruencial aditivo.

        Parameters
        ----------
        semillas_iniciales : list[int] | tuple[int, ...]
            Valores iniciales del estado (mínimo 2).
            Cada semilla se ajusta automáticamente con módulo m.
        m : int, optional
            Módulo de la recurrencia. Por defecto 2**32.

        Raises
        ------
        ValueError
            Si se proporcionan menos de 2 semillas.
            Si alguna semilla es negativa.
            Si m es menor o igual a 0.
        """
        if len(semillas_iniciales) < 2:
            raise ValueError("Debes proporcionar al menos 2 semillas iniciales.")
        if any(s < 0 for s in semillas_iniciales):
            raise ValueError("Todas las semillas deben ser no negativas.")
        if m <= 0:
            raise ValueError("El módulo m debe ser mayor que 0.")

        self.estado = [int(s) % m for s in semillas_iniciales]
        self.m = m

    def _siguiente_xi(self):
        """
        Genera el siguiente valor entero X_i de la secuencia.

        Returns
        -------
        int
            Siguiente valor pseudoaleatorio en forma entera (antes de normalizar).

        Notes
        -----
        Usa las dos últimas posiciones del estado:
        X_i = (X_{i-1} + X_{i-2}) mod m
        """
        xi = (self.estado[-1] + self.estado[-2]) % self.m
        self.estado.append(xi)
        return xi

    def siguiente_Ri_Congruencial_Aditivo(self, pasos: int):
        """
        Genera una secuencia de valores normalizados R_i en [0, 1).

        Parameters
        ----------
        pasos : int
            Cantidad de números a generar.

        Returns
        -------
        list[float]
            Lista con los valores R_i generados.
            Si pasos <= 0, retorna lista vacía.
        """
        if pasos <= 0:
            return []

        secuencia_Ri = []
        for _ in range(pasos):
            xi = self._siguiente_xi()
            ri = xi / self.m
            secuencia_Ri.append(ri)

        return secuencia_Ri