"""Operações de base do processamento digital de imagens.

Tudo em ``sentinela.pdi`` é construído sobre este módulo: convolução, tratamento de
borda e conversões de faixa. A única dependência é NumPy — ver ``AGENTS.md`` §5.

Convenção de representação interna:

- ``float32`` na faixa ``[0, 1]``
- ``[H, W]`` para imagem de banda única, ``[H, W, C]`` para multibanda
"""

from __future__ import annotations

import numpy as np

MODOS_BORDA = ("reflete", "replica", "zero", "circular")


class ErroImagem(ValueError):
    """Entrada inválida para uma operação de processamento de imagens."""


def validar_imagem(imagem: np.ndarray, *, bandas_aceitas: tuple[int, ...] = (2, 3)) -> np.ndarray:
    """Confere se o array tem formato utilizável e devolve-o como ``float32``.

    Levanta ``ErroImagem`` com mensagem explicativa em vez de deixar o NumPy falhar
    com erro de forma lá adiante — o enunciado pontua tratamento de erros (p.4, item II.2).
    """
    if not isinstance(imagem, np.ndarray):
        raise ErroImagem(f"esperado numpy.ndarray, recebido {type(imagem).__name__}")
    if imagem.ndim not in bandas_aceitas:
        raise ErroImagem(
            f"imagem deve ter {' ou '.join(map(str, bandas_aceitas))} dimensões, "
            f"recebido formato {imagem.shape}"
        )
    if imagem.size == 0:
        raise ErroImagem("imagem vazia")
    if not np.issubdtype(imagem.dtype, np.number):
        raise ErroImagem(f"imagem deve ser numérica, recebido dtype {imagem.dtype}")
    return imagem.astype(np.float32, copy=False)


def para_float(imagem: np.ndarray) -> np.ndarray:
    """Converte para ``float32`` em ``[0, 1]``.

    Imagem inteira é dividida pelo máximo do seu tipo (255 para ``uint8``, 65535 para
    ``uint16`` — este último é o caso do Sentinel-2). Imagem já em ponto flutuante é
    apenas recortada para a faixa válida.
    """
    if not isinstance(imagem, np.ndarray):
        raise ErroImagem(f"esperado numpy.ndarray, recebido {type(imagem).__name__}")

    if np.issubdtype(imagem.dtype, np.integer):
        maximo = float(np.iinfo(imagem.dtype).max)
        return (imagem.astype(np.float32) / maximo).astype(np.float32)

    return np.clip(imagem.astype(np.float32), 0.0, 1.0)


def para_uint8(imagem: np.ndarray) -> np.ndarray:
    """Converte de volta para ``uint8`` — usar apenas na fronteira de saída."""
    imagem = validar_imagem(imagem)
    return (np.clip(imagem, 0.0, 1.0) * 255.0).round().astype(np.uint8)


def aplicar_borda(imagem: np.ndarray, pad: tuple[int, int], modo: str = "reflete") -> np.ndarray:
    """Estende as bordas da imagem antes da convolução.

    Sem isso a convolução encolheria a imagem ou produziria artefato na margem.

    ``reflete``  espelha os pixels da borda (padrão — não cria descontinuidade)
    ``replica``  repete o pixel da borda
    ``zero``     preenche com zero (escurece a margem)
    ``circular`` a imagem dá a volta
    """
    if modo not in MODOS_BORDA:
        raise ErroImagem(f"modo de borda '{modo}' desconhecido; use um de {MODOS_BORDA}")

    ph, pw = pad
    if ph < 0 or pw < 0:
        raise ErroImagem(f"padding não pode ser negativo, recebido {pad}")

    larguras = [(ph, ph), (pw, pw)]
    if imagem.ndim == 3:
        larguras.append((0, 0))

    equivalente = {
        "reflete": "reflect",
        "replica": "edge",
        "zero": "constant",
        "circular": "wrap",
    }[modo]

    if equivalente == "constant":
        return np.pad(imagem, larguras, mode="constant", constant_values=0.0)
    return np.pad(imagem, larguras, mode=equivalente)


def correlacionar(
    imagem: np.ndarray, kernel: np.ndarray, modo_borda: str = "reflete"
) -> np.ndarray:
    """Correlação cruzada 2D entre a imagem e o kernel.

    Implementada varrendo as posições do kernel e acumulando a imagem deslocada e
    ponderada. São ``k*k`` operações vetorizadas sobre a imagem inteira, em vez de um
    laço Python por pixel — mesmo algoritmo, tempo viável para demonstração ao vivo.

    Imagem multibanda é processada banda a banda.
    """
    imagem = validar_imagem(imagem)
    kernel = np.asarray(kernel, dtype=np.float32)

    if kernel.ndim != 2:
        raise ErroImagem(f"kernel deve ser 2D, recebido formato {kernel.shape}")
    if kernel.shape[0] % 2 == 0 or kernel.shape[1] % 2 == 0:
        raise ErroImagem(
            f"kernel deve ter dimensões ímpares para ter centro definido, "
            f"recebido {kernel.shape}"
        )

    if imagem.ndim == 3:
        bandas = [
            correlacionar(imagem[:, :, b], kernel, modo_borda)
            for b in range(imagem.shape[2])
        ]
        return np.stack(bandas, axis=2)

    altura_k, largura_k = kernel.shape
    ph, pw = altura_k // 2, largura_k // 2

    if imagem.shape[0] < 1 or imagem.shape[1] < 1:
        raise ErroImagem(f"imagem pequena demais para o kernel {kernel.shape}")

    estendida = aplicar_borda(imagem, (ph, pw), modo_borda)
    altura, largura = imagem.shape
    saida = np.zeros((altura, largura), dtype=np.float32)

    for i in range(altura_k):
        for j in range(largura_k):
            peso = kernel[i, j]
            if peso != 0.0:
                saida += peso * estendida[i : i + altura, j : j + largura]

    return saida


