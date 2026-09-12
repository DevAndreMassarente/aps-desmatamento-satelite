# 7. Apêndice — código-fonte do programa

> **Gerado automaticamente** por `sentinela apendice`. Não editar à mão: a edição
> se perde na próxima geração, e um apêndice editado deixa de corresponder ao
> código entregue.

Os filtros de processamento de imagens em `pdi/` foram implementados pelo grupo,
com NumPy apenas, conforme exige o enunciado (p.3, item 3.a).

## Índice

- `sentinela/pdi/nucleo.py` — 262 linhas
- `sentinela/pdi/cor.py` — 248 linhas
- `sentinela/pdi/filtros.py` — 307 linhas
- `sentinela/pdi/limiar.py` — 292 linhas
- `sentinela/pdi/morfologia.py` — 174 linhas
- `sentinela/pdi/segmentacao.py` — 262 linhas
- `sentinela/dataio/imagem.py` — 112 linhas
- `sentinela/dataio/geo.py` — 77 linhas
- `sentinela/dataio/visual.py` — 122 linhas
- `sentinela/dataio/sintetico.py` — 127 linhas
- `sentinela/pipeline/deteccao.py` — 259 linhas
- `sentinela/pipeline/amostras.py` — 196 linhas
- `sentinela/modelo/caracteristicas.py` — 118 linhas
- `sentinela/modelo/classificador.py` — 312 linhas
- `sentinela/app/principal.py` — 535 linhas
- `sentinela/cli.py` — 399 linhas

**Total: 16 arquivos, 3802 linhas.**

---

## `sentinela/pdi/nucleo.py`

```python
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
```

---

## `sentinela/pdi/cor.py`

```python
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
```

---

## `sentinela/pdi/filtros.py`

```python
"""Filtros espaciais implementados pelo grupo.

Cobre a etapa "Filtragem" do enunciado (p.3, item 2.e.iii) e atende à exigência de
que os filtros sejam desenvolvidos pelo próprio grupo (p.3, item 3.a).

Nenhuma função aqui chama filtro pronto de biblioteca. Todos os kernels são construídos
neste módulo e aplicados pela convolução de ``nucleo.py``. Ver
``docs/decisions/001-filtros-proprios.md``.

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
```

---

## `sentinela/pdi/limiar.py`

```python
"""Limiarização — primeira etapa da segmentação.

Cobre parte da etapa "Segmentação" do enunciado (p.3, item 2.e.iv). O objetivo aqui é
converter o índice de vegetação contínuo em uma máscara binária: vegetação × não-vegetação.
"""

from __future__ import annotations

import numpy as np

from .nucleo import ErroImagem, histograma, janela_deslizante, validar_imagem


def binarizar(imagem: np.ndarray, limiar: float, inverter: bool = False) -> np.ndarray:
    """Aplica um limiar fixo, devolvendo máscara booleana.

    Com ``inverter=False`` marca ``imagem > limiar``. Na detecção de desmatamento o
    interessante costuma ser o inverso — o que ficou **abaixo** do limiar de vegetação.
    """
    imagem = validar_imagem(imagem, bandas_aceitas=(2,))

    if not np.isfinite(limiar):
        raise ErroImagem(f"limiar deve ser um número finito, recebido {limiar}")

    mascara = imagem <= limiar if inverter else imagem > limiar
    return mascara


# Piso teórico da distinguibilidade: cortar uma distribuição normal única no ponto ótimo
# produz duas meias-normais com médias em ±0,798σ e desvio 0,603σ, logo
# d = 1,596σ / 0,603σ ≈ 2,65. Ou seja, QUALQUER imagem unimodal — uma cena inteiramente
# florestada, por exemplo — atinge d ≈ 2,65 sem ter duas classes de verdade.
DISTINGUIBILIDADE_UNIMODAL = 2.65

# Acima deste valor o limiar está separando duas classes reais, não partindo ruído ao meio.
# Medido nas cenas sintéticas de `tests/test_integracao.py`: cena homogênea fica em
# d ≈ 2,69 (os três índices), e cena com corte raso detectável vai de 7,3 (VARI/ExG) a
# 12,0 (NDVI). O corte foi posto na folga. Reavaliar contra as imagens reais (R032).
DISTINGUIBILIDADE_MINIMA = 4.0


def _otsu_do_histograma(
    contagens: np.ndarray, centros: np.ndarray
) -> tuple[float, float]:
    """Núcleo do método de Otsu sobre um histograma já montado.

    Otsu varre todos os limiares possíveis e escolhe o que **maximiza a variância entre
    as duas classes** resultantes — equivalente a minimizar a variância dentro delas.
    A intuição: o melhor corte é o que deixa os dois grupos mais separados um do outro
    e mais compactos internamente.

    Para o peso ``ω`` e a média ``μ`` acumulados até cada faixa::

        σ²_entre(t) = [μ_total · ω(t) − μ(t)]² / [ω(t) · (1 − ω(t))]

    A formulação acumulada evita recalcular as médias das duas classes a cada limiar,
    reduzindo o método a uma varredura única sobre o histograma.

    Devolve ``(limiar, separabilidade)``. A separabilidade é a medida ``η = σ²_entre /
    σ²_total`` definida no artigo original: vale 1 quando as duas classes são
    perfeitamente distintas e tende a 0 quando o histograma tem um modo só.

    Referência: Otsu, N. (1979). "A Threshold Selection Method from Gray-Level Histograms".
    IEEE Transactions on Systems, Man, and Cybernetics, 9(1), 62–66.
    """
    total = contagens.sum()
    if total == 0:
        raise ErroImagem("histograma vazio — imagem sem pixels válidos")

    probabilidade = contagens.astype(np.float64) / total
    centros = centros.astype(np.float64)

    peso = np.cumsum(probabilidade)
    media_acumulada = np.cumsum(probabilidade * centros)
    media_total = media_acumulada[-1]

    denominador = peso * (1.0 - peso)
    # Limiares degenerados (uma das classes vazia) são descartados, não ajustados.
    valido = denominador > 1e-12

    if not valido.any():
        raise ErroImagem(
            "não foi possível calcular o limiar de Otsu: a imagem parece ter "
            "intensidade constante"
        )

    variancia_entre = np.zeros_like(denominador)
    variancia_entre[valido] = (
        (media_total * peso[valido] - media_acumulada[valido]) ** 2 / denominador[valido]
    )

    # Quando não há pixel algum entre os dois modos, todo limiar dentro do vão produz a
    # mesma partição e portanto a mesma variância entre classes. `argmax` devolveria o
    # primeiro desse platô, encostando o limiar na cauda do modo inferior. Tomar o centro
    # do platô deixa a margem equilibrada para os dois lados, que é mais robusto a ruído
    # na imagem real sem alterar a partição no caso sintético.
    maximo = variancia_entre.max()
    no_platô = np.flatnonzero(variancia_entre >= maximo * (1.0 - 1e-9))
    melhor = int(no_platô[len(no_platô) // 2])

    variancia_total = float((probabilidade * (centros - media_total) ** 2).sum())

    separabilidade = (
        float(variancia_entre[melhor] / variancia_total) if variancia_total > 1e-15 else 0.0
    )

    return float(centros[melhor]), separabilidade


def otsu(imagem: np.ndarray, faixas: int = 256) -> float:
    """Limiar ótimo de Otsu para a imagem.

    Funciona quando o histograma é bimodal — o caso de um índice de vegetação numa cena
    que tem floresta **e** área desmatada. Numa cena homogênea o valor devolvido não tem
    significado; use ``otsu_com_separabilidade`` para saber se dá para confiar nele.
    """
    return otsu_com_separabilidade(imagem, faixas)[0]


def otsu_com_separabilidade(imagem: np.ndarray, faixas: int = 256) -> tuple[float, float]:
    """Como ``otsu``, mas devolve também a separabilidade ``η`` do histograma.

    Usar quando a imagem pode não ter duas classes — por exemplo uma cena inteiramente
    florestada, em que qualquer limiar automático vai partir o ruído ao meio e inventar
    desmatamento onde não há. Comparar ``η`` com ``SEPARABILIDADE_MINIMA``.
    """
    imagem = validar_imagem(imagem, bandas_aceitas=(2,))

    if faixas < 2:
        raise ErroImagem(f"são necessárias ao menos 2 faixas, recebido {faixas}")

    contagens, centros = histograma(imagem, faixas)
    return _otsu_do_histograma(contagens, centros)


def distinguibilidade(imagem: np.ndarray, valor: float) -> float:
    """Tamanho de efeito padronizado entre as duas classes produzidas por um limiar.

    ``d = |μ_baixa − μ_alta| / sqrt[(σ²_baixa + σ²_alta) / 2]``

    Mede a distância entre as médias das duas classes em unidades do espalhamento
    interno delas. É o critério para decidir se o limiar encontrado separa duas
    populações reais ou apenas partiu uma população única ao meio.

    **Por que não usar a separabilidade η de Otsu para isso.** η vale
    ``σ²_entre / σ²_total``, e ``σ²_entre`` carrega o fator ``ω·(1−ω)`` — o produto das
    frações das duas classes. Uma área desmatada pequena (digamos 6% da cena) dá
    ``ω(1−ω) = 0,056``, contra ``0,25`` de uma partição meio a meio. Isso derruba η
    mecanicamente, por desbalanceamento, sem nenhuma relação com a qualidade da
    separação. Na prática η chega a ficar **mais alto** numa cena homogênea (onde Otsu
    corta 50/50) do que numa cena com desmatamento real pequeno — exatamente ao
    contrário do que se precisa.

    O tamanho de efeito não tem esse fator e é invariante ao tamanho relativo das classes.

    Ver ``DISTINGUIBILIDADE_UNIMODAL`` para o piso que qualquer imagem atinge.
    """
    imagem = validar_imagem(imagem, bandas_aceitas=(2,))

    baixa = imagem[imagem <= valor]
    alta = imagem[imagem > valor]

    if baixa.size < 2 or alta.size < 2:
        return 0.0

    espalhamento = np.sqrt((float(baixa.var()) + float(alta.var())) / 2.0)
    if espalhamento < 1e-12:
        return float("inf")

    return float(abs(float(baixa.mean()) - float(alta.mean())) / espalhamento)


def limiar_confiavel(
    *imagens: np.ndarray, faixas: int = 256
) -> tuple[float, bool, dict[str, float]]:
    """Calcula o limiar conjunto e avalia se ele é confiável.

    Devolve ``(valor, confiavel, metricas)``. ``metricas`` traz ``separabilidade``
    (o η do artigo de Otsu, útil para o relatório) e ``distinguibilidade`` (o critério
    efetivo de decisão).

    Usar isto, e não ``otsu`` cru, sempre que a cena puder não conter desmatamento:
    marcar ``confiavel=False`` e não emitir máscara é a resposta correta para uma
    floresta intacta. Emitir uma máscara ali seria inventar desmatamento.
    """
    valor, separabilidade = otsu_conjunto(*imagens, faixas=faixas)
    efeito = max(distinguibilidade(imagem, valor) for imagem in imagens)

    return (
        valor,
        efeito >= DISTINGUIBILIDADE_MINIMA,
        {"separabilidade": separabilidade, "distinguibilidade": efeito},
    )


def otsu_conjunto(*imagens: np.ndarray, faixas: int = 256) -> tuple[float, float]:
    """Limiar **único** de Otsu calculado sobre o histograma combinado das imagens.

    É o que a análise bi-temporal exige. Calcular Otsu separadamente em cada data dá a
    cada uma um limiar diferente — réguas diferentes — e a comparação entre as máscaras
    deixa de significar mudança no terreno: passa a medir a diferença entre os dois
    limiares.

    O caso que expõe o erro: se T1 é floresta intacta, o histograma de T1 sozinho é
    unimodal e o Otsu corta no meio do ruído do dossel, marcando metade da floresta como
    não-vegetação. A comparação com T2 acusaria desmatamento massivo inexistente.

    Com o histograma combinado, as duas datas são medidas pela mesma régua, e basta que
    **uma** delas contenha as duas classes para que o limiar seja bem definido.

    Devolve ``(limiar, separabilidade)``.
    """
    if not imagens:
        raise ErroImagem("é necessária ao menos uma imagem")

    if faixas < 2:
        raise ErroImagem(f"são necessárias ao menos 2 faixas, recebido {faixas}")

    validadas = [validar_imagem(img, bandas_aceitas=(2,)) for img in imagens]

    total_contagens = np.zeros(faixas, dtype=np.int64)
    centros = None
    for imagem in validadas:
        contagens, centros = histograma(imagem, faixas)
        total_contagens += contagens

    return _otsu_do_histograma(total_contagens, centros)


def otsu_binarizar(
    imagem: np.ndarray, faixas: int = 256, inverter: bool = False
) -> tuple[np.ndarray, float]:
    """Conveniência: calcula o limiar de Otsu e já aplica.

    Devolve ``(mascara, limiar)`` — o limiar é propagado para que apareça no relatório
    e na interface, já que "qual limiar vocês usaram?" é pergunta certa na banca.
    """
    limiar = otsu(imagem, faixas)
    return binarizar(imagem, limiar, inverter), limiar


def limiar_adaptativo(
    imagem: np.ndarray,
    tamanho: int = 31,
    deslocamento: float = 0.02,
    inverter: bool = False,
    modo_borda: str = "reflete",
) -> np.ndarray:
    """Limiarização adaptativa pela média local.

    Cada pixel é comparado à média da sua vizinhança, menos um deslocamento. Diferente
    do Otsu, que escolhe **um** limiar para a imagem inteira, este acompanha variações
    graduais de iluminação — sombra de nuvem, gradiente atmosférico, relevo sombreado —
    que fariam um limiar global errar sistematicamente num lado da cena.

    O custo é sensibilidade a ruído: em região homogênea a média local fica próxima do
    próprio pixel e o resultado vira textura aleatória. Suavizar antes, ou usar
    ``deslocamento`` maior.
    """
    imagem = validar_imagem(imagem, bandas_aceitas=(2,))

    if tamanho < 3 or tamanho % 2 == 0:
        raise ErroImagem(f"tamanho da janela deve ser ímpar e >= 3, recebido {tamanho}")

    media_local = janela_deslizante(imagem, tamanho, modo_borda).mean(axis=0)
    referencia = media_local - deslocamento

    return imagem <= referencia if inverter else imagem > referencia


def limiar_duplo(
    imagem: np.ndarray, limiar_baixo: float, limiar_alto: float
) -> tuple[np.ndarray, np.ndarray]:
    """Histerese: separa pixels fortes dos fracos.

    Devolve ``(fortes, fracos)``. Pixels acima de ``limiar_alto`` são seguramente da
    classe; os entre os dois limiares são candidatos, aceitos só se conectados a um
    forte — conexão resolvida em ``segmentacao.reconstruir_por_conexao``.

    É o mecanismo do detector de Canny e vale para reduzir falso positivo isolado na
    máscara de desmatamento.
    """
    imagem = validar_imagem(imagem, bandas_aceitas=(2,))

    if limiar_baixo >= limiar_alto:
        raise ErroImagem(
            f"limiar_baixo ({limiar_baixo}) deve ser menor que limiar_alto ({limiar_alto})"
        )

    fortes = imagem >= limiar_alto
    fracos = (imagem >= limiar_baixo) & ~fortes
    return fortes, fracos
```

