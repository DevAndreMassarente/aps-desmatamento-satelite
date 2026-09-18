# Falas — Fase Intermediária I (Qualificação)

Enunciado, p. 5: *"Fase Intermediária I — Qualificação do Projeto. Conteúdo: **Capítulo 1 e
os itens relativos a filtragem dos capítulos 2 e 3**. Esta etapa deve ser concluída antes do
desenvolvimento prático."*

> **Fica de fora:** separar as áreas, medir hectares, o modelo, a demonstração do programa e
> qualquer resultado. Tudo isso é da próxima entrega, e está em `FALAS-DEFESA.md`.

São **11 slides**, sendo o último de reserva. As mesmas falas estão nas notas do apresentador
em `entrega/apresentacao-qualificacao.pptx`.

## Como usar este documento

Cada pessoa tem duas partes:

1. **Antes de apresentar** — o que você precisa entender para falar com segurança. Leia isso
   com calma, é para estudar, não para decorar.
2. **A fala** — o que dizer em cada slide. É um guia; fale com as suas palavras.

> Se você não consegue explicar com as suas palavras, ainda não está pronto. Decorar não
> resolve, porque a pergunta da banca nunca é igual ao slide.

## Divisão — cerca de 11 minutos

| Slides | Quem | Assunto | Tempo |
|--------|------|---------|------:|
| 1–2 | André Massarente | Abertura e o problema | 2:00 |
| 3–4 | Enzo Consani | Por que importa e o que vamos construir | 2:30 |
| 5–7 | Isabel Da Silva | O que é filtragem | 3:30 |
| 8–10 | Jonathan Aparecido X Martins | Os filtros que escolhemos e o fecho | 3:00 |
| 11 | Isabel Da Silva | Reserva — **só se perguntarem** | +1:00 |

---

# André Massarente — slides 1 e 2

## Antes de apresentar

**O que é uma imagem de satélite.** O satélite não tira "foto" como um celular. Ele mede
quanta luz o chão devolve, em várias faixas separadas: vermelho, verde, azul, e também faixas
que o olho humano não vê — o infravermelho. Cada faixa dessas é chamada de **banda**, e chega
como uma imagem em tons de cinza. Juntando as bandas de vermelho, verde e azul você monta a
imagem colorida normal. Juntando outras bandas você monta uma imagem em **falsa cor**, que é o
que aparece na parte de baixo do slide 2: as cores não são reais, foram escolhidas para
destacar o que interessa.

**Por que o infravermelho ajuda.** Folha viva reflete muito infravermelho e pouco vermelho.
Terra exposta faz quase o contrário. Então, combinando essas duas bandas numa conta simples, dá
para separar mata de solo muito melhor do que olhando só a cor normal. Essa conta é o
**índice de vegetação** — o Jonathan fala dele no slide 8. Você não precisa saber a fórmula;
precisa saber que ela existe e para que serve.

**Por que duas datas, e não uma.** Esse é o coração do trabalho, e é o que você tem que
conseguir defender. Numa imagem só, um pasto que existe há trinta anos e uma área cortada mês
passado aparecem do mesmo jeito: os dois são claros, sem mata. Não dá para distinguir. O que
identifica desmatamento é a **mudança** entre duas datas da mesma área. Por isso todo o
programa é construído em cima de comparar um par de imagens.

**De onde vieram as nossas imagens.** Satélite Terra, da NASA, instrumento MODIS, pelo serviço
público GIBS. São de domínio público. A região é São Félix do Xingu, no Pará, nas datas
01/07/2002 e 05/07/2024 — as duas em julho de propósito, para a época do ano não atrapalhar a
comparação. Tudo isso está registrado no trabalho: produto, data, coordenadas, licença e
endereço de download.

**Se perguntarem por que não usaram uma imagem melhor:** existem satélites com muito mais
detalhe, como o Sentinel-2, mas eles exigem cadastro. A gente escolheu uma fonte que qualquer
pessoa consegue baixar sem conta, para o trabalho ser reproduzível. O custo dessa escolha
aparece na próxima entrega.

