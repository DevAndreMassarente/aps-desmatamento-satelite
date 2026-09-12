"""Aquisição e persistência — etapa 1 das cinco nomeadas pelo enunciado (p.3, 2.e.i).

Fronteira entre o disco e o núcleo de PDI. É o único pacote autorizado a usar Pillow
e rasterio; ``pdi/`` continua trabalhando só com NumPy.
"""

from .geo import RASTERIO_DISPONIVEL, metros_por_pixel, resolucao_do_satelite
from .imagem import ErroArquivo, carregar, carregar_par, salvar
from .sintetico import cena_sintetica, par_bitemporal
from .visual import (
    contornar_mascara,
    indice_em_falsa_cor,
    mapa_de_mudanca,
    sobrepor_mascara,
)

__all__ = [
    "ErroArquivo",
    "RASTERIO_DISPONIVEL",
    "carregar",
    "carregar_par",
    "cena_sintetica",
    "contornar_mascara",
    "indice_em_falsa_cor",
    "mapa_de_mudanca",
    "metros_por_pixel",
    "par_bitemporal",
    "resolucao_do_satelite",
    "salvar",
    "sobrepor_mascara",
]