---

## `sentinela/pdi/morfologia.py`

```python
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
```

---

## `sentinela/pdi/segmentacao.py`

```python
"""Rotulagem e análise de regiões segmentadas.

Fecha a etapa "Segmentação" do enunciado (p.3, item 2.e.iv). Enquanto ``limiar`` e
``morfologia`` produzem uma máscara, este módulo transforma a máscara em **objetos
contáveis e mensuráveis** — que é o que permite responder "quantos hectares foram
desmatados, e em quantos polígonos distintos?".
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .morfologia import _validar_mascara, dilatacao, elemento_cruz, elemento_quadrado


@dataclass(frozen=True)
class Regiao:
    """Uma região conexa da máscara.

    ``caixa`` é ``(linha_min, coluna_min, linha_max, coluna_max)``, com os limites
    máximos exclusivos, no padrão de fatiamento do NumPy.
    """

    rotulo: int
    area_pixels: int
    centroide: tuple[float, float]
    caixa: tuple[int, int, int, int]

    def area_hectares(self, metros_por_pixel: float) -> float:
        """Converte a área para hectares. 1 ha = 10.000 m²."""
        if metros_por_pixel <= 0:
            raise ValueError(
                f"metros_por_pixel deve ser positivo, recebido {metros_por_pixel}"
            )
        return self.area_pixels * (metros_por_pixel**2) / 10_000.0


class _UnionFind:
    """Estrutura união-busca para equivalência de rótulos.

    Usada pela rotulagem de dois passos: quando duas etiquetas provisórias se revelam
    da mesma região, em vez de reetiquetar a imagem inteira, apenas registra-se que
    elas são equivalentes.
    """

    def __init__(self) -> None:
        self._pai: dict[int, int] = {}

    def criar(self, item: int) -> None:
        self._pai.setdefault(item, item)

    def buscar(self, item: int) -> int:
        raiz = item
        while self._pai[raiz] != raiz:
            raiz = self._pai[raiz]
        # Compressão de caminho: aplana a árvore para acelerar as buscas seguintes.
        while self._pai[item] != raiz:
            self._pai[item], item = raiz, self._pai[item]
        return raiz

    def unir(self, a: int, b: int) -> None:
        raiz_a, raiz_b = self.buscar(a), self.buscar(b)
        if raiz_a != raiz_b:
            self._pai[max(raiz_a, raiz_b)] = min(raiz_a, raiz_b)


def rotular(mascara: np.ndarray, conectividade: int = 8) -> tuple[np.ndarray, int]:
    """Rotula componentes conexos pelo algoritmo de dois passos.

    Devolve ``(rotulos, quantidade)``, onde ``rotulos`` é um array inteiro com 0 no
    fundo e 1..N nas regiões.

    **Primeiro passo:** varre a imagem em ordem de leitura. Para cada pixel marcado,
    olha apenas os vizinhos **já visitados** (acima e à esquerda). Sem vizinho marcado,
    cria etiqueta nova; com um ou mais, adota a menor e registra na união-busca que as
    demais são equivalentes a ela.

    **Segundo passo:** substitui cada etiqueta provisória pela raiz da sua classe de
    equivalência e renumera para 1..N contíguos.

    ``conectividade=4`` considera vizinhos ortogonais; ``8`` inclui as diagonais. Para
    desmatamento, 8 é o padrão razoável — uma área de corte ligada apenas na diagonal
    ainda é a mesma área no terreno.
    """
    mascara = _validar_mascara(mascara) > 0.5

    if conectividade not in (4, 8):
        raise ValueError(f"conectividade deve ser 4 ou 8, recebido {conectividade}")

    altura, largura = mascara.shape
    rotulos = np.zeros((altura, largura), dtype=np.int32)
    conjuntos = _UnionFind()
    proximo = 1

    if conectividade == 4:
        vizinhos = ((-1, 0), (0, -1))
    else:
        vizinhos = ((-1, -1), (-1, 0), (-1, 1), (0, -1))

    for linha in range(altura):
        for coluna in range(largura):
            if not mascara[linha, coluna]:
                continue

            candidatos = []
            for dl, dc in vizinhos:
                vl, vc = linha + dl, coluna + dc
                if 0 <= vl < altura and 0 <= vc < largura and rotulos[vl, vc] != 0:
                    candidatos.append(int(rotulos[vl, vc]))

            if not candidatos:
                conjuntos.criar(proximo)
                rotulos[linha, coluna] = proximo
                proximo += 1
                continue

            menor = min(candidatos)
            rotulos[linha, coluna] = menor
            for outro in candidatos:
                conjuntos.unir(menor, outro)

    if proximo == 1:
        return rotulos, 0

    resolvidos = {etiqueta: conjuntos.buscar(etiqueta) for etiqueta in range(1, proximo)}
    finais = sorted(set(resolvidos.values()))
    renumerado = {raiz: indice for indice, raiz in enumerate(finais, start=1)}

    tabela = np.zeros(proximo, dtype=np.int32)
    for etiqueta, raiz in resolvidos.items():
        tabela[etiqueta] = renumerado[raiz]

    return tabela[rotulos], len(finais)


def descrever_regioes(rotulos: np.ndarray, quantidade: int | None = None) -> list[Regiao]:
    """Extrai área, centroide e caixa delimitadora de cada região rotulada."""
    if rotulos.ndim != 2:
        raise ValueError(f"rótulos devem ser 2D, recebido {rotulos.shape}")

    if quantidade is None:
        quantidade = int(rotulos.max())
    if quantidade == 0:
        return []

    regioes: list[Regiao] = []
    for rotulo in range(1, quantidade + 1):
        linhas, colunas = np.nonzero(rotulos == rotulo)
        if linhas.size == 0:
            continue
        regioes.append(
            Regiao(
                rotulo=rotulo,
                area_pixels=int(linhas.size),
                centroide=(float(linhas.mean()), float(colunas.mean())),
                caixa=(
                    int(linhas.min()),
                    int(colunas.min()),
                    int(linhas.max()) + 1,
                    int(colunas.max()) + 1,
                ),
            )
        )
    return regioes


def filtrar_por_area(
    mascara: np.ndarray,
    area_minima: int = 0,
    area_maxima: int | None = None,
    conectividade: int = 8,
) -> np.ndarray:
    """Descarta regiões fora da faixa de área informada.

    Este é o filtro que separa desmatamento real de ruído residual: uma clareira de
    3 pixels numa imagem Sentinel-2 (10 m/pixel) corresponde a 300 m², abaixo do que
    qualquer sistema de monitoramento considera evento. Filtrar por área é mais honesto
    que erodir repetidamente, porque o critério fica explícito e mensurável.
    """
    if area_minima < 0:
        raise ValueError(f"area_minima não pode ser negativa, recebido {area_minima}")
    if area_maxima is not None and area_maxima < area_minima:
        raise ValueError(
            f"area_maxima ({area_maxima}) não pode ser menor que area_minima ({area_minima})"
        )

    rotulos, quantidade = rotular(mascara, conectividade)
    if quantidade == 0:
        return np.zeros_like(rotulos, dtype=bool)

    resultado = np.zeros_like(rotulos, dtype=bool)
    for regiao in descrever_regioes(rotulos, quantidade):
        if regiao.area_pixels < area_minima:
            continue
        if area_maxima is not None and regiao.area_pixels > area_maxima:
            continue
        resultado |= rotulos == regiao.rotulo

    return resultado


def reconstruir_por_conexao(
    marcadores: np.ndarray, permitido: np.ndarray, conectividade: int = 8
) -> np.ndarray:
    """Reconstrução morfológica: expande os marcadores dentro da máscara permitida.

    Dilata os marcadores repetidamente, mantendo apenas o que cai dentro de
    ``permitido``, até nada mais mudar. O resultado é o conjunto de regiões de
    ``permitido`` que **contêm** ao menos um marcador.

    É assim que a histerese de ``limiar.limiar_duplo`` se completa: os pixels fortes são
    os marcadores, fortes ∪ fracos é o permitido, e só os fracos conectados a algum forte
    sobrevivem.
    """
    marcadores = _validar_mascara(marcadores) > 0.5
    permitido = _validar_mascara(permitido) > 0.5

    if marcadores.shape != permitido.shape:
        raise ValueError(
            f"formatos incompatíveis: marcadores {marcadores.shape}, "
            f"permitido {permitido.shape}"
        )

    elemento = elemento_cruz(3) if conectividade == 4 else elemento_quadrado(3)

    atual = marcadores & permitido
    while True:
        expandido = dilatacao(atual, elemento) & permitido
        if np.array_equal(expandido, atual):
            return atual
        atual = expandido


def mudanca_entre_mascaras(
    antes: np.ndarray, depois: np.ndarray
) -> dict[str, np.ndarray]:
    """Compara duas máscaras de vegetação e classifica a mudança pixel a pixel.

    Coração da abordagem bi-temporal (``docs/ARCHITECTURE.md``): ``perda`` é a máscara de
    desmatamento — onde havia vegetação em T1 e não há mais em T2.

    ``ganho`` (regeneração ou erro de registro) e ``estavel`` acompanham porque servem
    de controle: um ``ganho`` alto demais indica que as duas imagens não estão bem
    alinhadas, ou que a variação sazonal está sendo lida como mudança real.
    """
    antes = _validar_mascara(antes) > 0.5
    depois = _validar_mascara(depois) > 0.5

    if antes.shape != depois.shape:
        raise ValueError(
            f"as duas datas precisam ter o mesmo recorte: antes {antes.shape}, "
            f"depois {depois.shape}"
        )

    return {
        "perda": antes & ~depois,
        "ganho": ~antes & depois,
        "estavel_vegetado": antes & depois,
        "estavel_nao_vegetado": ~antes & ~depois,
    }
```

---

## `sentinela/dataio/imagem.py`

```python
"""Leitura e escrita de imagens — a fronteira entre o disco e os arrays de ``pdi``.

Este é o único lugar do projeto autorizado a usar Pillow. O núcleo de PDI trabalha
exclusivamente com arrays NumPy e não sabe o que é um arquivo — ver `AGENTS.md` §5.

Convenção de fronteira: tudo que **entra** vira ``float32`` em ``[0, 1]``; tudo que
**sai** volta para ``uint8``. A conversão acontece aqui e em nenhum outro lugar.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

from ..pdi.nucleo import ErroImagem, para_float, para_uint8, validar_imagem

EXTENSOES_SUPORTADAS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")


class ErroArquivo(ErroImagem):
    """Falha ao ler ou escrever um arquivo de imagem.

    Herda de ``ErroImagem`` para que a interface possa capturar um tipo só e ainda
    assim distinguir o caso quando precisar.
    """


def carregar(caminho: str | Path, *, cinza: bool = False) -> np.ndarray:
    """Carrega uma imagem do disco como ``float32`` em ``[0, 1]``.

    Devolve ``[H, W]`` com ``cinza=True`` e ``[H, W, 3]`` caso contrário. Canal alfa é
    descartado: transparência não tem significado radiométrico numa cena orbital.

    Levanta ``ErroArquivo`` com mensagem explicativa em vez de deixar vazar o erro do
    Pillow — o enunciado pontua tratamento de erros (p.4, item II.2).
    """
    caminho = Path(caminho)

    if not caminho.exists():
        raise ErroArquivo(f"arquivo não encontrado: {caminho}")
    if not caminho.is_file():
        raise ErroArquivo(f"caminho não é um arquivo: {caminho}")

    try:
        with Image.open(caminho) as arquivo:
            arquivo = arquivo.convert("L" if cinza else "RGB")
            dados = np.array(arquivo)
    except UnidentifiedImageError as erro:
        raise ErroArquivo(
            f"'{caminho.name}' não é uma imagem que o Pillow reconheça. "
            f"Formatos suportados: {', '.join(EXTENSOES_SUPORTADAS)}."
        ) from erro
    except OSError as erro:
        raise ErroArquivo(f"falha ao ler '{caminho}': {erro}") from erro

    if dados.size == 0:
        raise ErroArquivo(f"'{caminho.name}' está vazia (0 pixels)")

    return para_float(dados)


def carregar_par(
    caminho_antes: str | Path, caminho_depois: str | Path, *, cinza: bool = False
) -> tuple[np.ndarray, np.ndarray]:
    """Carrega as duas datas e exige que tenham o mesmo recorte.

    Formas diferentes significam que as cenas não foram recortadas sobre a mesma área.
    Comparar mesmo assim produziria um mapa de desmatamento sem sentido, então o erro
    é levantado aqui, no ponto em que ainda dá para explicar a causa ao usuário.
    """
    antes = carregar(caminho_antes, cinza=cinza)
    depois = carregar(caminho_depois, cinza=cinza)

    if antes.shape != depois.shape:
        raise ErroArquivo(
            f"as duas datas precisam ter o mesmo recorte: "
            f"'{Path(caminho_antes).name}' tem {antes.shape[:2]} e "
            f"'{Path(caminho_depois).name}' tem {depois.shape[:2]}. "
            "Recorte as duas cenas sobre a mesma área antes de comparar."
        )

    return antes, depois


def salvar(caminho: str | Path, imagem: np.ndarray) -> Path:
    """Grava um array em disco, convertendo para ``uint8`` na saída.

    Aceita ``[H, W]`` (cinza), ``[H, W, 3]`` (RGB) e máscara booleana, que vira preto
    e branco. Cria o diretório de destino se ele não existir.
    """
    caminho = Path(caminho)

    if imagem.dtype == np.bool_:
        imagem = imagem.astype(np.float32)

    imagem = validar_imagem(imagem)
    if imagem.ndim == 3 and imagem.shape[2] != 3:
        raise ErroArquivo(
            f"imagem com {imagem.shape[2]} bandas não pode ser salva como RGB; "
            "salve banda a banda ou componha três bandas antes"
        )

    caminho.parent.mkdir(parents=True, exist_ok=True)

    try:
        Image.fromarray(para_uint8(imagem)).save(caminho)
    except (OSError, ValueError) as erro:
        raise ErroArquivo(f"falha ao gravar '{caminho}': {erro}") from erro

    return caminho
```