## Slide 1 · Capa — 30 s

"Boa noite. Nosso tema é detecção de desmatamento em imagens de satélite."

"Eu sou o André, e comigo estão o Enzo, a Isabel e o Jonathan."

"Hoje é a qualificação do projeto. Então a gente apresenta o capítulo 1 — qual é o problema e
o que queremos fazer — e a parte de filtragem dos capítulos 2 e 3."

"A demonstração do programa e os resultados ficam para a próxima entrega."

## Slide 2 · O problema — 1:30

"Essa é a mesma região da Amazônia em duas datas. Em cima, 2002 e 2024 na cor normal. Embaixo,
as mesmas imagens com cores realçadas: verde escuro é mata fechada, amarelo é terra exposta."

"O ponto principal do nosso trabalho é esse: se eu olhar só a imagem de 2024, eu não consigo
dizer o que é pasto antigo e o que é corte recente. Os dois aparecem claros. O que mostra
desmatamento é a **diferença** entre as duas datas."

"Por isso o problema que a gente resolve é esse da caixa: duas imagens da mesma área em datas
diferentes, achar o que perdeu vegetação e medir quanto isso dá."

"E por que satélite: a região é enorme e de difícil acesso. Não dá para mandar gente olhar
tudo."

"As imagens são reais, do satélite Terra da NASA. São públicas e a gente registrou a origem de
cada uma no trabalho: data, coordenada, licença e endereço."

**→ passa para o Enzo.**

---

# Enzo Consani — slides 3 e 4

## Antes de apresentar

**Os quatro efeitos do desmatamento.** Você vai citar quatro, e é bom entender cada um em uma
frase:

- **Carbono** — a árvore guarda carbono enquanto está viva. Quando a mata é derrubada e
  queimada, esse carbono vai para a atmosfera como gás de efeito estufa.
- **Bichos** — muitas espécies só vivem em mata fechada e contínua. Quando a floresta é
  cortada em pedaços, esses grupos ficam ilhados e não conseguem se misturar.
- **Água** — a floresta puxa água do solo e devolve para o ar pelas folhas. Isso alimenta a
  chuva em outras regiões. Vegetação baixa não faz isso na mesma medida.
- **Solo** — sem a copa segurando, a chuva bate direto no chão e leva a camada fértil embora.

**Os dois números, e o que eles significam.**

- **5.731 km²** é a área derrubada na Amazônia Legal entre agosto de 2024 e julho de 2025,
  medida pelo INPE. Foi 12% menos que no ano anterior. Se perguntarem: é o sistema PRODES, que
  é o monitoramento oficial do Brasil.
- **42%** é a fatia das emissões brutas de gases de efeito estufa do Brasil em 2024 que veio de
  mudança de uso da terra — basicamente desmatamento. São 906 milhões de toneladas. A fonte é
  o SEEG.

Só cite esses dois. Qualquer outro número sem fonte na mão é um risco desnecessário.

**Por que a forma do corte importa.** Duas áreas do mesmo tamanho não fazem o mesmo estrago. Um
corte comprido e estreito ao longo de uma estrada tem muito mais **borda** do que um corte
quadrado da mesma área. E borda é onde a floresta sofre: fica mais seca, mais quente e pega
fogo mais fácil. Isso teve consequência direta no nosso programa: não basta dar um número
total de área. O sistema precisa listar **cada região separada**, com tamanho e posição. É por
isso que ele identifica regiões uma a uma em vez de só somar pixels.

**O que significa "preparar dados para um modelo de visão computacional".** Essa é a frase mais
importante do slide 4, e a que mais confunde. Um modelo de visão computacional é um programa
que aprende a reconhecer coisas em imagens. Para aprender, ele precisa de exemplos já marcados:
"este pedaço aqui é desmatado", "este aqui é mata". Marcar isso na mão, em milhares de pedaços,
é inviável.

O que o nosso trabalho faz é usar processamento de imagens para **produzir essas marcações
automaticamente**. Comparando as duas datas, o programa descobre onde houve perda, e usa essa
descoberta para rotular pedaços da imagem. Esses pedaços rotulados é que alimentam o modelo
depois.

