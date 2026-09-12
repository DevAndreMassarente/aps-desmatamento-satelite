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

`[RASCUNHO — a ser completado antes da entrega final. O conteúdo já existe no
repositório: data/raw/FONTES.md e scripts/baixar_imagens.py.]`

Pontos a desenvolver, todos já apurados e verificáveis:

- Sensores e resoluções: MODIS (250 m), Landsat (30 m), Sentinel-2 (10 m).
- Serviços de acesso e por que a escolha recaiu sobre um que dispensa credencial.
- Critérios de qualidade de cena: ausência de dado, cobertura de nuvem e **bruma**.
- O achado de que **fumaça de queimada atravessa o infravermelho de ondas curtas**, e por
  que isso invalidou a primeira tentativa de aquisição.
- A necessidade de casar a estação do ano entre as duas datas.

### 2.e.ii. Manipulação das imagens

`[RASCUNHO — a ser completado. Implementação em src/sentinela/pdi/cor.py.]`

Pontos a desenvolver:

- Conversão para tons de cinza por luminância ponderada e conversão RGB→HSV.
- **NDVI** `= (NIR − V)/(NIR + V)`: vegetação sadia reflete no infravermelho próximo e
  absorve no vermelho pela clorofila.
- **NDMI** `= (NIR − SWIR)/(NIR + SWIR)`: mede água do dossel. Separa floresta de pastagem
  vigorosa melhor que o NDVI, que confunde as duas por serem ambas verdes.
- **ExG** e **VARI**, alternativas quando só há bandas visíveis.
- Por que a razão normalizada é robusta a variação multiplicativa de iluminação.
- A limitação do produto de visualização usado, cujo realce não linear torna o índice
  qualitativo.

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

`[RASCUNHO — a ser completado. Implementação em pdi/limiar.py, pdi/morfologia.py e
pdi/segmentacao.py.]`

Pontos a desenvolver, todos já implementados:

- Limiarização de Otsu: maximização da variância entre classes sobre o histograma.
- Limiar adaptativo e limiar duplo com histerese.
- Morfologia binária: erosão, dilatação, abertura, fechamento, gradiente morfológico e
  preenchimento de buracos.
- Rotulagem de componentes conexos por união-busca, com conectividade 4 e 8.
- Filtro por área como critério explícito e mensurável, preferível a erodir repetidamente.

### 2.e.v. Proposta teórica do modelo de visão computacional

`[RASCUNHO — a ser completado. Implementação em src/sentinela/modelo/.]`

Pontos a desenvolver:

- Por que a etapa de PDI é **preparação de dados**, conforme a redação do objetivo no
  enunciado, e não um fim em si.
- Descritores extraídos de cada recorte, todos calculados com os filtros do próprio grupo.
- Escolha de floresta aleatória pela explicabilidade — o modelo informa quais descritores
  pesaram na decisão, o que permite responder à arguição.
- Por que a divisão treino/teste precisa ser **espacial** quando os recortes se sobrepõem.
- Métricas adequadas a conjunto desbalanceado: precisão, revocação e F1, não acurácia.