---

## `sentinela/dataio/geo.py`

```python
"""Metadado geográfico — resolução espacial para converter pixels em hectares.

`rasterio` é **opcional**: ele arrasta o GDAL como dependência nativa e falha de
instalar em máquina sem as bibliotecas de sistema. Sem ele o programa continua
funcionando com PNG/JPEG, perdendo apenas a conversão automática para hectares,
que passa a depender da resolução informada à mão.

Degradação explícita, nunca silenciosa: quem chama recebe ``None`` e sabe por quê.
"""

from __future__ import annotations

from pathlib import Path

try:  # pragma: no cover - depende do ambiente, não da lógica
    import rasterio

    RASTERIO_DISPONIVEL = True
except ImportError:  # pragma: no cover
    rasterio = None
    RASTERIO_DISPONIVEL = False

# Resoluções nominais das bandas ópticas mais usadas em detecção de desmatamento.
RESOLUCOES_CONHECIDAS = {
    "sentinel-2": 10.0,  # bandas B02, B03, B04, B08
    "landsat-8": 30.0,
    "landsat-9": 30.0,
    "cbers-4a": 8.0,  # câmera WPM multiespectral
}


def metros_por_pixel(caminho: str | Path) -> float | None:
    """Lê a resolução espacial do GeoTIFF, em metros por pixel.

    Devolve ``None`` quando `rasterio` não está instalado, quando o arquivo não é
    georreferenciado, ou quando o CRS não é métrico — caso em que o valor do
    transform está em graus e usá-lo como metro daria uma área errada por ordens
    de grandeza.
    """
    if not RASTERIO_DISPONIVEL:
        return None

    caminho = Path(caminho)
    if not caminho.exists():
        return None

    try:
        with rasterio.open(caminho) as cena:
            if cena.crs is None or not cena.crs.is_projected:
                return None
            return float(abs(cena.transform.a))
    except Exception:  # rasterio levanta uma família grande de erros de formato
        return None


def resolucao_do_satelite(nome: str) -> float | None:
    """Resolução nominal de um satélite conhecido, para quando não há GeoTIFF.

    Usado pela interface quando o usuário sobe PNG recortado de um visualizador:
    o pixel continua tendo tamanho real, ele só não está gravado no arquivo.
    """
    return RESOLUCOES_CONHECIDAS.get(nome.strip().lower())


def descrever_origem_da_resolucao(
    metros: float | None, veio_do_arquivo: bool
) -> str:
    """Frase curta dizendo de onde saiu a resolução, para aparecer na evidência.

    Área em hectares sem origem declarada é número solto: na banca, "de onde veio o
    tamanho do pixel?" é pergunta certa.
    """
    if metros is None:
        return "resolução desconhecida — área reportada apenas em pixels"
    if veio_do_arquivo:
        return f"{metros:.2f} m/pixel lidos do metadado geográfico do arquivo"
    return f"{metros:.2f} m/pixel informados manualmente"
```

---

## `sentinela/dataio/visual.py`

```python
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
```

---

## `sentinela/dataio/sintetico.py`

```python
"""Cena **sintética** de floresta — demonstração e teste, nunca evidência.

> **Nenhuma imagem gerada aqui pode aparecer no trabalho escrito como se fosse real.**
> `AGENTS.md` §11 proíbe. A interface rotula toda saída desta origem como sintética,
> e a validação sobre imagem real é requisito à parte (R032).

Existe por dois motivos legítimos: permitir que os testes verifiquem a cadeia completa
contra uma área de corte de tamanho **conhecido**, e permitir demonstrar o programa
antes das cenas reais estarem baixadas.

O modelo radiométrico é o mínimo que torna o NDVI significativo: floresta absorve no
vermelho (clorofila) e reflete forte no infravermelho próximo; solo exposto reflete de
forma parecida nas duas faixas, e o NDVI cai para perto de zero.
"""

from __future__ import annotations

import numpy as np

# Refletâncias aproximadas, em [0, 1]. Valores de ordem de grandeza realista para
# dossel fechado e solo exposto, não medidas de campo.
FLORESTA = {"vermelho": 0.05, "verde": 0.09, "azul": 0.04, "nir": 0.55, "swir": 0.12}
SOLO_EXPOSTO = {"vermelho": 0.33, "verde": 0.30, "azul": 0.24, "nir": 0.37, "swir": 0.34}

# Desvio do ruído gaussiano: variação de dossel somada ao ruído do sensor.
RUIDO_PADRAO = 0.012


def cena_sintetica(
    semente: int,
    corte: tuple[slice, slice] | None = None,
    *,
    tamanho: tuple[int, int] = (80, 80),
    ruido: float = RUIDO_PADRAO,
) -> tuple[np.ndarray, np.ndarray]:
    """Constrói uma cena RGB + NIR imitando floresta, com área de corte opcional.

    ``corte`` é um par de fatias NumPy delimitando a região desmatada; ``None`` produz
    floresta intacta, que é o controle negativo da detecção.

    Devolve ``(rgb, nir)`` — ``[H, W, 3]`` e ``[H, W]``, ambos ``float32`` em ``[0, 1]``.
    """
    gerador = np.random.default_rng(semente)
    altura, largura = tamanho

    vermelho = np.full((altura, largura), FLORESTA["vermelho"], dtype=np.float32)
    verde = np.full((altura, largura), FLORESTA["verde"], dtype=np.float32)
    azul = np.full((altura, largura), FLORESTA["azul"], dtype=np.float32)
    nir = np.full((altura, largura), FLORESTA["nir"], dtype=np.float32)

    if corte is not None:
        vermelho[corte] = SOLO_EXPOSTO["vermelho"]
        verde[corte] = SOLO_EXPOSTO["verde"]
        azul[corte] = SOLO_EXPOSTO["azul"]
        nir[corte] = SOLO_EXPOSTO["nir"]

    perturbar = lambda: gerador.normal(0, ruido, (altura, largura)).astype(np.float32)
    rgb = np.clip(
        np.stack([vermelho + perturbar(), verde + perturbar(), azul + perturbar()], axis=2),
        0,
        1,
    )
    return rgb.astype(np.float32), np.clip(nir + perturbar(), 0, 1).astype(np.float32)


def banda_swir(
    semente: int,
    corte: tuple[slice, slice] | None = None,
    *,
    tamanho: tuple[int, int] = (80, 80),
    ruido: float = RUIDO_PADRAO,
) -> np.ndarray:
    """Banda de infravermelho de ondas curtas, para permitir NDMI na demonstração.

    Fica **fora** de ``cena_sintetica`` de propósito: aquela função tem saída fixada por
    semente e é usada como verdade de terreno em dezenas de testes. Mudar o que ela
    consome do gerador mudaria toda a cena. Aqui o gerador é independente, deslocado por
    um primo para não correlacionar com o ruído das outras bandas.

    Dossel fechado é cheio de água e **absorve** no SWIR; solo exposto e pasto seco
    refletem. É a inversão do NIR, e é o que dá ao NDMI o poder de separar floresta de
    pastagem vigorosa, que o NDVI confunde por serem as duas verdes.
    """
    gerador = np.random.default_rng(semente + 7919)
    altura, largura = tamanho

    swir = np.full((altura, largura), FLORESTA["swir"], dtype=np.float32)
    if corte is not None:
        swir[corte] = SOLO_EXPOSTO["swir"]

    perturbacao = gerador.normal(0, ruido, (altura, largura)).astype(np.float32)
    return np.clip(swir + perturbacao, 0, 1).astype(np.float32)


def par_bitemporal(
    corte: tuple[slice, slice] | None = (slice(30, 50), slice(30, 50)),
    *,
    semente: int = 101,
    tamanho: tuple[int, int] = (80, 80),
) -> dict[str, np.ndarray | int]:
    """Par de datas da mesma área sintética: T1 intacta, T2 com o corte aplicado.

    ``corte=None`` devolve duas datas de floresta intacta — o caso que o sistema
    precisa classificar como *não confiável* em vez de inventar desmatamento.

    ``area_esperada`` é a contagem exata de pixels do corte construído, o que permite
    comparar a detecção contra a verdade de terreno nos testes.
    """
    rgb_antes, nir_antes = cena_sintetica(semente, tamanho=tamanho)
    rgb_depois, nir_depois = cena_sintetica(semente + 101, corte=corte, tamanho=tamanho)

    if corte is None:
        area = 0
    else:
        marcador = np.zeros(tamanho, dtype=bool)
        marcador[corte] = True
        area = int(marcador.sum())

    return {
        "rgb_antes": rgb_antes,
        "nir_antes": nir_antes,
        "swir_antes": banda_swir(semente, tamanho=tamanho),
        "rgb_depois": rgb_depois,
        "nir_depois": nir_depois,
        "swir_depois": banda_swir(semente + 101, corte=corte, tamanho=tamanho),
        "area_esperada": area,
    }
```

---

## `sentinela/pipeline/deteccao.py`

```python
"""Orquestração das cinco etapas do enunciado (p.3, item 2.e).

```text
Aquisição  →  Manipulação  →  Filtragem  →  Segmentação  →  Modelo
dataio/       pdi/cor       pdi/filtros    pdi/limiar        modelo/
                                           pdi/morfologia
                                           pdi/segmentacao
