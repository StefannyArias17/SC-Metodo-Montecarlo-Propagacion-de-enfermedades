"""Generador de variables aleatorias con distribucion Uniforme continua.

Usa la transformada inversa para mapear una secuencia U(0, 1)
al intervalo objetivo [a, b) mediante:

    X = a + U * (b - a)
"""


class GeneradorDistribucionUniforme:
    """Generador de numeros pseudoaleatorios con distribucion U(a, b).

    Attributes
    ----------
    --> a (float): Limite inferior del intervalo.
    --> b (float): Limite superior del intervalo (debe cumplir a < b).
    """

    def __init__(self, a: float, b: float):
        """Inicializa el generador para el intervalo U(a, b).

        Parameters
        ----------
        a : float
            Limite inferior.
        b : float
            Limite superior; debe ser mayor que a.
        """
        if a >= b:
            raise ValueError(
                f"El límite inferior 'a' ({a}) debe ser estrictamente menor "
                f"que el límite superior 'b' ({b})."
            )
        self.a = a
        self.b = b

    # Método principal

    def generar(self, uniformes_base: list[float]) -> list[float]:
        """Genera una muestra U(a, b) aplicando transformada inversa.

        Parameters
        ----------
        uniformes_base : list[float]
            Lista de valores en el intervalo [0, 1).

        Returns
        -------
        list[float]
            Lista transformada al intervalo [a, b).

        Raises
        ------
        ValueError
            Si la lista esta vacia o si algun valor no pertenece a [0, 1).
        """
        self._validar_entrada(uniformes_base)

        amplitud = self.b - self.a  # (b - a): factor de escala del intervalo

        # Transformada inversa: F⁻¹(u) = a + u · (b - a)
        return [self.a + u * amplitud for u in uniformes_base]

    # Métodos auxiliares

    def _validar_entrada(self, uniformes_base: list[float]) -> None:
        """Valida que la lista no este vacia y que todos sus valores esten en [0, 1)."""
        if not uniformes_base:
            raise ValueError(
                "La lista 'uniformes_base' no puede estar vacía."
            )

        for i, u in enumerate(uniformes_base):
            if not (0.0 <= u < 1.0):
                raise ValueError(
                    f"El valor en el índice {i} ({u}) está fuera del "
                    f"intervalo válido [0, 1)."
                )
