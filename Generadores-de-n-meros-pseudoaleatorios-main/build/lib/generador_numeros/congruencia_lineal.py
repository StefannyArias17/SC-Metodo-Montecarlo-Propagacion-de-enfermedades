class GeneradorCongruenciaLineal:
    """
    Generador de números pseudoaleatorios usando el método de Congruencia Lineal.

    Fórmula: X_{n+1} = (a * X_n + c) mod m

    Attributes
    ----------
    --> semilla (int): Valor inicial para la secuencia pseudoaleatoria (X_0).
    --> a (int): Multiplicador (1664525, valor recomendado por Numerical Recipes).
    --> c (int): Incremento (1013904223).
    --> m (int): Módulo (2^32, rango máximo de valores).
    --> Método Formal: Ri = Xi / m


    Methods
    -------
    generar_Xi(pasos)
        Genera una secuencia de números enteros pseudoaleatorios X_i.

    generar_Ri(pasos)
        Genera una secuencia de números pseudoaleatorios uniformes en [0, 1).

    Notes
    -----
    - Los parámetros (a, c, m) están optimizados según Numerical Recipes
    - La semilla debe ser un entero positivo menor que m
    - La secuencia es determinista: misma semilla = misma secuencia
    """

    def __init__(self, semilla):
        """
        Inicializar el generador con una semilla específica.

        Parameters
        ----------
        semilla : int
            Valor inicial para la secuencia pseudoaleatoria. Debe ser un
            entero no negativo menor que 2^32.
        """
        self.semilla = semilla  # Semilla
        self.a = 1664525  # Multiplicador
        self.c = 1013904223  # Incremento
        self.m = 2**32  # Módulo

    def siguiente_Ri_Congruencia_Lineal(self, pasos: int):
        """
        Genera el siguiente número pseudoaleatorio R_i en el rango [0, 1).

        Aplica la fórmula de congruencia lineal para actualizar el estado
        interno (self.semilla) y devuelve el número normalizado R_i.

        Returns
        -------
        float
            El siguiente número pseudoaleatorio R_i en el rango [0, 1).

        Notes
        -----
        - Cada llamada a este método avanza la secuencia y modifica el estado
          interno del generador.
        - El valor devuelto es siempre >= 0 y < 1.
        """
        secuencia_Ri = []
        for _ in range(pasos):
            # Calcular el siguiente X_i usando la fórmula de congruencia lineal
            siguiente_Xi = (self.a * self.semilla + self.c) % self.m
            self.semilla = siguiente_Xi
            # Normalizar X_i para obtener R_i en el rango [0, 1)
            Ri_normalizado = siguiente_Xi / self.m
            secuencia_Ri.append(Ri_normalizado)
        return secuencia_Ri
