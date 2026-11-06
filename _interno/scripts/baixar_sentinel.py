"""Baixa um recorte bi-temporal Sentinel-2 L2A sem credencial (AWS Open Data).

Lê só a janela pedida dos arquivos COG, via catálogo STAC Earth Search. Grava as bandas
originais em 16 bits e as versões de 8 bits que o pipeline consome.

As quatro bandas usam a MESMA escala linear de reflectância nas duas datas. Um realce por
banda ou por data mudaria o NDVI e criaria diferença falsa entre as cenas.

A janela foi escolhida antes de consultar o PRODES, com o próprio par em amostragem de 100 m.
Janelas de 15 km, a passos de 2,5 km, com menos de 0,5% de dado ruim, menos de 1% de água e
mais de 30% de floresta nas duas datas (NDVI > 0,75). Entre elas, a de maior perda (NDVI de
mais de 0,75 para menos de 0,6). O recorte concentra perda de propósito e não representa a
região inteira.

Execução, sem acrescentar `rasterio` ao ambiente do projeto:

    uv run --no-project --with rasterio --with numpy --with pillow \
        python _interno/scripts/baixar_sentinel.py
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.windows import Window

CATALOGO = "https://earth-search.aws.element84.com/v1/collections/sentinel-2-c1-l2a/items/"
CENAS = {
    "2018-07-03": "S2B_T22MCU_20180703T135111_L2A",
    "2024-07-16": "S2A_T22MCU_20240716T135306_L2A",
}
JANELA = Window(col_off=750, row_off=9250, width=1500, height=1500)
BANDAS = {"blue": "B02", "green": "B03", "red": "B04", "nir": "B08"}
REFLECTANCIA_MAXIMA = 0.5
# Classes da SCL tratadas como dado ruim: sem dado, saturado, sombra de nuvem, nuvem e neve.
SCL_RUINS = (0, 1, 3, 8, 9, 10, 11)
SAIDA = Path(__file__).resolve().parents[2] / "_interno" / "data" / "raw" / "sentinel-2"


def para_8_bits(banda: np.ndarray, escala: float, deslocamento: float) -> np.ndarray:
    """Converte número digital em reflectância e aplica a escala linear comum."""
    reflectancia = banda.astype("float32") * escala + deslocamento
    return np.round(np.clip(reflectancia / REFLECTANCIA_MAXIMA, 0, 1) * 255).astype("uint8")


def baixar_cena(data: str, identificador: str) -> dict:
    with urllib.request.urlopen(CATALOGO + identificador, timeout=60) as resposta:
        item = json.load(resposta)

    canais = {}
    urls = {}
    for nome, codigo in BANDAS.items():
        urls[codigo] = item["assets"][nome]["href"]
        with rasterio.open(urls[codigo]) as origem:
            dados = origem.read(1, window=JANELA)
            perfil = origem.profile | {
                "driver": "GTiff",
                "height": JANELA.height,
                "width": JANELA.width,
                "transform": origem.window_transform(JANELA),
                "compress": "deflate",
            }
            perfil.pop("blockxsize", None)
            perfil.pop("blockysize", None)
            perfil.pop("tiled", None)
            perfil.pop("interleave", None)
            escala, deslocamento = origem.scales[0], origem.offsets[0]
            crs = str(origem.crs)
            transformacao = list(perfil["transform"])[:6]
        with rasterio.open(SAIDA / f"{data}_{codigo}.tif", "w", **perfil) as destino:
            destino.write(dados, 1)
        canais[nome] = para_8_bits(dados, escala, deslocamento)

    # O SWIR 2 (B12) tem 20 m/px: cada pixel é repetido para casar com a grade de 10 m.
    urls["B12"] = item["assets"]["swir22"]["href"]
    with rasterio.open(urls["B12"]) as origem:
        swir = origem.read(
            1,
            window=Window(JANELA.col_off // 2, JANELA.row_off // 2, 750, 750),
            out_shape=(JANELA.height, JANELA.width),
            resampling=Resampling.nearest,
        )
        Image.fromarray(para_8_bits(swir, origem.scales[0], origem.offsets[0])).save(
            SAIDA / f"{data}_swir2.png"
        )

    urls["SCL"] = item["assets"]["scl"]["href"]
    # A SCL tem 20 m/px: a janela de 1500 px a 10 m equivale a 750 px a 20 m.
    with rasterio.open(urls["SCL"]) as origem:
        scl = origem.read(
            1, window=Window(JANELA.col_off // 2, JANELA.row_off // 2, 750, 750)
        )

    rgb = np.dstack([canais["red"], canais["green"], canais["blue"]])
    Image.fromarray(rgb).save(SAIDA / f"{data}_rgb.png")
    Image.fromarray(canais["nir"]).save(SAIDA / f"{data}_nir.png")
    # Um arquivo por data para a demonstração: cor nas três primeiras bandas e
    # infravermelho próximo na quarta (lido por `dataio.carregar_com_infravermelho`).
    Image.fromarray(np.dstack([rgb, canais["nir"]]), "RGBA").save(
        SAIDA / f"{data}_cor-e-infravermelho.png"
    )

    return {
        "cena": identificador,
        "coletado_em": item["properties"]["datetime"],
        "nuvem_cena_percentual": item["properties"]["eo:cloud_cover"],
        "pixels_ruins_recorte_percentual": float(np.isin(scl, SCL_RUINS).mean() * 100),
        "processamento": item["properties"].get("s2:processing_baseline"),
        "crs": crs,
        "transformacao": transformacao,
        "urls": urls,
    }


def principal() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")
    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")

    manifesto = {
        "fonte": CATALOGO,
        "janela": {
            "col": JANELA.col_off,
            "lin": JANELA.row_off,
            "largura": JANELA.width,
            "altura": JANELA.height,
        },
        "metros_por_pixel": 10,
        "reflectancia_maxima_8_bits": REFLECTANCIA_MAXIMA,
        "cenas": {data: baixar_cena(data, nome) for data, nome in CENAS.items()},
    }
    (SAIDA / "manifesto.json").write_text(
        json.dumps(manifesto, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"gravado em {SAIDA}")


if __name__ == "__main__":
    principal()
