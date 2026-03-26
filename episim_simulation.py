"""
Motor de simulación Monte Carlo del modelo SEIR de EpiSim
 
Implementa la mecánica estocástica completa descrita:
    - Pool de 10M números pseudoaleatorios generados con el LCG del Punto 3
    - Simulaciones PAREADAS: cada par sin/con vacunación comparte los mismos
      parámetros epidemiológicos base, de manera que la única variable que cambia
      entre escenarios es el factor de vacunación
    - Los tres pasos estocásticos (contactos, selección, transmisión) se ejecutan
      día a día durante 365 días por simulación
"""

import math
import time
import constants
from pseudorandom_adapter          import generar_pool_global, validar_generador, graficar_validacion
from score               import SimulationResult, ScenarioResults
from contagion_conversion import (DailyContactsConverter,
                                  UnvaccinatedTransmissionConverter,
                                  VaccinatedTransmissionConverter,
                                  crear_conversor_transmision)

# POOL GLOBAL DE NÚMEROS PSEUDOALEATORIOS
class PoolGlobal:
    """
    Gestiona el banco de números U(0,1) que alimenta toda la simulación.
 
    Se genera un pool de N_POOL números al inicio usando el LCG del Punto 3.
    Cuando el pool se agota, se recarga con una semilla derivada
    y el evento queda registrado en la Matriz s,x para trazabilidad.
 
    Atributos:
        semilla_maestra (int)  : semilla inicial del generador
        n_pool          (int)  : tamaño del pool (default N_POOL del constants)
        _ciclo          (int)  : número de recargas realizadas
        _consumo_total  (int)  : cantidad total de números entregados
        matriz_sx       (dict) : registro de la Matriz s,x (semilla, parámetros, ciclos)
        res_val         (dict) : resultados del Probador General sobre el pool inicial
    """

    def __init__(self, semilla: int = constants.SEMILLA_MAESTRA,
                 n: int = constants.N_POOL):
        self.semilla_maestra = semilla
        self.n_pool          = n
        self._ciclo          = 0
        self._consumo_total  = 0
        self.matriz_sx = {
            "semilla_inicial" : semilla,
            "a": 1_664_525, "c": 1_013_904_223, "m": 2**32,
            "origen"          : "Punto 3 — Congruencia Lineal",
            "ciclos"          : [],
        }

        print("=" * 60)
        print("  EpiSim — Generando pool de números pseudoaleatorios")
        print(f"  Fuente: Biblioteca del Punto 3 (Congruencia Lineal)")
        print(f"  Pool: {n:,} números | Semilla: {semilla}")
        print("=" * 60)
        self._pool = generar_pool_global(semilla=semilla, n=n)
        self._idx  = 0

        print("\n  Ejecutando Probador General...")
        self.res_val = validar_generador(self._pool, verbose=True)
        if not self.res_val["todas_aprueban"]:
            print("  ADVERTENCIA: el generador no pasó todas las pruebas.")

    def siguiente(self) -> float:
        """
        Devuelve el siguiente número U(0,1) del pool.
 
        Si el pool se agotó, genera uno nuevo con semilla derivada de forma
        silenciosa y registra el evento en la Matriz s,x.
        """
        if self._idx >= len(self._pool):
            self._ciclo  += 1
            s_nueva       = self.semilla_maestra + self._ciclo * 1_000_003
            self.matriz_sx["ciclos"].append({
                "ciclo": self._ciclo, "semilla": s_nueva,
                "consumo_antes": self._consumo_total,
            })
            # Recarga silenciosa el evento queda en la Matriz s,x
            self._pool = self._generar_silencioso(s_nueva)
            self._idx  = 0
        val = self._pool[self._idx]
        self._idx           += 1
        self._consumo_total += 1
        return val

    def _generar_silencioso(self, semilla: int) -> list:
        """Genera un nuevo pool sin imprimir en consola (usa Punto 3 LCG)."""
        import sys, os
        _P3_ROOT = os.path.join(os.path.dirname(__file__), "generadores_p3")
        if _P3_ROOT not in sys.path:
            sys.path.insert(0, _P3_ROOT)
        from generador_numeros.congruencia_lineal import GeneradorCongruenciaLineal
        gen = GeneradorCongruenciaLineal(semilla=semilla)
        return gen.siguiente_Ri_Congruencia_Lineal(self.n_pool)

    def guardar_validacion(self, ruta: str):
        graficar_validacion(self._pool, self.res_val, ruta)

    def imprimir_matriz_sx(self):
        """Imprime el estado final de la Matriz s,x con todos los ciclos de recarga."""
        m = self.matriz_sx
        print("\n" + "=" * 55)
        print("  MATRIZ s,x — Estado Final del Generador")
        print("=" * 55)
        print(f"  Semilla inicial (s)  : {m['semilla_inicial']}")
        print(f"  a={m['a']:,}  c={m['c']:,}  m=2^32")
        print(f"  Ri totales consumidos: {self._consumo_total:,}")
        print(f"  Ciclos de recarga    : {len(m['ciclos'])}")
        for rec in m["ciclos"]:
            print(f"    Ciclo {rec['ciclo']}: semilla={rec['semilla']}, "
                  f"consumo previo={rec['consumo_antes']:,}")
        print("=" * 55)

