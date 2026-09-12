"""Manipulação de imagens: espaços de cor e índices de vegetação.

Cobre a etapa "Manipulação das imagens" nomeada pelo enunciado (p.3, item 2.e.ii)
e é onde o problema de desmatamento ganha sua primeira representação útil: o índice
de vegetação, que separa cobertura vegetal de solo exposto muito melhor que o RGB cru.
"""

from __future__ import annotations

import numpy as np

from .nucleo import ErroImagem, validar_imagem

# Coeficientes de luminância da recomendação ITU-R BT.601, os mesmos usados pela
# conversão padrão de vídeo e imagem. O verde pesa mais porque o olho humano é mais
# sensível a ele.
PESOS_LUMINANCIA = (0.299, 0.587, 0.114)


def _exigir_rgb(imagem: np.ndarray) -> np.ndarray:
    imagem = validar_imagem(imagem, bandas_aceitas=(3,))
    if imagem.shape[2] < 3:
        raise ErroImagem(
            f"esperada imagem com ao menos 3 bandas (R, G, B), recebido {imagem.shape[2]}"
        )
    return imagem


def para_cinza(imagem: np.ndarray, pesos: tuple[float, float, float] = PESOS_LUMINANCIA) -> np.ndarray:
    """Converte RGB para tons de cinza por média ponderada das bandas."""
    imagem = _exigir_rgb(imagem)
    peso = np.asarray(pesos, dtype=np.float32)

    if peso.shape != (3,):
        raise ErroImagem(f"pesos devem ser 3 valores, recebido {peso.shape}")

    soma = float(peso.sum())
    if soma <= 0:
        raise ErroImagem("a soma dos pesos deve ser positiva")

    return (imagem[:, :, :3] @ (peso / soma)).astype(np.float32)


def para_hsv(imagem: np.ndarray) -> np.ndarray:
    """Converte RGB em ``[0,1]`` para HSV.

    Devolve ``[H, W, 3]`` com matiz em ``[0,1]`` (equivalente a 0–360°), saturação e
    valor em ``[0,1]``.

    Serve para separar *cor* de *iluminação*: sombra de nuvem e relevo mudam o V sem
    mudar muito o H, então limiarizar sobre matiz é mais estável que sobre RGB.
    """
    imagem = _exigir_rgb(imagem)
    vermelho = imagem[:, :, 0]
    verde = imagem[:, :, 1]
    azul = imagem[:, :, 2]

    valor = np.maximum(np.maximum(vermelho, verde), azul)
    minimo = np.minimum(np.minimum(vermelho, verde), azul)
    amplitude = valor - minimo

    # Cinza puro tem amplitude zero: matiz indefinido, convencionado como 0.
    seguro = np.where(amplitude < 1e-12, 1.0, amplitude)

    matiz = np.zeros_like(valor, dtype=np.float32)
    e_vermelho = (valor == vermelho) & (amplitude >= 1e-12)
    e_verde = (valor == verde) & (amplitude >= 1e-12) & ~e_vermelho
    e_azul = (valor == azul) & (amplitude >= 1e-12) & ~e_vermelho & ~e_verde

    matiz[e_vermelho] = (((verde - azul) / seguro) % 6.0)[e_vermelho]
    matiz[e_verde] = (((azul - vermelho) / seguro) + 2.0)[e_verde]
    matiz[e_azul] = (((vermelho - verde) / seguro) + 4.0)[e_azul]
    matiz = matiz / 6.0

    saturacao = np.where(valor < 1e-12, 0.0, amplitude / np.where(valor < 1e-12, 1.0, valor))

    return np.stack(
        [matiz.astype(np.float32), saturacao.astype(np.float32), valor.astype(np.float32)],
        axis=2,
    )


def _divisao_segura(numerador: np.ndarray, denominador: np.ndarray) -> np.ndarray:
    """Divisão elemento a elemento devolvendo 0 onde o denominador seria zero.

    Índices de vegetação são todos razões, e pixel de água profunda ou de sombra pode
    zerar o denominador. Sem isto o resultado viria com ``nan`` que se propaga
    silenciosamente até a segmentação.
    """
    seguro = np.where(np.abs(denominador) < 1e-10, 1.0, denominador)
    resultado = numerador / seguro
    return np.where(np.abs(denominador) < 1e-10, 0.0, resultado).astype(np.float32)


def ndvi(vermelho: np.ndarray, infravermelho: np.ndarray) -> np.ndarray:
    """Índice de Vegetação por Diferença Normalizada.

    ``NDVI = (NIR - V) / (NIR + V)``, resultado em ``[-1, 1]``.

    Vegetação sadia reflete fortemente no infravermelho próximo e absorve no vermelho
    (clorofila), produzindo NDVI alto — tipicamente acima de 0,4. Solo exposto, que é
    a assinatura do desmatamento, fica próximo de zero; água fica negativa.

    Requer a banda NIR — no Sentinel-2 é a B08. Sem ela, usar ``exg`` ou ``vari``.
    """
    vermelho = validar_imagem(vermelho, bandas_aceitas=(2,))
    infravermelho = validar_imagem(infravermelho, bandas_aceitas=(2,))

    if vermelho.shape != infravermelho.shape:
        raise ErroImagem(
            f"bandas com formatos diferentes: vermelho {vermelho.shape}, "
            f"infravermelho {infravermelho.shape}"
        )

    return _divisao_segura(infravermelho - vermelho, infravermelho + vermelho)