```

Este módulo não implementa nenhum algoritmo: ele encadeia os que estão em ``pdi/`` e
guarda **todos os intermediários**, porque a interface precisa exibir etapa por etapa e
o trabalho escrito precisa mostrar o efeito de cada filtro (R033).

A decisão que mais importa aqui está em ``docs/decisions/003-limiar-bitemporal.md``: o
limiar é **único** para as duas datas. Otsu por data daria a cada uma uma régua
diferente, e a diferença entre as máscaras mediria a diferença entre os limiares, não a
mudança no terreno.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..pdi import cor, filtros, limiar, morfologia, segmentacao
from ..pdi.nucleo import ErroImagem, validar_imagem
from ..pdi.segmentacao import Regiao

# Acima desta razão ganho/perda, as duas datas provavelmente não estão alinhadas, ou a
# variação sazonal está sendo lida como mudança real. Regeneração de vegetação existe,
# mas no intervalo de meses de um par bi-temporal ela não compete em área com o corte.
PROPORCAO_GANHO_SUSPEITA = 0.5

# Fragmentos abaixo disto são resíduo de segmentação, não evento. A 10 m/pixel do
# Sentinel-2, 25 pixels = 2.500 m² = 0,25 ha.
AREA_MINIMA_PADRAO = 25


@dataclass(frozen=True)
class ResultadoDeteccao:
    """Saída completa de uma detecção, com todos os intermediários preservados.

    ``perda`` é a máscara de desmatamento já filtrada por área. Ela **existe mesmo
    quando ``confiavel`` é falso** — descartá-la esconderia do usuário o que o
    algoritmo fez. Mas nesse caso a área não deve ser reportada como resultado: ver
    ``resumo()``, que devolve ``None`` no lugar do número.
    """

    metodo_indice: str
    valor_limiar: float
    confiavel: bool
    metricas: dict[str, float]

    indice_antes: np.ndarray
    indice_depois: np.ndarray
    vegetacao_antes: np.ndarray
    vegetacao_depois: np.ndarray
    mudanca: dict[str, np.ndarray]
    perda: np.ndarray
    rotulos: np.ndarray
    regioes: list[Regiao]

    metros_por_pixel: float | None = None
    parametros: dict[str, object] = field(default_factory=dict)

    @property
    def area_pixels(self) -> int:
        """Área desmatada total, em pixels."""
        return int(self.perda.sum())

    @property
    def area_hectares(self) -> float | None:
        """Área desmatada em hectares, ou ``None`` sem resolução espacial conhecida."""
        if self.metros_por_pixel is None:
            return None
        return self.area_pixels * (self.metros_por_pixel**2) / 10_000.0

    @property
    def proporcao_da_cena(self) -> float:
        """Fração da cena classificada como desmatamento, em ``[0, 1]``."""
        return float(self.perda.sum() / self.perda.size)

    @property
    def alerta_de_registro(self) -> bool:
        """Verdadeiro quando o ganho de vegetação é alto demais para ser plausível.

        Controle de sanidade: as duas datas podem estar desalinhadas, ou a diferença
        pode ser sazonal. Não invalida o resultado sozinho — pede inspeção visual.
        """
        perdidos = float(self.mudanca["perda"].sum())
        if perdidos == 0:
            return bool(self.mudanca["ganho"].sum() > 0)
        return float(self.mudanca["ganho"].sum()) / perdidos > PROPORCAO_GANHO_SUSPEITA

    def resumo(self) -> dict[str, object]:
        """Números prontos para relatório — sem área quando a detecção não é confiável.

        Cena homogênea não tem duas classes para separar: o limiar automático corta o
        ruído do dossel ao meio e produziria uma área de desmatamento inexistente.
        Devolver ``None`` ali é a resposta correta, não uma falha.
        """
        reportavel = self.confiavel
        return {
            "confiavel": self.confiavel,
            "metodo_indice": self.metodo_indice,
            "limiar": round(self.valor_limiar, 4),
            "distinguibilidade": round(self.metricas["distinguibilidade"], 3),
            "separabilidade_otsu": round(self.metricas["separabilidade"], 4),
            "area_pixels": self.area_pixels if reportavel else None,
            "area_hectares": (
                round(self.area_hectares, 3)
                if reportavel and self.area_hectares is not None
                else None
            ),
            "proporcao_da_cena": round(self.proporcao_da_cena, 5) if reportavel else None,
            "regioes_detectadas": len(self.regioes) if reportavel else None,
            "alerta_de_registro": self.alerta_de_registro,
        }


def preparar_indice(
    rgb: np.ndarray,
    infravermelho: np.ndarray | None = None,
    *,
    metodo: str = "auto",
    suavizacao: int = 5,
    swir: np.ndarray | None = None,
) -> tuple[np.ndarray, str]:
    """Etapas 2 e 3: índice de vegetação, normalizado para ``[0, 1]`` e suavizado.

    A suavização vem **antes** da limiarização de propósito. Sem ela, o ruído do sensor
    atravessa o limiar pixel a pixel e a máscara sai esburacada, o que multiplica
    regiões conexas e inviabiliza a contagem por área.

    Devolve ``(indice_suavizado, nome_do_metodo)``.
    """
    indice, nome = cor.indice_vegetacao(rgb, infravermelho, metodo=metodo, swir=swir)
    unitario = cor.para_faixa_unitaria(indice)

    if suavizacao <= 1:
        return unitario, nome

    return filtros.gaussiano(unitario, tamanho=suavizacao), nome


def detectar_desmatamento(
    rgb_antes: np.ndarray,
    rgb_depois: np.ndarray,
    nir_antes: np.ndarray | None = None,
    nir_depois: np.ndarray | None = None,
    *,
    swir_antes: np.ndarray | None = None,
    swir_depois: np.ndarray | None = None,
    metodo: str = "auto",
    suavizacao: int = 5,
    area_minima: int = AREA_MINIMA_PADRAO,
    metros_por_pixel: float | None = None,
    limpar_mascara: bool = True,
) -> ResultadoDeteccao:
    """Executa a cadeia completa sobre um par bi-temporal da mesma área.

    ``rgb_antes`` e ``rgb_depois`` são a mesma região em duas datas, já recortadas sobre
    o mesmo extent. As bandas infravermelhas são opcionais: havendo as duas, usa-se
    NDVI; faltando, o sistema degrada para VARI, que trabalha só com o visível.

    Levanta ``ErroImagem`` quando as entradas são incompatíveis — checar aqui é o que
    evita um mapa de desmatamento sem sentido lá na frente (R036).
    """
    rgb_antes = validar_imagem(rgb_antes, bandas_aceitas=(3,))
    rgb_depois = validar_imagem(rgb_depois, bandas_aceitas=(3,))

    if rgb_antes.shape != rgb_depois.shape:
        raise ErroImagem(
            f"as duas datas precisam ter o mesmo recorte: antes {rgb_antes.shape[:2]}, "
            f"depois {rgb_depois.shape[:2]}"
        )

    if (nir_antes is None) != (nir_depois is None):
        raise ErroImagem(
            "infravermelho precisa estar presente nas duas datas ou em nenhuma: "
            "usar NDVI numa data e VARI na outra compara índices de escalas diferentes"
        )

    if (swir_antes is None) != (swir_depois is None):
        raise ErroImagem(
            "SWIR precisa estar presente nas duas datas ou em nenhuma: o NDMI de uma "
            "data não é comparável ao NDVI da outra"
        )

    for nome, banda in (
        ("nir_antes", nir_antes),
        ("nir_depois", nir_depois),
        ("swir_antes", swir_antes),
        ("swir_depois", swir_depois),
    ):
        if banda is not None and banda.shape[:2] != rgb_antes.shape[:2]:
            raise ErroImagem(
                f"'{nome}' tem formato {banda.shape[:2]}, diferente do RGB "
                f"{rgb_antes.shape[:2]}"
            )

    if area_minima < 0:
        raise ErroImagem(f"area_minima não pode ser negativa, recebido {area_minima}")
    if metros_por_pixel is not None and metros_por_pixel <= 0:
        raise ErroImagem(
            f"metros_por_pixel deve ser positivo, recebido {metros_por_pixel}"
        )

    # Etapas 2 e 3 — manipulação e filtragem.
    indice_antes, nome_metodo = preparar_indice(
        rgb_antes, nir_antes, metodo=metodo, suavizacao=suavizacao, swir=swir_antes
    )
    indice_depois, _ = preparar_indice(
        rgb_depois, nir_depois, metodo=metodo, suavizacao=suavizacao, swir=swir_depois
    )

    # Etapa 4 — segmentação, com régua única para as duas datas.
    valor, confiavel, metricas = limiar.limiar_confiavel(indice_antes, indice_depois)

    vegetacao_antes = limiar.binarizar(indice_antes, valor)
    vegetacao_depois = limiar.binarizar(indice_depois, valor)

    if limpar_mascara:
        limpar = lambda m: morfologia.fechamento(morfologia.abertura(m))
        vegetacao_antes = limpar(vegetacao_antes)
        vegetacao_depois = limpar(vegetacao_depois)

    mudanca = segmentacao.mudanca_entre_mascaras(vegetacao_antes, vegetacao_depois)
    perda = segmentacao.filtrar_por_area(mudanca["perda"], area_minima=area_minima)

    rotulos, quantidade = segmentacao.rotular(perda)
    regioes = sorted(
        segmentacao.descrever_regioes(rotulos, quantidade),
        key=lambda regiao: regiao.area_pixels,
        reverse=True,
    )

    return ResultadoDeteccao(
        metodo_indice=nome_metodo,
        valor_limiar=valor,
        confiavel=confiavel,
        metricas=metricas,
        indice_antes=indice_antes,
        indice_depois=indice_depois,
        vegetacao_antes=vegetacao_antes,
        vegetacao_depois=vegetacao_depois,
        mudanca=mudanca,
        perda=perda,
        rotulos=rotulos,
        regioes=regioes,
        metros_por_pixel=metros_por_pixel,
        parametros={
            "metodo": metodo,
            "suavizacao": suavizacao,
            "area_minima": area_minima,
            "limpar_mascara": limpar_mascara,
        },
    )
```

---

## `sentinela/pipeline/amostras.py`

```python
"""Extração de amostras rotuladas — a etapa que o objetivo do enunciado nomeia.

> "produzindo dados preparados que possam alimentar um modelo de visão computacional"
> — enunciado, p.2

É aqui que o PDI deixa de ser um fim e vira **preparação de dados** (R034). A máscara
de desmatamento produzida por ``deteccao`` serve de rótulo: cada recorte da imagem
recebe a classe da região que ele cobre, e o conjunto resultante é o que alimenta o
classificador em ``modelo/``.

Recortes ambíguos — que pegam parte de área desmatada e parte de floresta — são
**descartados**, não arredondados para a classe majoritária. Rotular a borda de um
corte como "desmatado" ensina o classificador a responder pela vizinhança em vez de
pelo conteúdo, e o erro só aparece depois, na matriz de confusão.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..pdi.nucleo import ErroImagem, validar_imagem

INTACTO = 0
DESMATADO = 1

# Um recorte só é rotulado quando é majoritariamente de uma classe. Entre os dois
# limites fica a zona ambígua, descartada.
COBERTURA_PARA_DESMATADO = 0.60
COBERTURA_PARA_INTACTO = 0.05


@dataclass(frozen=True)
class ConjuntoDeAmostras:
    """Recortes rotulados, prontos para o classificador.

    ``recortes`` tem formato ``[N, lado, lado, bandas]``; ``rotulos`` tem ``[N]``, com
    ``INTACTO``/``DESMATADO``. ``posicoes`` guarda o canto superior esquerdo de cada
    recorte na imagem original, para que qualquer amostra possa ser reencontrada na
    cena — sem isso não há como auditar um erro do modelo.
    """

    recortes: np.ndarray
    rotulos: np.ndarray
    posicoes: list[tuple[int, int]]
    descartados_ambiguos: int

    def __len__(self) -> int:
        return int(self.rotulos.size)

    @property
    def contagem_por_classe(self) -> dict[int, int]:
        return {
            INTACTO: int((self.rotulos == INTACTO).sum()),
            DESMATADO: int((self.rotulos == DESMATADO).sum()),
        }

    @property
    def equilibrio(self) -> float:
        """Razão entre a classe minoritária e a majoritária, em ``[0, 1]``.

        Perto de 0 significa conjunto desbalanceado: um classificador que responde
        sempre a classe majoritária teria acurácia alta e utilidade nenhuma.
        """
        contagens = list(self.contagem_por_classe.values())
        if max(contagens) == 0:
            return 0.0
        return min(contagens) / max(contagens)

    def resumo(self) -> dict[str, object]:
        contagens = self.contagem_por_classe
        return {
            "total": len(self),
            "intacto": contagens[INTACTO],
            "desmatado": contagens[DESMATADO],
            "equilibrio": round(self.equilibrio, 3),
            "descartados_ambiguos": self.descartados_ambiguos,
            "formato_do_recorte": tuple(self.recortes.shape[1:])
            if len(self)
            else None,
        }


def extrair_amostras(
    imagem: np.ndarray,
    mascara_desmatamento: np.ndarray,
    *,
    lado: int = 16,
    passo: int | None = None,
    cobertura_desmatado: float = COBERTURA_PARA_DESMATADO,
    cobertura_intacto: float = COBERTURA_PARA_INTACTO,
) -> ConjuntoDeAmostras:
    """Varre a imagem em janelas e rotula cada recorte pela máscara de desmatamento.

    ``passo`` menor que ``lado`` faz as janelas se sobreporem, o que aumenta a
    quantidade de amostras sem precisar de mais cena — útil porque um par bi-temporal
    de uma área pequena rende poucas janelas disjuntas. O padrão é ``lado // 2``.
    """
    imagem = validar_imagem(imagem)
    mascara = np.asarray(mascara_desmatamento) > 0.5

    if imagem.ndim == 2:
        imagem = imagem[:, :, None]

    if mascara.shape != imagem.shape[:2]:
        raise ErroImagem(
            f"máscara {mascara.shape} não corresponde à imagem {imagem.shape[:2]}"
        )
    if lado < 2:
        raise ErroImagem(f"lado do recorte deve ser ao menos 2, recebido {lado}")

    altura, largura = imagem.shape[:2]
    if lado > altura or lado > largura:
        raise ErroImagem(
            f"recorte de {lado}x{lado} não cabe numa imagem de {altura}x{largura}"
        )

    if not 0.0 <= cobertura_intacto < cobertura_desmatado <= 1.0:
        raise ErroImagem(
            "limiares de cobertura inválidos: é preciso "
            f"0 <= intacto ({cobertura_intacto}) < desmatado ({cobertura_desmatado}) <= 1"
        )

    passo = lado // 2 if passo is None else passo
    if passo < 1:
        raise ErroImagem(f"passo deve ser ao menos 1, recebido {passo}")

    recortes: list[np.ndarray] = []
    rotulos: list[int] = []
    posicoes: list[tuple[int, int]] = []
    ambiguos = 0

    for linha in range(0, altura - lado + 1, passo):
        for coluna in range(0, largura - lado + 1, passo):
            janela = mascara[linha : linha + lado, coluna : coluna + lado]
            cobertura = float(janela.mean())

            if cobertura >= cobertura_desmatado:
                rotulo = DESMATADO
            elif cobertura <= cobertura_intacto:
                rotulo = INTACTO
            else:
                ambiguos += 1
                continue

            recortes.append(imagem[linha : linha + lado, coluna : coluna + lado])
            rotulos.append(rotulo)
            posicoes.append((linha, coluna))

    if not recortes:
        return ConjuntoDeAmostras(
            recortes=np.empty((0, lado, lado, imagem.shape[2]), dtype=np.float32),
            rotulos=np.empty(0, dtype=np.int64),
            posicoes=[],
            descartados_ambiguos=ambiguos,
        )

    return ConjuntoDeAmostras(
        recortes=np.stack(recortes).astype(np.float32),
        rotulos=np.array(rotulos, dtype=np.int64),
        posicoes=posicoes,
        descartados_ambiguos=ambiguos,
    )


def equilibrar(
    conjunto: ConjuntoDeAmostras, *, semente: int = 0
) -> ConjuntoDeAmostras:
    """Reduz a classe majoritária ao tamanho da minoritária, por sorteio.

    Numa cena típica a floresta domina — 95% de amostras intactas não é incomum. Sem
    equilibrar, o classificador aprende a responder "intacto" sempre e acerta 95%,
    métrica que não significa nada. A subamostragem é o tratamento mais simples e o
    único que não inventa dado novo.
    """
    contagens = conjunto.contagem_por_classe
    alvo = min(contagens.values())

    if alvo == 0 or len(conjunto) == 0:
        return conjunto

    gerador = np.random.default_rng(semente)
    escolhidos: list[int] = []

    for classe in (INTACTO, DESMATADO):
        indices = np.nonzero(conjunto.rotulos == classe)[0]
        escolhidos.extend(gerador.choice(indices, size=alvo, replace=False).tolist())

    escolhidos.sort()
    return ConjuntoDeAmostras(
        recortes=conjunto.recortes[escolhidos],
        rotulos=conjunto.rotulos[escolhidos],
        posicoes=[conjunto.posicoes[i] for i in escolhidos],
        descartados_ambiguos=conjunto.descartados_ambiguos,
    )
```

