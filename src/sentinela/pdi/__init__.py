"""Núcleo de processamento digital de imagens, implementado pelo grupo.

A única dependência permitida neste pacote é NumPy. Nenhum filtro pronto de
biblioteca (`cv2`, `skimage`, `scipy.ndimage`, `PIL.ImageFilter`) pode ser usado
aqui — ver `AGENTS.md` §5 e `docs/decisions/001-filtros-proprios.md`.

Organização espelhando as etapas nomeadas pelo enunciado (p.3, item 2.e):

    nucleo       base: convolução, borda, normalização
    cor          Manipulação: espaços de cor, índices de vegetação
    filtros      Filtragem: gaussiano, mediana, Sobel, Laplaciano, nitidez
    limiar       Segmentação: Otsu, adaptativo, histerese
    morfologia   Segmentação: erosão, dilatação, abertura, fechamento
    segmentacao  Segmentação: componentes conexos, análise de regiões
"""

from . import cor, filtros, limiar, morfologia, nucleo, segmentacao
from .nucleo import ErroImagem

__all__ = [
    "ErroImagem",
    "cor",
    "filtros",
    "limiar",
    "morfologia",
    "nucleo",
    "segmentacao",
]
