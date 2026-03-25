"""
Implementación de la matriz S del modelo SEIR de EpiSim

Toma un número pseudoaleatorio Ri ∈[0,1) y define con precisión qué evento epidemiológico ocurre 
en cada paso del proceso estocástico

Paso 1 (Contactos Diarios) : Traduce Ri en un número entero de contactos diarios mediante la clase DailyContactsConverter
Paso 3 (Transmisión)       : Evalúa si un contacto resulta en contagio (S→E), 
    gestionando por separado la lógica para poblaciones no vacunadas y parcialmente vacunadas
"""

import math
from abc import ABC, abstractmethod
import constants

# CLASE BASE ABSTRACTA
class ContagionConverter(ABC):
    """
    Interfaz abstracta para todos los conversores de la Matriz S; cada implementación convierte un 
    Ri en el resultado del evento epidemiológico correspondiente (contactos generados o decisión de contagio).
    """

    @abstractmethod
    def evaluate(self, ri: float):
        """Evalúa el evento dado el número pseudoaleatorio Ri."""
        pass

# CONVERSOR DE CONTACTOS DIARIOS
class DailyContactsConverter(ContagionConverter):
    """Traduce Ri al número entero de contactos diarios del infectado i"""

    def __init__(self, beta: float, c_max: int = constants.C_MAX):
        """
        Atributos:
            beta (float) : -> tasa de contacto del infectado U(BETA_MIN, BETA_MAX)
            c_max  (int) : -> factor de escala (constants.C_MAX = 5)
        """
        self.beta  = beta
        self.c_max = c_max

    def evaluate(self, ri: float) -> int:
        """Retorna número de contactos = piso(Ri × C_MAX × beta)."""
        return math.floor(ri * self.c_max * self.beta)

# CONVERSOR DE CONTACTOS DIARIOS     
class UnvaccinatedTransmissionConverter(ContagionConverter):
    """
    Matriz S para transmisión en población NO vacunada.

    Criterio:
        Ri < p_base  -> CONTAGIO     (True)
        Ri ≥ p_base  -> NO CONTAGIO  (False)
    """

    def __init__(self, p_base: float):
        self.p_base     = p_base
        self.p_efectiva = p_base   # No tiene reducción por vacuna

    def evaluate(self, ri: float) -> bool:
        """Retorna True si hay contagio (Ri < p_base)."""
        return ri < self.p_efectiva

# CONVERSOR DE TRANSMISIÓN CON VACUNACIÓN
class VaccinatedTransmissionConverter(ContagionConverter):
    """
    Matriz S para transmisión en población PARCIALMENTE vacunada.

    Criterio:
        Ri < p_efectiva  -> CONTAGIO     (True)
        Ri ≥ p_efectiva  -> NO CONTAGIO  (False)
    """

    def __init__(self, p_base: float, tasa_vac: float, efec_vac: float):
        """
        Atributos:
            p_base     (float) : -> probabilidad base  U(P_TRANS_MIN, P_TRANS_MAX)
            tasa_vac   (float) : -> tasa de vacunación U(VAC_RATE_MIN, VAC_RATE_MAX)
            efec_vac   (float) : -> efectividad vacuna U(VAC_EFEC_MIN, VAC_EFEC_MAX)
            factor_vac (float) : -> factor de vulnerabilidad residual 1.0 - (tasa_vac x efec_vac)
            p_efectiva (float) : -> probabilidad de transmisión ajustada p_base x factor_vac
        """
        self.p_base     = p_base
        self.tasa_vac   = tasa_vac
        self.efec_vac   = efec_vac
        self.factor_vac = 1.0 - tasa_vac * efec_vac
        self.p_efectiva = p_base * self.factor_vac

    def evaluate(self, ri: float) -> bool:
        """Retorna True si hay contagio con reducción por vacunación."""
        return ri < self.p_efectiva

# MATRIZ DE TRANSMISIÓN
def crear_conversor_transmision(p_base: float, con_vacunacion: bool,
                                 tasa_vac: float = 0.0,
                                 efec_vac: float = 0.0) -> ContagionConverter:
    """
    Devuelve el conversor de transmisión adecuado para el escenario.

    Parámetros:
        p_base         (float) -> probabilidad base de transmisión
        con_vacunacion (bool)  -> True = escenario con vacunación
        tasa_vac       (float) -> tasa de vacunación (solo si con_vacunacion=True)
        efec_vac       (float) -> efectividad vacuna (solo si con_vacunacion=True)

    Retornos:
        VaccinatedTransmissionConverter   si con_vacunacion=True
        UnvaccinatedTransmissionConverter si con_vacunacion=False
    """
    if con_vacunacion:
        return VaccinatedTransmissionConverter(p_base, tasa_vac, efec_vac)
    return UnvaccinatedTransmissionConverter(p_base)