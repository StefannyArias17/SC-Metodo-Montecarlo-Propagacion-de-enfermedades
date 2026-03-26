"""Generador de variables aleatorias con distribucion Normal.

Usa el metodo de Box-Muller para transformar numeros U(0, 1) en
variables N(0, 1), y luego escala a N(mu, sigma^2).

Formulas base:
    Z1 = sqrt(-2 * ln(U1)) * cos(2 * pi * U2)
    Z2 = sqrt(-2 * ln(U1)) * sin(2 * pi * U2)
    X  = mu + sigma * Z
"""

import math
from statistics import NormalDist


class GeneradorDistribucionNormal:
    """Generador de numeros pseudoaleatorios con distribucion N(mu, sigma^2).

    Attributes
    ----------
    --> mu (float): Media de la distribucion.
    --> sigma (float): Desviacion estandar (debe ser > 0).

    Notes
    -----
    - Procesa la entrada en pares (U1, U2).
    - Cada par genera dos valores normales.
    """

    # Constante: 2π precalculada para evitar recomputarla en cada iteración
    _DOS_PI: float = 2.0 * math.pi
    _NORMAL_STD: NormalDist = NormalDist(mu=0.0, sigma=1.0)

    def __init__(self, mu: float = 0.0, sigma: float = 1.0):
        """Inicializa el generador.

        Parameters
        ----------
        mu : float
            Media de la distribucion normal.
        sigma : float
            Desviacion estandar; debe ser estrictamente positiva.
        """
        if sigma <= 0:
            raise ValueError(
                f"La desviación estándar 'sigma' ({sigma}) debe ser "
                f"estrictamente positiva."
            )
        self.mu = mu
        self.sigma = sigma

    # Método principal

    def generar(self, uniformes_base: list[float]) -> list[float]:
        """Genera una secuencia N(mu, sigma^2) a partir de uniformes base.

        Parameters
        ----------
        uniformes_base : list[float]
            Lista de valores en el intervalo (0, 1).

        Returns
        -------
        list[float]
            Muestra transformada con Box-Muller y escalada con mu y sigma.

        Raises
        ------
        ValueError
            Si la lista esta vacia o contiene valores fuera de (0, 1).
        """
        self._validar_entrada(uniformes_base)

        muestra: list[float] = []

        # Procesar pares completos con Box-Muller.
        n = len(uniformes_base)
        i = 0
        while i + 1 < n:
            u1 = uniformes_base[i]
            u2 = uniformes_base[i + 1]

            z1, z2 = self._transformacion_box_muller(u1, u2)

            # Escalar de N(0,1) a N(μ, σ²): X = μ + σ·Z
            muestra.append(self.mu + self.sigma * z1)
            muestra.append(self.mu + self.sigma * z2)

            i += 2

        # Si n es impar, transformar el último uniforme con inversa normal.
        if n % 2 != 0:
            z = self._inversa_normal_estandar(uniformes_base[-1])
            muestra.append(self.mu + self.sigma * z)

        return muestra

    # Métodos auxiliares

    def _transformacion_box_muller(
        self, u1: float, u2: float
    ) -> tuple[float, float]:
        """Transforma un par (u1, u2) de U(0, 1) a un par (z1, z2) de N(0, 1)."""
        # Amplitud radial: derivada de la CDF de la distribución chi² con 2 gl
        radio = math.sqrt(-2.0 * math.log(u1))

        # Ángulo uniformemente distribuido en [0, 2π)
        angulo = self._DOS_PI * u2

        # Proyección cartesiana: produce dos normales estándar independientes
        z1 = radio * math.cos(angulo)
        z2 = radio * math.sin(angulo)

        return z1, z2

    def _inversa_normal_estandar(self, u: float) -> float:
        """Obtiene z tal que P(Z <= z) = u para Z ~ N(0, 1)."""
        return self._NORMAL_STD.inv_cdf(u)

    def _validar_entrada(self, uniformes_base: list[float]) -> None:
        """Valida que la lista de entrada no sea vacia y que todos sus valores esten en (0, 1)."""
        if not uniformes_base:
            raise ValueError(
                "La lista 'uniformes_base' no puede estar vacía."
            )

        for i, u in enumerate(uniformes_base):
            if not (0.0 < u < 1.0):
                raise ValueError(
                    f"El valor en el índice {i} ({u}) está fuera del "
                    f"intervalo válido (0, 1). Box-Muller requiere u > 0 "
                    f"para que ln(u) esté definido."
                )
