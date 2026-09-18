#!/usr/bin/env python3
"""Gera as figuras da apresentação a partir das imagens reais em ``data/raw/``.

Existe para que nenhuma figura do trabalho seja um arquivo órfão: cada painel é
reproduzível pelo mesmo código que produz os resultados. As imagens de entrada não são
versionadas (``docs/decisions/002-dados-nao-versionados.md``); baixá-las de novo com
``python scripts/baixar_imagens.py --regiao sao-felix`` regenera as mesmas figuras.

Sobre o índice: a composição Bands721 do MODIS traz a **banda 7** (2105–2155 nm), que é
SWIR 2. O índice de NIR com SWIR 2 é o **NBR**, não o NDMI — este último exige SWIR 1
(banda 6). Uma versão anterior desta figura rotulava o painel como NDMI; o rótulo estava
errado e os valores, corretos.

```bash
python scripts/gerar_figuras.py
```
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from sentinela.dataio.imagem import carregar, salvar    # noqa: E402
from sentinela.dataio.visual import indice_em_falsa_cor  # noqa: E402
from sentinela.pdi.cor import nbr, para_faixa_unitaria    # noqa: E402
from sentinela.pdi.filtros import (                      # noqa: E402
    desvio_padrao_local, gaussiano, magnitude_gradiente, mediana,
)

BRUTO = RAIZ / "data" / "raw"
DESTINO = RAIZ / "docs" / "apresentacao" / "figuras"
MANIFESTO = BRUTO / "sao-felix_manifesto.json"
TELAS = RAIZ / "docs" / "resultados" / "telas"

# Recortes das capturas de tela para os slides. As capturas inteiras são páginas longas;
# num slide 16:9 elas ficariam ilegíveis. Coordenadas em pixels: (esquerda, topo, direita,
# base), conferidas contra as capturas de `scripts/capturar_telas.mjs`.
RECORTES_DE_TELA = {
    "tela-filtragem.png": ("01-etapas", (360, 1810, 1345, 2775)),
    "tela-aquisicao.png": ("01-etapas", (360, 640, 1345, 1805)),
    "tela-deteccao.png": ("02-deteccao", (360, 440, 1345, 1240)),
    "tela-modelo.png": ("03-modelo", (360, 690, 1345, 1400)),
    "tela-recusa.png": ("04-recusa", (360, 370, 1345, 700)),
}


def comparativo_real(destino: Path) -> Path:
    """Painel 2×2: cor natural e NBR em falsa cor, nas duas datas."""
    manifesto = json.loads(MANIFESTO.read_text(encoding="utf-8"))
    paineis = []
    for chave in ("antes", "depois"):
        entrada = manifesto["datas"][chave]
        arquivos = entrada["arquivos"]
        cor_real = carregar(BRUTO / arquivos["cor_real"])
        # Bands721 vem como (SWIR, NIR, vermelho): o canal 1 é o NIR e o 0, o SWIR 2.
        analise = carregar(BRUTO / arquivos["analise"])
        indice = nbr(analise[:, :, 1], analise[:, :, 0])
        paineis.append((entrada["data"], cor_real, indice_em_falsa_cor(indice)))

    figura, eixos = plt.subplots(2, 2, figsize=(8.9, 9.6), dpi=100)
    for coluna, (data, cor_real, falsa_cor) in enumerate(paineis):
        eixos[0][coluna].imshow(cor_real)
        eixos[0][coluna].set_title(f"{data} · cor real", loc="left", fontsize=13)
        eixos[1][coluna].imshow(falsa_cor)
        eixos[1][coluna].set_title(f"{data[:4]} · NBR (falsa cor)", loc="left", fontsize=13)
    for eixo in eixos.ravel():
        eixo.set_xticks([])
        eixo.set_yticks([])

    metros = manifesto["metros_por_pixel"]
    figura.text(0.012, 0.012,
                f"{manifesto['descricao'].split('—')[0].strip()} · {manifesto['fonte']} · "
                f"≈{metros:.0f} m/pixel · {manifesto['licenca'].split('(')[0].strip()}",
                fontsize=10, color="#333333")
    figura.tight_layout(rect=(0, 0.028, 1, 1))
    destino.parent.mkdir(parents=True, exist_ok=True)
    figura.savefig(destino, facecolor="white")
    plt.close(figura)
    return destino


def efeito_dos_filtros(destino: Path) -> Path:
    """Painel 2×3: o que cada filtro do grupo faz sobre a cena real de 2024.

    O enunciado (p.3, item 3.a) pede que o resultado dos filtros seja apresentado e
    analisado. Todos os seis painéis saem de ``sentinela.pdi``, implementado com NumPy.
    """
    manifesto = json.loads(MANIFESTO.read_text(encoding="utf-8"))
    arquivos = manifesto["datas"]["depois"]["arquivos"]
    analise = carregar(BRUTO / arquivos["analise"])
    indice = para_faixa_unitaria(nbr(analise[:, :, 1], analise[:, :, 0]))
    recorte = slice(120, 320)
    bruto = indice[recorte, recorte]

    suave = gaussiano(bruto, tamanho=5)
    paineis = [
        (carregar(BRUTO / arquivos["cor_real"])[recorte, recorte], "cor real (recorte 200×200)", None),
        (bruto, "NBR bruto", "viridis"),
        (suave, "gaussiano 5×5 — separável", "viridis"),
        (mediana(bruto, tamanho=3), "mediana 3×3 — remove sal-e-pimenta", "viridis"),
        (magnitude_gradiente(suave), "Sobel — magnitude do gradiente", "magma"),
        (desvio_padrao_local(bruto, tamanho=5), "desvio-padrão local — textura", "magma"),
    ]

    figura, eixos = plt.subplots(2, 3, figsize=(13.2, 9.2), dpi=100)
    for eixo, (imagem, rotulo, mapa) in zip(eixos.ravel(), paineis):
        eixo.imshow(imagem) if mapa is None else eixo.imshow(imagem, cmap=mapa)
        eixo.set_title(rotulo, loc="left", fontsize=12)
        eixo.set_xticks([])
        eixo.set_yticks([])
    figura.text(0.008, 0.012,
                "São Félix do Xingu (PA), 2024-07-05 · MODIS/Terra via NASA GIBS · "
                "todos os filtros implementados pelo grupo em sentinela/pdi (NumPy)",
                fontsize=10, color="#333333")
    figura.tight_layout(rect=(0, 0.03, 1, 1), h_pad=2.6)
    figura.savefig(destino, facecolor="white")
    plt.close(figura)
    return destino


def recortes_de_tela(destino: Path) -> list[Path]:
    """Recorta as capturas da interface para o tamanho que cabe num slide."""
    gerados = []
    for nome, (origem, (x0, y0, x1, y1)) in RECORTES_DE_TELA.items():
        tela = carregar(TELAS / f"{origem}.png")
        gerados.append(salvar(destino / nome, tela[y0:y1, x0:x1]))
    return gerados


def main() -> int:
    if not MANIFESTO.exists():
        print(f"Faltam as imagens de origem em {BRUTO}. "
              "Rode: python scripts/baixar_imagens.py --regiao sao-felix", file=sys.stderr)
        return 1
    gerados = [comparativo_real(DESTINO / "comparativo-real.png"),
               efeito_dos_filtros(DESTINO / "efeito-dos-filtros.png")]
    gerados += recortes_de_tela(DESTINO / "telas")
    for caminho in gerados:
        print(f"Figura gerada: {caminho.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