# PARÁMETROS ESTOCÁSTICOS DE LA SIMULACIÓN
class SimParams:
    """
    Muestrea y almacena los parámetros de la simulación desde el pool global.
 
    Cuando se pasa params_base, reutiliza beta/sigma/gamma/p_base del par anterior
    (simulación pareada) y solo muestrea los parámetros de vacunación. Esto garantiza
    que la comparación sin/con vacunación sea honesta, porque la única diferencia
    entre escenarios es el factor_vac.
 
    Atributos:
        beta          (float) : tasa de contacto básico muestreada U(BETA_MIN, BETA_MAX)
        sigma_inv     (float) : periodo de incubación muestreado U(SIGMA_INV_MIN, SIGMA_INV_MAX)
        gamma_inv     (float) : periodo infeccioso muestreado U(GAMMA_INV_MIN, GAMMA_INV_MAX)
        p_base        (float) : probabilidad base de transmisión U(P_TRANS_MIN, P_TRANS_MAX)
        tasa_vac      (float) : tasa de vacunación U(VAC_RATE_MIN, VAC_RATE_MAX) o 0 si no hay vacuna
        efec_vac      (float) : efectividad de la vacuna U(VAC_EFEC_MIN, VAC_EFEC_MAX) o 0
        factor_vac    (float) : vulnerabilidad residual = 1 - tasa_vac × efec_vac
        p_efectiva    (float) : probabilidad de contagio ajustada = p_base × factor_vac
        periodo_incub (int)   : días en estado E antes de pasar a I
        periodo_infec (int)   : días en estado I antes de pasar a R
        contactos_conv        : conversor Paso 1 (DailyContactsConverter)
        trans_conv            : conversor Paso 3 (vacunado o no vacunado)
    """

    def __init__(self, pool: PoolGlobal, con_vacunacion: bool = True,
                 params_base: dict = None):
        p = constants
        if params_base is None:
            # Simulación sin vacuna: muestrea todos los parámetros base desde el pool
            self.beta      = p.BETA_MIN    + (p.BETA_MAX    - p.BETA_MIN)    * pool.siguiente()
            self.sigma_inv = p.SIGMA_INV_MIN+(p.SIGMA_INV_MAX-p.SIGMA_INV_MIN)*pool.siguiente()
            self.gamma_inv = p.GAMMA_INV_MIN+(p.GAMMA_INV_MAX-p.GAMMA_INV_MIN)*pool.siguiente()
            self.p_base    = p.P_TRANS_MIN + (p.P_TRANS_MAX  - p.P_TRANS_MIN) * pool.siguiente()
        else:
            # Simulación con vacuna: hereda los parámetros del par ya corrido
            self.beta      = params_base["beta"]
            self.sigma_inv = params_base["sigma_inv"]
            self.gamma_inv = params_base["gamma_inv"]
            self.p_base    = params_base["p_base"]

        if con_vacunacion:
            self.tasa_vac   = p.VAC_RATE_MIN+(p.VAC_RATE_MAX-p.VAC_RATE_MIN)*pool.siguiente()
            self.efec_vac   = p.VAC_EFEC_MIN+(p.VAC_EFEC_MAX-p.VAC_EFEC_MIN)*pool.siguiente()
            self.factor_vac = 1.0 - self.tasa_vac * self.efec_vac
        else:
            self.tasa_vac = self.efec_vac = 0.0
            self.factor_vac = 1.0

        self.p_efectiva    = self.p_base * self.factor_vac
        # Los períodos se redondean al día más cercano; mínimo 1 para no bloquear la progresión
        self.periodo_incub = max(1, round(self.sigma_inv))
        self.periodo_infec = max(1, round(self.gamma_inv))

        # Conversores de la Matriz S (contagion_conversion.py)
        self.contactos_conv = DailyContactsConverter(self.beta, p.C_MAX)
        self.trans_conv     = crear_conversor_transmision(
            self.p_base, con_vacunacion, self.tasa_vac, self.efec_vac
        )

    def base_dict(self) -> dict:
        """Devuelve los parámetros base para pasarlos al par con vacunación."""
        return {"beta": self.beta, "sigma_inv": self.sigma_inv,
                "gamma_inv": self.gamma_inv, "p_base": self.p_base}

    def to_dict(self) -> dict:
        """Devuelve todos los parámetros para almacenarlos en SimulationResult."""
        d = self.base_dict()
        d.update({"tasa_vac": self.tasa_vac, "efec_vac": self.efec_vac,
                  "factor_vac": self.factor_vac, "p_efectiva": self.p_efectiva})
        return d

