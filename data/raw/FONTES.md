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

### São Félix do Xingu (PA) — par bi-temporal MODIS

Baixado em 2026-09-12 por `python scripts/baixar_imagens.py --regiao sao-felix`.
Manifesto completo, com as URLs exatas: `data/raw/sao-felix_manifesto.json`.

| Arquivo | Satélite / Produto | Data | Coordenadas (bbox) | Resolução | Nuvem | Bruma | Licença |
|---------|--------------------|------|--------------------|-----------|-------|-------|---------|
| `sao-felix_2002-07-01_*.png` | MODIS/Terra Corrected Reflectance (via NASA GIBS) | 2002-07-01 | -7,0 / -52,5 / -6,0 / -51,5 | ~253 m/px | 0,0% | p05 azul = 6 | Domínio público (NASA) |
| `sao-felix_2024-07-05_*.png` | MODIS/Terra Corrected Reflectance (via NASA GIBS) | 2024-07-05 | -7,0 / -52,5 / -6,0 / -51,5 | ~253 m/px | 0,0% | p05 azul = 6 | Domínio público (NASA) |

Três arquivos por data:

| Sufixo | Conteúdo | Para quê |
|--------|----------|----------|
| `_cor-real` | TrueColor — bandas 1, 4, 3 | Figuras do trabalho escrito |
| `_analise` | Bandas **1 (vermelho), 2 (NIR), 7 (SWIR)** nessa ordem | Entrada do pipeline |
| `_nir` | Banda 2 isolada, em tons de cinza | Entrada do pipeline |

### Por que o vermelho e o NIR saem do mesmo produto

O GIBS publica a banda 1 em dois produtos, com **realces de 8 bits diferentes**: média 88
na TrueColor contra 62 na Bands721, correlação 0,97. Medimos antes de usar. Montar o NDVI
com o vermelho de um e o NIR do outro embutiria um viés sistemático de origem puramente
gráfica. Por isso as duas bandas vêm da Bands721, cujos canais são (SWIR, NIR, vermelho) —
o arquivo `_analise` é essa composição reordenada para (vermelho, NIR, SWIR).

### Por que estas datas, e não agosto

A primeira tentativa usou 2001-08-20. A cena estava tomada por **fumaça de queimada** —
agosto é o auge da estação. O controle de qualidade não pegou porque media nuvem na
composição Bands721, e a banda 7 (SWIR) **atravessa fumaça**: a cena passou com 0% de
nuvem. O efeito no resultado foi grosseiro: o NDVI de 2001 caiu abaixo do de 2024, a
floresta apareceu menos vegetada que a pastagem, e o sistema corretamente recusou a
detecção com aviso de ganho de vegetação implausível.

A correção foi medir bruma no **canal azul da composição visível**, onde o espalhamento
aparece (`scripts/baixar_imagens.py::avaliar_qualidade`). As datas atuais são de início de
julho nas duas pontas: mesma estação e, medido, o mesmo nível de bruma.

### Resolução nativa das bandas

A grade de ≈253 m/pixel é a da renderização do GIBS, não a do sensor. No MODIS, as bandas 1
(vermelho) e 2 (NIR) têm 250 m; as bandas 3 (azul), 4 (verde) e 7 (SWIR 2) têm **500 m**
(NASA, [s. d.]). A banda SWIR destas imagens foi, portanto, reamostrada — e, por ser SWIR 2,
o índice NIR − SWIR calculado com ela é o **NBR**, não o NDMI.

### Limitação do produto

Corrected Reflectance é produto de **visualização**, com realce não linear para 8 bits. O
NDVI calculado sobre ele é **qualitativo**: serve para comparar duas datas e separar
classes, não para reportar valor absoluto comparável à literatura. Refletância de
superfície (MOD09, Sentinel-2 L2A) seria necessária para isso.

### O que estas imagens não resolvem

A 253 m/pixel, quase todo pixel numa frente de desmatamento é **mistura** de floresta,
pastagem, regeneração e estrada. As distribuições das duas datas se sobrepõem, o vale entre
as classes é raso, e o critério de confiabilidade recusou a detecção — corretamente. Ver
`docs/decisions/005-resolucao-espacial.md`.

**Para o resultado quantitativo do trabalho escrito é preciso imagem de 10 a 30 m.** Isso
exige conta no Copernicus Data Space ou no USGS EarthExplorer, que precisa ser criada por
um integrante do grupo. O GIBS não serve essa resolução sem credencial: as camadas HLS
existem no catálogo, mas com janela temporal de demonstração (S30 cobre apenas
2015-11-28 a 2015-12-11).