---

## `sentinela/modelo/caracteristicas.py`

```python
"""Descritores extraídos de cada recorte — a ponte entre o PDI e o classificador.

Etapa 5 do enunciado (p.3, item 2.e.v e 3.b). Cada recorte rotulado por
``pipeline.extrair_amostras`` vira um vetor de números que o classificador consegue
comparar.

**Todas as features saem de `pdi/`**, o núcleo implementado pelo grupo: não há descritor
vindo pronto de biblioteca. Isso mantém a exigência do enunciado de ponta a ponta — se o
professor perguntar de onde vem a textura, a resposta é `pdi.filtros.desvio_padrao_local`,
e o algoritmo está no repositório.

A escolha das features é deliberadamente **explicável**. Um descritor profundo daria
acurácia maior, mas o grupo precisa saber defender por que cada número existe
(`AGENTS.md` §12).

## Limitação conhecida das features de textura

`textura_media` e `textura_maxima` são justificadas pela literatura — dossel fechado é
irregular e produz desvio local alto, solo exposto e pasto são lisos e produzem desvio
baixo. **Na cena sintética isso não é observável**, porque o gerador aplica o mesmo
desvio de ruído às duas classes. Elas continuam no vetor porque devem separar em imagem
real, mas até R032 essa é uma hipótese, não um resultado. Não apresentar como validada.
"""

from __future__ import annotations

import numpy as np

from ..pdi import cor, filtros
from ..pdi.nucleo import ErroImagem, validar_imagem

# Vizinhança das medidas de textura. 5×5 num recorte de 16×16 cobre área suficiente
# para capturar a irregularidade do dossel sem virar estatística da imagem inteira.
JANELA_TEXTURA = 5

NOMES_DAS_FEATURES = (
    "media_vermelho",
    "media_verde",
    "media_azul",
    "desvio_vermelho",
    "desvio_verde",
    "desvio_azul",
    "media_exg",
    "desvio_exg",
    "media_vari",
    "textura_media",
    "textura_maxima",
    "borda_media",
    "brilho_p10",
    "brilho_mediana",
    "brilho_p90",
)


def descrever_recorte(recorte: np.ndarray) -> np.ndarray:
    """Extrai o vetor de características de **um** recorte RGB.

    A ordem dos valores corresponde a ``NOMES_DAS_FEATURES`` — a correspondência importa
    porque é ela que permite dizer, no trabalho escrito, qual medida o classificador
    considerou mais informativa.
    """
    recorte = validar_imagem(recorte, bandas_aceitas=(3,))

    cinza = cor.para_cinza(recorte)
    indice_exg = cor.exg(recorte)
    indice_vari = cor.vari(recorte)

    # Textura: floresta tem dossel irregular e desvio local alto; solo exposto e pasto
    # são homogêneos. Sozinha esta medida já separa razoavelmente as duas classes.
    textura = filtros.desvio_padrao_local(cinza, tamanho=JANELA_TEXTURA)

    # Borda: a fronteira entre floresta e corte produz gradiente forte.
    borda = filtros.magnitude_gradiente(cinza)

    return np.array(
        [
            recorte[:, :, 0].mean(),
            recorte[:, :, 1].mean(),
            recorte[:, :, 2].mean(),
            recorte[:, :, 0].std(),
            recorte[:, :, 1].std(),
            recorte[:, :, 2].std(),
            indice_exg.mean(),
            indice_exg.std(),
            indice_vari.mean(),
            textura.mean(),
            textura.max(),
            borda.mean(),
            np.percentile(cinza, 10),
            np.percentile(cinza, 50),
            np.percentile(cinza, 90),
        ],
        dtype=np.float32,
    )


def extrair_caracteristicas(recortes: np.ndarray) -> np.ndarray:
    """Transforma ``[N, lado, lado, 3]`` em ``[N, 15]``.

    Devolve matriz vazia com a quantidade certa de colunas quando não há recorte
    nenhum — assim quem chama não precisa tratar o caso vazio de forma diferente.
    """
    recortes = np.asarray(recortes)

    if recortes.ndim != 4:
        raise ErroImagem(
            f"esperado [N, lado, lado, bandas], recebido formato {recortes.shape}"
        )
    if recortes.shape[0] == 0:
        return np.empty((0, len(NOMES_DAS_FEATURES)), dtype=np.float32)
    if recortes.shape[3] != 3:
        raise ErroImagem(
            f"as features assumem recorte RGB; recebido {recortes.shape[3]} bandas"
        )

    return np.stack([descrever_recorte(recorte) for recorte in recortes]).astype(
        np.float32
    )
```

---

## `sentinela/modelo/classificador.py`

```python
"""Classificador de desmatamento sobre os recortes rotulados.

Etapa 5 — item 3.b do enunciado. Recebe o conjunto produzido por
``pipeline.extrair_amostras``, descreve cada recorte com ``caracteristicas`` e treina um
classificador do scikit-learn.

`scikit-learn` é permitido **aqui** (`AGENTS.md` §5): a restrição de implementação
própria vale para os filtros, não para o algoritmo de aprendizado. As features, essas
sim, saem todas do núcleo do grupo.

Floresta aleatória foi escolhida por ser defensável numa banca: ela informa quais
features pesaram na decisão, o que permite responder "por que o modelo classificou este
recorte como desmatado?" apontando para uma medida concreta. Uma rede convolucional
daria acurácia maior e nenhuma resposta a essa pergunta.

## A divisão espacial

O ponto metodológico que mais afeta o resultado está em ``dividir_espacialmente``. Os
recortes se sobrepõem, porque a varredura usa passo menor que o lado. Uma divisão
aleatória entre treino e teste colocaria **o mesmo pixel nos dois lados**, e a acurácia
medida seria fantasia. A divisão por faixa da imagem, com uma faixa-tampão descartada
entre elas, é o que torna a métrica honesta.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..pipeline.amostras import DESMATADO, INTACTO, ConjuntoDeAmostras
from .caracteristicas import NOMES_DAS_FEATURES, extrair_caracteristicas

# Abaixo disto a métrica de teste é ruído: com 10 amostras, um acerto a mais move a
# acurácia em 10 pontos. O número não é omitido, mas vem acompanhado de aviso.
AMOSTRAS_MINIMAS_PARA_METRICA = 20


class ErroModelo(RuntimeError):
    """Uso inválido do classificador — treino sem dado, previsão sem treino."""


@dataclass(frozen=True)
class Avaliacao:
    """Resultado de uma avaliação, com os avisos que o número sozinho esconde."""

    acuracia: float
    precisao: float
    revocacao: float
    f1: float
    matriz_confusao: np.ndarray
    total_teste: int
    avisos: tuple[str, ...] = ()

    def resumo(self) -> dict[str, object]:
        verdadeiro_negativo, falso_positivo, falso_negativo, verdadeiro_positivo = (
            self.matriz_confusao.ravel()
        )
        return {
            "acuracia": round(self.acuracia, 4),
            "precisao": round(self.precisao, 4),
            "revocacao": round(self.revocacao, 4),
            "f1": round(self.f1, 4),
            "amostras_de_teste": self.total_teste,
            "matriz_confusao": {
                "intacto_correto": int(verdadeiro_negativo),
                "falso_alarme": int(falso_positivo),
                "desmatamento_perdido": int(falso_negativo),
                "desmatamento_correto": int(verdadeiro_positivo),
            },
            "avisos": list(self.avisos),
        }


def dividir_espacialmente(
    conjunto: ConjuntoDeAmostras,
    *,
    proporcao_teste: float = 0.3,
    tamanho_bloco: int | None = None,
    semente: int = 0,
) -> tuple[ConjuntoDeAmostras, ConjuntoDeAmostras]:
    """Separa treino e teste por **blocos da imagem**, não por sorteio de recorte.

    A varredura usa passo menor que o lado do recorte, então recortes vizinhos
    compartilham pixels. Sortear recortes individualmente colocaria o mesmo pedaço de
    terreno nos dois conjuntos, e a acurácia medida seria vazamento, não generalização.

    Aqui a imagem é dividida em blocos quadrados, o **bloco** é sorteado para treino ou
    teste, e só entram recortes que cabem inteiros dentro de um bloco. Como os blocos são
    disjuntos, nenhum recorte de treino compartilha um pixel com um recorte de teste.

    O sorteio por bloco — em vez de um corte único ao meio — importa porque desmatamento
    costuma ser espacialmente concentrado: um corte único tende a deixar toda a área
    desmatada de um lado só, e o conjunto de teste fica com uma classe única.

    Recortes que cruzam fronteira de bloco são descartados. É o preço da separação.
    """
    if not 0.0 < proporcao_teste < 1.0:
        raise ErroModelo(
            f"proporcao_teste deve estar em (0, 1), recebido {proporcao_teste}"
        )
    if len(conjunto) == 0:
        return conjunto, conjunto

    lado = int(conjunto.recortes.shape[1])
    bloco = tamanho_bloco if tamanho_bloco is not None else 3 * lado

    if bloco < lado:
        raise ErroModelo(
            f"tamanho_bloco ({bloco}) precisa ser ao menos o lado do recorte ({lado})"
        )

    # Só entram recortes que cabem inteiros num bloco; os que cruzam fronteira sairiam
    # parcialmente para o outro conjunto e reintroduziriam o vazamento.
    dentro = [
        indice
        for indice, (linha, coluna) in enumerate(conjunto.posicoes)
        if linha % bloco + lado <= bloco and coluna % bloco + lado <= bloco
    ]

    blocos = sorted(
        {
            (conjunto.posicoes[i][0] // bloco, conjunto.posicoes[i][1] // bloco)
            for i in dentro
        }
    )
    if len(blocos) < 2:
        raise ErroModelo(
            f"a cena rende {len(blocos)} bloco(s) de {bloco}x{bloco} px — não dá para "
            "separar treino de teste sem compartilhar terreno. Use uma imagem maior, um "
            "recorte menor, ou reduza tamanho_bloco."
        )

    gerador = np.random.default_rng(semente)
    embaralhados = list(blocos)
    gerador.shuffle(embaralhados)
    quantidade_teste = max(1, round(len(blocos) * proporcao_teste))
    blocos_de_teste = set(map(tuple, embaralhados[:quantidade_teste]))

    def fatiar(indices: list[int]) -> ConjuntoDeAmostras:
        return ConjuntoDeAmostras(
            recortes=conjunto.recortes[indices],
            rotulos=conjunto.rotulos[indices],
            posicoes=[conjunto.posicoes[i] for i in indices],
            descartados_ambiguos=conjunto.descartados_ambiguos,
        )

    def no_teste(indice: int) -> bool:
        linha, coluna = conjunto.posicoes[indice]
        return (linha // bloco, coluna // bloco) in blocos_de_teste

    return (
        fatiar([i for i in dentro if not no_teste(i)]),
        fatiar([i for i in dentro if no_teste(i)]),
    )


class ClassificadorDesmatamento:
    """Envolve o classificador do scikit-learn com as regras deste projeto.

    Mantém a lista de nomes das features junto do modelo treinado, para que a
    importância relatada possa ser lida sem consultar outro arquivo.
    """

    def __init__(self, *, arvores: int = 100, semente: int = 0, profundidade: int | None = None):
        try:
            from sklearn.ensemble import RandomForestClassifier
        except ImportError as erro:  # pragma: no cover - depende do ambiente
            raise ErroModelo(
                "a etapa de modelo requer scikit-learn. Instale o extra:\n"
                '  pip install -e ".[modelo]"'
            ) from erro

        self._modelo = RandomForestClassifier(
            n_estimators=arvores,
            max_depth=profundidade,
            random_state=semente,
            class_weight="balanced",
        )
        self._treinado = False
        self.nomes_das_features = NOMES_DAS_FEATURES

    @property
    def treinado(self) -> bool:
        return self._treinado

    def treinar(self, conjunto: ConjuntoDeAmostras) -> "ClassificadorDesmatamento":
        """Ajusta o modelo. Exige as duas classes presentes."""
        if len(conjunto) == 0:
            raise ErroModelo("não há amostras para treinar")

        contagens = conjunto.contagem_por_classe
        if contagens[INTACTO] == 0 or contagens[DESMATADO] == 0:
            raise ErroModelo(
                f"o treino precisa das duas classes; recebido "
                f"{contagens[INTACTO]} intactas e {contagens[DESMATADO]} desmatadas. "
                "Um classificador treinado numa classe só responde sempre a mesma coisa."
            )

        self._modelo.fit(extrair_caracteristicas(conjunto.recortes), conjunto.rotulos)
        self._treinado = True
        return self

    def prever(self, recortes: np.ndarray) -> np.ndarray:
        """Classe prevista para cada recorte."""
        if not self._treinado:
            raise ErroModelo("o classificador precisa ser treinado antes de prever")
        return self._modelo.predict(extrair_caracteristicas(recortes))

    def probabilidade_de_desmatamento(self, recortes: np.ndarray) -> np.ndarray:
        """Confiança da classe 'desmatado', em ``[0, 1]``.

        Mais útil que a classe crua na apresentação: permite mostrar onde o modelo está
        inseguro em vez de fingir que toda decisão tem o mesmo peso.
        """
        if not self._treinado:
            raise ErroModelo("o classificador precisa ser treinado antes de prever")
        probabilidades = self._modelo.predict_proba(extrair_caracteristicas(recortes))
        indice = list(self._modelo.classes_).index(DESMATADO)
        return probabilidades[:, indice]

    def avaliar(self, conjunto: ConjuntoDeAmostras) -> Avaliacao:
        """Mede o desempenho num conjunto que o modelo não viu.

        Métrica sem aviso é métrica que engana: conjunto pequeno demais ou com uma
        classe só produz número alto que não significa nada, e isso vai declarado.
        """
        if not self._treinado:
            raise ErroModelo("o classificador precisa ser treinado antes de avaliar")
        if len(conjunto) == 0:
            raise ErroModelo("não há amostras para avaliar")

        from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

        previsto = self.prever(conjunto.recortes)
        real = conjunto.rotulos

        precisao, revocacao, f1, _ = precision_recall_fscore_support(
            real, previsto, average="binary", pos_label=DESMATADO, zero_division=0
        )

        avisos: list[str] = []
        if len(conjunto) < AMOSTRAS_MINIMAS_PARA_METRICA:
            avisos.append(
                f"conjunto de teste com {len(conjunto)} amostras — abaixo de "
                f"{AMOSTRAS_MINIMAS_PARA_METRICA}, a métrica é instável"
            )

        acuracia = float((previsto == real).mean())
        if acuracia == 1.0:
            avisos.append(
                "desempenho perfeito — em imagem real isso praticamente não acontece. "
                "Em cena sintética é esperado, porque a separação radiométrica entre as "
                "classes foi construída. Não apresente este número como validação do "
                "modelo sem repetir a medição em imagem real"
            )

        contagens = conjunto.contagem_por_classe
        if contagens[DESMATADO] == 0 or contagens[INTACTO] == 0:
            avisos.append(
                "o conjunto de teste tem uma classe só: a acurácia não distingue um "
                "modelo útil de um que responde sempre a mesma coisa"
            )
        elif conjunto.equilibrio < 0.3:
            avisos.append(
                f"conjunto de teste desbalanceado (equilíbrio {conjunto.equilibrio:.2f}) "
                "— leia a revocação e o F1, não a acurácia"
            )

        return Avaliacao(
            acuracia=acuracia,
            precisao=float(precisao),
            revocacao=float(revocacao),
            f1=float(f1),
            matriz_confusao=confusion_matrix(real, previsto, labels=[INTACTO, DESMATADO]),
            total_teste=len(conjunto),
            avisos=tuple(avisos),
        )

    def importancia_das_features(self) -> list[tuple[str, float]]:
        """Features ordenadas pelo peso que tiveram na decisão, da maior para a menor.

        É o que permite responder "por que o modelo decidiu isso?" na apresentação.
        """
        if not self._treinado:
            raise ErroModelo("o classificador precisa ser treinado antes")
        pares = zip(self.nomes_das_features, self._modelo.feature_importances_)
        return sorted(pares, key=lambda par: par[1], reverse=True)


def treinar_e_avaliar(
    conjunto: ConjuntoDeAmostras,
    *,
    proporcao_teste: float = 0.3,
    semente: int = 0,
) -> tuple[ClassificadorDesmatamento, Avaliacao]:
    """Fluxo completo: divide espacialmente, treina e avalia.

    Devolve ``(classificador, avaliacao)``. A divisão é espacial, nunca aleatória — ver
    ``dividir_espacialmente``.
    """
    treino, teste = dividir_espacialmente(conjunto, proporcao_teste=proporcao_teste)

    if len(treino) == 0 or len(teste) == 0:
        raise ErroModelo(
            f"a divisão espacial deixou treino com {len(treino)} e teste com "
            f"{len(teste)} amostras. A cena é pequena demais para separar as faixas: "
            "use um recorte menor, um passo menor, ou uma imagem maior."
        )

    classificador = ClassificadorDesmatamento(semente=semente).treinar(treino)
    return classificador, classificador.avaliar(teste)
```

