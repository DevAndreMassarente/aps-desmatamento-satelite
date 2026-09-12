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
verificado por 294 testes construídos contra propriedades matemáticas conhecidas, e não
contra a saída de outra biblioteca.

## O resultado principal não foi o esperado, e é o mais importante

A aplicação dos filtros sobre imagens reais de satélite terminou em **recusa**: o sistema
identificou que a cena disponível não sustentava a separação entre as classes e não
reportou área de desmatamento.

A recusa está correta. A 253 metros por pixel, quase todo pixel de uma frente de
desmatamento contém floresta, pastagem, regeneração e estrada simultaneamente. O índice
espectral de um pixel misto cai entre os valores das classes puras, e as distribuições das
duas datas se sobrepõem fortemente. O sinal de perda existe, e a mediana do índice cai de
forma clara entre as duas datas. Há um vale entre as classes, mas raso — e a limiarização
global precisa de um vale profundo para separar duas populações com confiança.

Seria trivial produzir um número: bastaria baixar o critério de aceitação de 4,0 para 3,0 e
o sistema reportaria uma área. **Isso não foi feito.** Ajustar a régua depois de ver a
medida é escolher o critério em função do resultado desejado, e o número que sairia dali
não significaria nada.

O que o trabalho entrega no lugar é mais defensável: um sistema com critério explícito de
recusa, o registro de que o critério disparou na primeira imagem real processada, e o
diagnóstico da causa obtido por medição — três hipóteses testadas e descartadas em ordem,
até a identificação da resolução espacial como fator limitante.

## O que foi aprendido

**Que a salvaguarda vale mais que o resultado.** O critério de confiabilidade foi projetado
para um caso hipotético — uma cena de floresta intacta em que o limiar automático cortaria
o ruído do dossel ao meio. Ele disparou numa situação diferente da prevista e estava certo
nas duas vezes: primeiro numa cena contaminada por fumaça de queimada, depois por
insuficiência de resolução. Um sistema que sempre emite veredito teria produzido, nas duas
ocasiões, um número errado sem nenhum sinal de alarme.

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
| Resolução de 253 m/pixel | impede a quantificação de área validada |
| Produto de imagem é de visualização, com realce não linear | o índice é qualitativo, não comparável à literatura |
| Desempenho do classificador medido só em cena sintética | não diz nada sobre imagem real |
| Descritores de textura não validados | hipótese da literatura, ainda não medida |
| Critério de confiabilidade calibrado em cena sintética | precisa de recalibração por procedimento independente |

## Trabalhos futuros

1. **Obter imagens de 10 a 30 metros por pixel** — Sentinel-2 ou Landsat. É a única
   limitação que separa o sistema de um resultado quantitativo, e a cadeia de filtros roda
   sem alteração sobre essa entrada: o que muda é a resolução, não o método.

2. **Recalibrar o critério de confiabilidade por procedimento independente** — medir a
   distribuição do tamanho de efeito em pares de floresta comprovadamente intacta, como
   controle negativo, e em pares com desmatamento validado por fonte externa, como controle
   positivo. Nunca sobre a cena cujo resultado se quer obter.

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

O que falta para o sistema produzir um número defensável sobre o mundo real não é código —
é resolução de imagem. E a demonstração de que o sistema **sabe disso**, e se recusa a
produzir o número enquanto não a tiver, é o resultado que este trabalho entrega.