Ou seja: o processamento de imagens aqui **não é o produto final** — ele é a fábrica de dados
de treino. É exatamente isso que o enunciado pede.

**O oitavo objetivo.** "Saber recusar quando a imagem não permite responder." Ele não estava no
plano original. A gente acrescentou depois de o programa recusar uma imagem de verdade — e a
recusa estar certa. O motivo completo é da próxima entrega. Hoje basta dizer que foi
acrescentado depois e que a gente explica na defesa.

## Slide 3 · Por que isso importa — 1:15

"Três motivos para resolver isso."

"O primeiro é o que se perde. A mata guarda carbono, e derrubar joga esse carbono no ar. Os
bichos que dependem de mata fechada perdem o lugar. A floresta ajuda a mover umidade pelo
continente. E o solo, exposto, erode."

"E a escala é grande: o INPE mediu 5.731 km² derrubados na Amazônia no último ano. O uso da
terra sozinho responde por 42% das emissões do Brasil."

"O segundo motivo é por que precisa ser automático: ninguém tem gente para percorrer a floresta
inteira. A fiscalização precisa saber onde olhar **primeiro**. E embargo, acordo ambiental,
essas coisas só valem se der para conferir depois — e conferir é comparar duas datas."

"O terceiro é que errar custa caro dos dois lados. Se o sistema aponta desmatamento onde não
houve, alguém é punido injustamente. Se deixa passar, a floresta não volta. Por isso a gente
acha que o sistema precisa conseguir dizer 'não tenho certeza'."

"E o quadro da direita mudou o nosso projeto: um corte comprido do lado de uma estrada faz
muito mais estrago que um corte quadrado do mesmo tamanho, porque tem muito mais borda. Então
não basta dar um número total — o sistema tem que mostrar cada área separada."

## Slide 4 · O que queremos construir — 1:15

"O objetivo é a frase da caixa, e ela vem do enunciado: um programa que compara duas imagens,
acha e mede o que perdeu vegetação, e **deixa os dados prontos** para treinar um modelo de
visão computacional."

"Essa última parte é importante: o processamento de imagens aqui não é o produto final. Ele
prepara os dados. O modelo vem depois, e só existe porque essa preparação acontece."

"Os oito passos estão aí em ordem: baixar imagem real, escrever os filtros por conta própria,
realçar a diferença entre mata e terra, separar as áreas, medir em hectares, recortar e rotular
pedaços, treinar o classificador, e o oitavo — saber recusar quando a imagem não permite
responder."

"Esse oitavo a gente acrescentou depois de começar, e explica o motivo na defesa."

"E à direita está o que a gente **não** se propõe a fazer. Isso é tão importante quanto, porque
é o que deixa o objetivo possível de conferir."

**→ passa para a Isabel.**

---

# Isabel Da Silva — slides 5, 6 e 7

## Antes de apresentar

Esta é a parte mais técnica da apresentação. Leia com calma — depois que a ideia central cai a
ficha, o resto vem junto.

### 1. Uma imagem é uma tabela de números

Para o computador, uma imagem em tons de cinza é uma tabela: cada posição guarda um número que
diz o quanto aquele ponto é claro ou escuro. Uma imagem colorida é três tabelas dessas
empilhadas — uma para vermelho, uma para verde, uma para azul.

Tudo que a gente faz com imagem é conta com esses números.

### 2. Filtrar é trocar cada número por uma conta com os vizinhos

Um filtro percorre a imagem ponto a ponto. Em cada ponto, ele olha os vizinhos em volta, faz
uma conta com eles, e o resultado dessa conta vira o novo valor daquele ponto.

Exemplo concreto, o mais simples de todos. Suponha que num pedaço da imagem os valores sejam:

```text
10  12  11
13  90  12      ← o 90 no meio é ruído: um ponto isolado esquisito
11  12  10
```

