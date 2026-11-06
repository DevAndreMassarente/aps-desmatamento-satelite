"""Mostra como uma imagem de quatro bandas é montada: cor nas três primeiras, infravermelho na quarta.

Imprime as bandas no terminal e grava uma figura com a cor e cada banda separada.

    .venv/bin/python _interno/scripts/ver_bandas.py _interno/data/raw/sentinel-2/2018-07-03_cor-e-infravermelho.png

A figura vai para /tmp/bandas.png, ou para o caminho passado em --saida. No Windows, abra
\\\\wsl.localhost\\Ubuntu\\tmp\\bandas.png.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

NOMES = ("Vermelho", "Verde", "Azul", "Infravermelho próximo")
LADO = 360


def esticar(banda: np.ndarray) -> np.ndarray:
    """Realce só para a tela: o percentil 99 vira branco."""
    alto = max(float(np.percentile(banda, 99)), 1.0)
    return (np.clip(banda / alto, 0, 1) * 255).astype(np.uint8)


def painel(dados: np.ndarray, titulo: str) -> Image.Image:
    figura = Image.fromarray(dados).convert("RGB").resize((LADO, LADO))
    tela = Image.new("RGB", (LADO, LADO + 34), "white")
    tela.paste(figura, (0, 34))
    ImageDraw.Draw(tela).text((8, 10), titulo, fill="black")
    return tela


def main() -> int:
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("imagem", type=Path)
    argumentos.add_argument("--saida", type=Path, default=Path("/tmp/bandas.png"))
    opcoes = argumentos.parse_args()

    with Image.open(opcoes.imagem) as arquivo:
        print(f"{opcoes.imagem.name}: {arquivo.size[0]} × {arquivo.size[1]} pixels, "
              f"modo {arquivo.mode}, {len(arquivo.getbands())} bandas")
        dados = np.array(arquivo)

    if dados.ndim != 3 or dados.shape[2] < 3:
        print("A imagem não tem três bandas de cor.")
        return 1

    nomes = NOMES[: dados.shape[2]]
    for indice, nome in enumerate(nomes):
        banda = dados[..., indice].astype(float)
        print(f"  banda {indice + 1}  {nome:22s}  média {banda.mean():6.1f}  "
              f"mín {banda.min():4.0f}  máx {banda.max():4.0f}")
    if dados.shape[2] == 4:
        print("\nAs três primeiras bandas formam a cor; a quarta é o infravermelho próximo.")

    cor = np.dstack([esticar(dados[..., i].astype(float)) for i in range(3)])
    paineis = [painel(cor, "Cor (bandas 1 a 3)")]
    # A fonte padrão do Pillow não tem acentos: os títulos da figura vão sem eles.
    titulos = ("Vermelho", "Verde", "Azul", "Infravermelho proximo (NIR)")
    paineis += [painel(esticar(dados[..., i].astype(float)), f"Banda {i + 1}: {titulos[i]}")
                for i in range(len(nomes))]

    figura = Image.new("RGB", (len(paineis) * (LADO + 10) - 10, LADO + 34), "white")
    for ordem, imagem in enumerate(paineis):
        figura.paste(imagem, (ordem * (LADO + 10), 0))
    opcoes.saida.parent.mkdir(parents=True, exist_ok=True)
    figura.save(opcoes.saida)
    print(f"\nFigura gravada em {opcoes.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
