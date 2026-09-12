# 2. Referencial teórico

## 2.d. Descrição formal do problema computacional

### Entrada

Duas imagens multiespectrais da mesma área geográfica, captadas em instantes distintos:

```text
I₁, I₂ ∈ ℝ^(H × L × B)
```

onde `H` e `L` são as dimensões em pixels e `B` o número de bandas espectrais. As duas
precisam estar recortadas sobre a mesma extensão geográfica e ter as mesmas dimensões —
caso contrário a comparação pixel a pixel não tem significado. Cada valor é a refletância
registrada numa banda, normalizada para o intervalo `[0, 1]`.

Opcionalmente, um escalar `r` com a resolução espacial em metros por pixel.

### Saída

1. Uma máscara binária de perda de cobertura vegetal:

```text
P ∈ {0, 1}^(H × L),   P(x, y) = 1  ⟺  havia vegetação em (x,y) em t₁ e não há em t₂
```

2. Um conjunto de regiões conexas `R = {r₁, …, r_n}` obtidas de `P`, cada uma com área em
   pixels, centroide e caixa delimitadora.
3. A área total perdida, em pixels e — se `r` for conhecido — em hectares:

```text
A_ha = |P| · r² / 10 000
```

4. Um veredito de confiabilidade `c ∈ {verdadeiro, falso}`. Quando `c` é falso, os itens 1
   a 3 **não constituem resultado**.

### Formulação

O problema decompõe-se em três passos.

**Passo 1 — redução de dimensionalidade espectral.** Cada imagem multiespectral é reduzida
a um mapa escalar em que a vegetação é separável do solo exposto:

```text
f : ℝ^B → [-1, 1]
V_i(x, y) = f(I_i(x, y, ·)),  i ∈ {1, 2}
```

A função `f` é um índice espectral. Este trabalho usa razões normalizadas entre pares de
bandas (seção 2.e.ii).

**Passo 2 — classificação binária por limiar.** Cada mapa é convertido em máscara de
vegetação por um limiar `t`:

```text
M_i(x, y) = 1  ⟺  V_i(x, y) > t
```

O ponto crítico da formulação: **`t` é único para as duas datas**, determinado sobre o
histograma conjunto `H(V₁) + H(V₂)`. Se cada data recebesse seu próprio limiar `t_i`, a
diferença entre `M₁` e `M₂` mediria a diferença entre `t₁` e `t₂` — uma propriedade dos
histogramas — e não a mudança no terreno. O caso que expõe o erro é uma data de floresta
intacta: seu histograma é unimodal, o limiar automático corta o ruído do dossel ao meio, e
a comparação acusaria supressão massiva inexistente.

**Passo 3 — diferença e filtragem por área.**

```text
P₀ = M₁ ∧ ¬M₂                            (perda)
G  = ¬M₁ ∧ M₂                            (ganho — usado como controle)
P  = { componentes conexos de P₀ com área ≥ a_min }
```

O ganho `G` não é descartado: em um intervalo de poucos anos, ganho de vegetação
comparável em área à perda indica que as duas cenas não estão alinhadas, ou que a
diferença é sazonal e não estrutural. É um controle de sanidade, não um resultado.

### O critério de confiabilidade

O limiar de Otsu **sempre** devolve um valor, mesmo quando não há duas classes a separar:
o método maximiza a separação entre dois grupos, e uma distribuição unimodal partida ao
meio ainda produz dois grupos. Aplicar o limiar sem verificação produziria desmatamento
onde há apenas ruído.

A verificação usa um tamanho de efeito padronizado entre as duas partes induzidas pelo
limiar:

```text
d(V, t) = |μ_alta − μ_baixa| / √((σ²_alta + σ²_baixa) / 2)
```

Partir uma distribuição normal unimodal no seu próprio centro produz `d ≈ 2,65` — esse é
o **piso**, o valor obtido quando não há classe nenhuma para separar. O sistema exige
`d ≥ 4,0` para declarar a detecção confiável.