Se o filtro for "tire a média dos nove", o 90 vira 20 e alguma coisa — o pico sumiu, a imagem
ficou mais lisa. É isso que suavizar significa.

### 3. O que muda de um filtro para outro é só a matriz de pesos

Essa matriz de pesos se chama **núcleo** (ou *kernel*). É quase sempre pequena, 3×3 ou 5×5.

A conta é: encosta o núcleo em cima do ponto, multiplica cada vizinho pelo peso que está em
cima dele, e soma tudo. Essa operação tem nome: **convolução**. É a fórmula do slide 5.

- Se todos os pesos forem iguais, você tem o filtro de **média**.
- Se os pesos do centro forem maiores que os das pontas, você tem o **gaussiano**.
- Se os pesos de um lado forem positivos e do outro negativos, você tem um detector de
  **borda**.

O núcleo muda; a conta é a mesma. **Por isso a gente escreveu essa conta uma vez só no
programa, e todos os filtros usam ela.** Se alguém perguntar como os filtros foram
implementados, é essa a resposta.

### 4. O problema da beirada

No ponto que está na margem da imagem, metade dos vizinhos que a conta pede simplesmente não
existe. Três saídas possíveis:

- cortar a margem, e a imagem encolhe;
- inventar um valor, geralmente zero (preto);
- **espelhar** a imagem para fora da borda — é o que a gente faz.

Por que isso importa no nosso caso: se a gente preenchesse com preto, criaria uma faixa escura
em volta da imagem. Como o programa lê escuro-nesse-índice como terra exposta, ele ia marcar
desmatamento na moldura de toda cena. Um detalhe de implementação virando resultado errado.

### 5. Os três filtros de suavização, e por que eles são diferentes

| Filtro | Como funciona | Ponto forte | Ponto fraco |
|---|---|---|---|
| Média | soma os vizinhos e divide | simples e rápido | borra a borda tanto quanto o ruído |
| Gaussiano | vizinho perto pesa mais | tira ruído preservando melhor a borda | ainda borra um pouco |
| Mediana | pega o valor do meio, não a média | mata pixel isolado sem borrar nada | mais lento; não é convolução |

Sobre a mediana: "valor do meio" significa colocar os nove valores em ordem e pegar o quinto.
No exemplo lá de cima, os valores em ordem são 10, 10, 11, 11, 12, 12, 12, 13, 90 — o do meio é
12. O 90 simplesmente não influencia. Por isso ela é tão boa contra ponto isolado.

### 6. Por que suavizar é obrigatório no nosso caso

Depois da filtragem, o programa faz um corte: acima de certo valor é mata, abaixo não é. Isso
transforma a imagem em preto e branco.

Se o ruído chegar nessa etapa, cada ponto de ruído que estiver perto do valor de corte vai para
o lado errado. O resultado fica furado como uma peneira. E aí, quando o programa for contar as
áreas, ele vai achar centenas de manchinhas de três pontos onde existe uma área só.

Lembrando o que o Enzo falou: a gente precisa listar cada área separada. Uma máscara furada
destrói exatamente isso.

### 7. A otimização do gaussiano (o gráfico do slide 6)

O gaussiano 2D pode ser feito em duas passadas simples: uma na horizontal e outra na vertical.
O resultado é **exatamente o mesmo**, e é muito mais rápido, porque numa janela de lado *k* você
faz *2k* contas em vez de *k×k*.

Por que dá o mesmo: o peso do gaussiano num ponto depende da distância, e a fórmula dele se
separa no produto de um pedaço que só depende de *x* por outro que só depende de *y*. É
identidade matemática, não aproximação.

Na nossa medição, numa janela 21×21 ficou **9,4 vezes** mais rápido, e a diferença entre os dois
caminhos foi da ordem de 0,000001 — o que é só arredondamento do computador.

**Cuidado:** o filtro de média também tem essa propriedade. A mediana **não** tem, porque "o
valor do meio de um quadrado" não é "o valor do meio dos valores do meio de cada linha".

### 8. Achar borda é achar mudança brusca

