# 3. Proposta

## 3.a. Processamento digital de imagens

Esta seção está completa — é parte da Fase Intermediária I.

### Filtros escolhidos e a função de cada um

A escolha não foi por catálogo. Cada filtro entrou porque resolve um problema concreto
que aparece na cadeia, e sai um passo antes de onde ele atrapalharia.

| Etapa | Filtro | Por que está aqui |
|-------|--------|-------------------|
| Realce espectral | Índice de vegetação (NDVI / NDMI) | Reduz as bandas a um mapa escalar onde vegetação e solo exposto ficam em extremos opostos |
| Suavização | Gaussiano 5×5 | Impede que o ruído do sensor atravesse o limiar pixel a pixel |
| Limiarização | Otsu sobre o histograma **conjunto** | Separa vegetação de não-vegetação com a mesma régua nas duas datas |
| Limpeza | Abertura seguida de fechamento | Remove respingos isolados e fecha buracos internos |
| Contorno | Gradiente morfológico | Extrai a borda das regiões para exibição |
| Realce de borda | Sobel — magnitude do gradiente | Torna visível a fronteira floresta/corte na apresentação |
| Textura | Desvio padrão local 5×5 | Descritor para a etapa de modelo |

### As três decisões que determinam o resultado

#### 1. Suavizar antes de limiarizar, não depois

A ordem não é indiferente. Suavizar **depois** da limiarização operaria sobre uma máscara
binária — seria morfologia, não filtragem — e não recuperaria a informação já destruída
pelo limiar. O ruído precisa ser atenuado enquanto o dado ainda é contínuo.

O efeito de omitir esse passo é mensurável: sem suavização a máscara sai esburacada, e a
contagem de componentes conexos explode. O sistema reportaria centenas de regiões de
poucos pixels onde existe uma só, inviabilizando a análise por região que o Capítulo 1
justifica como necessária.

#### 2. Um limiar único para as duas datas

É a decisão mais importante da proposta, e a mais fácil de errar.

O caminho intuitivo — calcular Otsu em cada data e comparar as máscaras — está errado.
Cada data receberia um limiar diferente, adaptado ao seu próprio histograma, e a diferença
entre as máscaras passaria a medir a diferença entre os limiares em vez da mudança no
terreno.

O caso que expõe o erro: se a primeira data é floresta intacta, seu histograma é unimodal;
o Otsu corta o ruído do dossel ao meio e classifica metade da floresta como não-vegetação.
A comparação com a segunda data acusaria desmatamento massivo inexistente.

A solução adotada calcula o limiar sobre o histograma **combinado** das duas datas. As
duas passam a ser medidas pela mesma régua, e basta que **uma** delas contenha as duas
classes para que o limiar seja bem definido.

Isso é verificável no repositório: em uma cena de teste, o Otsu isolado de cada data
difere em mais de 0,15, enquanto o limiar conjunto fica a menos de 0,05 do limiar da data
que contém as duas classes.

#### 3. Filtrar por área em vez de erodir repetidamente

Fragmentos residuais da segmentação poderiam ser removidos por erosões sucessivas. A
proposta descarta regiões abaixo de uma área mínima explícita.

A diferença é de prestação de contas: erosão remove por um critério implícito — quantas
vezes foi aplicada, com que elemento estruturante — enquanto o filtro por área declara o
critério em unidade física. A 10 m/pixel, 25 pixels são 2.500 m², e o texto pode dizer
exatamente isso. Além disso, a erosão encolhe as regiões que sobrevivem, o que enviesaria
a quantificação de área para baixo.

### Resultados obtidos

#### Verificação em cena sintética

Antes de aplicar em imagem real, a cadeia foi verificada contra uma cena construída com
área de desmatamento de tamanho **conhecido**. A cena é sintética e está identificada como
tal em todo o material — ela serve para verificar a correção do encadeamento, não como
evidência sobre o mundo.

| Verdade de terreno | Detectado | Erro |
|--------------------|-----------|------|
| 400 pixels (corte de 20×20) | 400 pixels | 0,0% |
| 6.400 pixels (corte de 80×80) | 6.400 pixels | 0,0% |

A 10 m/pixel, os 6.400 pixels correspondem a 64,0 ha. O controle negativo também foi
verificado: um par de duas datas de floresta intacta é corretamente classificado como não
confiável, e nenhuma área é reportada.

#### Aplicação em imagens reais

| | |
|---|---|
| Área | São Félix do Xingu (PA) — frente de expansão da pecuária |
| Sensor | MODIS/Terra Corrected Reflectance, via NASA GIBS |
| Datas | 2002-07-01 e 2024-07-05 |
| Resolução | ≈253 m/pixel |
| Qualidade | 0,0% de nuvem, bruma equiparada entre as datas |

A mudança na paisagem entre as duas datas é visualmente inequívoca: a cena de 2002 é
floresta contínua; a de 2024 apresenta clareiras extensas.

**O sistema recusou-se a quantificar.**

| Índice | Tamanho de efeito | Veredito |
|--------|-------------------|----------|
| NDVI | 2,994 | recusado |
| NDMI | 3,509 | recusado |
| Limiarização da imagem de diferença | 2,788 | recusado |
| *Mínimo exigido* | *4,000* | — |
| *Piso de uma distribuição sem duas classes* | *2,650* | — |

### Análise do resultado

O resultado negativo tem causa identificada, e ela não está no código.

A 253 m/pixel, numa frente de desmatamento, quase todo pixel é **mistura**: contém
floresta, pastagem, regeneração e estrada simultaneamente. O índice espectral de um pixel
misto cai entre os valores das classes puras. O resultado é um histograma contínuo, sem o
vale que a limiarização global precisa para separar duas populações.

