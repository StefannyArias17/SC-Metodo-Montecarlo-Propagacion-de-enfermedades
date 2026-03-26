from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from app_services.generacion_service import GeneracionService
from app_services.validacion_service import ValidacionService


@dataclass(frozen=True)
class ResultadoCorrida:
    """
    Resultado de una corrida con todas sus validaciones.

    Attributes
    ----------
    corrida : str
        Descripción de la corrida.
    metodo : str
        Nombre del método generador usado.
    semilla : Any
        Semilla o semillas iniciales.
    secuencia : list[float]
        Números pseudoaleatorios generados.
    validaciones : list[tuple[str, bool, str]]
        Resultados de pruebas (nombre, pasó, detalles).
    """
    corrida: str
    metodo: str
    semilla: Any
    secuencia: list[float]
    validaciones: list[tuple[str, bool, str]]


class BibliotecaGeneradorPseudoaleatorio:
    """
    API pública para generar, transformar y validar secuencias pseudoaleatorias.

    Orquesta los servicios de generación y validación para crear un flujo
    completo desde la generación base hasta la validación estadística.

    Attributes
    ----------
    _ESCALA_TRUNCADO : int
        Escala para truncar a 5 decimales (100000).
    """

    _ESCALA_TRUNCADO = 100000

    def __init__(self) -> None:
        """Inicializa los servicios de generación y validación."""
        self._generacion_service = GeneracionService()
        self._validacion_service = ValidacionService()

    @classmethod
    def truncar_ri_5(cls, secuencia: list[float]) -> list[float]:
        """
        Trunca valores a 5 decimales sin redondeo.

        Parameters
        ----------
        secuencia : list[float]
            Valores a truncar.

        Returns
        -------
        list[float]
            Secuencia truncada.
        """
        return [math.trunc(float(ri) * cls._ESCALA_TRUNCADO) / cls._ESCALA_TRUNCADO for ri in secuencia]

    def generar_base(
        self,
        metodo: str,
        semillas: list[int],
        pasos: int,
        corridas: int = 1,
        digitos: int = 8,
        a_mult: int = 1664525,
        m: int = 2**32,
        truncar_ri: bool = True,
    ) -> dict[str, tuple[str, Any, list[float]]]:
        """
        Genera números pseudoaleatorios de base con el método especificado.

        Parameters
        ----------
        metodo : str
            Nombre del generador.
        semillas : list[int]
            Valores iniciales.
        pasos : int
            Cantidad de números a generar.
        corridas : int, optional
            Número de corridas. Por defecto 1.
        digitos : int, optional
            Dígitos para Cuadrados Medios. Por defecto 8.
        a_mult : int, optional
            Parámetro para Congruencial Multiplicativo. Por defecto 1664525.
        m : int, optional
            Módulo. Por defecto 2**32.
        truncar_ri : bool, optional
            Si truncar a 5 decimales. Por defecto True.

        Returns
        -------
        dict[str, tuple[str, Any, list[float]]]
            Diccionario de corridas generadas.
        """
        corridas_base = self._generacion_service.generar_por_metodo(
            metodo=metodo,
            semillas=semillas,
            pasos=pasos,
            corridas=corridas,
            digitos=digitos,
            a_mult=a_mult,
            m=m,
        )

        if not truncar_ri:
            return corridas_base

        corridas_truncadas: dict[str, tuple[str, Any, list[float]]] = {}
        for corrida, (metodo_out, semilla, secuencia) in corridas_base.items():
            corridas_truncadas[corrida] = (
                metodo_out,
                semilla,
                self.truncar_ri_5(secuencia),
            )
        return corridas_truncadas

    def generar_distribuciones(
        self,
        corridas_base: dict[str, tuple[str, Any, list[float]]],
        incluir_uniforme: bool = False,
        incluir_normal: bool = False,
        a: float = 0.0,
        b: float = 1.0,
        mu: float = 0.0,
        sigma: float = 1.0,
        truncar_ri: bool = True,
    ) -> dict[str, tuple[str, Any, list[float]]]:
        """
        Genera distribuciones (uniforme, normal) desde secuencias base.

        Parameters
        ----------
        corridas_base : dict
            Corridas base obtenidas de generar_base().
        incluir_uniforme : bool, optional
            Generar Uniforme(a, b). Por defecto False.
        incluir_normal : bool, optional
            Generar Normal(mu, sigma). Por defecto False.
        a, b : float, optional
            Parámetros uniforme. Por defecto 0, 1.
        mu, sigma : float, optional
            Parámetros normal. Por defecto 0, 1.
        truncar_ri : bool, optional
            Si truncar a 5 decimales. Por defecto True.

        Returns
        -------
        dict[str, tuple[str, Any, list[float]]]
            Diccionario de distribuciones generadas.
        """
        corridas_dist = self._generacion_service.generar_distribuciones_desde_bases(
            corridas_base=corridas_base,
            incluir_uniforme=incluir_uniforme,
            incluir_normal=incluir_normal,
            a=a,
            b=b,
            mu=mu,
            sigma=sigma,
        )

        if not truncar_ri:
            return corridas_dist

        corridas_truncadas: dict[str, tuple[str, Any, list[float]]] = {}
        for corrida, (metodo_out, semilla, secuencia) in corridas_dist.items():
            corridas_truncadas[corrida] = (
                metodo_out,
                semilla,
                self.truncar_ri_5(secuencia),
            )
        return corridas_truncadas

    def validar(
        self,
        secuencia: list[float],
        pruebas_activas: list[str],
        metodo: str | None = None,
        params_dist: dict[str, float] | None = None,
        truncar_ri: bool = True,
    ) -> list[tuple[str, bool, str]]:
        """
        Ejecuta pruebas de validación sobre una secuencia.

        Parameters
        ----------
        secuencia : list[float]
            Números a validar.
        pruebas_activas : list[str]
            Nombres de pruebas a ejecutar.
        metodo : str, optional
            Distribución para transformación.
        params_dist : dict, optional
            Parámetros de distribución.
        truncar_ri : bool, optional
            Si truncar a 5 decimales. Por defecto True.

        Returns
        -------
        list[tuple[str, bool, str]]
            Resultados (prueba, pasó, detalles).
        """
        datos = self.truncar_ri_5(secuencia) if truncar_ri else secuencia
        return self._validacion_service.ejecutar_pruebas(
            datos,
            pruebas_activas,
            metodo=metodo,
            params_dist=params_dist,
        )

    def ejecutar_pipeline(
        self,
        metodos_base: list[str],
        semillas: list[int],
        pasos: int,
        corridas: int,
        pruebas_activas: list[str],
        incluir_uniforme: bool = False,
        incluir_normal: bool = False,
        a: float = 0.0,
        b: float = 1.0,
        mu: float = 0.0,
        sigma: float = 1.0,
        digitos: int = 8,
        a_mult: int = 1664525,
        m: int = 2**32,
        truncar_ri: bool = True,
    ) -> list[ResultadoCorrida]:
        """
        Ejecuta el flujo completo: genera, transforma y valida secuencias.

        Parameters
        ----------
        metodos_base : list[str]
            Métodos generadores a usar.
        semillas : list[int]
            Semillas iniciales.
        pasos : int
            Números a generar por corrida.
        corridas : int
            Número de corridas.
        pruebas_activas : list[str]
            Pruebas a ejecutar.
        incluir_uniforme, incluir_normal : bool, optional
            Generar distribuciones. Por defecto False.
        a, b, mu, sigma : float, optional
            Parámetros de distribuciones.
        digitos, a_mult, m : int, optional
            Parámetros de generación.
        truncar_ri : bool, optional
            Si truncar a 5 decimales. Por defecto True.

        Returns
        -------
        list[ResultadoCorrida]
            Resultados completos de todas las corridas.
        """
        if not metodos_base and not (incluir_uniforme or incluir_normal):
            raise ValueError("Debes seleccionar al menos un método base o una distribución.")

        corridas_totales: dict[str, tuple[str, Any, list[float]]] = {}

        for metodo in metodos_base:
            corridas_metodo = self.generar_base(
                metodo=metodo,
                semillas=semillas,
                pasos=pasos,
                corridas=corridas,
                digitos=digitos,
                a_mult=a_mult,
                m=m,
                truncar_ri=truncar_ri,
            )
            corridas_totales.update(corridas_metodo)

        if incluir_uniforme or incluir_normal:
            corridas_distribucion = self.generar_distribuciones(
                corridas_base=corridas_totales,
                incluir_uniforme=incluir_uniforme,
                incluir_normal=incluir_normal,
                a=a,
                b=b,
                mu=mu,
                sigma=sigma,
                truncar_ri=truncar_ri,
            )
            corridas_totales.update(corridas_distribucion)

        params_dist = {"a": a, "b": b, "mu": mu, "sigma": sigma}
        resultados: list[ResultadoCorrida] = []

        for corrida, (metodo, semilla, secuencia) in corridas_totales.items():
            validaciones = self.validar(
                secuencia=secuencia,
                pruebas_activas=pruebas_activas,
                metodo=metodo,
                params_dist=params_dist,
                truncar_ri=truncar_ri,
            )
            resultados.append(
                ResultadoCorrida(
                    corrida=corrida,
                    metodo=metodo,
                    semilla=semilla,
                    secuencia=secuencia,
                    validaciones=validaciones,
                )
            )

        return resultados
