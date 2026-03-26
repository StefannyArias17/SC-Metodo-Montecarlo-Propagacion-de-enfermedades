from generador_numeros.cuadrados_medios import GeneradorCuadradosMedios
from generador_numeros.congruencia_lineal import GeneradorCongruenciaLineal
from generador_numeros.congruencial_multiplicativo import GeneradorCongruencialMultiplicativo
from generador_numeros.congruencial_aditivo import GeneradorCongruencialAditivo
from distribuciones.uniforme import GeneradorDistribucionUniforme
from distribuciones.normal import GeneradorDistribucionNormal


class GeneracionService:
    """
    Servicio para generar números pseudoaleatorios y sus distribuciones.

    Proporciona métodos estáticos para instanciar diferentes generadores
    según el método solicitado, ejecutar múltiples corridas y generar
    distribuciones univariadas (uniforme y normal) desde secuencias base.

    Notes
    -----
    - Todos los métodos son estáticos, no requiere instanciación.
    - Soporta métodos: Cuadrados Medios, Congruencia Lineal,
      Congruencial Multiplicativo y Congruencial Aditivo.
    - Cada corrida se registra con un clave única que contiene metainformación.
    """

    @staticmethod
    def generar_por_metodo(metodo, semillas, pasos, corridas=1, digitos=8, a_mult=1664525, m=2**32):
        """
        Genera números pseudoaleatorios utilizando el método y parámetros especificados.

        Crea múltiples corridas de una secuencia pseudoaleatoria según el método
        seleccionado. Cada corrida se almacena con metainformación única.

        Parameters
        ----------
        metodo : str
            Nombre del método generador. Valores válidos:
            'Cuadrados Medios', 'Congruencia Lineal',
            'Congruencial Multiplicativo', 'Congruencial Aditivo'.
        semillas : list[int]
            Lista de semillas iniciales. Congruencial Aditivo requiere >= 2.
        pasos : int
            Cantidad de números pseudoaleatorios a generar por corrida.
        corridas : int, optional
            Número de corridas independientes. Por defecto 1.
        digitos : int, optional
            Dígitos para Cuadrados Medios. Por defecto 8.
        a_mult : int, optional
            Parámetro 'a' para Congruencial Multiplicativo. Por defecto 1664525.
        m : int, optional
            Módulo para generadores congruenciales. Por defecto 2**32.

        Returns
        -------
        dict[str, tuple]
            Diccionario donde cada clave es una descripción de la corrida
            (metodo | corrida=X | semilla=Y) y cada valor es una tupla
            (nombre_metodo, semilla_usada, secuencia_generada).

        Raises
        ------
        ValueError
            Si el método es 'Congruencial Aditivo' y hay menos de 2 semillas.
        """
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
        """
        Genera distribuciones univariadas desde secuencias pseudoaleatorias base.

        Transforma secuencias base U(0,1) a distribuciones uniforme y/o normal
        usando los parámetros especificados.

        Parameters
        ----------
        corridas_base : dict[str, tuple]
            Diccionario de corridas base obtenido de generar_por_metodo().
            Cada valor contiene (metodo, semilla, secuencia).
        incluir_uniforme : bool, optional
            Si True, genera distribución Uniforme(a, b). Por defecto False.
        incluir_normal : bool, optional
            Si True, genera distribución Normal(mu, sigma). Por defecto False.
        a : float, optional
            Límite inferior para distribución uniforme. Por defecto 0.0.
        b : float, optional
            Límite superior para distribución uniforme. Por defecto 1.0.
        mu : float, optional
            Media para distribución normal. Por defecto 0.0.
        sigma : float, optional
            Desviación estándar para distribución normal. Por defecto 1.0.

        Returns
        -------
        dict[str, tuple]
            Diccionario con distribuciones generadas. Cada clave describe
            la distribución y su base, cada valor es tupla
            (nombre_distribucion, semilla_base, secuencia_transformada).

        Raises
        ------
        ValueError
            Si a >= b para distribución uniforme.
            Si sigma <= 0 para distribución normal.
        """
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