O sinal de perda existe e tem a direção correta. Na escala nativa dos índices, `[-1, 1]`,
a mediana cai de +0,944 para +0,794 no NDVI (queda de 0,150) e de +0,799 para +0,504 no
NDMI (queda de 0,295). São quedas grandes — mas é um **deslocamento da distribuição
inteira**, não a separação de dois modos. Toda a cena ficou menos vegetada; não há um
subconjunto que se destaque do resto.

Três hipóteses foram testadas antes de chegar a essa conclusão:

| Hipótese | Teste | Resultado |
|----------|-------|-----------|
| O índice é inadequado | NDVI × NDMI × NBR | NDMI é o melhor (3,509 contra 2,994), ainda insuficiente |
| A abordagem é inadequada | Limiarizar a diferença em vez de classificar cada data | **Pior**: 2,788, e marcaria 40% da cena como perda |
| A resolução é insuficiente | Inspeção das distribuições | **Confirmado** |

É a mesma razão pela qual sistemas oficiais de monitoramento de desmatamento operam com
imagens de 20 a 30 metros e não com MODIS.

#### Uma decisão metodológica deliberada

Seria trivial atingir o critério baixando o valor exigido de 4,0 para 3,0. **Isso não foi
feito**, e a recusa foi mantida como resultado.

Ajustar o limiar de aceitação depois de ver a medida é escolher a régua em função do
resultado desejado. O valor 4,0 foi calibrado em cena sintética e de fato precisa de
recalibração — mas por um procedimento honesto: medir a distribuição do tamanho de efeito
em pares de floresta comprovadamente intacta, como controle negativo, e em pares com
desmatamento validado por fonte independente, como controle positivo. Nunca sobre a cena
cujo resultado se quer obter.

#### O que este resultado demonstra

Que o sistema tem um critério de recusa, que o critério disparou na primeira imagem real
processada, e que a causa foi diagnosticada por medição em vez de suposição.

Um sistema que sempre emite um veredito teria, nesta mesma cena, reportado uma área de
desmatamento — e o Capítulo 1 já argumentou que o custo de um falso positivo recai sobre
alguém.

#### Achado secundário: fumaça atravessa o infravermelho de ondas curtas

A primeira tentativa de aquisição usou uma data de agosto, auge da estação de queimadas na
região. A cena estava tomada por fumaça, e o controle de qualidade a aprovou com 0% de
nuvem — porque media a cobertura sobre a composição em infravermelho de ondas curtas, e
essa faixa **atravessa a fumaça**.

O efeito sobre o resultado foi grosseiro e fácil de diagnosticar: o índice de vegetação da
floresta de 2001 caiu **abaixo** do da pastagem de 2024, invertendo a comparação. O
sistema recusou a detecção e emitiu o aviso de ganho de vegetação implausível — o controle
de sanidade descrito na seção 2.d funcionou como projetado.

A correção foi passar a medir bruma no canal azul da composição **visível**, onde o
espalhamento atmosférico aparece, usando o percentil 5: a fumaça levanta o piso da
distribuição porque elimina os pixels escuros da cena. A calibração é reproduzível — 78 na
cena com fumaça contra 6 a 34 nas cenas limpas da mesma área e estação.

#### Limitação declarada do produto de imagem

O produto utilizado é de **visualização**, com realce não linear para 8 bits. O índice
calculado sobre ele é **qualitativo**: serve para comparar duas datas e separar classes,
não para reportar valor absoluto comparável à literatura. Valor absoluto exigiria produto
de refletância de superfície.

Uma consequência prática foi medida: o serviço publica a mesma banda espectral em dois
produtos diferentes, com realces diferentes — média 88 em um e 62 no outro, com correlação
0,97. Montar um índice com a banda vermelha de um produto e a infravermelha do outro
embutiria um viés sistemático de origem puramente gráfica. Por isso as duas bandas são
extraídas do mesmo produto.

### O que falta para o resultado quantitativo

Imagem de 10 a 30 m/pixel — Sentinel-2 ou Landsat. As duas fontes exigem cadastro
gratuito. Com essa entrada, a mesma cadeia de filtros roda sem alteração: o que muda é a
resolução da entrada, não o método.

---

## 3.b. Modelagem

`[RASCUNHO — a ser completado antes da entrega final. Implementação em
src/sentinela/modelo/, com 25 testes.]`

Pontos a desenvolver, todos já implementados e verificáveis:

- **O papel do PDI como preparação de dados.** A máscara de segmentação fornece o rótulo
  de cada recorte; é assim que o processamento de imagens alimenta o modelo, conforme a
  redação do objetivo no enunciado.
- **Descritores.** Quinze medidas por recorte — estatísticas por banda, índices
  espectrais, textura, borda e percentis de brilho — todas calculadas com os filtros do
  próprio grupo.
- **Escolha do algoritmo.** Floresta aleatória, pela explicabilidade: o modelo informa
  quais descritores pesaram na decisão.
- **Rotulagem.** Recortes ambíguos, que cobrem parte de floresta e parte de corte, são
  **descartados** em vez de arredondados para a classe majoritária. Rotular a borda de um
  corte ensinaria o classificador a responder pela vizinhança em vez de pelo conteúdo.
- **Divisão treino/teste espacial.** Como os recortes se sobrepõem, o sorteio é feito por
  **blocos** da imagem, não por recorte. A ausência de pixels compartilhados entre treino
  e teste é verificada por enumeração.
- **Métricas.** Precisão, revocação, F1 e matriz de confusão nomeando os dois tipos de
  erro. A acurácia é relatada mas acompanhada de ressalva quando o conjunto é
  desbalanceado.
- **Limitação declarada.** O desempenho medido até agora vem de cena sintética, onde a
  separação foi construída, e **não valida o modelo**.
