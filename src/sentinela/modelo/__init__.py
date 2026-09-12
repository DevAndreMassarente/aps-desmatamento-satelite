"""Etapa de modelo — item 3.b do enunciado.

Consome o conjunto rotulado de ``pipeline.extrair_amostras``. As features saem do núcleo
de PDI do grupo; o algoritmo de aprendizado vem do scikit-learn, que é permitido aqui.
"""

from .caracteristicas import (
    NOMES_DAS_FEATURES,
    descrever_recorte,
    extrair_caracteristicas,
)
from .classificador import (
    Avaliacao,
    ClassificadorDesmatamento,
    ErroModelo,
    dividir_espacialmente,
    treinar_e_avaliar,
)

__all__ = [
    "Avaliacao",
    "ClassificadorDesmatamento",
    "ErroModelo",
    "NOMES_DAS_FEATURES",
    "descrever_recorte",
    "dividir_espacialmente",
    "extrair_caracteristicas",
    "treinar_e_avaliar",
]