A separabilidade `η` do artigo original de Otsu **não** serve para esse papel neste
problema, e a razão é mensurável: `η` carrega o fator `ω(1−ω)`, com `ω` a proporção da
classe. Uma cena homogênea partida em 50/50 tem `ω(1−ω) = 0,25`; uma cena com desmatamento
pequeno tem `ω(1−ω) ≈ 0,06`. Esse fator entra na variância entre classes e derruba o `η`
do caso real **abaixo** do caso homogêneo, invertendo o critério. O tamanho de efeito, que
não carrega o fator, ordena os dois casos corretamente. O teste que demonstra essa
inversão está em `tests/test_integracao.py`.

> `[NEEDS_SOURCE: OTSU, N. A threshold selection method from gray-level histograms.
> Localizar a referência completa (periódico, volume, ano, páginas) e conferir a definição
> de η no texto original antes de citar.]`

> `[NEEDS_SOURCE: definição formal de tamanho de efeito padronizado e a convenção de
> interpretação de magnitude. Conferir antes de citar.]`

---

## 2.e. Conceitos utilizados

### 2.e.i. Aquisição

Aquisição, no contexto deste trabalho, é obter duas cenas da mesma área geográfica em datas
distintas, com qualidade suficiente para que a comparação entre elas signifique mudança no
terreno e não diferença nas condições de captação.

#### Resolução espacial

A resolução espacial é o tamanho, no terreno, do lado de um pixel. Ela determina o que o
sistema consegue distinguir:

| Sensor | Resolução | Área de um pixel |
|--------|-----------|------------------|
| MODIS | 250 m | 6,25 ha |
| Landsat 8/9 | 30 m | 0,09 ha |
| Sentinel-2 | 10 m | 0,01 ha |

A consequência não é apenas de detalhe. Quando o alvo é menor que o pixel, o valor
registrado é uma **mistura** das refletâncias de tudo o que cabe dentro dele — o chamado
pixel misto. Numa frente de desmatamento, um pixel de 250 m contém simultaneamente
floresta, pastagem, regeneração e estrada, e seu índice espectral cai entre os valores das
classes puras. É por essa razão que o resultado deste trabalho sobre imagem real terminou
em recusa, e a discussão está no Capítulo 4.

#### Resolução temporal e a escolha das datas

Duas restrições governam a escolha das datas:

1. **Mesma estação do ano.** Vegetação tem ciclo sazonal. Comparar uma cena de estação
   chuvosa com uma de estação seca mede a estação, não o desmatamento.
2. **Intervalo suficiente.** O intervalo precisa ser grande o bastante para que a mudança
   acumulada se destaque da variação natural entre aquisições.

#### Qualidade da cena

Três defeitos invalidam uma cena, e cada um se manifesta de forma diferente:

| Defeito | Como aparece | O que provoca na detecção |
|---------|--------------|---------------------------|
| Ausência de dado | região sem valor, tipicamente escura | fronteira falsa entre o vazio e a cena |
| Nuvem | alta refletância em todas as bandas | lida como perda de vegetação |
| Bruma e fumaça | espalhamento que levanta o piso da cena | desloca o índice da cena inteira |

**A fumaça é o caso traiçoeiro, e este trabalho aprendeu isso por medição.** O espalhamento
atmosférico é fortemente dependente do comprimento de onda: intenso no azul, fraco no
infravermelho. A consequência prática é que **a fumaça é quase invisível no infravermelho
de ondas curtas**. Uma cena de agosto na Amazônia, tomada por fumaça de queimada, pode
passar sem alteração aparente numa composição que use essa faixa — e ao mesmo tempo ter o
seu NDVI severamente deprimido, porque o NDVI usa a banda vermelha, que a fumaça afeta.

