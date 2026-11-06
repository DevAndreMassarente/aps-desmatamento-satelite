"""Mede o critério de confiabilidade e a detecção contra o PRODES, em Sentinel-2.

Divide o tile T22MCU em janelas de 15 km e usa o PRODES como referência independente:

- ``calibrar``: mede NDVI, NDMI e NBR nas janelas, sem o recorte de teste;
- ``testar``: mede o recorte de teste com o índice fixado (NBR) e o limite vigente.

A perda da referência é o desmatamento PRODES de 2019 a 2024. O PRODES mapeia supressão de
vegetação primária, e a máscara do programa também reage a pasto e rebrota, então a
precisão medida aqui não separa erro do método de diferença de definição.

Execução, sem acrescentar `rasterio` ao ambiente do projeto:

    uv run --no-project --with rasterio --with numpy --with pillow \
        python _interno/scripts/validar_prodes.py calibrar
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.warp import transform_geom
from rasterio.windows import Window

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from sentinela.pdi import limiar  # noqa: E402
from sentinela.pipeline.deteccao import detectar_desmatamento, preparar_indice  # noqa: E402

BASE = "https://e84-earth-search-sentinel-data.s3.us-west-2.amazonaws.com/sentinel-2-c1-l2a/22/M/CU/"
ANTES = BASE + "2018/7/S2B_T22MCU_20180703T135111_L2A/"
DEPOIS = BASE + "2024/7/S2A_T22MCU_20240716T135306_L2A/"
WFS = "https://terrabrasilis.dpi.inpe.br/geoserver/ows"
BBOX_TILE = "-52.82,-6.45,-51.80,-5.40"
CAMADAS = ("yearly_deforestation", "accumulated_deforestation_2007", "no_forest", "hydrography")
ANO_INICIAL, ANO_FINAL = 2019, 2024

LADO = 1500
TILE = 10980
TRANSFORMACAO = from_origin(300000, 9400000, 10, 10)
TESTE_LIN, TESTE_COL = 9250, 750
REFLECTANCIA_MAXIMA = 0.5
AGUA_MAXIMA = 0.01
INDICES = {"ndvi": None, "ndmi": "B11", "nbr": "B12"}
GANHO_VISUAL = 3.0
COR_SOBREPOSICAO = (230, 57, 70)

PRODES = RAIZ / "_interno" / "data" / "raw" / "prodes"
RESULTADOS = RAIZ / "_interno" / "docs" / "resultados" / "sentinel-2"


def baixar_prodes() -> None:
    PRODES.mkdir(parents=True, exist_ok=True)
    for camada in CAMADAS:
        destino = PRODES / f"{camada}.json"
        if destino.exists():
            continue
        consulta = urllib.parse.urlencode(
            {
                "service": "WFS",
                "version": "1.0.0",
                "request": "GetFeature",
                "typeName": f"prodes-legal-amz:{camada}",
                "outputFormat": "application/json",
                "bbox": BBOX_TILE,
            }
        )
        with urllib.request.urlopen(f"{WFS}?{consulta}", timeout=300) as resposta:
            destino.write_bytes(resposta.read())


def rasterizar(camada: str, aceita=lambda propriedades: True) -> np.ndarray:
    dados = json.loads((PRODES / f"{camada}.json").read_text(encoding="utf-8"))
    geometrias = [
        transform_geom("EPSG:4674", "EPSG:32722", feicao["geometry"])
        for feicao in dados["features"]
        if aceita(feicao["properties"])
    ]
    return rasterize(
        geometrias,
        out_shape=(TILE, TILE),
        transform=TRANSFORMACAO,
        fill=0,
        default_value=1,
        dtype="uint8",
    ).astype(bool)


def referencias() -> dict[str, np.ndarray]:
    return {
        "nova": rasterizar(
            "yearly_deforestation", lambda p: ANO_INICIAL <= p["year"] <= ANO_FINAL
        ),
        "antiga": rasterizar("yearly_deforestation", lambda p: p["year"] < ANO_INICIAL)
        | rasterizar("accumulated_deforestation_2007")
        | rasterizar("no_forest"),
        "agua": rasterizar("hydrography"),
    }


def ler_banda(base: str, banda: str, lin: int, col: int, *, meia_resolucao: bool = False) -> np.ndarray:
    """Lê a janela com a mesma escala linear de 8 bits de ``baixar_sentinel.py``."""
    with rasterio.open(f"{base}{banda}.tif") as origem:
        if meia_resolucao:
            janela = Window(col // 2, lin // 2, LADO // 2, LADO // 2)
            dados = origem.read(
                1, window=janela, out_shape=(LADO, LADO), resampling=Resampling.nearest
            )
        else:
            dados = origem.read(1, window=Window(col, lin, LADO, LADO))
        reflectancia = dados.astype("float32") * origem.scales[0] + origem.offsets[0]
    return (np.round(np.clip(reflectancia / REFLECTANCIA_MAXIMA, 0, 1) * 255) / 255).astype("float32")


def ler_data(base: str, metodo: str, lin: int, col: int) -> dict[str, np.ndarray | None]:
    vermelho = ler_banda(base, "B04", lin, col)
    swir = None
    if INDICES[metodo]:
        swir = ler_banda(base, INDICES[metodo], lin, col, meia_resolucao=True)
    return {
        "rgb": np.dstack([vermelho] * 3),
        "nir": ler_banda(base, "B08", lin, col),
        "swir": swir,
    }


def comparar(perda: np.ndarray, referencia: np.ndarray) -> dict[str, float]:
    comum = int((perda & referencia).sum())
    return {
        "perda_fracao": round(float(perda.mean()), 4),
        "precisao": round(comum / max(int(perda.sum()), 1), 3),
        "revocacao": round(comum / max(int(referencia.sum()), 1), 3),
    }


def calibrar() -> None:
    mapas = referencias()
    linhas = []
    for lin in range(0, TILE - LADO + 1, LADO):
        for col in range(0, TILE - LADO + 1, LADO):
            cruza_teste = (
                lin + LADO > TESTE_LIN
                and lin < TESTE_LIN + LADO
                and col + LADO > TESTE_COL
                and col < TESTE_COL + LADO
            )
            recorte = (slice(lin, lin + LADO), slice(col, col + LADO))
            if cruza_teste or mapas["agua"][recorte].mean() >= AGUA_MAXIMA:
                continue
            linha = {
                "lin": lin,
                "col": col,
                "nova": round(float(mapas["nova"][recorte].mean()), 4),
                "antiga": round(float(mapas["antiga"][recorte].mean()), 4),
            }
            for metodo in INDICES:
                antes = ler_data(ANTES, metodo, lin, col)
                depois = ler_data(DEPOIS, metodo, lin, col)
                ia, _ = preparar_indice(
                    antes["rgb"], antes["nir"], metodo=metodo, suavizacao=5, swir=antes["swir"]
                )
                id_, _ = preparar_indice(
                    depois["rgb"], depois["nir"], metodo=metodo, suavizacao=5, swir=depois["swir"]
                )
                valor, _, metricas = limiar.limiar_confiavel(ia, id_)
                linha[metodo] = {
                    "distinguibilidade": round(metricas["distinguibilidade"], 3),
                    **comparar((ia > valor) & (id_ <= valor), mapas["nova"][recorte]),
                }
            linhas.append(linha)
            print(linha, flush=True)
    (RESULTADOS / "calibracao.json").write_text(
        json.dumps(linhas, indent=1, ensure_ascii=False), encoding="utf-8"
    )


def testar() -> None:
    mapas = referencias()
    recorte = (slice(TESTE_LIN, TESTE_LIN + LADO), slice(TESTE_COL, TESTE_COL + LADO))
    antes = ler_data(ANTES, "nbr", TESTE_LIN, TESTE_COL)
    depois = ler_data(DEPOIS, "nbr", TESTE_LIN, TESTE_COL)
    resultado = detectar_desmatamento(
        antes["rgb"],
        depois["rgb"],
        antes["nir"],
        depois["nir"],
        swir_antes=antes["swir"],
        swir_depois=depois["swir"],
        metodo="nbr",
        metros_por_pixel=10,
    )
    referencia = mapas["nova"][recorte]
    saida = {
        "limite_vigente": limiar.DISTINGUIBILIDADE_MINIMA,
        "confiavel": bool(resultado.confiavel),
        "distinguibilidade": round(resultado.metricas["distinguibilidade"], 3),
        "limiar_faixa_0_1": round(float(resultado.valor_limiar), 4),
        "limiar_nbr_nativo": round(float(resultado.valor_limiar) * 2 - 1, 4),
        "area_programa_ha": resultado.resumo()["area_hectares"],
        "area_mascara_ha": round(float(resultado.perda.sum()) * 0.01, 1),
        "area_prodes_ha": round(float(referencia.sum()) * 0.01, 1),
        "prodes_antigo_fracao": round(float(mapas["antiga"][recorte].mean()), 4),
        "regioes": len(resultado.regioes),
        **comparar(resultado.perda, referencia),
    }
    (RESULTADOS / "teste.json").write_text(
        json.dumps(saida, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    salvar_figuras(resultado.perda, referencia)
    print(json.dumps(saida, indent=1, ensure_ascii=False))


def salvar_figuras(perda: np.ndarray, referencia: np.ndarray) -> None:
    """Grava os painéis do slide. O ganho de brilho serve só para visualização."""
    pasta = RAIZ / "_interno" / "data" / "raw" / "sentinel-2"
    figuras = RAIZ / "_interno" / "docs" / "apresentacao" / "figuras"

    def clarear(data: str) -> np.ndarray:
        rgb = np.asarray(Image.open(pasta / f"{data}_rgb.png"), dtype="float32")
        return np.clip(rgb * GANHO_VISUAL, 0, 255).astype("uint8")

    antes, depois = clarear("2018-07-03"), clarear("2024-07-16")

    def sobrepor(mascara: np.ndarray) -> np.ndarray:
        painel = depois.copy()
        painel[mascara] = COR_SOBREPOSICAO
        return painel

    paineis = {
        "sentinel-antes": antes,
        "sentinel-depois": depois,
        "sentinel-mascara": sobrepor(perda),
        "sentinel-prodes": sobrepor(referencia),
    }
    for nome, painel in paineis.items():
        Image.fromarray(painel).resize((750, 750), Image.Resampling.BILINEAR).save(figuras / f"{nome}.png")


if __name__ == "__main__":
    os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")
    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
    comandos = {"calibrar": calibrar, "testar": testar}
    if len(sys.argv) != 2 or sys.argv[1] not in comandos:
        sys.exit("uso: validar_prodes.py {calibrar|testar}")
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    baixar_prodes()
    comandos[sys.argv[1]]()