def convoluir(imagem: np.ndarray, kernel: np.ndarray, modo_borda: str = "reflete") -> np.ndarray:
    """Convolução 2D propriamente dita.

    Diferença em relação à correlação: o kernel é rotacionado 180° antes de ser
    aplicado. Para kernels simétricos (gaussiano, média) o resultado é idêntico; para
    kernels assimétricos (Sobel) o sinal do gradiente inverte. A distinção é cobrada
    na teoria da disciplina, então as duas operações existem separadas e nomeadas.
    """
    kernel = np.asarray(kernel, dtype=np.float32)
    if kernel.ndim != 2:
        raise ErroImagem(f"kernel deve ser 2D, recebido formato {kernel.shape}")
    return correlacionar(imagem, kernel[::-1, ::-1], modo_borda)


def janela_deslizante(imagem: np.ndarray, tamanho: int, modo_borda: str = "reflete") -> np.ndarray:
    """Empilha todas as vizinhanças ``tamanho x tamanho`` ao longo de um novo eixo 0.

    Base dos filtros de estatística de ordem (mediana, mínimo, máximo) e dos
    operadores morfológicos, que não podem ser expressos como convolução porque não
    são combinações lineares da vizinhança.

    Devolve array de formato ``[tamanho*tamanho, H, W]``.
    """
    imagem = validar_imagem(imagem, bandas_aceitas=(2,))

    if tamanho < 1 or tamanho % 2 == 0:
        raise ErroImagem(f"tamanho da janela deve ser ímpar e positivo, recebido {tamanho}")

    pad = tamanho // 2
    estendida = aplicar_borda(imagem, (pad, pad), modo_borda)
    altura, largura = imagem.shape

    return np.stack(
        [
            estendida[i : i + altura, j : j + largura]
            for i in range(tamanho)
            for j in range(tamanho)
        ],
        axis=0,
    )


def normalizar(imagem: np.ndarray) -> np.ndarray:
    """Reescala linearmente para ``[0, 1]`` usando mínimo e máximo da imagem.

    Imagem constante devolve zeros — evita divisão por zero sem mascarar o problema.
    """
    imagem = validar_imagem(imagem)
    minimo = float(imagem.min())
    maximo = float(imagem.max())

    if maximo - minimo < 1e-12:
        return np.zeros_like(imagem, dtype=np.float32)

    return ((imagem - minimo) / (maximo - minimo)).astype(np.float32)


def alongar_contraste(
    imagem: np.ndarray, percentil_baixo: float = 2.0, percentil_alto: float = 98.0
) -> np.ndarray:
    """Alongamento de contraste por percentil.

    Preferível ao ``normalizar`` puro em imagem de satélite: um único pixel saturado
    (reflexo em água, nuvem) comprime toda a faixa útil se o máximo absoluto for usado.
    Cortar nos percentis descarta esses extremos.
    """
    imagem = validar_imagem(imagem)

    if not 0.0 <= percentil_baixo < percentil_alto <= 100.0:
        raise ErroImagem(
            f"percentis inválidos: baixo={percentil_baixo}, alto={percentil_alto} "
            "(exigido 0 <= baixo < alto <= 100)"
        )

    corte_baixo = float(np.percentile(imagem, percentil_baixo))
    corte_alto = float(np.percentile(imagem, percentil_alto))

    if corte_alto - corte_baixo < 1e-12:
        return np.zeros_like(imagem, dtype=np.float32)

    esticada = (imagem - corte_baixo) / (corte_alto - corte_baixo)
    return np.clip(esticada, 0.0, 1.0).astype(np.float32)


def histograma(imagem: np.ndarray, faixas: int = 256) -> tuple[np.ndarray, np.ndarray]:
    """Histograma de intensidades. Devolve ``(contagens, centros_das_faixas)``."""
    imagem = validar_imagem(imagem, bandas_aceitas=(2,))
    contagens, bordas = np.histogram(imagem, bins=faixas, range=(0.0, 1.0))
    centros = ((bordas[:-1] + bordas[1:]) / 2.0).astype(np.float32)
    return contagens.astype(np.int64), centros


def equalizar_histograma(imagem: np.ndarray, faixas: int = 256) -> np.ndarray:
    """Equalização de histograma pela função de distribuição acumulada.

    Redistribui as intensidades para aproximar um histograma uniforme, realçando
    detalhe em regiões de baixo contraste — útil em cena de satélite com névoa.
    """
    imagem = validar_imagem(imagem, bandas_aceitas=(2,))

    contagens, _ = np.histogram(imagem, bins=faixas, range=(0.0, 1.0))
    acumulado = np.cumsum(contagens).astype(np.float64)

    total = acumulado[-1]
    if total == 0:
        return np.zeros_like(imagem, dtype=np.float32)

    acumulado_min = acumulado[acumulado > 0][0]
    denominador = total - acumulado_min
    if denominador <= 0:
        return np.zeros_like(imagem, dtype=np.float32)

    mapeamento = ((acumulado - acumulado_min) / denominador).clip(0.0, 1.0)

    indices = np.clip((imagem * faixas).astype(np.int32), 0, faixas - 1)
    return mapeamento[indices].astype(np.float32)
