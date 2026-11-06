"""Filtros espaciais implementados pelo grupo.

Cobre a etapa "Filtragem" do enunciado (p.3, item 2.e.iii) e atende à exigência de
que os filtros sejam desenvolvidos pelo próprio grupo (p.3, item 3.a).

Nenhuma função aqui chama filtro pronto de biblioteca. Todos os kernels são construídos
neste módulo e aplicados pela convolução de ``nucleo.py``. Ver
``_interno/docs/decisions/001-filtros-proprios.md``.

Papel de cada filtro na detecção de desmatamento:

- **gaussiano / média** — suavizam ruído de sensor e variação de dossel antes da
  segmentação, evitando máscara cheia de buracos.
- **mediana** — remove ruído sal-e-pimenta (pixel morto, reflexo especular) sem borrar
  a fronteira entre floresta e área cortada, que é o que se quer preservar.
- **Sobel / Prewitt** — realçam essa fronteira, dando o contorno da área desmatada.
- **Laplaciano / nitidez** — realçam detalhe fino; úteis para delimitar estradas
  vicinais e o padrão "espinha de peixe" típico de ocupação.
"""

from __future__ import annotations

import numpy as np

from .nucleo import (
    ErroImagem,
    correlacionar,
    janela_deslizante,
    normalizar,
    validar_imagem,
)

# --------------------------------------------------------------------------------------
# Construção de kernels
# --------------------------------------------------------------------------------------

SOBEL_X = np.array([[-1.0, 0.0, 1.0], [-2.0, 0.0, 2.0], [-1.0, 0.0, 1.0]], dtype=np.float32)
SOBEL_Y = np.array([[-1.0, -2.0, -1.0], [0.0, 0.0, 0.0], [1.0, 2.0, 1.0]], dtype=np.float32)

PREWITT_X = np.array([[-1.0, 0.0, 1.0], [-1.0, 0.0, 1.0], [-1.0, 0.0, 1.0]], dtype=np.float32)
PREWITT_Y = np.array([[-1.0, -1.0, -1.0], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], dtype=np.float32)

LAPLACIANO_4 = np.array([[0.0, 1.0, 0.0], [1.0, -4.0, 1.0], [0.0, 1.0, 0.0]], dtype=np.float32)
LAPLACIANO_8 = np.array([[1.0, 1.0, 1.0], [1.0, -8.0, 1.0], [1.0, 1.0, 1.0]], dtype=np.float32)


def kernel_media(tamanho: int = 3) -> np.ndarray:
    """Kernel de média: todos os pesos iguais, somando 1."""
    if tamanho < 1 or tamanho % 2 == 0:
        raise ErroImagem(f"tamanho deve ser ímpar e positivo, recebido {tamanho}")
    return np.full((tamanho, tamanho), 1.0 / (tamanho * tamanho), dtype=np.float32)


def kernel_gaussiano(tamanho: int = 5, sigma: float | None = None) -> np.ndarray:
    """Kernel gaussiano 2D normalizado para somar 1.

    ``G(x,y) = exp(-(x² + y²) / (2σ²))``, amostrada nas posições inteiras da janela e
    normalizada ao final. Somar 1 é o que garante que o filtro não altere o brilho médio.

    Com ``sigma=None`` usa ``σ = tamanho / 6``, a convenção que faz a janela cobrir
    aproximadamente ±3σ — onde está mais de 99% da massa da gaussiana.
    """
    if tamanho < 1 or tamanho % 2 == 0:
        raise ErroImagem(f"tamanho deve ser ímpar e positivo, recebido {tamanho}")

    if sigma is None:
        sigma = tamanho / 6.0
    if sigma <= 0:
        raise ErroImagem(f"sigma deve ser positivo, recebido {sigma}")

    raio = tamanho // 2
    eixo = np.arange(-raio, raio + 1, dtype=np.float32)
    x, y = np.meshgrid(eixo, eixo)

    kernel = np.exp(-(x**2 + y**2) / (2.0 * sigma**2))
    return (kernel / kernel.sum()).astype(np.float32)


