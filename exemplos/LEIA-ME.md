# Imagens de exemplo

Par de imagens reais do satélite Sentinel-2, da mesma área do Pará, para testar o programa
logo depois de instalar. Envie a de 2018 em **Imagem antes** e a de 2024 em **Imagem depois**.

| Arquivo | Data | Cena |
|---------|------|------|
| `2018-07-03_cor-e-infravermelho.png` | 2018-07-03 | `S2B_T22MCU_20180703T135111_L2A` |
| `2024-07-16_cor-e-infravermelho.png` | 2024-07-16 | `S2A_T22MCU_20240716T135306_L2A` |

Cada arquivo é um PNG de quatro bandas: vermelho, verde e azul formam a cor, e a quarta banda
é o infravermelho próximo. Por isso o arquivo pode parecer transparente num visualizador
comum. Recorte de 1.500 × 1.500 pixels, 10 m por pixel.

Procedência completa em `_interno/data/raw/FONTES.md`. As imagens são regeneradas por
`_interno/scripts/baixar_sentinel.py`.

Contains modified Copernicus Sentinel data 2018, 2024.