# LA MECÁNICA DÍA A DÍA
class DaySimulation:
    """
    Ejecuta un día del modelo estocástico SEIR.
 
    Implementa los tres pasos del enunciado más la progresión determinística de estados. 
    Se instancia una vez por simulación y se llama 365 veces (Los días del año dahhh).
 
    Atributos:
        params (SimParams)  : parámetros epidemiológicos de la simulación
        pool   (PoolGlobal) : fuente de números pseudoaleatorios
    """
    def __init__(self, params: SimParams, pool: PoolGlobal):
        self.params = params
        self.pool   = pool

    def execute(self, S, E_cola, I_cola, R):
        """
        Avanza un día completo de propagación.
 
        Parámetros:
            S      (int)  : susceptibles al inicio del día
            E_cola (list) : días acumulados en E para cada expuesto
            I_cola (list) : días acumulados en I para cada infectado
            R      (int)  : recuperados acumulados
 
        Retorna:
            S      (int)  : susceptibles al final del día
            E_cola (list) : cola actualizada de expuestos
            I_cola (list) : cola actualizada de infectados
            R      (int)  : recuperados al final del día
            nuevos_E (int): nuevas infecciones ocurridas este día
        """
        nuevos_E = 0

        # PASO 1 - por cada infectado activo se generan sus contactos del día
        for _ in I_cola:
            if S <= 0:
                break
            nc = self.params.contactos_conv.evaluate(self.pool.siguiente())
            for _ in range(nc):
                if S <= 0:
                    break
                # PASO 2 - selección real del susceptible contactado
                ri_s = self.pool.siguiente()
                _idx = int(ri_s * S) # índice en [0, S-1]; todos son susceptibles en modelo mezclado
                # PASO 3 - evaluación estocástica de transmisión
                if self.params.trans_conv.evaluate(self.pool.siguiente()):
                    S -= 1; nuevos_E += 1

        # PROGRESIÓN E → I (determinística por días acumulados)
        E_nueva  = []; nuevos_I = 0
        for d in E_cola:
            d += 1
            if d >= self.params.periodo_incub: nuevos_I += 1
            else: E_nueva.append(d)
        E_nueva.extend([0] * nuevos_E) # los que están recién expuestos entran con cero días

        # PROGRESIÓN I → R (determinística por días acumulados)
        I_nueva  = []; nuevos_R = 0
        for d in I_cola:
            d += 1
            if d >= self.params.periodo_infec: nuevos_R += 1
            else: I_nueva.append(d)
        I_nueva.extend([0] * nuevos_I)

        return S, E_nueva, I_nueva, R + nuevos_R, nuevos_E

