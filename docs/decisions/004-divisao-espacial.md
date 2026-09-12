# 004 — Divisão treino/teste por blocos espaciais, não por sorteio de recorte

**Status:** aceito
**Contexto:** etapa de modelo (enunciado p.3, item 3.b) — R035, R039

## Problema

`pipeline.extrair_amostras` varre a imagem com **passo menor que o lado do recorte**, de
propósito: um par bi-temporal de área pequena rende poucas janelas disjuntas, e a
sobreposição multiplica a quantidade de amostras sem precisar de mais cena.

O efeito colateral é que recortes vizinhos **compartilham pixels**. Com `lado=16` e
`passo=8`, dois recortes adjacentes têm metade da área em comum.

Se a divisão entre treino e teste for feita sorteando recortes individualmente — que é o
padrão de `train_test_split` — o mesmo pedaço de terreno cai dos dois lados. O modelo é
avaliado em pixels que já viu no treino, e a métrica mede memorização, não
generalização.

O sintoma é traiçoeiro: a acurácia sobe. Não há erro, não há exceção, e o número fica
bom. É exatamente o tipo de resultado que passa despercebido numa apresentação e não
sobrevive a uma pergunta de banca.

## Decisão

A imagem é dividida em **blocos quadrados** de lado `3 × lado_do_recorte`. O sorteio
para treino ou teste é feito **por bloco**, não por recorte. Só entram no conjunto os
recortes que cabem inteiros dentro de um bloco; os que cruzam fronteira são descartados.

Como os blocos são disjuntos e cada recorte está contido em exatamente um deles, nenhum
recorte de treino compartilha um pixel com um recorte de teste. A propriedade é
verificada por força bruta em `tests/test_modelo.py::test_nenhum_pixel_e_compartilhado_entre_treino_e_teste`,
que enumera os pixels dos dois conjuntos e checa a interseção.

## Alternativa descartada: corte único ao meio

A primeira implementação cortava a imagem numa linha vertical, com uma faixa-tampão
descartada. É mais simples e garante o isolamento igualmente bem.

Foi descartada na medição: desmatamento é **espacialmente concentrado**. Numa cena com o
corte no centro, a divisão vertical jogou a área desmatada inteira para o lado do treino,
e o conjunto de teste ficou com **uma classe só** — 156 amostras, todas intactas.
O resultado foi acurácia 1,0 com precisão e revocação 0,0: um modelo que responde sempre
"intacto" acerta tudo quando não há nada para encontrar.

Blocos sorteados espalham as duas classes pelos dois conjuntos, porque o desmatamento
cruza vários blocos.

## Custo aceito

Recortes que cruzam fronteira de bloco são perdidos. Com bloco de `3 × lado` e passo de
`lado/2`, isso descarta em torno de 1 em cada 6 recortes por eixo. É o preço do
isolamento e está declarado.

A divisão também exige **pelo menos dois blocos** com recortes válidos. Cena pequena
demais produz um bloco só, e aí não existe divisão honesta possível: o código levanta
`ErroModelo` explicando que a cena é pequena, em vez de devolver uma métrica sem
significado.

## Consequência para o trabalho escrito

A métrica reportada no Capítulo 4.d precisa vir acompanhada da descrição da divisão. Uma
acurácia de modelo de visão computacional sobre patches sobrepostos, sem menção ao
isolamento espacial, é um número que não se sustenta se alguém perguntar como foi medido.

## Referência

A prática é conhecida na literatura de aprendizado sobre dados geoespaciais como
*spatial block cross-validation*, motivada pela autocorrelação espacial: amostras
próximas não são independentes. `NEEDS_SOURCE` — localizar a referência formal antes de
citar no trabalho escrito; **não citar de memória**.
