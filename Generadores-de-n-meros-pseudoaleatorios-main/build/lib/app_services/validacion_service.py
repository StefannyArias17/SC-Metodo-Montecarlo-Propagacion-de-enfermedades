from validadores.prueba_chi_cuadrado import PruebaChiCuadrado
from validadores.prueba_kolmogorov_smirnov import PruebaKolmogorovSmirnov
from validadores.prueba_medias import PruebaMedias
from validadores.prueba_varianza import PruebaVarianza
from validadores.prueba_poker import PruebaPoker
from validadores.prueba_rachas import PruebaRachas
from statistics import NormalDist
import io
from contextlib import redirect_stdout


class ValidacionService:
    _NORMAL_STD = NormalDist(mu=0.0, sigma=1.0)
    _ESCALA_TRUNCADO = 100000

    @staticmethod
    def _transformar_para_validacion(seq, metodo=None, params_dist=None):
        """Transforma secuencias de distribuciones a U(0,1) para validar con pruebas actuales."""
        if metodo == "Distribucion Uniforme":
            if not params_dist:
                return seq
            a = float(params_dist.get("a", 0.0))
            b = float(params_dist.get("b", 1.0))
            if a >= b:
                raise ValueError("Para validar distribución uniforme debe cumplirse a < b.")
            amplitud = b - a
            return [min(max((float(x) - a) / amplitud, 0.0), 1.0 - 1e-12) for x in seq]

        if metodo == "Distribucion Normal":
            if not params_dist:
                return seq
            mu = float(params_dist.get("mu", 0.0))
            sigma = float(params_dist.get("sigma", 1.0))
            if sigma <= 0:
                raise ValueError("Para validar distribución normal, sigma debe ser mayor que 0.")
            return [
                min(max(ValidacionService._NORMAL_STD.cdf((float(x) - mu) / sigma), 1e-12), 1.0 - 1e-12)
                for x in seq
            ]

        return seq

    @staticmethod
    def _truncar_a_5_decimales(seq):
        """Trunca cada valor a 5 decimales sin redondeo."""
        escala = ValidacionService._ESCALA_TRUNCADO
        return [int(float(x) * escala) / escala for x in seq]

    @staticmethod
    def _compactar_salida(texto):
        """Convierte la salida multilinea de consola en una linea util para tabla/csv."""
        if not texto:
            return ""
        lineas = []
        for line in texto.splitlines():
            linea = line.strip()
            if not linea:
                continue

            if linea.lower().startswith("resultado:"):
                continue
            if linea.lower().startswith("prueba "):
                continue

            lineas.append(linea)

        return " | ".join(lineas)

    @staticmethod
    def _ejecutar_y_capturar(funcion):
        """Ejecuta una prueba capturando su salida impresa y retornando (ok, detalle)."""
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            ok = funcion()
        salida = buffer.getvalue().strip()

        # Mantener visibilidad en consola como hasta ahora.
        if salida:
            print(salida)

        return ok, ValidacionService._compactar_salida(salida)

    @staticmethod
    def ejecutar_pruebas(seq, pruebas_activas, metodo=None, params_dist=None):
        seq_validacion = ValidacionService._transformar_para_validacion(
            seq, metodo=metodo, params_dist=params_dist
        )
        seq_validacion = ValidacionService._truncar_a_5_decimales(seq_validacion)
        resultados = []

        for prueba in pruebas_activas:
            try:
                if prueba == "Chi Cuadrado":
                    k = max(10, min(100, len(seq_validacion) // 5))
                    ok, detalle = ValidacionService._ejecutar_y_capturar(
                        lambda: PruebaChiCuadrado().prueba_chi_cuadrado(seq_validacion, k=k)
                    )
                    detalle_final = f"k={k}"
                    if detalle:
                        detalle_final = f"{detalle_final} | {detalle}"
                    resultados.append((prueba, ok, detalle_final))
                elif prueba == "Kolmogorov Smirnov":
                    ok, detalle = ValidacionService._ejecutar_y_capturar(
                        lambda: PruebaKolmogorovSmirnov().prueba_kolmogorov_smirnov(seq_validacion)
                    )
                    detalle_final = "alpha=0.05"
                    if detalle:
                        detalle_final = f"{detalle_final} | {detalle}"
                    resultados.append((prueba, ok, detalle_final))
                elif prueba == "Medias":
                    ok, detalle = ValidacionService._ejecutar_y_capturar(
                        lambda: PruebaMedias().prueba_medias(seq_validacion)
                    )
                    detalle_final = "alpha=0.05"
                    if detalle:
                        detalle_final = f"{detalle_final} | {detalle}"
                    resultados.append((prueba, ok, detalle_final))
                elif prueba == "Varianza":
                    ok, detalle = ValidacionService._ejecutar_y_capturar(
                        lambda: PruebaVarianza().prueba_varianza(seq_validacion)
                    )
                    detalle_final = "alpha=0.05"
                    if detalle:
                        detalle_final = f"{detalle_final} | {detalle}"
                    resultados.append((prueba, ok, detalle_final))
                elif prueba == "Poker":
                    ok, detalle = ValidacionService._ejecutar_y_capturar(
                        lambda: PruebaPoker().prueba_poker(seq_validacion)
                    )
                    detalle_final = "5 digitos"
                    if detalle:
                        detalle_final = f"{detalle_final} | {detalle}"
                    resultados.append((prueba, ok, detalle_final))
                elif prueba == "Rachas":
                    ok, detalle = ValidacionService._ejecutar_y_capturar(
                        lambda: PruebaRachas().prueba_rachas(seq_validacion)
                    )
                    detalle_final = "mediana=0.5"
                    if detalle:
                        detalle_final = f"{detalle_final} | {detalle}"
                    resultados.append((prueba, ok, detalle_final))
            except Exception as e:
                resultados.append((prueba, False, f"Error: {e}"))

        return resultados