Daí a regra adotada: **a bruma é medida nas bandas visíveis, não na composição de análise**.
O indicador é o percentil 5 do canal azul, porque a fumaça elimina os pixels escuros da
cena e levanta o piso da distribuição.

#### Reprodutibilidade da aquisição

Uma imagem sem procedência registrada não sustenta resultado acadêmico: não há como outro
grupo repetir a medição, nem como conferir se a cena é a que o texto afirma ser. Por isso
cada arquivo baixado neste trabalho tem satélite, produto, data, coordenadas do recorte,
licença e a URL exata da requisição registrados em manifesto.

A escolha de um serviço de acesso **sem credencial** foi deliberada: ela mantém a aquisição
reproduzível por qualquer integrante do grupo e por quem avalia o trabalho.

> `[NEEDS_SOURCE: dependência do espalhamento atmosférico com o comprimento de onda —
> espalhamento Rayleigh e Mie. Livro-texto de sensoriamento remoto. Conferir antes de
> citar.]`

> `[NEEDS_SOURCE: problema do pixel misto e o efeito da resolução espacial na
> classificação. Mesma referência serve. Ver também B10.]`

### 2.e.ii. Manipulação das imagens

Manipulação, aqui, é transformar a representação da imagem para que a informação de
interesse fique acessível. Nenhuma dessas operações remove ruído ou segmenta — elas mudam
o espaço em que a imagem está descrita.

#### Conversão para tons de cinza

A conversão por luminância pondera as bandas segundo a sensibilidade do olho humano:

```text
Y = 0,299·V + 0,587·G + 0,114·A
```

Os pesos não são iguais porque a percepção de brilho não é. Note que essa é uma
transformação **perceptual**, não radiométrica: para análise espectral ela descarta
justamente a informação que distingue as coberturas. Neste trabalho a conversão para cinza
é usada em medidas de textura e de borda, nunca para decidir se um pixel é vegetação.

#### Espaço HSV

A separação em matiz, saturação e valor desacopla a cor da intensidade. Sua utilidade em
imagem orbital é limitada — variação de iluminação entre datas afeta o valor mais que o
matiz — mas o espaço está implementado porque a conversão é conteúdo da disciplina e porque
permite inspecionar a cena por matiz na interface.

#### Índices espectrais como razões normalizadas

A forma comum a todos os índices usados é a razão normalizada entre duas bandas:

```text
ND(A, B) = (A − B) / (A + B)
```

Essa forma tem duas propriedades que a tornam adequada a imagem de satélite:

1. **Resultado limitado a `[-1, 1]`**, independentemente da escala das bandas.
2. **Robustez a variação multiplicativa.** Se as duas bandas forem escaladas por um mesmo
   fator — o que descreve, aproximadamente, uma diferença de iluminação — o fator cancela
   no numerador e no denominador. É isso que torna a razão comparável entre datas.

Essa robustez tem limite: variação **aditiva**, como a causada por espalhamento
atmosférico, não cancela. Por isso a seção anterior trata a bruma como defeito que invalida
a cena, em vez de algo que o índice resolveria.

#### NDVI — índice de vegetação por diferença normalizada

```text
NDVI = (NIR − V) / (NIR + V)
```

A base física: a clorofila absorve fortemente no vermelho, para fotossíntese, enquanto a
estrutura celular da folha reflete fortemente no infravermelho próximo. Vegetação sadia
combina, portanto, vermelho baixo e infravermelho alto — e o índice fica alto. Solo exposto
reflete de forma semelhante nas duas faixas, e o índice cai para perto de zero. Água
absorve mais no infravermelho que no vermelho, e o índice fica negativo.

**Limitação.** O NDVI satura em dossel denso: acima de certa biomassa ele para de
responder. E, por medir "verde", ele distingue mal floresta de pastagem vigorosa — as duas
são verdes.

#### NDMI — índice de umidade por diferença normalizada

