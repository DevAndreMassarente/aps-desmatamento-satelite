"""Orquestração das etapas — encadeia ``pdi/`` sem implementar algoritmo próprio.

Ver `docs/ARCHITECTURE.md` para o fluxo completo.
"""

from .amostras import (
    DESMATADO,
    INTACTO,
    ConjuntoDeAmostras,
    equilibrar,
    extrair_amostras,
)
from .deteccao import ResultadoDeteccao, detectar_desmatamento, preparar_indice

__all__ = [
    "ConjuntoDeAmostras",
    "DESMATADO",
    "INTACTO",
    "ResultadoDeteccao",
    "detectar_desmatamento",
    "equilibrar",
    "extrair_amostras",
    "preparar_indice",
]