---

## `sentinela/app/principal.py`

```python
"""Interface de demonstração — o que roda no seminário (R044, R050).

Streamlit foi escolhido porque a apresentação é ao vivo e o enunciado pede demonstração
do programa: uma tela permite trocar parâmetro e mostrar o efeito na hora, coisa que um
script de terminal não faz sem parecer ensaiado.

A interface não decide nada. Ela chama ``pipeline.detectar_desmatamento`` e exibe os
intermediários que o resultado já carrega. Nenhum algoritmo de PDI mora aqui.

Executar com:

```bash
streamlit run src/sentinela/app/principal.py
```
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import streamlit as st

# Permite `streamlit run src/sentinela/app/principal.py` sem instalar o pacote.
RAIZ_SRC = Path(__file__).resolve().parents[2]
if str(RAIZ_SRC) not in sys.path:
    sys.path.insert(0, str(RAIZ_SRC))

from sentinela.dataio import (  # noqa: E402
    ErroArquivo,
    carregar,
    indice_em_falsa_cor,
    mapa_de_mudanca,
    par_bitemporal,
    resolucao_do_satelite,
    sobrepor_mascara,
)
from sentinela.pdi import filtros  # noqa: E402
from sentinela.pdi.nucleo import ErroImagem, para_uint8  # noqa: E402
from sentinela.pipeline import (  # noqa: E402
    detectar_desmatamento,
    equilibrar,
    extrair_amostras,
)

st.set_page_config(page_title="Sentinela — detecção de desmatamento", layout="wide")


def mostrar(imagem: np.ndarray, legenda: str) -> None:
    """Exibe um array como imagem, convertendo para ``uint8`` na fronteira."""
    if imagem.dtype == np.bool_:
        imagem = imagem.astype(np.float32)
    st.image(para_uint8(imagem), caption=legenda, width="stretch")


def ler_upload(arquivo, *, cinza: bool = False) -> np.ndarray | None:
    """Carrega um arquivo enviado pelo navegador, gravando num temporário."""
    if arquivo is None:
        return None

    destino = Path(st.session_state["_temporarios"]) / arquivo.name
    destino.write_bytes(arquivo.getbuffer())
    return carregar(destino, cinza=cinza)


def barra_lateral() -> dict:
    """Monta os controles e devolve as escolhas do usuário."""
    st.sidebar.title("Sentinela")
    st.sidebar.caption("APS — Processamento de Imagens e Visão Computacional · UNIP 2026/2")

    fonte = st.sidebar.radio(
        "Fonte das imagens",
        ("Cena sintética (demonstração)", "Enviar imagens"),
        help="A cena sintética serve para demonstrar o programa; ela não é evidência.",
    )

    st.sidebar.subheader("Parâmetros do processamento")
    metodo = st.sidebar.selectbox(
        "Índice de vegetação",
        ("auto", "ndvi", "ndmi", "vari", "exg"),
        help=(
            "auto usa NDVI quando há banda infravermelha e VARI quando só há o visível. "
            "O NDMI mede água do dossel em vez de verde e exige banda SWIR — separa "
            "melhor floresta de pastagem, mas não entra no automático porque troca a "
            "grandeza medida."
        ),
    )
    suavizacao = st.sidebar.slider(
        "Suavização gaussiana (lado do kernel)", 1, 15, 5, step=2,
        help="Aplicada antes da limiarização. Sem ela, o ruído do sensor esburaca a máscara.",
    )
    area_minima = st.sidebar.slider(
        "Área mínima da região (pixels)", 0, 400, 25,
        help="Descarta fragmentos residuais da segmentação.",
    )

    st.sidebar.subheader("Escala espacial")
    satelite = st.sidebar.selectbox(
        "Resolução", ("Sentinel-2 (10 m/px)", "Landsat-8/9 (30 m/px)",
                      "CBERS-4A (8 m/px)", "Desconhecida"),
    )
    mapa_resolucao = {
        "Sentinel-2 (10 m/px)": resolucao_do_satelite("sentinel-2"),
        "Landsat-8/9 (30 m/px)": resolucao_do_satelite("landsat-8"),
        "CBERS-4A (8 m/px)": resolucao_do_satelite("cbers-4a"),
        "Desconhecida": None,
    }

    return {
        "fonte": fonte,
        "metodo": metodo,
        "suavizacao": suavizacao,
        "area_minima": area_minima,
        "metros_por_pixel": mapa_resolucao[satelite],
    }


def obter_imagens(opcoes: dict) -> dict | None:
    """Resolve a fonte escolhida em quatro arrays (RGB e NIR das duas datas)."""
    if opcoes["fonte"].startswith("Cena sintética"):
        st.info(
            "**Cena sintética.** Floresta simulada com uma área de corte de tamanho "
            "conhecido, usada para demonstrar o programa e conferir a quantificação. "
            "Não é imagem de satélite e não entra no trabalho escrito como evidência.",
            icon="🧪",
        )
        col1, col2 = st.columns(2)
        lado = col1.slider("Tamanho da cena (pixels)", 40, 200, 80, step=20)
        area = col2.slider("Lado da área desmatada (pixels)", 0, 60, 20, step=5)

        corte = None
        if area > 0:
            inicio = (lado - area) // 2
            corte = (slice(inicio, inicio + area), slice(inicio, inicio + area))

        par = par_bitemporal(corte=corte, tamanho=(lado, lado))
        st.session_state["area_esperada"] = par["area_esperada"]
        return par

    st.session_state.pop("area_esperada", None)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Data 1 — antes**")
        rgb_antes = st.file_uploader("RGB antes", type=["png", "jpg", "jpeg", "tif"])
        nir_antes = st.file_uploader("Infravermelho antes (opcional)",
                                     type=["png", "jpg", "jpeg", "tif"])
        swir_antes = st.file_uploader("SWIR antes (opcional — habilita NDMI)",
                                      type=["png", "jpg", "jpeg", "tif"])
    with col2:
        st.markdown("**Data 2 — depois**")
        rgb_depois = st.file_uploader("RGB depois", type=["png", "jpg", "jpeg", "tif"])
        nir_depois = st.file_uploader("Infravermelho depois (opcional)",
                                      type=["png", "jpg", "jpeg", "tif"])
        swir_depois = st.file_uploader("SWIR depois (opcional — habilita NDMI)",
                                       type=["png", "jpg", "jpeg", "tif"])

    if rgb_antes is None or rgb_depois is None:
        st.warning(
            "Envie as duas datas da **mesma área**, recortadas sobre o mesmo extent. "
            "Sem infravermelho o sistema usa VARI, que trabalha só com o visível.",
            icon="📂",
        )
        return None

    return {
        "rgb_antes": ler_upload(rgb_antes),
        "nir_antes": ler_upload(nir_antes, cinza=True),
        "swir_antes": ler_upload(swir_antes, cinza=True),
        "rgb_depois": ler_upload(rgb_depois),
        "nir_depois": ler_upload(nir_depois, cinza=True),
        "swir_depois": ler_upload(swir_depois, cinza=True),
    }


def painel_resultado(resultado, opcoes: dict) -> None:
    """Cabeçalho com o número que interessa — ou a recusa em produzi-lo."""
    resumo = resultado.resumo()

    if not resultado.confiavel:
        st.error(
            f"**Detecção não confiável — nenhuma área é reportada.**\n\n"
            f"A distinguibilidade entre as duas classes ficou em "
            f"`{resumo['distinguibilidade']}`, abaixo do mínimo de `4.0`. Isso acontece "
            f"quando a cena é homogênea: sem duas classes reais para separar, o limiar "
            f"automático corta o ruído do dossel ao meio e produziria desmatamento onde "
            f"não houve. Recusar o número é a resposta correta.",
            icon="🚫",
        )
    else:
        colunas = st.columns(4)
        colunas[0].metric("Área desmatada", f"{resumo['area_pixels']} px")
        colunas[1].metric(
            "Em hectares",
            f"{resumo['area_hectares']:.2f} ha"
            if resumo["area_hectares"] is not None
            else "—",
            help="Requer resolução espacial conhecida.",
        )
        colunas[2].metric("Regiões detectadas", resumo["regioes_detectadas"])
        colunas[3].metric("Da cena", f"{resumo['proporcao_da_cena'] * 100:.2f}%")

        esperada = st.session_state.get("area_esperada")
        if esperada:
            erro = abs(resumo["area_pixels"] - esperada) / esperada * 100
            st.caption(
                f"Verdade de terreno da cena sintética: **{esperada} px**. "
                f"Detectado: **{resumo['area_pixels']} px** — erro de {erro:.1f}%."
            )

    if resultado.alerta_de_registro:
        st.warning(
            "**Ganho de vegetação alto demais.** As duas datas podem não estar "
            "alinhadas, ou a diferença pode ser sazonal e não desmatamento. "
            "Inspecione o mapa de mudança antes de usar este resultado.",
            icon="⚠️",
        )


def aba_etapas(imagens: dict, resultado, opcoes: dict) -> None:
    """As cinco etapas do enunciado, uma seção cada."""
    st.subheader("1 · Aquisição")
    col1, col2 = st.columns(2)
    with col1:
        mostrar(imagens["rgb_antes"], "Data 1 — antes")
    with col2:
        mostrar(imagens["rgb_depois"], "Data 2 — depois")

    st.subheader("2 · Manipulação — índice de vegetação")
    st.caption(
        f"Índice em uso: **{resultado.metodo_indice.upper()}**. "
        "Verde = vegetação densa, marrom = solo exposto."
    )
    col1, col2 = st.columns(2)
    with col1:
        mostrar(indice_em_falsa_cor(resultado.indice_antes), "Índice — antes")
    with col2:
        mostrar(indice_em_falsa_cor(resultado.indice_depois), "Índice — depois")

    st.subheader("3 · Filtragem")
    st.caption(
        "Filtros implementados pelo grupo, com NumPy puro — exigência do enunciado "
        "(p.3, item 3.a). Nenhuma chamada a OpenCV ou scikit-image."
    )
    col1, col2, col3 = st.columns(3)
    bruto, _ = _indice_sem_suavizar(imagens, opcoes)
    with col1:
        mostrar(bruto, "Índice bruto")
    with col2:
        mostrar(resultado.indice_depois, f"Gaussiano {opcoes['suavizacao']}×{opcoes['suavizacao']}")
    with col3:
        mostrar(filtros.magnitude_gradiente(resultado.indice_depois), "Sobel — magnitude do gradiente")

    st.subheader("4 · Segmentação")
    st.caption(
        f"Limiar de Otsu **único** para as duas datas: `{resultado.valor_limiar:.4f}`. "
        "Calcular um limiar por data daria réguas diferentes, e a comparação mediria a "
        "diferença entre os limiares, não a mudança no terreno."
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        mostrar(resultado.vegetacao_antes, "Vegetação — antes")
    with col2:
        mostrar(resultado.vegetacao_depois, "Vegetação — depois")
    with col3:
        mostrar(mapa_de_mudanca(resultado.mudanca), "Mapa de mudança")

    st.markdown(
        "<small>🟥 perda de vegetação &nbsp;·&nbsp; 🟩 ganho &nbsp;·&nbsp; "
        "🌲 vegetação estável &nbsp;·&nbsp; ⬜ solo exposto nas duas datas</small>",
        unsafe_allow_html=True,
    )


def _indice_sem_suavizar(imagens: dict, opcoes: dict):
    """Índice cru da segunda data, para a comparação lado a lado da filtragem."""
    from sentinela.pipeline import preparar_indice

    return preparar_indice(
        imagens["rgb_depois"],
        imagens.get("nir_depois"),
        metodo=opcoes["metodo"],
        suavizacao=1,
        swir=imagens.get("swir_depois"),
    )


def aba_deteccao(imagens: dict, resultado) -> None:
    """Sobreposição e tabela de regiões."""
    if not resultado.confiavel:
        st.info(
            "A máscara abaixo é exibida para inspeção, mas **não deve ser usada como "
            "resultado** enquanto a detecção estiver marcada como não confiável.",
            icon="ℹ️",
        )

    col1, col2 = st.columns([3, 2])
    with col1:
        mostrar(
            sobrepor_mascara(imagens["rgb_depois"], resultado.perda),
            "Áreas desmatadas sobre a imagem de depois",
        )
    with col2:
        if resultado.regioes:
            st.markdown("**Regiões detectadas**")
            linhas = []
            for ordem, regiao in enumerate(resultado.regioes[:15], start=1):
                area_ha = (
                    regiao.area_hectares(resultado.metros_por_pixel)
                    if resultado.metros_por_pixel
                    else None
                )
                linhas.append(
                    {
                        "#": ordem,
                        "Área (px)": regiao.area_pixels,
                        "Área (ha)": round(area_ha, 3) if area_ha is not None else "—",
                        "Centro (lin, col)": (
                            f"{regiao.centroide[0]:.0f}, {regiao.centroide[1]:.0f}"
                        ),
                    }
                )
            st.dataframe(linhas, width="stretch", hide_index=True)
            if len(resultado.regioes) > 15:
                st.caption(f"Mostrando as 15 maiores de {len(resultado.regioes)} regiões.")
        else:
            st.success("Nenhuma região de desmatamento acima da área mínima.", icon="🌳")

    with st.expander("Métricas de decisão do limiar"):
        st.json(resultado.resumo())


def aba_amostras(imagens: dict, resultado) -> None:
    """Preparação de dados para o modelo — o objetivo literal do enunciado."""
    st.caption(
        "O objetivo do enunciado (p.2) é usar o PDI como **preparação de dados** para "
        "alimentar um modelo de visão computacional. A máscara de desmatamento serve "
        "de rótulo: cada recorte recebe a classe da região que cobre."
    )

    col1, col2 = st.columns(2)
    lado = col1.slider("Lado do recorte (pixels)", 8, 48, 16, step=8)
    passo = col2.slider("Passo da varredura (pixels)", 4, 48, 8, step=4)

    try:
        conjunto = extrair_amostras(
            imagens["rgb_depois"], resultado.perda, lado=lado, passo=passo
        )
    except ErroImagem as erro:
        st.error(f"Não foi possível extrair amostras: {erro}", icon="🚫")
        return

    equilibrado = equilibrar(conjunto)

    colunas = st.columns(4)
    colunas[0].metric("Amostras extraídas", len(conjunto))
    colunas[1].metric("Intacto", conjunto.contagem_por_classe[0])
    colunas[2].metric("Desmatado", conjunto.contagem_por_classe[1])
    colunas[3].metric(
        "Equilíbrio", f"{conjunto.equilibrio:.2f}",
        help="Razão entre a classe minoritária e a majoritária. Perto de 0 = desbalanceado.",
    )

    st.caption(
        f"{conjunto.descartados_ambiguos} recortes ambíguos foram **descartados** — "
        "eles pegam parte de floresta e parte de corte. Rotulá-los pela classe "
        "majoritária ensinaria o classificador a responder pela vizinhança."
    )

    if len(equilibrado):
        st.markdown(f"**Conjunto equilibrado por subamostragem — {len(equilibrado)} amostras**")
        amostrar = min(8, len(equilibrado))
        colunas = st.columns(amostrar)
        for coluna, indice in zip(colunas, range(amostrar)):
            with coluna:
                mostrar(
                    equilibrado.recortes[indice],
                    "desmatado" if equilibrado.rotulos[indice] == 1 else "intacto",
                )
    else:
        st.info(
            "Sem amostras das duas classes não há conjunto de treino. Aumente a área "
            "desmatada, reduza o lado do recorte ou diminua o passo.",
            icon="ℹ️",
        )


def aba_modelo(imagens: dict, resultado) -> None:
    """Etapa 5 — classificador treinado sobre as amostras rotuladas."""
    from sentinela.modelo import ErroModelo, treinar_e_avaliar

    st.caption(
        "Floresta aleatória treinada sobre os recortes rotulados. As **features saem do "
        "núcleo de PDI do grupo** (`pdi.filtros.desvio_padrao_local`, "
        "`pdi.cor.exg`, ...); o scikit-learn entra só no algoritmo de aprendizado, que o "
        "enunciado permite."
    )

    col1, col2, col3 = st.columns(3)
    lado = col1.slider("Lado do recorte", 8, 32, 16, step=8, key="modelo_lado")
    proporcao = col2.slider("Fração para teste", 0.1, 0.5, 0.3, step=0.1)
    semente = col3.number_input("Semente do sorteio de blocos", 0, 999, 0)

    try:
        conjunto = extrair_amostras(
            imagens["rgb_depois"], resultado.perda, lado=lado, passo=lado // 2
        )
    except ErroImagem as erro:
        st.error(f"Não foi possível extrair amostras: {erro}", icon="🚫")
        return

    st.info(
        "**Treino e teste são separados por blocos da imagem, não por sorteio de "
        "recorte.** Os recortes se sobrepõem: sortear individualmente colocaria o mesmo "
        "pedaço de terreno nos dois lados e a acurácia medida seria vazamento. Recortes "
        "que cruzam fronteira de bloco são descartados.",
        icon="🧭",
    )

    try:
        classificador, avaliacao = treinar_e_avaliar(
            conjunto, proporcao_teste=proporcao, semente=int(semente)
        )
    except ErroModelo as erro:
        st.warning(f"**Modelo não treinado.** {erro}", icon="⚠️")
        return

    resumo = avaliacao.resumo()
    colunas = st.columns(4)
    colunas[0].metric("Acurácia", f"{resumo['acuracia']:.3f}")
    colunas[1].metric("Precisão", f"{resumo['precisao']:.3f}")
    colunas[2].metric(
        "Revocação", f"{resumo['revocacao']:.3f}",
        help="Fração do desmatamento real que o modelo encontrou.",
    )
    colunas[3].metric("F1", f"{resumo['f1']:.3f}")

    for aviso in avaliacao.avisos:
        st.warning(aviso, icon="⚠️")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Matriz de confusão**")
        matriz = resumo["matriz_confusao"]
        st.dataframe(
            [
                {"Resultado": "Intacto classificado como intacto",
                 "Amostras": matriz["intacto_correto"]},
                {"Resultado": "Desmatamento encontrado",
                 "Amostras": matriz["desmatamento_correto"]},
                {"Resultado": "Falso alarme", "Amostras": matriz["falso_alarme"]},
                {"Resultado": "Desmatamento perdido",
                 "Amostras": matriz["desmatamento_perdido"]},
            ],
            width="stretch",
            hide_index=True,
        )
        st.caption(
            f"{resumo['amostras_de_teste']} amostras de teste, de blocos que o modelo "
            "não viu no treino."
        )

    with col2:
        st.markdown("**O que pesou na decisão**")
        importancias = classificador.importancia_das_features()
        st.dataframe(
            [{"Feature": nome, "Peso": round(peso, 4)} for nome, peso in importancias[:8]],
            width="stretch",
            hide_index=True,
        )
        st.caption(
            "É o que permite responder *por que o modelo classificou assim* na "
            "apresentação."
        )


def principal() -> None:
    st.title("Sentinela — detecção e quantificação de desmatamento")
    st.caption(
        "Compara a mesma região em duas datas, segmenta a perda de cobertura vegetal "
        "e prepara recortes rotulados para um modelo de visão computacional."
    )

    if "_temporarios" not in st.session_state:
        import tempfile

        st.session_state["_temporarios"] = tempfile.mkdtemp(prefix="sentinela-")

    opcoes = barra_lateral()

    try:
        imagens = obter_imagens(opcoes)
    except (ErroArquivo, ErroImagem) as erro:
        st.error(str(erro), icon="🚫")
        return

    if imagens is None:
        return

    try:
        resultado = detectar_desmatamento(
            imagens["rgb_antes"],
            imagens["rgb_depois"],
            imagens.get("nir_antes"),
            imagens.get("nir_depois"),
            swir_antes=imagens.get("swir_antes"),
            swir_depois=imagens.get("swir_depois"),
            metodo=opcoes["metodo"],
            suavizacao=opcoes["suavizacao"],
            area_minima=opcoes["area_minima"],
            metros_por_pixel=opcoes["metros_por_pixel"],
        )
    except ErroImagem as erro:
        st.error(f"**Não foi possível processar:** {erro}", icon="🚫")
        return

    painel_resultado(resultado, opcoes)

    etapas, deteccao, amostras, classificacao = st.tabs(
        ["Etapas do processamento", "Detecção", "Amostras para o modelo", "Modelo"]
    )
    with etapas:
        aba_etapas(imagens, resultado, opcoes)
    with deteccao:
        aba_deteccao(imagens, resultado)
    with amostras:
        aba_amostras(imagens, resultado)
    with classificacao:
        aba_modelo(imagens, resultado)


if __name__ == "__main__":
    principal()
```