```text
NDMI = (NIR − SWIR) / (NIR + SWIR)
```

Mede o conteúdo de água do dossel. Folha viva é cheia de água, que **absorve** no
infravermelho de ondas curtas; pastagem seca e solo exposto refletem bem nessa faixa.

É onde o NDMI ganha do NDVI: a diferença de água entre um dossel florestal e um capim é
grande mesmo quando a diferença de verde é pequena. Neste trabalho o efeito foi medido
sobre a cena real — o NDMI elevou a separabilidade entre as classes de 2,994 para 3,509.

#### ExG e VARI — quando só há bandas visíveis

Nem toda imagem disponível tem banda infravermelha. Duas alternativas operam só com o
visível:

```text
ExG  = 2g − v − a          sobre as bandas normalizadas pela soma
VARI = (G − V) / (G + V − A)
```

O ExG é mais sensível a variação de iluminação. O VARI inclui o termo do azul, que compensa
parte do espalhamento atmosférico, e por isso é mais estável em cena de satélite com bruma
leve. Nenhum dos dois substitui o NDVI: ambos medem "quão verde", não a assinatura
estrutural que o infravermelho revela.

#### Normalização de faixa

Os índices produzem valores em `[-1, 1]`, enquanto a limiarização e a morfologia deste
trabalho operam em `[0, 1]`. A conversão é afim, `(x + 1) / 2`, e portanto preserva a ordem
— um limiar encontrado na faixa convertida corresponde exatamente a um limiar do índice
original.

**Atenção ao relatar valores:** a conversão divide qualquer diferença pela metade. Toda
diferença de índice citada neste trabalho está na escala nativa `[-1, 1]`.

> `[NEEDS_SOURCE: NDVI — definição original e faixas típicas por tipo de cobertura.
> Ver B8.]`

> `[NEEDS_SOURCE: NDMI — definição e aplicação a umidade de dossel. Ver B9.]`

> `[NEEDS_SOURCE: ExG e VARI — proposição original de cada um. Conferir antes de citar.]`

> `[NEEDS_SOURCE: coeficientes de luminância da conversão RGB para tons de cinza —
> recomendação que os define. Conferir antes de citar.]`

### 2.e.iii. Filtragem

Esta seção está completa — é parte da Fase Intermediária I.

#### Convolução como operação base

Todos os filtros espaciais deste trabalho são casos particulares de uma operação só. A
convolução de uma imagem `I` por um núcleo `K` de dimensões `(2a+1) × (2b+1)` é:

```text
(I * K)(x, y) = Σ_{i=-a}^{a} Σ_{j=-b}^{b} K(i, j) · I(x − i, y − j)
```

A correlação cruzada é a mesma soma sem a inversão dos índices do núcleo:

```text
(I ⊗ K)(x, y) = Σ_{i} Σ_{j} K(i, j) · I(x + i, y + j)
```

A distinção importa e é frequentemente ignorada. Para núcleos simétricos — média,
gaussiano, laplaciano — as duas operações dão o mesmo resultado. Para núcleos
antissimétricos, como os operadores de Sobel e Prewitt, elas diferem no **sinal** do
resultado: uma borda clara-para-escura troca de sinal com uma escura-para-clara. Como
neste trabalho o que interessa é a magnitude do gradiente, o sinal não altera a conclusão
— mas a implementação precisa saber qual das duas está executando, e a deste trabalho
implementa as duas separadamente.

#### Tratamento de borda

Num pixel da margem, parte da vizinhança exigida pelo núcleo cai fora da imagem. Há três
saídas: encolher a imagem, inventar valores, ou estender a imagem por uma regra explícita.
Este trabalho estende, e oferece quatro regras:

| Modo | Regra | Efeito |
|------|-------|--------|
| `reflete` | espelha os pixels em torno da margem | padrão; não cria descontinuidade artificial |
| `replica` | repete o pixel da margem | usado em morfologia, onde o valor extremo importa |
| `zero` | preenche com zero | cria borda escura artificial; evitar em imagem de satélite |
| `circular` | trata a imagem como toroidal | raramente apropriado aqui |

