# 005 — A resolução de 250 m não sustenta a detecção; o critério de confiabilidade provou isso

**Status:** aceito — registra um resultado negativo e o que ele exige
**Contexto:** R032 (filtros em imagens reais), B5 (calibração da distinguibilidade)

## O que foi feito

Primeira execução do pipeline sobre **imagem real de satélite**: par bi-temporal de São
Félix do Xingu (PA), frente de expansão da pecuária na Amazônia, MODIS/Terra Corrected
Reflectance via NASA GIBS, 2002-07-01 e 2024-07-05, ~253 m/pixel.

A mudança na paisagem é visualmente inequívoca: em 2002 a cena é floresta contínua; em
2024 há clareiras extensas ocupando boa parte do recorte.

## O que aconteceu

O sistema **recusou-se a reportar área**. A distinguibilidade entre as duas classes ficou
em 2,99, contra o mínimo exigido de 4,0 — e o piso teórico de partir uma distribuição
unimodal ao meio é 2,65. Ou seja: a métrica ficou a 13% do valor que se obteria numa cena
sem classe nenhuma para separar.

Três hipóteses foram testadas, em ordem:

| Hipótese | Teste | Resultado |
|----------|-------|-----------|
| O índice está errado | NDVI × NDMI (NIR-SWIR) × NBR | NDMI é melhor — distinguibilidade 3,51 contra 2,99 — mas ainda abaixo de 4,0 |
| A abordagem está errada | Limiarizar a imagem de **diferença** em vez de classificar cada data | Pior: 2,79, colado no piso unimodal, e marcaria 40% da cena como perda |
| A resolução não permite | Inspeção das distribuições | **Confirmado** — ver abaixo |

## Causa

A 253 m/pixel, numa frente de desmatamento, **quase todo pixel é mistura**: floresta,
pastagem, regeneração e estrada dentro do mesmo pixel. O índice de vegetação de um pixel
misto cai entre as duas classes puras, e o histograma sai contínuo em vez de bimodal.

Os dois histogramas ficaram unimodais e sobrepostos. O sinal existe e tem a direção certa:
na escala nativa do índice, `[-1, 1]`, a mediana cai de +0,944 para +0,794 no NDVI (0,150)
e de +0,799 para +0,504 no NDMI (0,295). Mas a queda é da **distribuição inteira** — não
há vale no histograma onde cortar.

> Atenção à escala ao reproduzir estes números: internamente o pipeline mapeia o índice
> para `[0, 1]` por `(x+1)/2` antes de limiarizar, o que reduz qualquer diferença à
> metade. As quedas acima estão na escala nativa do índice.

Não é limitação do código. É a razão pela qual o PRODES, do INPE, mapeia desmatamento com
Landsat a 20–30 m e não com MODIS.

## Decisão

1. **Não ajustar `DISTINGUIBILIDADE_MINIMA` para fazer esta cena passar.** Baixar o limiar
   até o resultado aparecer é escolher a régua depois de ver a medida. O número foi
   calibrado em cena sintética (B5) e de fato precisa de recalibração, mas por um
   procedimento honesto: medir a distribuição da métrica em pares de floresta intacta
   (controle negativo) e em pares com desmatamento validado pelo PRODES, não neste par.
2. **Manter o resultado negativo como resultado.** A recusa é o comportamento correto e
   demonstrável: o sistema não inventou 40% de desmatamento onde o histograma não
   sustentava a divisão.
3. **Obter imagem de 10 a 30 m** antes de reportar quantificação no trabalho escrito.
   Sentinel-2 (10 m, Copernicus Data Space) ou Landsat 8/9 (30 m, USGS EarthExplorer).
   As duas exigem cadastro, que precisa ser feito por um integrante do grupo. O NASA GIBS,
   usado aqui por não exigir credencial, não serve essa resolução: as camadas HLS existem
   no catálogo mas com janela de demonstração (S30 cobre 2015-11-28 a 2015-12-11).
4. **Adotar NDMI quando houver banda SWIR.** Medido: separa melhor que o NDVI nesta cena
   (3,51 contra 2,99). **Implementado** em `pdi.cor.ndmi`, exposto por `--metodo ndmi` e
   pela interface. Não entra no modo automático: ele mede água do dossel, não verde, e
   trocar a grandeza sem o usuário pedir mudaria a interpretação do resultado sem aviso.

## Achado secundário: fumaça atravessa o SWIR

A primeira tentativa usou 2001-08-20, auge da estação de queimadas. O controle de
qualidade mediu nuvem na composição Bands721 e aprovou a cena com 0%. A banda 7 é
infravermelho de ondas curtas e **atravessa a fumaça**; a banda 1, usada pelo NDVI, não.

O resultado foi uma inversão: a floresta de 2001 apareceu **menos** vegetada que a
pastagem de 2024. O sistema recusou a detecção e emitiu o aviso de ganho de vegetação
implausível — o controle de registro funcionou como projetado.

A correção foi medir bruma no canal azul da composição **visível**, onde o espalhamento
aparece, usando o percentil 5: fumaça levanta o piso da distribuição porque elimina os
pixels escuros da cena. Calibração: 78 na cena com fumaça, 6 a 34 nas cenas limpas da
mesma área e estação.

## Consequência para o trabalho escrito

Este resultado negativo **vale mais que um número bonito** no Capítulo 4.d, e é defensável
numa banca: mostra que o sistema tem um critério de recusa, que o critério disparou na
primeira imagem real, e que a causa foi diagnosticada com medição em vez de suposição.

O que **não** pode acontecer é apresentar uma área desmatada calculada a partir desta
cena. O próprio programa se recusa a produzi-la.

## Referências

`NEEDS_SOURCE` — antes de citar no trabalho escrito, localizar e conferir:

- Metodologia PRODES/INPE e a justificativa da escolha de sensor e resolução.
- Literatura sobre o problema do pixel misto em sensoriamento remoto.
- Definição formal do NDMI e sua aplicação a estresse hídrico e cobertura florestal.

**Não citar nenhuma dessas de memória.**
