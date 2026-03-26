class GeneradorCongruencialMultiplicativo:
    """
    Generador de números pseudoaleatorios por el método congruencial multiplicativo.

    Este método usa una recurrencia modular de primer orden:

        X_{n+1} = (a * X_n) mod m

    Cada valor entero X_i se normaliza al intervalo [0, 1) con:

        R_i = X_i / m

    Attributes
    ----------
    semilla : int
        Estado interno actual del generador (valor X_n).
    a : int
        Multiplicador de la recurrencia.
    m : int
        Módulo de la operación congruencial.

    Notes
    -----
    - Requiere una semilla inicial X_0 > 0.
    - El generador es determinista:
      mismos parámetros (semilla, a, m) => misma secuencia.
    - La calidad y el periodo dependen de la elección de a y m.
    """

    def __init__(self, semilla: int, a: int = 1664525, m: int = 2**32):
        """
        Inicializa el generador congruencial multiplicativo.

        Parameters
        ----------
        semilla : int
            Valor inicial X_0. Debe ser mayor que 0.
        a : int, optional
            Multiplicador de la recurrencia. Por defecto 1664525.
        m : int, optional
            Módulo de la recurrencia. Por defecto 2**32.

        Raises
        ------
        ValueError
            Si semilla <= 0.
            Si a <= 0.
            Si m <= 0.
        """
        if semilla <= 0:
            raise ValueError("semilla debe ser mayor que 0.")
        if a <= 0:
            raise ValueError("a (multiplicador) debe ser mayor que 0.")
        if m <= 0:
            raise ValueError("m (módulo) debe ser mayor que 0.")

        self.semilla = semilla % m
        self.a = a
        self.m = m

    def _siguiente_xi(self) -> int:
        """
        Calcula el siguiente valor entero de la secuencia (X_{n+1}).

        Returns
        -------
        int
            Siguiente valor pseudoaleatorio entero X_i.
        """
        xi = (self.a * self.semilla) % self.m
        self.semilla = xi
        return xi

    def siguiente_Ri_Congruencial_Multiplicativo(self, pasos: int):
        """
        Genera una secuencia de números pseudoaleatorios normalizados R_i en [0, 1).

        Parameters
        ----------
        pasos : int
            Cantidad de valores a generar.

        Returns
        -------
        list[float]
            Lista de valores R_i generados.
            Si pasos <= 0, retorna una lista vacía.
        """
        if pasos <= 0:
            return []

        secuencia_Ri = []
        for _ in range(pasos):
            xi = self._siguiente_xi()
            ri = xi / self.m
            secuencia_Ri.append(ri)

        return secuencia_Ri