A escolha não é cosmética: preencher com zero numa cena de floresta cria uma faixa escura
na margem que o índice de vegetação lê como solo exposto, e que a segmentação marcaria
como desmatamento na borda da imagem.

#### Filtros de suavização

**Média aritmética.** Núcleo com todos os pesos iguais a `1/k²`. Reduz ruído, mas borra
bordas com o mesmo peso com que borra o ruído, porque trata todos os vizinhos igualmente.

**Gaussiano.** Os pesos decaem com a distância ao centro:

```text
K(i, j) = (1 / 2πσ²) · exp(−(i² + j²) / 2σ²)
```

normalizado para somar 1, o que preserva o brilho médio da imagem. É o filtro usado antes
da limiarização neste trabalho. A razão é concreta: sem suavização, o ruído do sensor faz
pixels individuais atravessarem o limiar em ambas as direções, e a máscara sai esburacada.
Uma máscara esburacada multiplica a contagem de componentes conexos e inviabiliza a
análise por região — o sistema reportaria centenas de "áreas desmatadas" de poucos pixels
onde há uma só.

#### Separabilidade: uma propriedade algébrica com efeito mensurável

A convolução 2D direta custa `k²` multiplicações por pixel. Para o núcleo gaussiano esse
custo pode ser reduzido a `2k`, e a redução **não é uma aproximação**.

O expoente da gaussiana é uma soma, e o expoente de uma soma é o produto de exponenciais:

```text
G(x, y) = exp(−(x² + y²) / 2σ²) = exp(−x² / 2σ²) · exp(−y² / 2σ²) = g(x) · g(y)
```

O núcleo 2D é exatamente o produto externo de dois núcleos 1D idênticos. Convoluir a
imagem pelo núcleo 2D equivale a convoluí-la por `g` na horizontal e depois por `g` na
vertical. A normalização acompanha: se cada núcleo 1D soma 1, o produto externo soma 1,
que é a mesma condição imposta ao núcleo 2D.

O ganho foi medido sobre uma imagem de 440 × 440 pixels, comparando os dois caminhos:

| Lado da janela | 2D direto | Dois passes 1D | Ganho |
|----------------|-----------|----------------|-------|
| 3 | 0,9 ms | 0,7 ms | 1,4× |
| 5 | 1,8 ms | 0,8 ms | 2,2× |
| 9 | 5,1 ms | 1,3 ms | 3,9× |
| 15 | 13,5 ms | 2,6 ms | 5,2× |
| 21 | 23,9 ms | 2,5 ms | 9,4× |

A maior diferença observada entre os resultados dos dois caminhos foi de 1,0 × 10⁻⁶ —
compatível com o arredondamento de ponto flutuante de precisão simples, e não com uma
diferença de método. A equivalência é verificada por teste, inclusive nas bordas e nos
quatro modos de tratamento de margem, porque é lá que ela poderia falhar.

Nem todo filtro tem essa propriedade. O filtro de média também é separável, pelo mesmo
argumento de produto. O de mediana **não é**: a mediana de uma janela 2D não é a mediana
das medianas das linhas, porque estatísticas de ordem não se decompõem dessa forma.

**Mediana.** Não é uma convolução: substitui cada pixel pela mediana da vizinhança. Por ser
uma estatística de ordem, remove ruído impulsivo — pixel isolado com valor extremo — sem
borrar a borda, porque um valor extremo isolado não altera a mediana de uma janela. O
custo é ser mais caro que a convolução.

#### Filtros de realce de borda

Bordas são descontinuidades. Detectá-las é estimar derivadas espaciais.

**Sobel.** Aproxima as derivadas parciais combinando diferenciação numa direção com
suavização na outra:

