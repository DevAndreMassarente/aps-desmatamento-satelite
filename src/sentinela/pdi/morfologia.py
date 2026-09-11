"""Operadores morfológicos sobre máscaras binárias.

Completa a etapa "Segmentação" do enunciado (p.3, item 2.e.iv).

Depois da limiarização a máscara vem suja: pixels isolados que passaram por ruído,
buracos dentro de áreas que deveriam ser sólidas, bordas irregulares. A morfologia
limpa isso raciocinando sobre **forma**, não sobre intensidade.

O elemento estruturante é a "régua": a forma que se tenta encaixar na máscara.
"""

from __future__ import annotations

import numpy as np

from .nucleo import ErroImagem, janela_deslizante


def _validar_mascara(mascara: np.ndarray) -> np.ndarray:
    if not isinstance(mascara, np.ndarray):
        raise ErroImagem(f"esperado numpy.ndarray, recebido {type(mascara).__name__}")
    if mascara.ndim != 2:
        raise ErroImagem(f"máscara deve ser 2D, recebido formato {mascara.shape}")
    if mascara.size == 0:
        raise ErroImagem("máscara vazia")
    return mascara.astype(np.float32)


def elemento_quadrado(tamanho: int = 3) -> np.ndarray:
    """Elemento estruturante quadrado (conectividade 8)."""
    if tamanho < 1 or tamanho % 2 == 0:
        raise ErroImagem(f"tamanho deve ser ímpar e positivo, recebido {tamanho}")
    return np.ones((tamanho, tamanho), dtype=bool)


def elemento_cruz(tamanho: int = 3) -> np.ndarray:
    """Elemento estruturante em cruz (conectividade 4).

    Menos agressivo que o quadrado: preserva melhor cantos e estruturas diagonais finas,
    como estradas vicinais.
    """
    if tamanho < 1 or tamanho % 2 == 0:
        raise ErroImagem(f"tamanho deve ser ímpar e positivo, recebido {tamanho}")
    elemento = np.zeros((tamanho, tamanho), dtype=bool)
    meio = tamanho // 2
    elemento[meio, :] = True
    elemento[:, meio] = True
    return elemento


def elemento_disco(raio: int = 2) -> np.ndarray:
    """Elemento estruturante circular — erode/dilata igualmente em todas as direções."""
    if raio < 1:
        raise ErroImagem(f"raio deve ser positivo, recebido {raio}")
    eixo = np.arange(-raio, raio + 1)
    x, y = np.meshgrid(eixo, eixo)
    return (x**2 + y**2) <= raio**2


def _aplicar(mascara: np.ndarray, elemento: np.ndarray, operacao: str) -> np.ndarray:
    """Núcleo compartilhado de erosão e dilatação.

    Ambas são estatísticas de ordem sobre a vizinhança definida pelo elemento
    estruturante: erosão é o mínimo, dilatação é o máximo. Escrever as duas a partir
    daqui evita duplicar o tratamento de borda e o mapeamento do elemento.
    """
    mascara = _validar_mascara(mascara)
    elemento = np.asarray(elemento, dtype=bool)

    if elemento.ndim != 2:
        raise ErroImagem(f"elemento estruturante deve ser 2D, recebido {elemento.shape}")
    if elemento.shape[0] % 2 == 0 or elemento.shape[1] % 2 == 0:
        raise ErroImagem(
            f"elemento estruturante deve ter dimensões ímpares, recebido {elemento.shape}"
        )
    if elemento.shape[0] != elemento.shape[1]:
        raise ErroImagem(
            f"elemento estruturante deve ser quadrado, recebido {elemento.shape}"
        )
    if not elemento.any():
        raise ErroImagem("elemento estruturante não pode ser todo falso")

    tamanho = elemento.shape[0]

    # Erosão precisa que os pixels fora da imagem não derrubem o mínimo, e a dilatação
    # que não inflem o máximo; replicar a borda satisfaz os dois casos.
    janelas = janela_deslizante(mascara, tamanho, modo_borda="replica")

    ativos = elemento.reshape(-1)
    janelas = janelas[ativos]

    resultado = janelas.min(axis=0) if operacao == "erosao" else janelas.max(axis=0)
    return resultado > 0.5


def erosao(mascara: np.ndarray, elemento: np.ndarray | None = None) -> np.ndarray:
    """Erosão: mantém o pixel apenas se o elemento couber inteiro dentro da região.

    Encolhe as regiões e **elimina** as menores que o elemento estruturante — é assim
    que respingos isolados somem.
    """
    if elemento is None:
        elemento = elemento_quadrado(3)
    return _aplicar(mascara, elemento, "erosao")


def dilatacao(mascara: np.ndarray, elemento: np.ndarray | None = None) -> np.ndarray:
    """Dilatação: marca o pixel se o elemento tocar a região em alguma posição.

    Expande as regiões e **funde** as próximas, fechando pequenas falhas.
    """
    if elemento is None:
        elemento = elemento_quadrado(3)
    return _aplicar(mascara, elemento, "dilatacao")


def abertura(mascara: np.ndarray, elemento: np.ndarray | None = None) -> np.ndarray:
    """Abertura = erosão seguida de dilatação.

    Remove ruído isolado **preservando o tamanho** das regiões que sobreviveram: a
    erosão elimina o que é pequeno demais, a dilatação devolve as sobreviventes ao
    tamanho aproximado original.

    Na máscara de desmatamento, apaga pixels espúrios de solo exposto dentro da floresta.
    """
    return dilatacao(erosao(mascara, elemento), elemento)


def fechamento(mascara: np.ndarray, elemento: np.ndarray | None = None) -> np.ndarray:
    """Fechamento = dilatação seguida de erosão.

    Operação dual da abertura: fecha buracos e fendas dentro das regiões, sem inflá-las.

    Na máscara de desmatamento, tapa as ilhas de árvores remanescentes que fragmentariam
    uma área de corte contígua em dezenas de polígonos.
    """
    return erosao(dilatacao(mascara, elemento), elemento)


def gradiente_morfologico(mascara: np.ndarray, elemento: np.ndarray | None = None) -> np.ndarray:
    """Diferença entre dilatação e erosão — devolve o contorno das regiões.

    Útil para desenhar o limite da área desmatada sobre a imagem original na
    apresentação, sem esconder a imagem atrás de um preenchimento sólido.
    """
    return dilatacao(mascara, elemento) & ~erosao(mascara, elemento)


def preencher_buracos(mascara: np.ndarray) -> np.ndarray:
    """Preenche buracos completamente cercados pela região.

    Funciona por complemento: inunda o fundo a partir das bordas da imagem; o que ficou
    de fundo sem ser alcançado está encapsulado pela região, logo é buraco.

    Diferente do fechamento, não tem limite de tamanho — um buraco enorme e fechado é
    preenchido do mesmo jeito.
    """
    mascara = _validar_mascara(mascara) > 0.5
    fundo = ~mascara

    alcancado = np.zeros_like(fundo, dtype=bool)
    alcancado[0, :] |= fundo[0, :]
    alcancado[-1, :] |= fundo[-1, :]
    alcancado[:, 0] |= fundo[:, 0]
    alcancado[:, -1] |= fundo[:, -1]

    elemento = elemento_cruz(3)
    while True:
        expandido = dilatacao(alcancado, elemento) & fundo
        if np.array_equal(expandido, alcancado):
            break
        alcancado = expandido

    return mascara | (fundo & ~alcancado)
