import math
import time
import constants
from pseudorandom_adapter          import generar_pool_global, validar_generador, graficar_validacion
from score               import SimulationResult, ScenarioResults
from contagion_conversion import (DailyContactsConverter,
                                  UnvaccinatedTransmissionConverter,
                                  VaccinatedTransmissionConverter,
                                  crear_conversor_transmision)

class PoolGlobal:

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
        if self._idx >= len(self._pool):
            self._ciclo  += 1
            s_nueva       = self.semilla_maestra + self._ciclo * 1_000_003
            self.matriz_sx["ciclos"].append({
                "ciclo": self._ciclo, "semilla": s_nueva,
                "consumo_antes": self._consumo_total,
            })
            # Recarga silenciosa — el evento queda en la Matriz s,x
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


class SimParams:

    def __init__(self, pool: PoolGlobal, con_vacunacion: bool = True,
                 params_base: dict = None):
        p = constants
        if params_base is None:
            self.beta      = p.BETA_MIN    + (p.BETA_MAX    - p.BETA_MIN)    * pool.siguiente()
            self.sigma_inv = p.SIGMA_INV_MIN+(p.SIGMA_INV_MAX-p.SIGMA_INV_MIN)*pool.siguiente()
            self.gamma_inv = p.GAMMA_INV_MIN+(p.GAMMA_INV_MAX-p.GAMMA_INV_MIN)*pool.siguiente()
            self.p_base    = p.P_TRANS_MIN + (p.P_TRANS_MAX  - p.P_TRANS_MIN) * pool.siguiente()
        else:
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
        self.periodo_incub = max(1, round(self.sigma_inv))
        self.periodo_infec = max(1, round(self.gamma_inv))

        # Conversores de la Matriz S (contagion_conversion.py)
        self.contactos_conv = DailyContactsConverter(self.beta, p.C_MAX)
        self.trans_conv     = crear_conversor_transmision(
            self.p_base, con_vacunacion, self.tasa_vac, self.efec_vac
        )

    def base_dict(self) -> dict:
        return {"beta": self.beta, "sigma_inv": self.sigma_inv,
                "gamma_inv": self.gamma_inv, "p_base": self.p_base}

    def to_dict(self) -> dict:
        d = self.base_dict()
        d.update({"tasa_vac": self.tasa_vac, "efec_vac": self.efec_vac,
                  "factor_vac": self.factor_vac, "p_efectiva": self.p_efectiva})
        return d

class DaySimulation:
    def __init__(self, params: SimParams, pool: PoolGlobal):
        self.params = params
        self.pool   = pool

    def execute(self, S, E_cola, I_cola, R):
        nuevos_E = 0
        for _ in I_cola:
            if S <= 0:
                break
            nc = self.params.contactos_conv.evaluate(self.pool.siguiente())
            for _ in range(nc):
                if S <= 0:
                    break
                ri_s = self.pool.siguiente()
                _idx = int(ri_s * S)
                if self.params.trans_conv.evaluate(self.pool.siguiente()):
                    S -= 1; nuevos_E += 1

        E_nueva  = []; nuevos_I = 0
        for d in E_cola:
            d += 1
            if d >= self.params.periodo_incub: nuevos_I += 1
            else: E_nueva.append(d)
        E_nueva.extend([0] * nuevos_E)

        I_nueva  = []; nuevos_R = 0
        for d in I_cola:
            d += 1
            if d >= self.params.periodo_infec: nuevos_R += 1
            else: I_nueva.append(d)
        I_nueva.extend([0] * nuevos_I)

        return S, E_nueva, I_nueva, R + nuevos_R, nuevos_E

def _sim_pico_rapido(pool: PoolGlobal, beta, p_base, tasa_vac, efec_vac) -> int:
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


class EpiSim:

    def __init__(self):
        self.pool = None
        self.sin_vacunacion = ScenarioResults("Sin Vacunación")
        self.con_vacunacion = ScenarioResults("Con Vacunación")
        self.sensibilidad   = {}
        self.tiempo_total_s = 0.0

    def execute(self):
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

            # CON vacuna: reutiliza mismos parámetros base → solo varía factor_vac
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
        """5 niveles por parámetro, 50 reps cada uno. Corrección #6."""
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