```text
        ⎡ −1  0  +1 ⎤              ⎡ −1  −2  −1 ⎤
  K_x = ⎢ −2  0  +2 ⎥        K_y = ⎢  0   0   0 ⎥
        ⎣ −1  0  +1 ⎦              ⎣ +1  +2  +1 ⎦
```

O peso 2 na linha central é a suavização perpendicular, e é o que torna o Sobel menos
sensível a ruído que uma diferença simples.

**Prewitt.** Mesma estrutura com pesos uniformes — sem a ponderação central. Mais sensível
a ruído, e implementado aqui para permitir a comparação.

**Magnitude e direção do gradiente:**

```text
|∇I| = √(G_x² + G_y²)        θ = arctan(G_y / G_x)
```

A magnitude é invariante à orientação da borda; é ela que realça o contorno entre floresta
e área desmatada independentemente da direção do corte.

**Laplaciano.** Operador de segunda derivada, isotrópico:

```text
      ⎡  0  1  0 ⎤
  K = ⎢  1 −4  1 ⎥
      ⎣  0  1  0 ⎦
```

Por ser segunda derivada, responde a **mudança de taxa** de variação, o que o torna
sensível a detalhe fino e a ruído. A soma dos pesos é zero: uma região de intensidade
constante é levada a zero, e uma rampa linear também — propriedade usada como caso de
teste analítico neste trabalho.

**Realce de nitidez.** Subtrair uma fração do laplaciano da imagem original acentua as
transições:

```text
I' = I − c · ∇²I
```

#### Textura por desvio padrão local

O desvio padrão de uma janela deslizante é uma medida simples de textura. Sua motivação
neste problema é direta: dossel florestal fechado é irregular em altura e sombreamento,
produzindo desvio local alto; pastagem e solo exposto são homogêneos e produzem desvio
baixo.

Esta é uma hipótese da literatura, **ainda não validada neste trabalho** — a discussão
está no Capítulo 3.

#### Por que os filtros foram implementados pelo grupo

O enunciado exige (p.3, item 3.a). Além da exigência, a implementação própria tem
consequência prática sobre a defesa do trabalho: uma chamada a `cv2.GaussianBlur` não
permite responder o que acontece na borda, por que o núcleo é normalizado, ou por que o
resultado difere entre convolução e correlação. Com a implementação no repositório, cada
uma dessas perguntas tem resposta localizável em uma linha de código.

A restrição foi aplicada de forma verificável: dentro de `src/sentinela/pdi/` a única
dependência permitida é `numpy`, e a ausência de `cv2`, `skimage`, `scipy` e `PIL` é
conferida por inspeção do código.

> `[NEEDS_SOURCE: livro-texto de processamento digital de imagens para os operadores
> clássicos — convolução, Sobel, Prewitt, Laplaciano, filtro de mediana. Uma referência
> consolidada cobre todos. Conferir edição, capítulo e páginas antes de citar.]`

> `[NEEDS_SOURCE: proposição original dos operadores de Sobel e de Prewitt. Verificar se
> as fontes primárias são acessíveis; se não forem, citar pelo livro-texto e deixar isso
> explícito no texto.]`

### 2.e.iv. Segmentação

Segmentação é particionar a imagem em regiões com significado. Aqui, o significado é
binário — vegetação ou não — e a partição é feita por limiar, seguida de limpeza
morfológica e agrupamento em componentes conexos.

#### Limiarização de Otsu

O método busca o limiar que melhor separa duas classes num histograma, maximizando a
variância **entre** as classes:

```text
σ²_entre(t) = ω₀(t)·ω₁(t)·[μ₀(t) − μ₁(t)]²
```

onde `ω₀` e `ω₁` são as proporções das duas classes induzidas pelo limiar `t`, e `μ₀` e
`μ₁` suas médias. Maximizar a variância entre classes é equivalente a minimizar a soma
ponderada das variâncias internas — as duas formulações são a mesma decisão, porque a
variância total do histograma não depende de `t`.

