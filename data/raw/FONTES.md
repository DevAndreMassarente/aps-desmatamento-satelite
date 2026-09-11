# Fontes das imagens

As imagens **não são versionadas** (ver `docs/decisions/002-dados-nao-versionados.md`).
Este arquivo registra a origem de cada uma para que qualquer integrante reproduza o download.

> **Regra:** nenhuma imagem entra em `data/raw/` sem uma linha aqui.
> Nenhuma imagem sintética pode ser apresentada como real.

## Onde obter dados de desmatamento

| Fonte | O que oferece | Acesso |
|-------|---------------|--------|
| Copernicus Browser | Sentinel-2, 10 m/pixel, bandas RGB + NIR (B08) | https://browser.dataspace.copernicus.eu/ |
| INPE — TerraBrasilis | Polígonos e dados do PRODES/DETER (Amazônia) | http://terrabrasilis.dpi.inpe.br/ |
| INPE — Catálogo de Imagens | CBERS, Landsat, Sentinel | http://www.dgi.inpe.br/catalogo/ |
| USGS EarthExplorer | Landsat 8/9, 30 m/pixel | https://earthexplorer.usgs.gov/ |

Para a abordagem bi-temporal deste projeto é preciso **duas imagens da mesma área**, em datas
diferentes, preferencialmente com pouca cobertura de nuvem e no mesmo período do ano (para
evitar que variação sazonal seja confundida com desmatamento).

## Registro

Preencher conforme as imagens forem baixadas:

| Arquivo | Satélite / Produto | Data | Coordenadas (centro) | Resolução | Nuvens | Licença | URL |
|---------|--------------------|------|----------------------|-----------|--------|---------|-----|
| _(vazio)_ | | | | | | | |

## Modelo de preenchimento

```text
| area01_t1.tif | Sentinel-2 L2A | 2023-07-14 | -9.15, -63.02 | 10 m | 2% | Copernicus (aberta) | <url> |
| area01_t2.tif | Sentinel-2 L2A | 2025-07-19 | -9.15, -63.02 | 10 m | 4% | Copernicus (aberta) | <url> |
```
