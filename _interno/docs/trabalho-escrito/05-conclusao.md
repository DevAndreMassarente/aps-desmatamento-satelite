# 5. Conclusão

## O que foi construído

O trabalho entregou um sistema completo de detecção bi-temporal de perda de cobertura
vegetal, cobrindo as cinco etapas nomeadas pelo enunciado: aquisição, manipulação,
filtragem, segmentação e modelo de visão computacional.

Todos os filtros de processamento digital de imagens foram implementados pelo grupo, com
NumPy como única dependência do núcleo — convolução e correlação, tratamento de borda em
quatro modos, suavização gaussiana e por média, filtro de mediana, operadores de Sobel,
Prewitt e Laplaciano, realce de nitidez, textura por desvio padrão local, limiarização de
Otsu, morfologia binária e rotulagem de componentes conexos por união-busca.

O sistema é operável por três caminhos — biblioteca, linha de comando e interface web — e é
verificado por 363 testes automatizados. Os filtros são testados contra propriedades
matemáticas conhecidas, e não contra a saída de outra biblioteca.

## O resultado principal não foi o esperado, e é o mais importante

A aplicação dos filtros sobre imagens reais de satélite terminou em **recusa**: o sistema
identificou que a cena disponível não sustentava a separação entre as classes e não
reportou área de desmatamento.

No par MODIS, a recusa é coerente com o que as distribuições mostram. A 253 metros por pixel, quase todo pixel de uma frente de
desmatamento contém floresta, pastagem, regeneração e estrada simultaneamente. O índice
espectral de um pixel misto cai entre os valores das classes puras, e as distribuições das
duas datas se sobrepõem fortemente. O sinal de perda existe, e a mediana do índice cai de
forma clara entre as duas datas. Há um vale entre as classes, mas raso — e a limiarização
global precisa de um vale profundo para separar duas populações com confiança.

Seria trivial produzir um número: bastaria baixar o critério de aceitação de 4,0 para 3,0 e
o sistema reportaria uma área. **Isso não foi feito.** Ajustar a régua depois de ver a
medida é escolher o critério em função do resultado desejado, e o número que sairia dali
não significaria nada.

A hipótese de resolução foi então testada com imagem Sentinel-2 de 10 metros por pixel. Os
talhões ficaram visíveis, mas o recorte também foi recusado, com tamanho de efeito de 3,974.
Comparada ao PRODES apenas como diagnóstico, a máscara marcou 7.974,6 ha contra 4.124,8 ha, com
precisão de 0,383 e revocação de 0,740. Portanto, a resolução explica só parte do problema.

O que o trabalho entrega no lugar é mais defensável: um sistema com critério explícito de
recusa, o registro de que o critério disparou em imagens reais, e uma medição do erro contra
uma referência independente.

## O que foi aprendido

**Que a salvaguarda vale mais que o resultado.** O critério de confiabilidade foi projetado
para um caso hipotético — uma cena de floresta intacta em que o limiar automático cortaria
o ruído do dossel ao meio. Ele também disparou em situações diferentes da prevista: numa
cena contaminada por fumaça de queimada, no par MODIS e no recorte Sentinel-2. Neste último, a
comparação com o PRODES mostrou que a máscara ainda não sustentava um número em hectares. Um
sistema que sempre emite veredito teria reportado essa área sem nenhum sinal de alarme.

**Que a etapa de aquisição decide o resultado tanto quanto o algoritmo.** O erro mais caro
do projeto não esteve em nenhum filtro: esteve em medir cobertura de nuvem sobre uma
composição em infravermelho de ondas curtas, faixa que atravessa a fumaça. A cena passou no
controle com 0% de nuvem e inverteu a comparação entre as datas. Nenhuma melhoria no
processamento teria corrigido isso.

**Que medir é diferente de supor.** Três premissas do trabalho foram testadas e
**refutadas** pela medição: a de que bandas do mesmo produto de imagem teriam o mesmo
realce, a de que os descritores de textura separariam as classes na cena de validação, e a
de que um índice melhor resolveria a limitação de resolução. Todas as três estavam
plausíveis no papel.

**Que a forma de medir o desempenho de um modelo pode inventá-lo.** Como os recortes de
treino se sobrepõem, uma divisão aleatória entre treino e teste colocaria o mesmo pedaço de
terreno nos dois lados e a acurácia mediria memorização. A primeira tentativa de divisão
espacial, por corte único da imagem, produziu um conjunto de teste com uma classe só —
acurácia 1,0 com revocação 0,0.

## Limitações

| Limitação | Consequência |
|-----------|--------------|
| Máscara não validada: recusa a 253 m e a 10 m, e área quase 2× maior que a do PRODES no recorte | impede a quantificação de área validada |
| Validação em um único recorte, escolhido para concentrar perda, e calibração em um único tile | os números não representam a região inteira |
| Produto de imagem é de visualização, com realce não linear | o índice é qualitativo, não comparável à literatura |
| Desempenho do classificador medido só em cena sintética | não diz nada sobre imagem real |
| Descritores de textura não validados | hipótese da literatura, ainda não medida |
| Critério de confiabilidade calibrado em cena sintética, com primeira medição real em poucos controles | precisa de calibração com mais controles e outros tiles |

## Trabalhos futuros

1. **Separar melhor a floresta de pastagem e regeneração** — reduzir a área marcada a mais
   na comparação com o PRODES, usando mais de um índice ou uma máscara de floresta da primeira
   data.

2. **Ampliar a calibração do critério de confiabilidade** — medir o tamanho de efeito com mais
   controles negativos e positivos, em outros tiles e datas. Nunca sobre a cena cujo resultado
   se quer obter.

3. **Normalização radiométrica relativa entre as datas** — alvos invariantes na cena
   permitiriam corrigir a diferença sistemática entre aquisições separadas por décadas,
   antes da comparação.

4. **Validar os descritores de textura em imagem real**, onde a hipótese de que dossel
   fechado é mais irregular que pastagem pode de fato ser medida.

5. **Paralelizar a mediana**, o único filtro de suavização que não admite forma separável
   — estatística de ordem não se decompõe em passes de uma dimensão.

## Considerações finais

O objetivo declarado no enunciado é usar o processamento digital de imagens como
**preparação de dados** para um modelo de visão computacional, e não como produto final.
Essa cadeia está completa e funcionando: a segmentação produz a máscara, a máscara rotula
os recortes, os recortes alimentam o classificador, e o classificador informa quais
descritores pesaram na sua decisão.

O sistema ainda não produz um número defensável sobre o mundo real: a resolução de 10 metros
não bastou, e o método precisa separar melhor as classes. O que este trabalho entrega é a cadeia
funcionando, um critério que recusa esse número e a medição do erro contra uma referência
independente.
