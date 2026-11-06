"""Composição visual dos resultados — o que a banca vê na tela.

Só montagem de cor para apresentação. Nenhuma decisão de detecção acontece aqui: as
máscaras chegam prontas de ``pdi`` e ``pipeline``. Mantido fora de ``pdi/`` porque
sobreposição colorida é apresentação, não processamento.

O contorno das regiões usa o gradiente morfológico do próprio grupo
(``pdi.morfologia``), não uma função de desenho de biblioteca.
"""

from __future__ import annotations

import numpy as np

from ..pdi.cor import para_cinza
from ..pdi.morfologia import gradiente_morfologico
from ..pdi.nucleo import validar_imagem

# Vermelho para perda, verde para ganho: convenção dos boletins de desmatamento
# (PRODES/DETER do INPE), para que a leitura seja imediata na apresentação.
COR_PERDA = (0.90, 0.16, 0.16)
COR_GANHO = (0.18, 0.70, 0.30)
COR_ESTAVEL_VEGETADO = (0.10, 0.30, 0.12)
COR_ESTAVEL_EXPOSTO = (0.62, 0.58, 0.50)


def _como_rgb(imagem: np.ndarray) -> np.ndarray:
    """Promove uma imagem em tons de cinza para três bandas iguais."""
    imagem = validar_imagem(imagem)
    if imagem.ndim == 2:
        return np.repeat(imagem[:, :, None], 3, axis=2)
    return imagem


def sobrepor_mascara(
    base: np.ndarray,
    mascara: np.ndarray,
    cor: tuple[float, float, float] = COR_PERDA,
    intensidade: float = 0.55,
) -> np.ndarray:
    """Pinta a máscara sobre a imagem base, com transparência.

    A base é dessaturada antes da mistura: sobre uma cena de floresta, que já é
    verde-escura, uma sobreposição vermelha translúcida sem dessaturar fica marrom e
    perde legibilidade justamente na área que importa mostrar.
    """
    base = _como_rgb(base)
    mascara = np.asarray(mascara)

    if mascara.shape != base.shape[:2]:
        raise ValueError(
            f"máscara {mascara.shape} não corresponde à imagem {base.shape[:2]}"
        )
    if not 0.0 <= intensidade <= 1.0:
        raise ValueError(f"intensidade deve estar em [0, 1], recebido {intensidade}")

    fundo = np.repeat(para_cinza(base)[:, :, None], 3, axis=2)
    fundo = 0.45 * fundo + 0.55 * base

    tinta = np.array(cor, dtype=np.float32).reshape(1, 1, 3)
    seletor = (mascara > 0.5)[:, :, None].astype(np.float32) * intensidade

    return np.clip(fundo * (1 - seletor) + tinta * seletor, 0, 1).astype(np.float32)


def contornar_mascara(
    base: np.ndarray, mascara: np.ndarray, cor: tuple[float, float, float] = COR_PERDA
) -> np.ndarray:
    """Desenha apenas a borda das regiões, deixando o interior visível.

    Útil quando é preciso mostrar **o que havia** dentro da área detectada — numa
    sobreposição sólida o terreno some debaixo da tinta.
    """
    borda = gradiente_morfologico(np.asarray(mascara) > 0.5)
    return sobrepor_mascara(base, borda, cor=cor, intensidade=1.0)


def mapa_de_mudanca(mudanca: dict[str, np.ndarray]) -> np.ndarray:
    """Converte as quatro classes de ``mudanca_entre_mascaras`` em um mapa colorido.

    Vermelho = perda de vegetação (desmatamento), verde = ganho, verde-escuro =
    vegetação estável, cinza = solo exposto nas duas datas.
    """
    exigidas = ("perda", "ganho", "estavel_vegetado", "estavel_nao_vegetado")
    faltando = [chave for chave in exigidas if chave not in mudanca]
    if faltando:
        raise ValueError(f"faltam as classes {faltando} no dicionário de mudança")

    altura, largura = mudanca["perda"].shape
    mapa = np.zeros((altura, largura, 3), dtype=np.float32)

    for chave, cor in (
        ("estavel_nao_vegetado", COR_ESTAVEL_EXPOSTO),
        ("estavel_vegetado", COR_ESTAVEL_VEGETADO),
        ("ganho", COR_GANHO),
        ("perda", COR_PERDA),
    ):
        mapa[mudanca[chave] > 0.5] = cor

    return mapa


def indice_em_falsa_cor(indice: np.ndarray) -> np.ndarray:
    """Colore um índice de vegetação em ``[0, 1]``: marrom (baixo) a verde (alto).

    Rampa linear de três pontos, calculada à mão — não é mapa de cores de biblioteca.
    Serve para que a diferença entre floresta e solo exposto seja visível na tela sem
    depender de o observador interpretar tons de cinza.
    """
    indice = np.clip(validar_imagem(indice), 0, 1)
    if indice.ndim != 2:
        raise ValueError(f"índice deve ser 2D, recebido {indice.shape}")

    baixo = np.array([0.45, 0.32, 0.18], dtype=np.float32)
    meio = np.array([0.85, 0.80, 0.45], dtype=np.float32)
    alto = np.array([0.08, 0.42, 0.15], dtype=np.float32)

    peso = indice[:, :, None]
    primeira_metade = baixo + (meio - baixo) * (peso / 0.5)
    segunda_metade = meio + (alto - meio) * ((peso - 0.5) / 0.5)

    return np.where(peso < 0.5, primeira_metade, segunda_metade).astype(np.float32)


def realcar_par(antes: np.ndarray, depois: np.ndarray, *, percentis=(1.0, 99.0)):
    """Estica o brilho das duas datas com a mesma régua, só para visualização.

    Imagens de refletância ficam escuras na tela. Os percentis são calculados sobre as duas
    datas juntas, para que a diferença de brilho entre elas continue visível. O resultado
    não volta para o processamento.
    """
    antes, depois = validar_imagem(antes), validar_imagem(depois)
    baixo, alto = np.percentile(np.concatenate([antes.ravel(), depois.ravel()]), percentis)
    escala = max(float(alto - baixo), 1e-6)
    ajustar = lambda imagem: np.clip((imagem - baixo) / escala, 0.0, 1.0).astype(np.float32)
    return ajustar(antes), ajustar(depois)