Onde a mata acaba e o corte começa, o valor da imagem muda de repente. Achar borda é achar essa
mudança.

O **Sobel** faz isso com dois núcleos: um com pesos negativos de um lado e positivos do outro na
horizontal, outro igual na vertical. Onde não há mudança, os lados se cancelam e o resultado dá
zero. Onde há mudança, sobra um valor alto.

Como são dois resultados (horizontal e vertical), a gente combina os dois pela raiz da soma dos
quadrados — como a hipotenusa de um triângulo. Isso se chama **magnitude**, e a vantagem é que
ela não depende da direção da borda: o corte pode estar torto que o filtro acha do mesmo jeito.

Um detalhe que rende pergunta: no Sobel, o peso do meio é 2 e não 1. Esse peso maior no centro
é uma suavização na direção perpendicular, e é o que faz o Sobel ser menos sensível a ruído que
uma subtração pura. O filtro de **Prewitt** é a mesma coisa sem esse peso — a gente implementou
os dois para poder comparar.

### 9. Laplaciano

Se o Sobel mede a mudança, o laplaciano mede a **mudança da mudança**. Consequência prática: ele
responde muito a detalhe fino, e também muito a ruído.

Ele tem uma propriedade que a gente usa como teste: os pesos dele somam zero. Então, numa área
de valor constante, o resultado tem que dar zero. Numa rampa suave também. A gente escreveu um
teste que passa uma rampa e confere se o resultado é zero — é assim que sabemos que a nossa
implementação está certa, **sem comparar com biblioteca nenhuma**. Esse ponto é forte: mostra
que os testes verificam matemática, não coincidência com o OpenCV.

### 10. Textura

Ideia diferente das anteriores: em vez de olhar a borda, mede o quanto os valores oscilam
dentro de um quadradinho. Isso é o **desvio padrão local**.

A hipótese é: mata fechada tem copa irregular e cheia de sombra, então os valores variam muito;
pasto é liso, varia pouco.

**Seja honesta sobre isso:** é hipótese da literatura, e nós ainda não confirmamos que funciona
no nosso caso. Está escrito assim no trabalho. Se perguntarem, a resposta certa é "ainda não
sabemos".

### Se der branco

A frase que salva qualquer momento deste bloco é: *"todos os filtros são a mesma conta — a
convolução — com pesos diferentes. Muda a matriz de pesos, muda o efeito."*

## Slide 5 · O que é filtrar uma imagem — 1:15

"Agora a parte de filtragem, que é o conteúdo da nossa disciplina."

"Começando pelo básico: uma imagem, para o computador, é uma tabela de números. Cada pixel é um
número. Filtrar é trocar cada número por uma conta feita com ele e com os vizinhos em volta."

"E o que muda de um filtro para outro é só a conta. A conta se chama convolução, e é essa
fórmula. Parece complicada, mas o que ela diz é simples: pega uma matriz pequena de pesos, o K,
encosta ela em cima do pixel, multiplica cada vizinho pelo peso correspondente e soma tudo."

"Trocar o K é trocar o filtro. Todos os filtros que eu vou mostrar agora são a **mesma** conta,
só com pesos diferentes. Por isso a gente escreveu essa conta uma vez só."

"Do lado direito tem um detalhe que parece bobo e não é: o pixel da beirada. Nele, metade dos
vizinhos que a conta pede não existe. A gente resolve espelhando a imagem para fora."

"Se em vez disso a gente preenchesse com preto, ia criar uma moldura escura na imagem. E o
programa leria essa moldura como terra exposta — ou seja, ia marcar desmatamento na borda de
toda cena."

## Slide 6 · Filtros que tiram o ruído — 1:15

"Três filtros que tiram ruído, e eles não são iguais."

"A **média** é a mais simples: soma os vizinhos e divide. Só que ela trata todo mundo igual,
então borra a borda com a mesma força com que tira o ruído."

"O **gaussiano** resolve isso: vizinho perto pesa mais que vizinho longe. É esse que a gente
usa."