A vantagem do método é não exigir parâmetro: ele deriva o limiar do próprio histograma.
Essa é também a origem do seu risco, tratado na seção 2.d — ele devolve um valor mesmo
quando não há duas classes a separar.

#### Limiar adaptativo

Quando a iluminação varia ao longo da cena, um limiar global falha: o valor que separa as
classes numa região não separa na outra. O limiar adaptativo calcula um limiar local por
vizinhança, tipicamente a média local menos um deslocamento.

Este trabalho o implementa, mas **não** o usa no caminho principal: a comparação
bi-temporal exige uma régua única para as duas datas, e uma régua que varia com a posição
inviabilizaria a comparação entre cenas.

#### Limiarização com histerese

Dois limiares em vez de um: pixels acima do limiar alto são aceitos incondicionalmente;
pixels entre os dois limiares são aceitos apenas se conectados a algum pixel já aceito.
O resultado é mais robusto a ruído que um limiar único, porque exige evidência de
vizinhança para os casos duvidosos.

#### Morfologia matemática

Operadores sobre máscaras binárias, definidos por um elemento estruturante:

| Operador | Definição | Efeito |
|----------|-----------|--------|
| Erosão | mínimo local sob o elemento | encolhe regiões, elimina detalhe menor que o elemento |
| Dilatação | máximo local sob o elemento | expande regiões, preenche vãos estreitos |
| Abertura | erosão seguida de dilatação | remove salientes e ruído isolado, preservando o tamanho geral |
| Fechamento | dilatação seguida de erosão | fecha buracos e vãos, preservando o tamanho geral |
| Gradiente morfológico | dilatação menos erosão | extrai o contorno |

Abertura e fechamento são **idempotentes**: aplicá-las duas vezes dá o mesmo resultado que
aplicá-las uma vez. Essa propriedade é usada como caso de teste neste trabalho.

A sequência adotada é abertura seguida de fechamento: primeiro remover o respingo isolado,
depois fechar o buraco interno. A ordem inversa fecharia buracos ao redor de respingos antes
de removê-los, consolidando o ruído.

#### Componentes conexos

Uma máscara binária diz quais pixels pertencem à classe, mas não quais formam a mesma
região. Agrupá-los exige definir vizinhança:

- **conectividade 4** — apenas vizinhos ortogonais;
- **conectividade 8** — incluindo as diagonais.

A escolha altera o resultado: duas regiões que se tocam apenas na diagonal são uma só em
conectividade 8 e duas em conectividade 4. Este trabalho usa 8 como padrão, porque cortes
de desmatamento têm contorno irregular e a conectividade 4 os fragmentaria artificialmente.

O algoritmo usado é a varredura em duas passagens com estrutura de **união-busca**. A
alternativa recursiva estoura a pilha em regiões grandes; a união-busca não tem esse
limite. O caso que exige a resolução de equivalências é uma região em forma de "U", cujos
dois braços recebem rótulos diferentes na primeira passagem e precisam ser unificados.

#### Descrição das regiões e filtro por área

De cada componente extraem-se área em pixels, centroide e caixa delimitadora. É o que
permite tratar cada evento de desmatamento como uma entidade, e não apenas somar pixels —
necessidade justificada no Capítulo 1 pela dependência do impacto ecológico em relação à
geometria do corte.

O filtro por área descarta regiões abaixo de um mínimo. Ele é preferível a erosões
sucessivas por duas razões: o critério fica explícito em unidade física, e a erosão
encolheria as regiões sobreviventes, enviesando a quantificação para baixo.

> `[NEEDS_SOURCE: método de Otsu — formulação da variância entre classes. Ver B4.]`

> `[NEEDS_SOURCE: morfologia matemática — definição dos operadores e a propriedade de
> idempotência de abertura e fechamento. Livro-texto de PDI. Ver B6.]`

