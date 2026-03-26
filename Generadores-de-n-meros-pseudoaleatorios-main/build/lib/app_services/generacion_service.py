from generador_numeros.cuadrados_medios import GeneradorCuadradosMedios
from generador_numeros.congruencia_lineal import GeneradorCongruenciaLineal
from generador_numeros.congruencial_multiplicativo import GeneradorCongruencialMultiplicativo
from generador_numeros.congruencial_aditivo import GeneradorCongruencialAditivo
from distribuciones.uniforme import GeneradorDistribucionUniforme
from distribuciones.normal import GeneradorDistribucionNormal


class GeneracionService:
    @staticmethod
    def generar_por_metodo(metodo, semillas, pasos, corridas=1, digitos=8, a_mult=1664525, m=2**32):
        corridas_generadas = {}

        if metodo == "Cuadrados Medios":
            for s in semillas:
                for i in range(corridas):
                    semilla_i = s + i
                    gen = GeneradorCuadradosMedios(semilla=semilla_i, digitos=digitos)
                    seq = gen.siguiente_Ri_Cuadrados_Medios(pasos)
                    key = f"{metodo} | corrida={i + 1} | semilla={semilla_i}"
                    corridas_generadas[key] = (metodo, semilla_i, seq)

        elif metodo == "Congruencia Lineal":
            for s in semillas:
                for i in range(corridas):
                    semilla_i = s + i
                    gen = GeneradorCongruenciaLineal(semilla=semilla_i)
                    seq = gen.siguiente_Ri_Congruencia_Lineal(pasos)
                    key = f"{metodo} | corrida={i + 1} | semilla={semilla_i}"
                    corridas_generadas[key] = (metodo, semilla_i, seq)

        elif metodo == "Congruencial Multiplicativo":
            for s in semillas:
                for i in range(corridas):
                    semilla_i = s + i
                    gen = GeneradorCongruencialMultiplicativo(
                        semilla=semilla_i,
                        a=a_mult,
                        m=m,
                    )
                    seq = gen.siguiente_Ri_Congruencial_Multiplicativo(pasos)
                    key = f"{metodo} | corrida={i + 1} | semilla={semilla_i}"
                    corridas_generadas[key] = (metodo, semilla_i, seq)

        elif metodo == "Congruencial Aditivo":
            if len(semillas) < 2:
                raise ValueError("Congruencial aditivo requiere al menos 2 semillas.")
            for i in range(corridas):
                semillas_i = [s + i for s in semillas]
                gen = GeneradorCongruencialAditivo(semillas_iniciales=semillas_i, m=m)
                seq = gen.siguiente_Ri_Congruencial_Aditivo(pasos)
                key = f"{metodo} | corrida={i + 1} | semillas={semillas_i}"
                corridas_generadas[key] = (metodo, f"lista+{i}", seq)

        return corridas_generadas

    @staticmethod
    def generar_distribuciones_desde_bases(
        corridas_base,
        incluir_uniforme=False,
        incluir_normal=False,
        a=0.0,
        b=1.0,
        mu=0.0,
        sigma=1.0,
    ):
        corridas_distribucion = {}

        if not (incluir_uniforme or incluir_normal):
            return corridas_distribucion

        if incluir_uniforme and a >= b:
            raise ValueError("Para distribucion uniforme debe cumplirse a < b.")
        if incluir_normal and sigma <= 0:
            raise ValueError("Para distribucion normal, sigma debe ser mayor que 0.")

        for key_base, (_, semilla_base, seq_base) in corridas_base.items():
            if incluir_uniforme:
                gen_u = GeneradorDistribucionUniforme(a=a, b=b)
                seq_u = gen_u.generar(seq_base)
                key_u = f"Distribucion Uniforme | base=({key_base})"
                corridas_distribucion[key_u] = (
                    "Distribucion Uniforme",
                    semilla_base,
                    seq_u,
                )

            if incluir_normal:
                epsilon = 1e-12
                seq_ajustada = [
                    min(max(float(u), epsilon), 1.0 - epsilon) for u in seq_base
                ]
                gen_n = GeneradorDistribucionNormal(mu=mu, sigma=sigma)
                seq_n = gen_n.generar(seq_ajustada)[: len(seq_base)]
                key_n = f"Distribucion Normal | base=({key_base})"
                corridas_distribucion[key_n] = (
                    "Distribucion Normal",
                    semilla_base,
                    seq_n,
                )

        return corridas_distribucion
