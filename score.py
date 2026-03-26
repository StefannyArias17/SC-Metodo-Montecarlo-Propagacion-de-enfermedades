"""
Clases de datos para almacenar los resultados del modelo EpiSim 

Almacena los resultados de cada simulación individual y agrega estadísticas
por escenario (Sin Vacunación / Con Vacunación).
"""

import constants

class SimulationResult:
    """
    Resultado completo de UNA simulación SEIR de DAYS días.

    Atributos:
        id          (int)   : Identificador del número de la simulación (0 a N_SIMULATIONS-1)
        curva_S     (list)  : Susceptibles por día [0 a DAYS-1]
        curva_E     (list)  : Expuestos por día
        curva_I     (list)  : Infectados activos por día
        curva_R     (list)  : Recuperados/removidos por día
        pico_I      (int)   : Valor más alto de infectados activos
        dia_pico    (int)   : Día del pico (empieza en 1 por defecto)
        total_inf   (int)   : Total infectados acumulados al finalizar la simulación
        dia_ctrl    (int)   : Día en que I cae bajo el 1% del pico (cuando la epidemia se controla)
        params      (dict)  : Parámetros estocásticos de esta corrida
    """

    def __init__(self, id: int):
        self.id        = id
        self.curva_S   = []
        self.curva_E   = []
        self.curva_I   = []
        self.curva_R   = []
        self.pico_I    = 0
        self.dia_pico  = 1
        self.total_inf = 0
        self.dia_ctrl  = constants.DAYS
        self.params    = {}

    def finalizar(self):
        """Calcula métricas derivadas al terminar la simulación."""
        if self.curva_I:
            self.pico_I   = max(self.curva_I)
            self.dia_pico = self.curva_I.index(self.pico_I) + 1

        # Total infectados = R final + I final + E final
        self.total_inf = ((self.curva_R[-1] if self.curva_R else 0) +
                          (self.curva_I[-1] if self.curva_I else 0) +
                          (self.curva_E[-1] if self.curva_E else 0))

        # Día de control: primera vez que I < 1% del pico (post-pico)
        umbral = max(1, self.pico_I * 0.01)
        for d in range(self.dia_pico - 1, len(self.curva_I)):
            if self.curva_I[d] < umbral:
                self.dia_ctrl = d + 1
                break

class ScenarioResults:
    """
    Agrega los resultados de todas las simulaciones de UN escenario (vacunación / no vacunaición).
    
    Atributos:
        nombre       (str)         : 'Sin Vacunación' o 'Con Vacunación'
        resultados   (list)        : Lista de SimulationResult
        prom_S/E/I/R (list[float]) : Promedio diario de cada compartimento sobre el total de simulaciones
        lo_S/E/I/R   (list[float]) : Percentil 2.5% por día (IC 95% inferior)
        hi_S/E/I/R   (list[float]) : Percentil 97.5% por día (IC 95% superior)
        stats        (dict)        : Estadísticas descriptivas de métricas clave
        tiempo_s     (float)       : Tiempo de CPU del escenario en segundos
    """

    def __init__(self, nombre: str):
        self.nombre = nombre
        self.resultados = []
        for attr in ("prom_S", "prom_E", "prom_I", "prom_R",
                     "lo_S",   "hi_S",   "lo_E",   "hi_E",
                     "lo_I",   "hi_I",   "lo_R",   "hi_R"):
            setattr(self, attr, [])
        self.stats    = {}
        self.tiempo_s = 0.0

    def agregar(self, r: SimulationResult):
        """Añade el resultado de una simulación individual."""
        self.resultados.append(r)

    def calcular_agregados(self):
        """Calcula promedios e IC 95% tras completar todas las simulaciones."""
        n = len(self.resultados)
        dias = constants.DAYS
        if n == 0:
            return

        # Promedio diario de cada curva
        def prom(k):
            return [sum(getattr(r, k)[d] for r in self.resultados) / n
                    for d in range(dias)]

        # Intervalo de confianza para dibujar la sombra
        def ic(k):
            i_lo = max(0, int(0.025 * n))
            i_hi = min(n - 1, int(0.975 * n))
            lo, hi = [], []
            for d in range(dias):
                v = sorted(getattr(r, k)[d] for r in self.resultados)
                lo.append(v[i_lo])
                hi.append(v[i_hi])
            return lo, hi

        self.prom_S, (self.lo_S, self.hi_S) = prom("curva_S"), ic("curva_S")
        self.prom_E, (self.lo_E, self.hi_E) = prom("curva_E"), ic("curva_E")
        self.prom_I, (self.lo_I, self.hi_I) = prom("curva_I"), ic("curva_I")
        self.prom_R, (self.lo_R, self.hi_R) = prom("curva_R"), ic("curva_R")

        # Estadísticas descriptivas
        def _s(lst):
            nn = len(lst)
            mu = sum(lst) / nn
            sd = (sum((x - mu)**2 for x in lst) / max(1, nn - 1))**0.5
            s  = sorted(lst)
            return {
                "media":    mu,
                "desv_std": sd,
                "mediana":  s[nn // 2],
                "min":      s[0],
                "max":      s[-1],
                "p25":      s[nn // 4],
                "p75":      s[3 * nn // 4],
                "raw":      lst,
            }

        # Análisis estadístico (creo)
        self.stats = {
            "picos":   _s([r.pico_I    for r in self.resultados]),
            "dias_p":  _s([r.dia_pico  for r in self.resultados]),
            "totales": _s([r.total_inf for r in self.resultados]),
            "dias_c":  _s([r.dia_ctrl  for r in self.resultados]),
            "betas":   _s([r.params.get("beta", 0)        for r in self.resultados]),
            "p_efec":  _s([r.params.get("p_efectiva", 0)  for r in self.resultados]),
        }