def kernel_gaussiano_1d(tamanho: int = 5, sigma: float | None = None) -> np.ndarray:
    """Kernel gaussiano de uma dimensão, normalizado para somar 1, no formato ``(1, k)``.

    A gaussiana 2D é **separável**, e isso não é uma aproximação:

    ``G(x,y) = exp(-(x² + y²) / 2σ²) = exp(-x² / 2σ²) · exp(-y² / 2σ²)``

    O expoente de uma soma vira produto de exponenciais, então o núcleo 2D é exatamente
    o produto externo de dois núcleos 1D idênticos. A normalização acompanha: se cada
    1D soma 1, o produto externo soma 1, que é a mesma condição do núcleo 2D.

    A consequência prática está em ``gaussiano``: convoluir duas vezes em 1D custa
    ``2k`` multiplicações por pixel em vez de ``k²``.
    """
    if tamanho < 1 or tamanho % 2 == 0:
        raise ErroImagem(f"tamanho deve ser ímpar e positivo, recebido {tamanho}")

    if sigma is None:
        sigma = tamanho / 6.0
    if sigma <= 0:
        raise ErroImagem(f"sigma deve ser positivo, recebido {sigma}")

    raio = tamanho // 2
    eixo = np.arange(-raio, raio + 1, dtype=np.float32)
    kernel = np.exp(-(eixo**2) / (2.0 * sigma**2))
    return (kernel / kernel.sum()).astype(np.float32).reshape(1, tamanho)


# --------------------------------------------------------------------------------------
# Filtros de suavização
# --------------------------------------------------------------------------------------


def media(
    imagem: np.ndarray,
    tamanho: int = 3,
    modo_borda: str = "reflete",
    separavel: bool = True,
) -> np.ndarray:
    """Filtro de média (passa-baixa). Suaviza, mas borra bordas igualmente.

    O núcleo de média também é **separável**, por um argumento ainda mais simples que o
    do gaussiano: uma matriz ``k × k`` com todos os pesos iguais a ``1/k²`` é o produto
    externo de dois vetores com todos os pesos iguais a ``1/k``. Com ``separavel=True``
    (padrão) aplica dois passes de uma dimensão; ``separavel=False`` usa o núcleo 2D e
    existe para a verificação por teste.
    """
    if not separavel:
        return correlacionar(imagem, kernel_media(tamanho), modo_borda)

    if tamanho < 1 or tamanho % 2 == 0:
        raise ErroImagem(f"tamanho deve ser ímpar e positivo, recebido {tamanho}")

    linha = np.full((1, tamanho), 1.0 / tamanho, dtype=np.float32)
    horizontal = correlacionar(imagem, linha, modo_borda)
    return correlacionar(horizontal, linha.T, modo_borda)


def gaussiano(
    imagem: np.ndarray,
    tamanho: int = 5,
    sigma: float | None = None,
    modo_borda: str = "reflete",
    separavel: bool = True,
) -> np.ndarray:
    """Filtro gaussiano (passa-baixa).

    Pondera a vizinhança pela distância ao centro, produzindo suavização mais natural
    que a média — sem o artefato de "caixa" que o kernel uniforme deixa.

    Com ``separavel=True`` (padrão) aplica dois passes de uma dimensão — horizontal e
    depois vertical — explorando a separabilidade demonstrada em ``kernel_gaussiano_1d``.
    O resultado é o **mesmo** do núcleo 2D, a menos de erro de ponto flutuante; o custo
    cai de ``k²`` para ``2k`` multiplicações por pixel, o que importa em janela grande e
    em cena de satélite inteira.

    ``separavel=False`` aplica o núcleo 2D diretamente. Existe para que a equivalência
    entre os dois caminhos possa ser verificada por teste, e para a demonstração do
    conceito na apresentação.
    """
    if not separavel:
        return correlacionar(imagem, kernel_gaussiano(tamanho, sigma), modo_borda)

    linha = kernel_gaussiano_1d(tamanho, sigma)
    horizontal = correlacionar(imagem, linha, modo_borda)
    return correlacionar(horizontal, linha.T, modo_borda)


def mediana(imagem: np.ndarray, tamanho: int = 3, modo_borda: str = "reflete") -> np.ndarray:
    """Filtro de mediana (estatística de ordem).

    Não é convolução: não existe kernel que produza a mediana, porque ela não é
    combinação linear da vizinhança. Por isso usa ``janela_deslizante``.

    Vantagem sobre o gaussiano: remove ruído impulsivo preservando a borda, já que a
    mediana de uma vizinhança que cruza uma fronteira cai de um lado ou do outro, nunca
    num valor intermediário inexistente.
    """
    imagem = validar_imagem(imagem)

    if imagem.ndim == 3:
        bandas = [mediana(imagem[:, :, b], tamanho, modo_borda) for b in range(imagem.shape[2])]
        return np.stack(bandas, axis=2)

    janelas = janela_deslizante(imagem, tamanho, modo_borda)
    return np.median(janelas, axis=0).astype(np.float32)


# --------------------------------------------------------------------------------------
# Filtros de realce de borda
# --------------------------------------------------------------------------------------


