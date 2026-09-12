# Resultados — imagens REAIS de satélite

Diferente de `docs/evidence/demo-sintetica/`, **estas imagens são reais** e podem ser
usadas no trabalho escrito, com as ressalvas abaixo.

## Origem

| | |
|---|---|
| Área | São Félix do Xingu (PA) — frente de expansão da pecuária na Amazônia |
| Recorte | -7,0 / -52,5 / -6,0 / -51,5 (EPSG:4326), ~110 km de lado |
| Sensor | MODIS/Terra Corrected Reflectance, via NASA GIBS |
| Datas | 2002-07-01 e 2024-07-05 |
| Resolução | ~253 m/pixel (aproximada) |
| Procedência | `data/raw/FONTES.md` e `data/raw/sao-felix_manifesto.json` |

Reproduzir:

```bash
python scripts/baixar_imagens.py --regiao sao-felix
sentinela detectar \
  --antes  data/raw/sao-felix_2002-07-01_analise.png \
  --depois data/raw/sao-felix_2024-07-05_analise.png \
  --nir-antes   data/raw/sao-felix_2002-07-01_nir.png \
  --nir-depois  data/raw/sao-felix_2024-07-05_nir.png \
  --swir-antes  data/raw/sao-felix_2002-07-01_swir.png \
  --swir-depois data/raw/sao-felix_2024-07-05_swir.png \
  --metodo ndmi --metros-por-pixel 253 --area-minima 4 --saida docs/evidence/results
```

As imagens desta pasta foram geradas com `--metodo ndmi`, que é a melhor leitura
disponível para esta cena.

## O resultado foi uma RECUSA

**Nenhuma área desmatada é reportada para esta cena.**

| Índice | Distinguibilidade | Veredito |
|--------|-------------------|----------|
| NDVI | 2,99 | recusado |
| **NDMI** (NIR − SWIR) | **3,51** | recusado |
| Mínimo exigido | 4,00 | — |
| Piso de uma distribuição sem duas classes | 2,65 | — |

O NDMI mede água do dossel em vez de verde e separa melhor floresta de pastagem, mas o
ganho não bastou.

A 253 m/pixel quase todo pixel da frente de desmatamento é mistura de floresta, pastagem,
regeneração e estrada. O índice sai contínuo em vez de bimodal, e não existe vale no
histograma onde cortar. A perda existe e tem a direção certa — na escala nativa do índice,
a mediana do NDVI cai 0,150 e a do NDMI cai 0,295 entre as duas datas — mas é um
deslocamento da distribuição inteira, não separável por limiar global.

Diagnóstico completo, com as três hipóteses testadas: `docs/decisions/005-resolucao-espacial.md`.

> **Não calcule área a partir destas imagens.** O programa se recusa a produzi-la, e o
> motivo é metodológico, não um defeito.

## O que as imagens mostram

| Arquivo | Conteúdo |
|---------|----------|
| `01-antes.png`, `02-depois.png` | Composição de análise (vermelho, NIR, SWIR) das duas datas |
| `03-indice-antes.png`, `04-indice-depois.png` | NDVI em falsa cor — a perda de vegetação é visível |
| `05-vegetacao-antes.png`, `06-vegetacao-depois.png` | Máscaras do limiar de Otsu |
| `07-mapa-mudanca.png` | Classificação em perda / ganho / estável |
| `08-perda-detectada.png` | Máscara de perda após filtro de área |
| `09-sobreposicao.png` | Sobreposição sobre a cena de 2024 |
| `resumo.json` | Métricas — com `area_pixels: null`, que é a recusa |

As máscaras das etapas 05 a 09 **são exibidas para inspeção**, não como resultado. Elas
mostram o que o algoritmo fez com um limiar que ele próprio classificou como não
confiável.

## Para obter um resultado quantitativo

É preciso imagem de 10 a 30 m/pixel:

| Fonte | Resolução | Acesso |
|-------|-----------|--------|
| Copernicus Data Space — Sentinel-2 L2A | 10 m | cadastro gratuito |
| USGS EarthExplorer — Landsat 8/9 | 30 m | cadastro gratuito |

As duas exigem conta, que precisa ser criada por um integrante do grupo.
