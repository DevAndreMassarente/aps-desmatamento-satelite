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
FLORESTA = {"vermelho": 0.05, "verde": 0.09, "azul": 0.04, "nir": 0.55}
SOLO_EXPOSTO = {"vermelho": 0.33, "verde": 0.30, "azul": 0.24, "nir": 0.37}

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
        "rgb_depois": rgb_depois,
        "nir_depois": nir_depois,
        "area_esperada": area,
    }
