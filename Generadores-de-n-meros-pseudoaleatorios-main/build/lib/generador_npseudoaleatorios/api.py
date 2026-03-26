from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from app_services.generacion_service import GeneracionService
from app_services.validacion_service import ValidacionService


@dataclass(frozen=True)
class ResultadoCorrida:
    corrida: str
    metodo: str
    semilla: Any
    secuencia: list[float]
    validaciones: list[tuple[str, bool, str]]


class BibliotecaGeneradorPseudoaleatorio:
    """API publica para generar, transformar y validar secuencias pseudoaleatorias."""

    _ESCALA_TRUNCADO = 100000

    def __init__(self) -> None:
        self._generacion_service = GeneracionService()
        self._validacion_service = ValidacionService()

    @classmethod
    def truncar_ri_5(cls, secuencia: list[float]) -> list[float]:
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
        if not metodos_base and not (incluir_uniforme or incluir_normal):
            raise ValueError("Debes seleccionar al menos un metodo base o una distribucion.")

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