> `[NEEDS_SOURCE: rotulagem de componentes conexos por varredura em duas passagens com
> união-busca. Conferir antes de citar.]`

### 2.e.v. Proposta teórica do modelo de visão computacional

#### O papel do processamento de imagens

A redação do objetivo no enunciado é explícita: o processamento digital de imagens produz
**dados preparados que possam alimentar um modelo de visão computacional**. O PDI não é o
produto final.

A articulação entre as duas etapas, neste trabalho, é a seguinte: a máscara de segmentação
não é apenas o resultado — ela é a **fonte de rótulos**. Cada recorte da imagem recebe a
classe da região que ele cobre, e o conjunto resultante é o que um classificador consome.
É assim que a etapa de PDI alimenta a etapa de aprendizado sem que nenhuma anotação manual
seja necessária.

#### Descritores em vez de pixels crus

Um recorte de 16 × 16 em três bandas tem 768 valores. Entregá-los crus a um classificador
clássico exigiria que ele aprendesse, dos dados, quais combinações importam — e a
quantidade de amostras extraíveis de um par de cenas não sustenta isso.

A alternativa adotada é descrever cada recorte por um conjunto reduzido de medidas com
significado conhecido: estatísticas por banda, índices espectrais, textura, resposta de
borda e percentis de brilho. Cada número tem uma justificativa física, e **todos são
calculados pelos filtros implementados pelo grupo**.

#### Escolha do algoritmo

Uma rede neural convolucional é o estado da arte para classificação de imagens, e daria
desempenho superior. Ela **não** foi escolhida, e a razão é o critério de avaliação do
enunciado: a apresentação inclui arguição, e o trabalho precisa ser defensável.

Floresta aleatória foi escolhida por informar quais descritores pesaram na decisão. Isso
permite responder "por que o modelo classificou este recorte como desmatado?" apontando
para uma medida concreta, calculada por um filtro cujo código está no apêndice. Uma rede
convolucional treinada sobre algumas centenas de recortes daria um número melhor e nenhuma
resposta a essa pergunta.

#### O problema de avaliação: vazamento espacial

Aqui está a decisão metodológica que mais afeta a credibilidade da métrica.

Os recortes são extraídos por varredura com passo menor que o lado, de propósito — a
sobreposição multiplica a quantidade de amostras. A consequência é que recortes vizinhos
**compartilham pixels**.

Uma divisão aleatória entre treino e teste colocaria o mesmo pedaço de terreno nos dois
conjuntos. O modelo seria avaliado sobre pixels que já viu, e a métrica mediria memorização
em vez de generalização. O sintoma é traiçoeiro porque a acurácia **sobe**: não há erro,
não há exceção, e o número fica bom.

A solução adotada divide a imagem em blocos, sorteia o **bloco** — não o recorte — e admite
apenas recortes que cabem inteiros dentro de um bloco. Como os blocos são disjuntos, nenhum
recorte de treino compartilha pixel com um de teste.

#### Métricas adequadas

Numa cena típica a floresta domina, e o conjunto de amostras é desbalanceado. A acurácia é
inadequada nesse cenário: um classificador que responde sempre "intacto" acerta a maioria.

O trabalho reporta precisão, revocação e F1, além da matriz de confusão com os dois tipos de
erro nomeados — falso alarme e desmatamento não detectado. A distinção importa porque os
dois custam coisas diferentes, como o Capítulo 1 argumenta.

> `[NEEDS_SOURCE: floresta aleatória — formulação original e a medida de importância de
> variáveis. Conferir antes de citar.]`

> `[NEEDS_SOURCE: validação cruzada espacial e autocorrelação em dados geoespaciais.
> Ver B12.]`

> `[NEEDS_SOURCE: métricas para classificação com classes desbalanceadas — definição de
> precisão, revocação e F1. Conferir antes de citar.]`