---

## `sentinela/cli.py`

```python
"""Linha de comando do Sentinela.

Três usos:

```bash
sentinela app                                     # abre a interface no navegador
sentinela detectar --antes t1.png --depois t2.png # processa um par e grava as saídas
sentinela demo --saida docs/evidence/results      # roda a cena sintética de demonstração
```

Existe porque a demonstração ao vivo depende do Streamlit, mas a geração de evidência
para o trabalho escrito precisa ser **reproduzível por comando**: um resultado que só
existe depois de alguém clicar numa tela não é reproduzível.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from .dataio import (
    ErroArquivo,
    carregar,
    carregar_par,
    indice_em_falsa_cor,
    mapa_de_mudanca,
    metros_por_pixel as ler_metros_por_pixel,
    par_bitemporal,
    salvar,
    sobrepor_mascara,
)
from .pdi.nucleo import ErroImagem
from .pipeline import detectar_desmatamento, equilibrar, extrair_amostras


def _gravar_saidas(destino: Path, imagens: dict, resultado) -> list[Path]:
    """Grava os intermediários que entram na evidência do trabalho escrito."""
    destino.mkdir(parents=True, exist_ok=True)

    saidas = {
        "01-antes.png": imagens["rgb_antes"],
        "02-depois.png": imagens["rgb_depois"],
        "03-indice-antes.png": indice_em_falsa_cor(resultado.indice_antes),
        "04-indice-depois.png": indice_em_falsa_cor(resultado.indice_depois),
        "05-vegetacao-antes.png": resultado.vegetacao_antes,
        "06-vegetacao-depois.png": resultado.vegetacao_depois,
        "07-mapa-mudanca.png": mapa_de_mudanca(resultado.mudanca),
        "08-perda-detectada.png": resultado.perda,
        "09-sobreposicao.png": sobrepor_mascara(imagens["rgb_depois"], resultado.perda),
    }

    gravados = [salvar(destino / nome, dados) for nome, dados in saidas.items()]

    relatorio = destino / "resumo.json"
    relatorio.write_text(
        json.dumps(resultado.resumo(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    gravados.append(relatorio)

    return gravados


def _relatar(resultado, gravados: list[Path] | None = None) -> None:
    """Imprime o resumo no terminal, com a recusa explícita quando for o caso."""
    resumo = resultado.resumo()

    print(f"\nÍndice de vegetação : {resumo['metodo_indice'].upper()}")
    print(f"Limiar de Otsu      : {resumo['limiar']:.4f} (único para as duas datas)")
    print(f"Distinguibilidade   : {resumo['distinguibilidade']:.3f}")

    if not resultado.confiavel:
        print(
            "\n  DETECÇÃO NÃO CONFIÁVEL — nenhuma área reportada.\n"
            "  A cena não apresenta duas classes separáveis. Sem elas o limiar\n"
            "  automático corta o ruído do dossel ao meio e produziria desmatamento\n"
            "  onde não houve."
        )
    else:
        print(f"\nÁrea desmatada      : {resumo['area_pixels']} pixels")
        if resumo["area_hectares"] is not None:
            print(f"                      {resumo['area_hectares']:.3f} hectares")
        else:
            print("                      (sem resolução espacial: só em pixels)")
        print(f"Regiões detectadas  : {resumo['regioes_detectadas']}")
        print(f"Fração da cena      : {resumo['proporcao_da_cena'] * 100:.2f}%")

    if resultado.alerta_de_registro:
        print(
            "\n  AVISO: ganho de vegetação alto demais. As duas datas podem não estar\n"
            "  alinhadas, ou a diferença pode ser sazonal."
        )

    if gravados:
        print(f"\n{len(gravados)} arquivos gravados em {gravados[0].parent}")


def _treinar_e_relatar(conjunto, *, proporcao_teste: float, semente: int) -> int:
    """Treina o classificador sobre as amostras e imprime a avaliação.

    Separado dos comandos porque `detectar` e `demo` relatam da mesma forma.
    """
    from .modelo import ErroModelo, treinar_e_avaliar

    print(f"\nAmostras             : {conjunto.resumo()}")

    try:
        classificador, avaliacao = treinar_e_avaliar(
            conjunto, proporcao_teste=proporcao_teste, semente=semente
        )
    except ErroModelo as erro:
        print(f"\nModelo não treinado: {erro}", file=sys.stderr)
        return 1

    resumo = avaliacao.resumo()
    matriz = resumo["matriz_confusao"]

    print("\n--- Classificador (floresta aleatória) ---")
    print(f"Amostras de teste    : {resumo['amostras_de_teste']}")
    print(f"Acurácia             : {resumo['acuracia']:.4f}")
    print(f"Precisão             : {resumo['precisao']:.4f}")
    print(f"Revocação            : {resumo['revocacao']:.4f}")
    print(f"F1                   : {resumo['f1']:.4f}")
    print("\nMatriz de confusão:")
    print(f"  intacto correto      {matriz['intacto_correto']:>5}")
    print(f"  desmatamento correto {matriz['desmatamento_correto']:>5}")
    print(f"  falso alarme         {matriz['falso_alarme']:>5}")
    print(f"  desmatamento perdido {matriz['desmatamento_perdido']:>5}")

    print("\nFeatures mais influentes:")
    for nome, peso in classificador.importancia_das_features()[:5]:
        print(f"  {nome:<20} {peso:.4f}")

    for aviso in avaliacao.avisos:
        print(f"\n  AVISO: {aviso}")

    return 0


def comando_app(args: argparse.Namespace) -> int:
    """Sobe a interface Streamlit no navegador."""
    from .app import CAMINHO_APP

    try:
        import streamlit  # noqa: F401
    except ImportError:
        print(
            "Streamlit não está instalado. Instale o extra da interface:\n"
            '  pip install -e ".[app]"',
            file=sys.stderr,
        )
        return 1

    comando = [sys.executable, "-m", "streamlit", "run", CAMINHO_APP,
               "--server.port", str(args.porta)]
    return subprocess.call(comando)


def comando_detectar(args: argparse.Namespace) -> int:
    """Processa um par bi-temporal vindo do disco."""
    try:
        rgb_antes, rgb_depois = carregar_par(args.antes, args.depois)
        nir_antes = carregar(args.nir_antes, cinza=True) if args.nir_antes else None
        nir_depois = carregar(args.nir_depois, cinza=True) if args.nir_depois else None
        swir_antes = carregar(args.swir_antes, cinza=True) if args.swir_antes else None
        swir_depois = carregar(args.swir_depois, cinza=True) if args.swir_depois else None
    except ErroArquivo as erro:
        print(f"Erro de leitura: {erro}", file=sys.stderr)
        return 1

    metros = args.metros_por_pixel or ler_metros_por_pixel(args.depois)

    try:
        resultado = detectar_desmatamento(
            rgb_antes, rgb_depois, nir_antes, nir_depois,
            swir_antes=swir_antes, swir_depois=swir_depois,
            metodo=args.metodo,
            suavizacao=args.suavizacao,
            area_minima=args.area_minima,
            metros_por_pixel=metros,
        )
    except ErroImagem as erro:
        print(f"Erro de processamento: {erro}", file=sys.stderr)
        return 1

    gravados = None
    if args.saida:
        imagens = {"rgb_antes": rgb_antes, "rgb_depois": rgb_depois}
        gravados = _gravar_saidas(Path(args.saida), imagens, resultado)

    _relatar(resultado, gravados)

    if args.modelo:
        conjunto = extrair_amostras(rgb_depois, resultado.perda, lado=args.lado)
        return _treinar_e_relatar(
            conjunto, proporcao_teste=args.proporcao_teste, semente=args.semente
        )

    return 0


def comando_demo(args: argparse.Namespace) -> int:
    """Roda a cadeia completa sobre a cena **sintética** de demonstração."""
    print(
        "CENA SINTÉTICA — demonstração do programa.\n"
        "Não é imagem de satélite e não pode ser apresentada como evidência real\n"
        "(AGENTS.md §11). A validação sobre imagem real é o requisito R032.\n"
    )

    lado = args.tamanho
    corte_lado = args.area
    corte = None
    if corte_lado > 0:
        inicio = (lado - corte_lado) // 2
        corte = (slice(inicio, inicio + corte_lado), slice(inicio, inicio + corte_lado))

    par = par_bitemporal(corte=corte, tamanho=(lado, lado))

    resultado = detectar_desmatamento(
        par["rgb_antes"], par["rgb_depois"], par["nir_antes"], par["nir_depois"],
        metros_por_pixel=args.metros_por_pixel,
    )

    gravados = _gravar_saidas(Path(args.saida), par, resultado) if args.saida else None
    _relatar(resultado, gravados)

    esperada = par["area_esperada"]
    if esperada and resultado.confiavel:
        erro = abs(resultado.area_pixels - esperada) / esperada * 100
        print(f"\nVerdade de terreno  : {esperada} pixels")
        print(f"Erro da detecção    : {erro:.1f}%")

    conjunto = extrair_amostras(par["rgb_depois"], resultado.perda)

    if not args.modelo:
        print(f"\nAmostras para o modelo: {conjunto.resumo()}")
        print(f"Após equilibrar       : {equilibrar(conjunto).resumo()}")
        print("\nUse --modelo para treinar e avaliar o classificador.")
        return 0

    return _treinar_e_relatar(
        conjunto, proporcao_teste=args.proporcao_teste, semente=args.semente
    )


def comando_apendice(args: argparse.Namespace) -> int:
    """Gera o apêndice de código-fonte exigido pelo Capítulo 7 do enunciado (R018).

    Automatizado de propósito: um apêndice copiado à mão diverge do código entregue na
    primeira correção feita depois de copiar, e a divergência é exatamente o tipo de
    coisa que uma banca encontra.
    """
    raiz = Path(__file__).resolve().parents[2]
    origem = raiz / "src" / "sentinela"

    if not origem.is_dir():
        print(f"Código-fonte não encontrado em {origem}", file=sys.stderr)
        return 1

    # Ordem de leitura, não alfabética: o apêndice é lido por quem quer entender o
    # sistema, e o núcleo vem antes de quem o consome.
    ordem = [
        "pdi/nucleo.py", "pdi/cor.py", "pdi/filtros.py", "pdi/limiar.py",
        "pdi/morfologia.py", "pdi/segmentacao.py",
        "dataio/imagem.py", "dataio/geo.py", "dataio/visual.py", "dataio/sintetico.py",
        "pipeline/deteccao.py", "pipeline/amostras.py",
        "modelo/caracteristicas.py", "modelo/classificador.py",
        "app/principal.py", "cli.py",
    ]

    encontrados = [caminho for caminho in ordem if (origem / caminho).is_file()]
    restantes = sorted(
        str(caminho.relative_to(origem))
        for caminho in origem.rglob("*.py")
        if caminho.is_file()
        and str(caminho.relative_to(origem)) not in encontrados
        and "__pycache__" not in str(caminho)
        and caminho.name != "__init__.py"
    )
    arquivos = encontrados + restantes

    cabecalho = [
        "# 7. Apêndice — código-fonte do programa",
        "",
        "> **Gerado automaticamente** por `sentinela apendice`. Não editar à mão: a edição",
        "> se perde na próxima geração, e um apêndice editado deixa de corresponder ao",
        "> código entregue.",
        "",
        "Os filtros de processamento de imagens em `pdi/` foram implementados pelo grupo,",
        "com NumPy apenas, conforme exige o enunciado (p.3, item 3.a).",
        "",
        "## Índice",
        "",
    ]

    indice = []
    corpo = []
    total_linhas = 0

    for relativo in arquivos:
        texto = (origem / relativo).read_text(encoding="utf-8").rstrip()
        linhas = len(texto.splitlines())
        total_linhas += linhas

        indice.append(f"- `sentinela/{relativo}` — {linhas} linhas")
        corpo.extend(
            ["", "---", "", f"## `sentinela/{relativo}`", "", "```python", texto, "```"]
        )

    rodape = ["", f"**Total: {len(arquivos)} arquivos, {total_linhas} linhas.**"]

    destino = Path(args.saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(cabecalho + indice + rodape + corpo) + "\n", encoding="utf-8")

    print(f"Apêndice gerado: {destino}")
    print(f"{len(arquivos)} arquivos, {total_linhas} linhas.")
    print(
        "\nAo montar o documento final, conferir se o volume do apêndice é compatível "
        "com o limite de páginas do trabalho."
    )
    return 0


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sentinela",
        description="Detecção e quantificação de desmatamento em imagens de satélite.",
    )
    subcomandos = parser.add_subparsers(dest="comando", required=True)

    app = subcomandos.add_parser("app", help="abre a interface no navegador")
    app.add_argument("--porta", type=int, default=8501)
    app.set_defaults(funcao=comando_app)

    detectar = subcomandos.add_parser("detectar", help="processa um par de imagens")
    detectar.add_argument("--antes", required=True, help="imagem RGB da primeira data")
    detectar.add_argument("--depois", required=True, help="imagem RGB da segunda data")
    detectar.add_argument("--nir-antes", dest="nir_antes")
    detectar.add_argument("--nir-depois", dest="nir_depois")
    detectar.add_argument("--swir-antes", dest="swir_antes",
                          help="banda SWIR da primeira data — necessária para --metodo ndmi")
    detectar.add_argument("--swir-depois", dest="swir_depois")
    detectar.add_argument("--saida", help="diretório para gravar as imagens e o resumo")
    detectar.add_argument("--metodo", default="auto",
                          choices=("auto", "ndvi", "ndmi", "vari", "exg"))
    detectar.add_argument("--suavizacao", type=int, default=5)
    detectar.add_argument("--area-minima", dest="area_minima", type=int, default=25)
    detectar.add_argument("--metros-por-pixel", dest="metros_por_pixel", type=float,
                          help="sobrepõe o metadado geográfico do arquivo")
    detectar.add_argument("--modelo", action="store_true",
                          help="treina e avalia o classificador sobre as amostras")
    detectar.add_argument("--lado", type=int, default=16,
                          help="lado do recorte das amostras, em pixels")
    detectar.add_argument("--proporcao-teste", dest="proporcao_teste", type=float,
                          default=0.3)
    detectar.add_argument("--semente", type=int, default=0)
    detectar.set_defaults(funcao=comando_detectar)

    demo = subcomandos.add_parser("demo", help="roda a cena sintética de demonstração")
    demo.add_argument("--saida", help="diretório para gravar as imagens e o resumo")
    demo.add_argument("--tamanho", type=int, default=80, help="lado da cena, em pixels")
    demo.add_argument("--area", type=int, default=20,
                      help="lado da área desmatada; 0 gera floresta intacta")
    demo.add_argument("--metros-por-pixel", dest="metros_por_pixel", type=float,
                      default=10.0)
    demo.add_argument("--modelo", action="store_true",
                      help="treina e avalia o classificador sobre as amostras")
    demo.add_argument("--proporcao-teste", dest="proporcao_teste", type=float, default=0.3)
    demo.add_argument("--semente", type=int, default=0)
    demo.set_defaults(funcao=comando_demo)

    apendice = subcomandos.add_parser(
        "apendice", help="gera o apêndice de código-fonte do trabalho escrito"
    )
    apendice.add_argument("--saida", default="docs/trabalho-escrito/07-apendice.md")
    apendice.set_defaults(funcao=comando_apendice)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)

    try:
        return args.funcao(args)
    except KeyboardInterrupt:
        print("\nInterrompido.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
```