def _sim_pico_rapido(pool: PoolGlobal, beta, p_base, tasa_vac, efec_vac) -> int:
    """
    Corre una simulación completa de 365 días y devuelve solo el pico de infectados.
 
    Se usa exclusivamente en el análisis de sensibilidad, donde se necesitan
    cientos de simulaciones rápidas con parámetros fijos y es reutiliza en DaySimulation
    para no duplicar la mecánica de contagio.
 
    Parámetros:
        pool      (PoolGlobal) : pool compartido con el run principal
        beta      (float)      : tasa de contacto fija para este nivel
        p_base    (float)      : probabilidad de transmisión base
        tasa_vac  (float)      : tasa de vacunación fija
        efec_vac  (float)      : efectividad de la vacuna
 
    Retorna:
        pico (int) : máximo de infectados simultáneos en los 365 días
    """
    import types
    p = types.SimpleNamespace(
        beta      = beta,
        sigma_inv = (constants.SIGMA_INV_MIN + constants.SIGMA_INV_MAX) / 2,
        gamma_inv = (constants.GAMMA_INV_MIN + constants.GAMMA_INV_MAX) / 2,
        p_base    = p_base,
        tasa_vac  = tasa_vac,
        efec_vac  = efec_vac,
        factor_vac       = 1.0 - tasa_vac * efec_vac,
        p_efectiva       = p_base * (1.0 - tasa_vac * efec_vac),
        periodo_incub    = max(1, round((constants.SIGMA_INV_MIN + constants.SIGMA_INV_MAX) / 2)),
        periodo_infec    = max(1, round((constants.GAMMA_INV_MIN + constants.GAMMA_INV_MAX) / 2)),
        contactos_conv   = DailyContactsConverter(beta, constants.C_MAX),
        trans_conv       = crear_conversor_transmision(p_base, tasa_vac > 0, tasa_vac, efec_vac),
    )
    sim_dia = DaySimulation(p, pool)
    S = constants.N_POPULATION - constants.I0_INFECTED
    E = []; I = [0] * constants.I0_INFECTED; R = 0
    pico = constants.I0_INFECTED
    for _ in range(constants.DAYS):
        if S <= 0:
            break
        S, E, I, R, _ = sim_dia.execute(S, E, I, R)
        if len(I) > pico:
            pico = len(I)
    return pico