def ndmi(infravermelho: np.ndarray, swir: np.ndarray) -> np.ndarray:
    """Índice de Umidade por Diferença Normalizada.

    ``NDMI = (NIR - SWIR) / (NIR + SWIR)``, resultado em ``[-1, 1]``.

    Mede o conteúdo de água do dossel. Folha viva é opticamente espessa e cheia de água:
    reflete forte no infravermelho próximo e **absorve** no infravermelho de ondas curtas.
    Pastagem seca, solo exposto e cicatriz de queimada têm pouca água e refletem bem no
    SWIR, derrubando o índice.

    Onde ele ganha do NDVI: o NDVI satura em dossel denso — acima de certa biomassa ele
    para de responder — e confunde floresta com pastagem vigorosa, porque as duas são
    verdes. O NDMI continua separando, porque a diferença de água entre um dossel
    florestal e um capim é grande mesmo quando a diferença de verde é pequena.

    Medido neste projeto sobre MODIS/Terra em São Félix do Xingu (2002 × 2024): o NDMI
    elevou a distinguibilidade entre as classes de 2,99 para 3,51 sobre a mesma cena
    (`docs/decisions/005-resolucao-espacial.md`). Não foi suficiente para atingir o
    critério de confiabilidade naquela resolução, mas é a melhor leitura disponível
    quando há banda SWIR.

    Requer a banda SWIR — no Sentinel-2 é a B11 (1610 nm); no MODIS, a banda 7 (2130 nm).
    """
    infravermelho = validar_imagem(infravermelho, bandas_aceitas=(2,))
    swir = validar_imagem(swir, bandas_aceitas=(2,))

    if infravermelho.shape != swir.shape:
        raise ErroImagem(
            f"bandas com formatos diferentes: infravermelho {infravermelho.shape}, "
            f"swir {swir.shape}"
        )

    return _divisao_segura(infravermelho - swir, infravermelho + swir)


def exg(imagem: np.ndarray) -> np.ndarray:
    """Excesso de Verde — ``ExG = 2g - v - a`` sobre as bandas RGB normalizadas.

    Alternativa ao NDVI quando só há bandas visíveis (foto aérea, imagem RGB exportada
    de navegador de satélite). Resultado em ``[-1, 1]``; vegetação fica positiva.

    É mais sensível a variação de iluminação que o NDVI — a normalização por banda
    ajuda, mas não elimina o efeito. Escolha documentada na interface.
    """
    imagem = _exigir_rgb(imagem)
    vermelho = imagem[:, :, 0]
    verde = imagem[:, :, 1]
    azul = imagem[:, :, 2]

    total = vermelho + verde + azul
    v = _divisao_segura(vermelho, total)
    g = _divisao_segura(verde, total)
    a = _divisao_segura(azul, total)

    return (2.0 * g - v - a).astype(np.float32)


def vari(imagem: np.ndarray) -> np.ndarray:
    """Índice de Vegetação Resistente à Atmosfera — ``VARI = (G - V) / (G + V - A)``.

    Também usa só bandas visíveis, mas o termo do azul compensa parte do espalhamento
    atmosférico, o que o torna mais estável que o ExG em cena de satélite com névoa.
    """
    imagem = _exigir_rgb(imagem)
    vermelho = imagem[:, :, 0]
    verde = imagem[:, :, 1]
    azul = imagem[:, :, 2]

    return _divisao_segura(verde - vermelho, verde + vermelho - azul)


def indice_vegetacao(
    imagem: np.ndarray,
    infravermelho: np.ndarray | None = None,
    metodo: str = "auto",
    swir: np.ndarray | None = None,
) -> tuple[np.ndarray, str]:
    """Calcula o índice de vegetação disponível para a imagem dada.

    Com ``metodo="auto"`` usa NDVI se houver banda infravermelha e VARI caso contrário.
    O NDMI **não** entra no automático mesmo quando há SWIR: ele mede água do dossel, não
    verde, e trocar de grandeza sem o usuário pedir mudaria a interpretação do resultado
    sem aviso. Quem quiser NDMI pede ``metodo="ndmi"``.

    Devolve ``(indice, nome_do_metodo_usado)`` — o nome é propagado até a interface para
    que fique explícito qual índice está em uso na demonstração.
    """
    metodos_validos = ("auto", "ndvi", "ndmi", "exg", "vari")
    if metodo not in metodos_validos:
        raise ErroImagem(f"método '{metodo}' desconhecido; use um de {metodos_validos}")

    if metodo == "auto":
        metodo = "ndvi" if infravermelho is not None else "vari"

    if metodo == "ndmi":
        if infravermelho is None or swir is None:
            faltando = []
            if infravermelho is None:
                faltando.append("infravermelho")
            if swir is None:
                faltando.append("SWIR")
            raise ErroImagem(
                f"NDMI requer as bandas {' e '.join(faltando)}. "
                "No MODIS a banda 7 é o SWIR; no Sentinel-2, a B11."
            )
        return ndmi(infravermelho, swir), "ndmi"

    if metodo == "ndvi":
        if infravermelho is None:
            raise ErroImagem(
                "NDVI requer a banda infravermelha (B08 no Sentinel-2). "
                "Sem ela, use metodo='vari' ou metodo='exg'."
            )
        imagem = _exigir_rgb(imagem)
        return ndvi(imagem[:, :, 0], infravermelho), "ndvi"

    if metodo == "exg":
        return exg(imagem), "exg"

    return vari(imagem), "vari"


def para_faixa_unitaria(indice: np.ndarray) -> np.ndarray:
    """Mapeia um índice de ``[-1, 1]`` para ``[0, 1]``.

    Os índices de vegetação são assinados, mas limiarização e morfologia trabalham em
    ``[0, 1]``. A conversão é afim e preserva a ordem, então o limiar encontrado aqui
    corresponde a um limiar do índice original.
    """
    indice = validar_imagem(indice)
    return np.clip((indice + 1.0) / 2.0, 0.0, 1.0).astype(np.float32)
