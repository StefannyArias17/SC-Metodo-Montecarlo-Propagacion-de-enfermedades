import math
from abc import ABC, abstractmethod
import constants

class ContagionConverter(ABC):
    """
    Interfaz abstracta para todos los conversores de la Matriz S; cada implementación convierte un 
    Ri en el resultado del evento epidemiológico correspondiente (contactos generados o decisión de contagio).
    """

    @abstractmethod
    def evaluate(self, ri: float):
        """
        Evalúa el evento dado el número pseudoaleatorio Ri.
        """
        pass

class DailyContactsConverter(ContagionConverter):
    """
    Traduce Ri al número entero de contactos diarios del infectado i
    """

    def __init__(self, beta: float, c_max: int = constants.C_MAX):
        self.beta  = beta
        self.c_max = c_max

    def evaluate(self, ri: float) -> int:
        """Retorna número de contactos = piso(Ri × C_MAX × beta)."""
        return math.floor(ri * self.c_max * self.beta)
    
class UnvaccinatedTransmissionConverter(ContagionConverter):
    """
    Matriz S para transmisión en población NO vacunada.

    Criterio:
        Ri < p_base  → CONTAGIO  (True)
        Ri ≥ p_base  → NO CONTAGIO (False)
    """

    def __init__(self, p_base: float):
        self.p_base     = p_base
        self.p_efectiva = p_base   # sin reducción por vacuna

    def evaluate(self, ri: float) -> bool:
        """Retorna True si hay contagio (Ri < p_base)."""
        return ri < self.p_efectiva

class VaccinatedTransmissionConverter(ContagionConverter):
    """
    Matriz S para transmisión en población PARCIALMENTE vacunada.

    Criterio:
        Ri < p_efectiva  → CONTAGIO  (True)
        Ri ≥ p_efectiva  → NO CONTAGIO (False)
    """

    def __init__(self, p_base: float, tasa_vac: float, efec_vac: float):
        self.p_base     = p_base
        self.tasa_vac   = tasa_vac
        self.efec_vac   = efec_vac
        self.factor_vac = 1.0 - tasa_vac * efec_vac
        self.p_efectiva = p_base * self.factor_vac

    def evaluate(self, ri: float) -> bool:
        """Retorna True si hay contagio con reducción por vacunación."""
        return ri < self.p_efectiva

def crear_conversor_transmision(p_base: float, con_vacunacion: bool,
                                 tasa_vac: float = 0.0,
                                 efec_vac: float = 0.0) -> ContagionConverter:
    """
    Devuelve el conversor de transmisión adecuado para el escenario.

    Parámetros
    ----------
    p_base         : float → probabilidad base de transmisión
    con_vacunacion : bool  → True = escenario con vacunación
    tasa_vac       : float → tasa de vacunación (solo si con_vacunacion=True)
    efec_vac       : float → efectividad vacuna  (solo si con_vacunacion=True)

    Retorna
    -------
    VaccinatedTransmissionConverter   si con_vacunacion=True
    UnvaccinatedTransmissionConverter si con_vacunacion=False
    """
    if con_vacunacion:
        return VaccinatedTransmissionConverter(p_base, tasa_vac, efec_vac)
    return UnvaccinatedTransmissionConverter(p_base)