"A **mediana** é diferente: em vez de somar, ela pega o valor do meio da vizinhança. Um pixel
isolado com valor absurdo não muda o valor do meio, então ela limpa esse tipo de ruído sem
borrar nada. O preço é ser mais lenta."

"Por que isso é obrigatório: depois da filtragem o programa corta a imagem em duas — com mata e
sem mata. Se o ruído ficar, pixel solto passa para o lado errado e o resultado sai furado como
peneira. Aí o programa conta centenas de áreas minúsculas onde existe uma só. E a gente acabou
de dizer que precisa mostrar cada área separada."

"O gráfico é uma otimização nossa. O gaussiano dá para fazer em duas passadas simples em vez de
uma passada pesada — e o resultado é exatamente o mesmo. Numa janela grande ficou 9 vezes mais
rápido."

## Slide 7 · Filtros que acham a borda — 1:00

"Agora os filtros que acham a borda. A ideia: onde a mata acaba e o corte começa, o valor da
imagem muda de repente. Achar borda é achar essa mudança brusca."

"O **Sobel** faz isso com dois conjuntos de pesos: um procura mudança na horizontal, o outro na
vertical. Juntando os dois, o filtro acende no contorno da área cortada — e funciona em
qualquer direção, o corte pode estar torto que tanto faz."

"A **textura** é outra ideia. Em vez de olhar a borda, ela mede o quanto os valores oscilam
dentro de um quadradinho. Mata fechada é cheia de sombra e copa irregular, então varia muito.
Pasto é liso, varia pouco."

"E eu preciso ser honesta: isso é uma hipótese que a gente leu na literatura. Nós ainda **não**
confirmamos. Está escrito assim no trabalho."

"Por último o **laplaciano**. O Sobel responde à mudança; o laplaciano responde à mudança da
mudança. Isso deixa ele ótimo para detalhe fino e muito sensível a ruído."

"Ele tem uma propriedade que a gente aproveitou: numa área lisa, ou numa rampa suave, o
resultado tem que dar zero. Então a gente escreveu um teste que passa uma rampa e confere se dá
zero. É assim que a gente sabe que a nossa implementação está certa — sem comparar com
biblioteca nenhuma."

**→ passa para o Jonathan.**

---

# Jonathan Aparecido X Martins — slides 8, 9 e 10

## Antes de apresentar

Você apresenta a **escolha**: dos filtros que a Isabel explicou, quais entram no nosso programa,
em que ordem, e por quê. Entenda cada um em uma frase.

### 1. Índice de vegetação

Uma conta que junta duas bandas do satélite num valor só, escolhida de um jeito que mata e
terra exposta caem em extremos opostos.

A mais conhecida é o **NDVI**: pega o infravermelho e o vermelho e calcula a diferença dividida
pela soma. Folha viva reflete muito infravermelho e pouco vermelho, então dá um valor alto;
terra exposta dá baixo.

No nosso caso a gente usa o **NBR**, que é a mesma ideia com outra banda — o infravermelho de
ondas curtas. Por que: as imagens que a gente baixou trazem essa banda, e não a do NDVI
tradicional. Se perguntarem a diferença entre NBR e NDMI: é a mesma conta com uma banda
vizinha; a que veio nas nossas imagens dá o NBR.

**O índice é a base de tudo.** Sem ele, os filtros estariam trabalhando em cima da cor normal,
onde mata e pasto se confundem muito mais.

### 2. Limiar de Otsu

Depois de filtrar, o programa precisa decidir: a partir de qual valor é mata, e abaixo de qual
não é? Esse valor de corte se chama **limiar**.

Escolher o limiar na mão seria arbitrário e diferente para cada imagem. O método de **Otsu**
escolhe sozinho: ele testa todos os cortes possíveis e fica com aquele que deixa os dois grupos
resultantes o mais separados possível.

**Uma decisão nossa, que vale citar:** a gente calcula **um limiar só** juntando as duas datas,
e aplica o mesmo nas duas. Se calculasse um para cada, a comparação passaria a medir a
diferença entre as duas regras, e não a diferença no terreno.

