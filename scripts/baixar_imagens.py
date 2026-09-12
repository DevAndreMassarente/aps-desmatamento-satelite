#!/usr/bin/env python3
"""Baixa o par bi-temporal de imagens reais de satélite (R032).

Fonte: **NASA GIBS** (Global Imagery Browse Services), serviço WMS público que não exige
credencial. Produto: MODIS/Terra Corrected Reflectance, resolução nominal 250 m.

Por que GIBS e não Copernicus/USGS: as duas alternativas exigem cadastro e chave de API.
GIBS entrega imagem real, datada, georreferenciada e citável sem credencial, o que torna
a aquisição **reproduzível por qualquer integrante do grupo** — e reproduzibilidade é o
que o enunciado cobra quando pede que os resultados sejam demonstráveis.

## O detalhe que decide a qualidade do NDVI

O GIBS publica duas composições da mesma cena:

- `..._TrueColor`  = bandas 1, 4, 3  (vermelho, verde, azul)
- `..._Bands721`   = bandas 7, 2, 1  (SWIR, **NIR**, vermelho)

A tentação é pegar o vermelho da primeira e o NIR da segunda. **Medimos e não funciona:**
a banda 1 sai com média 88 na TrueColor e 62 na Bands721 — correlação 0,97, mas com
realce de 8 bits diferente por produto. Um NDVI montado com essa mistura carregaria um
viés sistemático de origem puramente gráfica.

Por isso o vermelho **e** o NIR saem os dois da Bands721: canal B é a banda 1, canal G é a
banda 2. Mesma cena, mesmo realce, razão comparável.

## Limitação que precisa constar no trabalho escrito

Corrected Reflectance é um produto de **visualização**, com realce não linear para 8 bits.
O NDVI calculado sobre ele é **qualitativo**: serve para separar vegetação de solo exposto
e comparar duas datas, não para reportar valor absoluto de NDVI comparável à literatura.
Para isso seria preciso refletância de superfície (MOD09, ou Sentinel-2 L2A).

## Uso

```bash
python scripts/baixar_imagens.py                    # região padrão, par 2001/2024
python scripts/baixar_imagens.py --listar-regioes
python scripts/baixar_imagens.py --regiao rondonia --largura 512
```
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

import numpy as np
from PIL import Image

WMS = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
CAMADA_VISUAL = "MODIS_Terra_CorrectedReflectance_TrueColor"
CAMADA_ANALISE = "MODIS_Terra_CorrectedReflectance_Bands721"

# Metro por grau de latitude (WGS-84, valor médio). A célula do WMS em EPSG:4326 é
# quadrada em GRAUS, não em metros: perto do equador a diferença é pequena, e é ela que
# torna a conversão para hectares aproximada.
METROS_POR_GRAU = 111_320.0

RAIZ = Path(__file__).resolve().parents[1]
DESTINO_PADRAO = RAIZ / "data" / "raw"

# Frentes de desmatamento na Amazônia Legal. As datas foram escolhidas varrendo o
# período seco e medindo cobertura de nuvem e ausência de dado — ver `_avaliar`.
REGIOES = {
    "sao-felix": {
        "descricao": "São Félix do Xingu (PA) — frente de expansão da pecuária",
        "bbox": (-7.0, -52.5, -6.0, -51.5),
        # Início de julho nas duas datas: mesma estação e, medido, o mesmo nível de
        # bruma (p05 do azul = 6 em ambas). Casar a atmosfera entre as datas importa
        # tanto quanto casar o recorte — ver `avaliar_qualidade`.
        "antes": "2002-07-01",
        "depois": "2024-07-05",
    },
    "rondonia": {
        "descricao": "Ariquemes / Ji-Paraná (RO) — padrão espinha de peixe",
        "bbox": (-11.0, -63.0, -10.0, -62.0),
        "antes": "2002-07-01",
        "depois": "2024-07-15",
    },
    "novo-progresso": {
        "descricao": "Novo Progresso (PA) — eixo da BR-163",
        "bbox": (-7.5, -55.9, -6.5, -54.9),
        "antes": "2002-07-01",
        "depois": "2024-07-05",
    },
}


class ErroAquisicao(RuntimeError):
    """Falha ao obter imagem do serviço."""


def _url(camada: str, bbox: tuple[float, ...], data: str, largura: int) -> str:
    parametros = {
        "SERVICE": "WMS",
        "REQUEST": "GetMap",
        "VERSION": "1.3.0",
        "LAYERS": camada,
        "STYLES": "",
        "CRS": "EPSG:4326",
        "BBOX": ",".join(str(v) for v in bbox),
        "WIDTH": largura,
        "HEIGHT": largura,
        "FORMAT": "image/png",
        "TIME": data,
    }
    return f"{WMS}?{urllib.parse.urlencode(parametros)}"


def baixar(camada: str, bbox: tuple[float, ...], data: str, largura: int) -> np.ndarray:
    """Requisita uma cena e devolve ``[H, W, 3]`` em ``uint8``."""
    endereco = _url(camada, bbox, data, largura)
    try:
        with urllib.request.urlopen(endereco, timeout=120) as resposta:
            bruto = resposta.read()
    except (urllib.error.URLError, TimeoutError) as erro:
        raise ErroAquisicao(f"falha ao acessar o GIBS: {erro}") from erro

    try:
        return np.array(Image.open(io.BytesIO(bruto)).convert("RGB"))
    except Exception as erro:
        raise ErroAquisicao(
            f"a resposta do GIBS não é uma imagem válida ({len(bruto)} bytes). "
            "Confira a data: nem toda data tem granulo disponível."
        ) from erro


# Percentil 5 da banda azul acima disto indica fumaça ou bruma. Calibrado comparando
# 2001-08-20 sobre São Félix (auge das queimadas, p05 = 78) com datas limpas da mesma
# área e estação (p05 entre 6 e 34).
BRUMA_SUSPEITA = 45.0


def avaliar_qualidade(visual: np.ndarray, analise: np.ndarray) -> dict[str, float]:
    """Mede ausência de dado, nuvem e **bruma**, em fração da cena.

    As três contaminam a detecção de forma diferente: buraco vira fronteira falsa,
    nuvem vira perda de vegetação, e bruma desloca o índice inteiro.

    ## Por que a bruma é medida na composição visível

    Este projeto já perdeu uma rodada por medir fumaça na composição Bands721: a banda 7
    é infravermelho de ondas curtas e **atravessa a fumaça**, então a cena de
    2001-08-20 sobre São Félix — coberta por fumaça de queimada — passou no teste com
    0% de nuvem. O NDVI dela saiu 0,04 abaixo do esperado, a floresta de 2001 apareceu
    menos vegetada que a pastagem de 2024, e o sistema corretamente recusou a detecção.

    O espalhamento da fumaça é forte no azul e some no SWIR. Por isso a bruma é medida
    no canal azul da composição **visível**, e o percentil 5 é o indicador: fumaça
    levanta o piso da distribuição, porque não existe mais pixel escuro na cena.
    """
    valores = analise.astype(np.float32)
    azul = visual.astype(np.float32)[:, :, 2]

    return {
        "ausente": float((valores.sum(axis=2) < 30).mean()),
        "nuvem": float((valores.min(axis=2) > 185).mean()),
        "bruma_p05_azul": float(np.percentile(azul, 5)),
    }


def composicao_para_analise(bands721: np.ndarray) -> np.ndarray:
    """Reordena a Bands721 para que o canal 0 seja o **vermelho**.

    O GIBS entrega a Bands721 na ordem (banda 7 = SWIR, banda 2 = NIR, banda 1 =
    vermelho). O núcleo de PDI assume que o canal 0 de uma imagem RGB é o vermelho —
    é dele que o NDVI tira o denominador. A troca de R com B corrige a ordem sem
    alterar nenhum valor de pixel.

    Resultado: ``(vermelho, NIR, SWIR)``. Só o NDVI faz sentido sobre esta composição;
    VARI e ExG, não, porque não há banda verde nem azul aqui.
    """
    return bands721[:, :, ::-1].copy()


def metros_por_pixel(bbox: tuple[float, ...], largura: int) -> float:
    """Resolução aproximada, em metros por pixel.

    Aproximada porque o recorte é quadrado em graus e não em metros: o pixel é
    ligeiramente mais estreito em longitude do que em latitude. Perto do equador,
    onde ficam as frentes de desmatamento, a diferença é de poucos por cento.
    """
    latitude_min, _, latitude_max, _ = bbox
    return abs(latitude_max - latitude_min) * METROS_POR_GRAU / largura


def _salvar(caminho: Path, imagem: np.ndarray) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(imagem).save(caminho)
    return caminho


def baixar_par(
    regiao: str, destino: Path, largura: int, *, verbose: bool = True
) -> dict:
    """Baixa as duas datas da região e grava as três imagens de cada uma."""
    if regiao not in REGIOES:
        raise ErroAquisicao(
            f"região '{regiao}' desconhecida. Disponíveis: {', '.join(REGIOES)}"
        )

    config = REGIOES[regiao]
    bbox = config["bbox"]
    registro = {
        "regiao": regiao,
        "descricao": config["descricao"],
        "bbox_epsg4326": list(bbox),
        "largura_px": largura,
        "metros_por_pixel": round(metros_por_pixel(bbox, largura), 2),
        "fonte": "NASA GIBS — MODIS/Terra Corrected Reflectance",
        "licenca": "domínio público (NASA open data policy)",
        "baixado_em": date.today().isoformat(),
        "datas": {},
    }

    for rotulo in ("antes", "depois"):
        data = config[rotulo]
        if verbose:
            print(f"  {rotulo:<7} {data} ...", end=" ", flush=True)

        visual = baixar(CAMADA_VISUAL, bbox, data, largura)
        bands721 = baixar(CAMADA_ANALISE, bbox, data, largura)
        analise = composicao_para_analise(bands721)

        qualidade = avaliar_qualidade(visual, bands721)
        prefixo = f"{regiao}_{data}"

        arquivos = {
            "cor_real": _salvar(destino / f"{prefixo}_cor-real.png", visual),
            "analise": _salvar(destino / f"{prefixo}_analise.png", analise),
            "nir": _salvar(destino / f"{prefixo}_nir.png", analise[:, :, 1]),
            "swir": _salvar(destino / f"{prefixo}_swir.png", analise[:, :, 2]),
        }

        registro["datas"][rotulo] = {
            "data": data,
            "qualidade": {k: round(v, 4) for k, v in qualidade.items()},
            "arquivos": {k: v.name for k, v in arquivos.items()},
            "url_visual": _url(CAMADA_VISUAL, bbox, data, largura),
            "url_analise": _url(CAMADA_ANALISE, bbox, data, largura),
        }

        if verbose:
            print(
                f"ok (ausente {qualidade['ausente']*100:.1f}%, "
                f"nuvem {qualidade['nuvem']*100:.1f}%, "
                f"bruma {qualidade['bruma_p05_azul']:.0f})"
            )

        if qualidade["ausente"] > 0.05 or qualidade["nuvem"] > 0.10:
            print(
                f"    AVISO: cena comprometida em {rotulo}. Nuvem vira falso "
                "desmatamento e buraco vira fronteira falsa. Escolha outra data.",
                file=sys.stderr,
            )
        if qualidade["bruma_p05_azul"] > BRUMA_SUSPEITA:
            print(
                f"    AVISO: bruma alta em {rotulo} (p05 do azul = "
                f"{qualidade['bruma_p05_azul']:.0f}, limite {BRUMA_SUSPEITA:.0f}). "
                "Provável fumaça de queimada: ela derruba o NDVI da cena inteira e "
                "pode inverter a comparação entre as datas. Escolha outra data.",
                file=sys.stderr,
            )

    return registro


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--regiao", default="sao-felix", choices=sorted(REGIOES))
    parser.add_argument("--largura", type=int, default=440,
                        help="lado da imagem em pixels; 440 ≈ 253 m/px num recorte de 1°")
    parser.add_argument("--destino", type=Path, default=DESTINO_PADRAO)
    parser.add_argument("--listar-regioes", action="store_true")
    args = parser.parse_args(argv)

    if args.listar_regioes:
        for nome, config in REGIOES.items():
            print(f"{nome:<16} {config['descricao']}")
            print(f"{'':<16} bbox {config['bbox']} | {config['antes']} → {config['depois']}")
        return 0

    print(f"Região: {args.regiao} — {REGIOES[args.regiao]['descricao']}")
    try:
        registro = baixar_par(args.regiao, args.destino, args.largura)
    except ErroAquisicao as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1

    manifesto = args.destino / f"{args.regiao}_manifesto.json"
    manifesto.write_text(
        json.dumps(registro, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"\nResolução: {registro['metros_por_pixel']} m/pixel (aproximada)")
    print(f"Manifesto: {manifesto}")
    print(
        "\nRegistre a procedência em data/raw/FONTES.md antes de usar as imagens "
        "no trabalho escrito."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
