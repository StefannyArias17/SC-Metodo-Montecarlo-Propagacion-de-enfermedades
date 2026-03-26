class GeneradorCuadradosMedios:
    """
    Generador de números pseudoaleatorios por el método de cuadrados medios.

    El método calcula el siguiente valor entero tomando los dígitos centrales
    del cuadrado del estado actual:

        X_{n+1} = centro((X_n)^2)

    Después normaliza cada valor al intervalo [0, 1):

        R_i = X_i / 10^d

    donde d es la cantidad de dígitos del estado (semilla de trabajo).

    Attributes
    ----------
    semilla : int
        Estado interno actual del generador (X_n).
    digitos : int
        Número de dígitos usados para extraer la parte central.
        Debe ser un número par.
    base_normalizacion : int
        Valor 10^d usado para convertir X_i a R_i en [0, 1).

    Notes
    -----
    - El método es determinista:
      misma semilla + mismo número de dígitos => misma secuencia.
    - Puede degenerar en ciclos cortos o en cero, dependiendo de la semilla.
    """

    def __init__(self, semilla: int, digitos: int = 8):
        """
        Inicializa el generador de cuadrados medios.

        Parameters
        ----------
        semilla : int
            Valor inicial X_0. Debe ser no negativo y menor que 10^d.
        digitos : int, optional
            Cantidad de dígitos de trabajo (d). Debe ser par.
            Por defecto: 8.

        Raises
        ------
        ValueError
            Si digitos no es par.
            Si semilla es negativa.
            Si semilla no cabe en d dígitos.
        """
        if digitos % 2 != 0:
            raise ValueError("digitos debe ser par (ej. 4, 6, 8).")
        if semilla < 0:
            raise ValueError("semilla debe ser no negativa.")
        if semilla >= 10**digitos:
            raise ValueError(
                f"semilla debe tener como máximo {digitos} dígitos."
            )

        self.semilla = semilla
        self.digitos = digitos
        self.base_normalizacion = 10**digitos

    def _siguiente_xi(self) -> int:
        """
        Calcula el siguiente valor entero X_i del método.

        Procedimiento:
        1. Elevar al cuadrado la semilla actual.
        2. Rellenar con ceros a la izquierda hasta longitud 2d.
        3. Extraer los d dígitos centrales.

        Returns
        -------
        int
            Siguiente valor entero X_i.
        """
        cuadrado = self.semilla * self.semilla

        # Asegura longitud 2d para poder extraer el centro correctamente
        cadena = str(cuadrado).zfill(2 * self.digitos)

        # Extrae los d dígitos centrales
        inicio = self.digitos // 2
        fin = inicio + self.digitos
        xi = int(cadena[inicio:fin])

        self.semilla = xi
        return xi

    def siguiente_Ri_Cuadrados_Medios(self, pasos: int):
        """
        Genera una secuencia de números pseudoaleatorios normalizados R_i.

        Parameters
        ----------
        pasos : int
            Cantidad de números a generar.

        Returns
        -------
        list[float]
            Lista de valores R_i en [0, 1).
            Si pasos <= 0, retorna lista vacía.
        """
        if pasos <= 0:
            return []

        secuencia_Ri = []
        for _ in range(pasos):
            xi = self._siguiente_xi()
            ri = xi / self.base_normalizacion
            secuencia_Ri.append(ri)

        return secuencia_Ri