# CLASE PRINCIPAL
class EpiSim:
    """
    Orquesta las 1.000 simulaciones Monte Carlo del modelo SEIR.
 
    Ejecuta dos escenarios en paralelo (sin y con vacunación) usando
    simulaciones pareadas, calcula los agregados estadísticos y corre
    el análisis de sensibilidad sobre los tres parámetros clave.
 
    Atributos:
        pool            (PoolGlobal)     : banco de números pseudoaleatorios
        sin_vacunacion  (ScenarioResults): resultados del escenario base
        con_vacunacion  (ScenarioResults): resultados del escenario con vacuna
        sensibilidad    (dict)           : impacto de β, p y vacunación sobre el pico
        tiempo_total_s  (float)          : tiempo total de ejecución en segundos
    """

    def __init__(self):
        self.pool = None
        self.sin_vacunacion = ScenarioResults("Sin Vacunación")
        self.con_vacunacion = ScenarioResults("Con Vacunación")
        self.sensibilidad   = {}
        self.tiempo_total_s = 0.0

    def execute(self):
        """
        Este es el punto de entrada principal. Ejecuta el modelo completo en este orden:
            1. Genera y valida el pool de números pseudoaleatorios
            2. Corre N_SIMULATIONS pares de simulaciones pareadas
            3. Calcula promedios e IC 95% por escenario
            4. Corre el análisis de sensibilidad
            5. Imprime la Matriz s,x final
        """
        t0 = time.time()
        n  = constants.N_SIMULATIONS

        print("\n" + "="*60)
        print("  EpiSim — Simulación Monte Carlo SEIR")
        print(f"  N={constants.N_POPULATION:,} | {constants.DAYS} días | {n:,} sims")
        print("="*60)

        self.pool    = PoolGlobal()

        print(f"\n  Ejecutando {n:,} pares de simulaciones (pareadas sin/con vacuna)...")
        t_sims = time.time()

        t_sin = 0.0   # acumulador tiempo sin vacunación
        t_con = 0.0   # acumulador tiempo con vacunación

        for i in range(n):
            # SIN vacuna: muestrea parámetros base
            t0_sin = time.time()
            res_sin, base = self._run_sim(i, con_vacunacion=False, params_base=None)
            t_sin += time.time() - t0_sin

            # Con vacuna: hereda los parámetros base, solo varía el factor de vacunación
            t0_con = time.time()
            res_con, _    = self._run_sim(i, con_vacunacion=True,  params_base=base)
            t_con += time.time() - t0_con

            self.sin_vacunacion.agregar(res_sin)
            self.con_vacunacion.agregar(res_con)

            if (i+1) % 200 == 0:
                elapsed = time.time() - t_sims
                ps = sum(r.pico_I for r in self.sin_vacunacion.resultados[-200:])/200
                pc = sum(r.pico_I for r in self.con_vacunacion.resultados[-200:])/200
                print(f"    [{i+1:>5}/{n}] {elapsed:>5.1f}s | "
                      f"pico sin={ps:.0f} | pico con={pc:.0f}")

        # Asignar tiempos individuales a cada escenario
        self.sin_vacunacion.tiempo_s = round(t_sin, 2)
        self.con_vacunacion.tiempo_s = round(t_con, 2)

        print("  Calculando agregados estadísticos...")
        self.sin_vacunacion.calcular_agregados()
        self.con_vacunacion.calcular_agregados()

        print("\n  Análisis de sensibilidad (5 niveles × 3 parámetros × 50 reps)...")
        self.sensibilidad = self._analisis_sensibilidad()

        self.tiempo_total_s = round(time.time()-t0, 2)
        self.pool.imprimir_matriz_sx()


    def _run_sim(self, id: int, con_vacunacion: bool,
                 params_base: dict) -> tuple:
        """
        Corre una simulación SEIR completa.
 
        Parámetros:
            id             (int)  : identificador de la simulación
            con_vacunacion (bool) : True si es el escenario con vacuna
            params_base    (dict) : parámetros del par sin vacuna (None si es la primera)
 
        Retorna:
            res  (SimulationResult) : resultado con curvas y métricas
            base (dict)             : parámetros base para pasarle al par con vacuna
        """
        params = SimParams(self.pool, con_vacunacion=con_vacunacion,
                           params_base=params_base)
        res    = SimulationResult(id=id)
        res.params = params.to_dict()
        S=constants.N_POPULATION-constants.I0_INFECTED
        E=[]; I=[0]*constants.I0_INFECTED; R=0
        sim = DaySimulation(params, self.pool)
        for _ in range(constants.DAYS):
            S,E,I,R,_ = sim.execute(S,E,I,R)
            res.curva_S.append(S);    res.curva_E.append(len(E))
            res.curva_I.append(len(I)); res.curva_R.append(R)
        res.finalizar()
        return res, params.base_dict()

    def _analisis_sensibilidad(self) -> dict:
        """
        Mide el impacto de cada parámetro sobre el pico de infectados.
 
        Para cada parámetro define 5 niveles de intensidad creciente y corre
        50 simulaciones rápidas por nivel. El rango (máximo - mínimo de picos
        promedio) indica cuánto influye ese parámetro sobre la epidemia.
 
        Retorna:
            dict con claves por parámetro, cada una conteniendo:
                picos     (list) : pico promedio por nivel
                etiquetas (list) : etiqueta del rango de cada nivel
                rango     (float): diferencia entre el nivel más alto y el más bajo
        """
        N_REP = 50
        config = {
            "β (tasa contacto)": [
                (0.10,0.20),(0.20,0.30),(0.30,0.40),(0.40,0.50),(0.50,0.65)],
            "p_trans": [
                (0.10,0.20),(0.25,0.35),(0.40,0.50),(0.55,0.65),(0.75,0.90)],
            "Tasa vacunación": [
                (0.00,0.00),(0.10,0.25),(0.30,0.50),(0.50,0.70),(0.70,0.95)],
        }
        resultados = {}
        for nombre, rangos in config.items():
            picos_niv, etiquetas = [], []
            for vmin, vmax in rangos:
                picos = []
                for i in range(N_REP):
                    ri  = (i+0.5)/N_REP
                    val = vmin+(vmax-vmin)*ri
                    if nombre=="β (tasa contacto)":
                        picos.append(_sim_pico_rapido(self.pool,val,0.5,0.5,0.875))
                    elif nombre=="p_trans":
                        picos.append(_sim_pico_rapido(self.pool,0.4,val,0.5,0.875))
                    else:
                        tv = 0.0 if vmax==0.0 else val
                        picos.append(_sim_pico_rapido(self.pool,0.4,0.5,tv,0.875))
                picos_niv.append(sum(picos)/N_REP)
                etiquetas.append(f"[{vmin:.2f},{vmax:.2f}]")
            resultados[nombre] = {
                "picos":picos_niv, "etiquetas":etiquetas,
                "rango":max(picos_niv)-min(picos_niv),
            }
        return resultados