### 3. Abertura e fechamento (morfologia)

São operações de limpeza que trabalham sobre a imagem já em preto e branco.

- **Abertura** encolhe e depois engorda as manchas. Efeito: respingo pequeno demais some, e o
  que é grande volta ao tamanho.
- **Fechamento** faz o contrário — engorda e depois encolhe. Efeito: buraquinho dentro de uma
  área grande é tapado.

Juntas, elas deixam as áreas com formato limpo, sem mudar o tamanho geral.

### 4. Por que a ordem importa

Suavizar tem que vir **antes** do corte.

Depois do corte a imagem só tem dois valores, preto e branco. A informação intermediária já foi
jogada fora. Suavizar nesse ponto seria mexer numa imagem que já perdeu o que importava — e não
recupera nada. Se alguém insistir: suavizar depois do corte já é morfologia, não é filtragem.

### 5. Por que escrevemos os filtros

Duas razões, e vale dar as duas.

A primeira é que o enunciado exige, na página 3: *"Os filtros devem ser desenvolvidos pelo
grupo."*

A segunda é prática, e é a que impressiona mais: se a gente chamasse uma função pronta de
biblioteca, não saberia responder o que o programa faz na borda da imagem, nem por que o
resultado é aquele. Com o código sendo nosso, cada uma dessas perguntas tem resposta
localizável.

E isso é verificável, não é promessa: dentro do núcleo do programa a única biblioteca permitida
é a de contas com números (NumPy). Não entra OpenCV, nem scikit-image, nem scipy. Qualquer um
pode abrir o repositório e conferir.

### 6. O que fica para a próxima entrega

Separar as áreas, medir em hectares, recortar e rotular os pedaços, treinar o modelo e discutir
os resultados. Se perguntarem sobre resultado hoje, a resposta é: "é conteúdo da Fase II".

## Slide 8 · Os filtros que escolhemos — 1:15

"A Isabel mostrou os filtros que existem. Eu mostro quais a gente escolheu e por quê — porque a
escolha não foi por catálogo, cada um resolve um problema."

"Primeiro o **índice de vegetação**. Ele junta as cores da imagem num valor só, escolhido de um
jeito que mata e terra exposta ficam em extremos opostos. É o que deixa o resto do trabalho
possível."

"Segundo o **gaussiano**, pelo motivo que a Isabel explicou: tirar o ruído antes do corte."

"Terceiro o **limiar de Otsu**. Ele olha a imagem e decide sozinho qual valor separa mata de
não-mata. E a gente usa o **mesmo** valor de corte nas duas datas — se usasse um para cada, a
comparação ia medir a diferença entre as regras, não a diferença no terreno."

"Quarto, abertura e fechamento: limpa respingo solto e tapa buraco dentro das áreas. Quinto, o
Sobel, para realçar o contorno. Sexto, a variação local, que é a textura para o modelo."

"E a frase de baixo é a regra de ouro: suavizar tem que vir **antes** do corte. Depois do corte
a imagem já virou preto e branco, e o que se perdeu não volta."

## Slide 9 · Os filtros rodando na imagem real — 1:00

"E aqui estão esses filtros rodando de verdade, num pedaço da imagem de 2024. Isso não é figura
de livro: é a saída do nosso programa."

"O primeiro painel é a imagem como ela é. O segundo já é o índice de vegetação: o amarelo é
terra exposta, o verde é mata. Só que olhem o granulado — aquilo é ruído."

"O terceiro painel é o mesmo depois do gaussiano. Comparem os dois: o granulado sumiu e o
desenho do terreno continuou lá. É exatamente isso que a gente precisava."

"Embaixo, à esquerda, a mediana fazendo um trabalho parecido. E os dois últimos são o Sobel e a
textura: repara que o contorno do corte e o rio acendem sozinhos."

"O enunciado pede que o resultado dos filtros seja mostrado **e analisado**. É isso que este
slide faz: cada painel tem um motivo de estar ali, e dá para ver o efeito."

## Slide 10 · Para fechar — 40 s

"Para fechar, três coisas."