def gradiente(
    imagem: np.ndarray, operador: str = "sobel", modo_borda: str = "reflete"
) -> tuple[np.ndarray, np.ndarray]:
    """Componentes horizontal e vertical do gradiente.

    Devolve ``(gx, gy)`` sem normalizar — os valores são assinados e o sinal indica a
    direção da transição. Use ``magnitude_gradiente`` para o resultado visualizável.
    """
    operadores = {
        "sobel": (SOBEL_X, SOBEL_Y),
        "prewitt": (PREWITT_X, PREWITT_Y),
    }
    if operador not in operadores:
        raise ErroImagem(
            f"operador '{operador}' desconhecido; use um de {tuple(operadores)}"
        )

    kx, ky = operadores[operador]
    return correlacionar(imagem, kx, modo_borda), correlacionar(imagem, ky, modo_borda)


def magnitude_gradiente(
    imagem: np.ndarray,
    operador: str = "sobel",
    modo_borda: str = "reflete",
    normalizar_saida: bool = True,
) -> np.ndarray:
    """Magnitude do gradiente: ``sqrt(gx² + gy²)``.

    É o mapa de bordas. Na detecção de desmatamento, o contorno de uma área de corte
    raso aparece aqui como uma linha fechada de alta magnitude.
    """
    gx, gy = gradiente(imagem, operador, modo_borda)
    mag = np.sqrt(gx**2 + gy**2).astype(np.float32)
    return normalizar(mag) if normalizar_saida else mag


def direcao_gradiente(
    imagem: np.ndarray, operador: str = "sobel", modo_borda: str = "reflete"
) -> np.ndarray:
    """Direção do gradiente em radianos, na faixa ``(-π, π]``.

    Útil para distinguir borda natural (orientação difusa, como margem de rio) de borda
    antrópica (orientação alinhada, como limite de propriedade ou estrada).
    """
    gx, gy = gradiente(imagem, operador, modo_borda)
    return np.arctan2(gy, gx).astype(np.float32)


def laplaciano(
    imagem: np.ndarray, conectividade: int = 4, modo_borda: str = "reflete"
) -> np.ndarray:
    """Laplaciano — derivada de segunda ordem, realça detalhe fino.

    ``conectividade=4`` considera apenas os vizinhos ortogonais; ``8`` inclui as
    diagonais e responde mais forte a texturas.

    Saída é assinada: positiva de um lado da borda, negativa do outro.
    """
    kernels = {4: LAPLACIANO_4, 8: LAPLACIANO_8}
    if conectividade not in kernels:
        raise ErroImagem(f"conectividade deve ser 4 ou 8, recebido {conectividade}")
    return correlacionar(imagem, kernels[conectividade], modo_borda)


def nitidez(
    imagem: np.ndarray,
    intensidade: float = 1.0,
    tamanho: int = 5,
    sigma: float | None = None,
    modo_borda: str = "reflete",
) -> np.ndarray:
    """Realce por máscara de nitidez (*unsharp masking*).

    ``resultado = original + intensidade * (original - borrada)``

    A diferença entre a imagem e sua versão borrada isola justamente o que o borramento
    removeu: o detalhe de alta frequência. Somá-lo de volta amplificado realça esse
    detalhe. Recortado em ``[0, 1]`` ao final.
    """
    imagem = validar_imagem(imagem)

    if intensidade < 0:
        raise ErroImagem(f"intensidade não pode ser negativa, recebido {intensidade}")

    borrada = gaussiano(imagem, tamanho, sigma, modo_borda)
    realcada = imagem + intensidade * (imagem - borrada)
    return np.clip(realcada, 0.0, 1.0).astype(np.float32)


# --------------------------------------------------------------------------------------
# Filtros de estatística local
# --------------------------------------------------------------------------------------


def minimo_local(imagem: np.ndarray, tamanho: int = 3, modo_borda: str = "replica") -> np.ndarray:
    """Mínimo da vizinhança. Base da erosão morfológica."""
    return janela_deslizante(imagem, tamanho, modo_borda).min(axis=0).astype(np.float32)


def maximo_local(imagem: np.ndarray, tamanho: int = 3, modo_borda: str = "replica") -> np.ndarray:
    """Máximo da vizinhança. Base da dilatação morfológica."""
    return janela_deslizante(imagem, tamanho, modo_borda).max(axis=0).astype(np.float32)


def desvio_padrao_local(
    imagem: np.ndarray, tamanho: int = 5, modo_borda: str = "reflete"
) -> np.ndarray:
    """Desvio padrão da vizinhança — medida simples de textura.

    Floresta primária tem dossel irregular e desvio alto; pasto e solo exposto são
    homogêneos e têm desvio baixo. É uma das features usadas na etapa de modelo, e
    sozinha já separa razoavelmente as duas classes.
    """
    janelas = janela_deslizante(imagem, tamanho, modo_borda)
    return janelas.std(axis=0).astype(np.float32)