"A primeira: os filtros são nossos. O enunciado exige que o grupo escreva os filtros, e a gente
escreveu. Dentro do núcleo do programa a única biblioteca que entra é a de contas com números.
Não tem OpenCV, não tem nada pronto."

"A segunda é por que isso foi bom para nós, além da exigência: se a gente chamasse uma função
pronta, não saberia responder o que acontece na borda da imagem, nem por que o resultado é
aquele. Com o código sendo nosso, cada pergunta dessas tem resposta."

"E a terceira é o que vem na próxima entrega: separar as áreas, medir em hectares, recortar e
rotular os pedaços, treinar o modelo e discutir os resultados."

"O capítulo 1 disse qual é o problema. O capítulo 2 explicou como se filtra uma imagem. O
capítulo 3 escolheu os filtros. O que falta é executar."

"Obrigado. Qualquer um de nós responde perguntas sobre qualquer parte."

---

# Slide 11 · Reserva — Isabel Da Silva

> **Não apresentar.** Só abrir se perguntarem se já existe código.

"O programa já existe e já aplica esses filtros. Essa é a tela dele."

"À esquerda o índice sem tratamento, no meio depois do gaussiano, à direita o Sobel. É a mesma
sequência que a gente acabou de descrever, rodando."

"Os painéis de baixo já são a etapa seguinte, que é conteúdo da próxima entrega — estou
mostrando só para dar o contexto."

---

# Checklist antes de apresentar

- [ ] `entrega/apresentacao-qualificacao.pptx` aberto no **modo apresentador**, com as notas
      visíveis (*Exibir → Modo de Exibição do Apresentador*)
- [ ] Cada um leu a sua seção "Antes de apresentar" e consegue explicar sem ler
- [ ] Um ensaio cronometrado, do slide 1 ao 10 — sem o slide de reserva
- [ ] Se for usar o slide 11: navegador **já aberto** em `localhost:8501`, na aba *Etapas do
      processamento*. Não subir o programa ao vivo

# Perguntas prováveis

| Pergunta | Resposta curta | Quem responde melhor |
|----------|----------------|----------------------|
| Vocês usaram OpenCV? | Não. No núcleo do programa só entra NumPy, e dá para conferir no repositório. | Jonathan |
| Como vocês sabem que o filtro está certo, se não compararam com biblioteca? | Por propriedade matemática. Ex.: o laplaciano tem que dar zero numa rampa, e existe um teste que confere isso. | Isabel |
| O que acontece no pixel da borda? | A imagem é espelhada para fora. Preencher com preto criaria desmatamento falso na moldura. | Isabel |
| Por que gaussiano e não média? | A média borra a borda com a mesma força com que tira o ruído. | Isabel |
| Por que duas datas? | Numa imagem só, pasto antigo e corte recente são iguais. Desmatamento é mudança. | André |
| Por que MODIS e não um satélite melhor? | Os melhores exigem cadastro. A gente quis uma fonte que qualquer um baixa. O custo aparece na Fase II. | André |
| Por que um limiar só para as duas datas? | Dois limiares mediriam a diferença entre as regras, não a diferença no terreno. | Jonathan |
| A textura funciona? | **Ainda não sabemos.** É hipótese da literatura, declarada como não confirmada. | Isabel |
| Já tem código pronto? | Sim, o protótipo roda. Mas o conteúdo desta fase é o que precisa estar decidido antes. | qualquer um |
| Qual a diferença entre convolução e correlação? | O sinal dos índices. Igual para pesos simétricos; troca o sinal no detector de borda. As duas estão implementadas. | Isabel |

# O que **não** dizer

- Nenhum resultado, área em hectares ou métrica de modelo — é conteúdo da próxima entrega.
- "A textura melhora a classificação." — não foi medido.
- Número de desmatamento que não seja um dos dois conferidos (INPE e SEEG).
- "Nossos filtros são os do OpenCV reescritos." — foram implementados a partir das definições
  do livro-texto (Gonzalez e Woods) e validados contra propriedades matemáticas.
