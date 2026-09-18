# Falas — Fase Intermediária I (Qualificação)

Enunciado, p. 5: *"Fase Intermediária I — Qualificação do Projeto. Conteúdo: **Capítulo 1
e os itens relativos a filtragem dos capítulos 2 e 3**. Esta etapa deve ser concluída
antes do desenvolvimento prático."*

> **O que fica de fora desta apresentação:** segmentação, quantificação, modelo,
> demonstração do protótipo e discussão de resultados. Tudo isso é da Fase Intermediária II
> — a defesa — e está em `FALAS-DEFESA.md`.

Este é o texto impresso das falas. As mesmas falas estão nas **notas do apresentador** de
cada slide de `entrega/apresentacao-qualificacao.pptx` — no PowerPoint, *Exibir → Modo de
Exibição do Apresentador*.

> As falas abaixo são um guia, não um texto para ler em voz alta. A regra do projeto vale
> aqui: se o integrante não consegue explicar com as próprias palavras, o trecho ainda não
> está pronto.

## Divisão — 13 minutos, com folga

| Slides | Bloco | Quem | Tempo |
|--------|-------|------|------:|
| 1–2 | Abertura e escopo da qualificação | André Massarente | 0:45 |
| 3–4 | Cap. 1.a — o problema e a relevância ambiental | André Massarente | 2:40 |
| 5–7 | Cap. 1.b e 1.c — contexto, impacto ecológico e objetivos | Enzo Consani | 3:00 |
| 8–11 | Cap. 2.e.iii — os conceitos de filtragem | Isabel Da Silva | 4:25 |
| 12–15 | Cap. 3.a — os filtros escolhidos e o encerramento | Jonathan Aparecido X Martins | 3:15 |
| 16 | Reserva: os filtros rodando — **só se pedirem** | Isabel Da Silva | +1:00 |
| | **Total** | | **≈14:05** |

> Se o tempo apertar, os cortes na ordem: o slide 16 (reserva), depois a coluna "fora do
> escopo" do slide 7, depois o laplaciano no slide 11.

---

# André Massarente — slides 1 a 4

## Slide 1 · Capa — 20 s

"Boa noite. Nós somos o grupo do tema de sustentabilidade ambiental: detecção e
quantificação de desmatamento em imagens de satélite."

"Eu sou o André, e comigo estão o Enzo, a Isabel e o Jonathan."

"Esta é a apresentação da Fase Intermediária I, a qualificação do projeto. Então o que a
gente traz hoje é o capítulo 1 — o problema, o contexto e os objetivos — e os itens de
filtragem dos capítulos 2 e 3: o que é filtragem e quais filtros a nossa solução usa."

## Slide 2 · O que esta qualificação cobre — 25 s

"A apresentação segue o conteúdo que o manual define para esta fase."

"Primeiro o capítulo 1: eu apresento o problema e a relevância ambiental, e o Enzo continua
no contexto e nos objetivos. Depois a Isabel apresenta a teoria de filtragem do capítulo 2.
E o Jonathan fecha com os filtros que a nossa proposta escolheu, no capítulo 3."

"A demonstração do programa e os resultados ficam para a Fase II, que é a defesa."

> Se perguntarem se já existe código: sim, o protótipo já roda. Oferecer mostrar no fim,
> se houver tempo — o slide 16 existe para isso.

## Slide 3 · 1.a — O problema é bi-temporal por definição — 1:30

"Desmatamento é a remoção da cobertura vegetal nativa de uma área. Detectar e quantificar
isso em escala regional não dá para fazer em campo: as frentes ficam em lugar de difícil
acesso, avançam o tempo todo e cobrem área grande demais. Satélite é o único instrumento
que acompanha isso de forma sistemática."

"O problema, formalmente, é esse da caixa: dado um **par** de imagens da mesma área em
datas diferentes, identificar as regiões que perderam cobertura vegetal e quantificar essa
perda em área."

"E o 'par' não é detalhe, é a definição. Olhem a imagem: 2002 à esquerda, 2024 à direita,
em cor natural em cima e no índice em falsa cor embaixo. Se eu mostrasse só a de 2024, eu
não conseguiria dizer o que é pasto de trinta anos e o que é corte do mês passado — as duas
coisas são claras na imagem. A informação está na **diferença**."

"As imagens são reais, do satélite Terra da NASA, pelo serviço GIBS, de domínio público, e
a procedência está registrada: produto, data, coordenadas, licença e URL."

## Slide 4 · 1.a — Relevância em termos de sustentabilidade — 1:10

"Por que esse problema importa para sustentabilidade. A supressão de vegetação age por
quatro caminhos ao mesmo tempo: carbono, habitat, ciclo da água e solo."

"Carbono: a floresta guarda carbono na biomassa; derrubar e queimar joga isso na atmosfera.
Habitat: espécies que dependem de dossel contínuo perdem o ambiente, e a fragmentação isola
o que sobra. Água: a floresta bombeia umidade pela evapotranspiração. E solo: exposto, ele
erode e perde fertilidade."

"A escala é medida oficialmente. O INPE consolidou 5.731 km² na Amazônia Legal no período
de agosto de 2024 a julho de 2025 — 12% a menos que no ano anterior. E o SEEG mostra que em
2024 o uso da terra respondeu por 42% das emissões brutas de gases de efeito estufa do
Brasil, 906 milhões de toneladas."

"Mas o ponto que liga tudo isso à nossa disciplina é o quadro da direita: todos esses
efeitos vêm de uma mudança **opticamente observável**. Dossel florestal reflete diferente
de solo exposto. É essa diferença que os nossos filtros vão realçar."

> Não citar número de desmatamento sem ser um destes dois — eles estão conferidos na
> bibliografia (INPE, 2026; SEEG, 2025).

**→ passa para o Enzo.**

---

# Enzo Consani — slides 5 a 7

## Slide 5 · 1.b — Por que resolver este problema importa — 1:15

"Três razões pelas quais resolver isso importa."

"Primeira: **saber onde olhar**. Fiscalização ambiental não tem efetivo para percorrer a
frente inteira. O que ela precisa é de um sistema que diga quais polígonos mudaram desde a
última vez. Detecção automática não substitui o fiscal — ela transforma um problema de
vigilância impossível num problema de priorização."

"Segunda: **conferir compromissos**. Embargo, acordo de restauração, rastreabilidade de
cadeia produtiva, desmatamento zero — nada disso tem efeito se não dá para verificar. E
verificar é, na prática, comparar duas datas. É o mesmo problema."

"Terceira: **assimetria de informação**. Sem monitoramento independente, quem sabe o que
acontece numa frente de expansão é só quem está lá. Dado orbital aberto e método
reproduzível são um contrapeso. E isso não é abstrato: a Comissão Pastoral da Terra
registrou 1.593 conflitos no campo em 2025, dos quais 824 na Amazônia Legal."

"E embaixo, uma ideia que volta no fim: errar custa caro dos **dois** lados. Falso positivo
pune quem não desmatou; falso negativo deixa passar. Por isso a gente acha que um sistema
honesto precisa saber dizer 'não tenho informação suficiente'."

## Slide 6 · 1.b — Impacto ecológico: a geometria importa — 50 s

"Uma coisa que a gente aprendeu escrevendo o capítulo 1 e que mudou o desenho do projeto: o
impacto do desmatamento não depende só de **quanto** foi removido, mas da **forma**."

"Olhem a imagem: o corte acompanha as estradas. É o padrão que chamam de espinha de peixe.
Um corte alongado desse tipo produz muito mais borda por unidade de área do que um corte
compacto do mesmo tamanho."

"E borda importa porque é onde o microclima muda: a floresta de borda é mais seca, mais
quente e mais vulnerável ao fogo. Além disso a fragmentação isola espécies que não
atravessam área aberta."

"A consequência para o nosso sistema está no quadro escuro: **não basta** um número de área
total. O sistema precisa entregar as regiões uma a uma, com forma e localização. É por isso
que a nossa solução rotula componentes conexos e descreve cada região, em vez de só somar
pixels. O requisito ecológico virou requisito de software."

## Slide 7 · 1.c — Objetivos — 55 s

"O objetivo geral é a frase da caixa escura, e ela foi escrita colada no enunciado: uma
aplicação em Python que aplica processamento de imagens sobre um par de datas para detectar
e quantificar perda de cobertura, **produzindo dados preparados** para alimentar um modelo
de visão computacional. O processamento de imagens aqui é preparação de dados, não é o
produto final."

"Os oito objetivos específicos: adquirir imagem real com procedência; implementar os filtros
por conta própria; realçar a diferença com índices; segmentar; quantificar; preparar
recortes rotulados; treinar e avaliar sem superestimar; e o oitavo, reconhecer os próprios
limites."

"Esse oitavo não estava na versão inicial. A gente acrescentou depois — e explica por quê na
defesa."

"E a coluna da direita é tão importante quanto: o que a gente **não** se propõe a fazer. Não
substituímos o INPE, não processamos cena inteira em escala operacional, não classificamos o
uso que veio depois da floresta e não produzimos índice comparável com a literatura.
Delimitar isso é o que torna os objetivos verificáveis."

**→ passa para a Isabel.**

---

# Isabel Da Silva — slides 8 a 11

## Slide 8 · 2.e.iii — Convolução e tratamento de borda — 1:15

"O capítulo 2 é a base teórica. E o ponto de partida é que todos os filtros espaciais que a
gente usa são casos particulares de **uma** operação: a convolução."

"A fórmula está aí: para cada pixel, você percorre a vizinhança, multiplica pelo peso
correspondente do núcleo e soma. Mudar o filtro é mudar o núcleo."

"Logo abaixo está a correlação cruzada, que é a mesma soma sem a inversão dos índices. Essa
distinção é muito ignorada, e a gente faz questão dela: para núcleo simétrico — média,
gaussiano, laplaciano — dá exatamente o mesmo resultado. Para núcleo antissimétrico, como o
Sobel, muda o **sinal**: uma borda de claro para escuro inverte em relação a uma de escuro
para claro."

"No nosso caso interessa a magnitude, então o sinal não muda a conclusão — mas a
implementação precisa saber qual das duas está rodando. Por isso as duas estão implementadas
separadamente no código."

"À direita, o tratamento de borda. No pixel da margem, parte da vizinhança cai fora da
imagem. Dá para encolher a imagem, inventar valor, ou estender por uma regra. A gente
estende, com quatro regras."

"E isso não é detalhe cosmético — está no quadro de baixo: se você preenche com **zero** numa
cena de floresta, cria uma faixa escura na margem. O índice de vegetação lê faixa escura como
solo exposto, e a segmentação marcaria desmatamento na borda da imagem. Por isso o padrão é
reflexão."

## Slide 9 · 2.e.iii — Filtros de suavização — 1:00

"Três filtros de suavização, e eles não são intercambiáveis."

"A **média** é o mais simples: todos os vizinhos com o mesmo peso. Reduz ruído, mas borra a
borda com a mesma força com que borra o ruído — justamente porque trata todo mundo igual."

"O **gaussiano** resolve isso fazendo o peso decair com a distância ao centro. E ele é
normalizado para somar 1, o que preserva o brilho médio da imagem. É esse que a gente usa
antes da limiarização."

"A **mediana** é diferente dos dois: ela nem é uma convolução. Ela troca o pixel pela mediana
da vizinhança. Como mediana é estatística de ordem, um pixel isolado com valor absurdo não
muda o resultado — então ela remove ruído impulsivo **sem** borrar a borda. O preço é ser
mais cara."

"E o quadro de baixo é a justificativa de tudo isso. Se a gente não suaviza, o ruído do
sensor faz pixel individual atravessar o limiar, e a máscara sai cheia de buraco. Aí a
contagem de componentes conexos explode: o sistema ia reportar centenas de 'áreas
desmatadas' de três pixels onde existe uma só. E a análise por região é exatamente o que o
capítulo 1 disse que era necessário."

## Slide 10 · 2.e.iii — Separabilidade — 1:00

"Essa é a parte mais bonita do capítulo 2, na nossa opinião, porque é álgebra pura com efeito
medido."

"Convolução 2D direta custa *k*² multiplicações por pixel. Para o gaussiano dá para baixar
isso para 2*k*. E não é aproximação — é identidade."

"A conta está aí: o expoente da gaussiana é uma **soma**, *x*² mais *y*². E exponencial de
soma é produto de exponenciais. Então o núcleo 2D é exatamente o produto externo de dois
núcleos 1D iguais. Convoluir pelo 2D é a mesma coisa que passar o 1D na horizontal e depois
na vertical."

"O gráfico é a medição no nosso código, numa imagem de 440 por 440. Numa janela 3 por 3 o
ganho é pequeno, 1,4 vezes. Numa 21 por 21 chega a 9,4 vezes. Faz sentido: o ganho cresce
com *k*."

"E a diferença entre os dois caminhos foi de 10⁻⁶ — isso é arredondamento de ponto flutuante,
não diferença de método. A gente tem teste que confere essa equivalência inclusive nas bordas
e nos quatro modos de margem, porque é lá que ela poderia falhar."

"A média também é separável. A mediana **não** é: a mediana de uma janela 2D não é a mediana
das medianas das linhas, porque estatística de ordem não se decompõe assim."

## Slide 11 · 2.e.iii — Realce de borda e textura — 1:10

"Bordas são descontinuidades. Detectar borda é estimar derivada espacial."

"O **Sobel** é a primeira derivada. São dois núcleos: um para a direção *x* e outro para *y*.
E tem um detalhe que vale explicar: o peso 2 na linha do meio não é enfeite — é suavização na
direção perpendicular. É isso que faz o Sobel ser menos sensível a ruído do que uma diferença
simples. O Prewitt é a mesma estrutura sem esse peso, e a gente implementou para poder
comparar."

"Dos dois sai a **magnitude do gradiente**, que é a raiz da soma dos quadrados. A magnitude é
invariante à orientação — e isso importa muito aqui, porque o corte pode estar em qualquer
direção. A magnitude acende o contorno de qualquer jeito."

"O **laplaciano** é segunda derivada, isotrópico. Como ele responde a mudança de taxa, é muito
sensível a detalhe fino e a ruído. Repara que a soma dos pesos é zero: isso significa que
região constante vai a zero, e rampa linear também. A gente usa exatamente isso como caso de
teste analítico."

"E o último quadro é a **textura**: desvio-padrão de uma janela deslizante. A ideia é que
dossel fechado é irregular, com sombra, então tem desvio alto; pasto é homogêneo, desvio
baixo. Eu preciso ser honesta: isso é hipótese da literatura e **ainda não foi validada** por
nós. Está declarado assim no trabalho."

**→ passa para o Jonathan.**

---

# Jonathan Aparecido X Martins — slides 12 a 15

## Slide 12 · 3.a — Os filtros escolhidos, e a função de cada um — 1:15

"Agora o capítulo 3, que é a nossa proposta. A Isabel mostrou o que existe; eu mostro o que a
gente escolheu e por quê."

"E o 'por quê' importa: a escolha não foi por catálogo. Cada filtro entrou porque resolve um
problema concreto que aparece na cadeia."

"Primeiro o índice de vegetação, que reduz várias bandas a um mapa escalar onde vegetação e
solo exposto ficam em extremos opostos. Depois o gaussiano 5 por 5, pelo motivo que a Isabel
explicou: sem ele o ruído atravessa o limiar."

"Aí vem o Otsu sobre o histograma **conjunto** das duas datas — e o 'conjunto' é uma decisão
nossa, que eu explico no próximo slide. Depois a limpeza morfológica: abertura tira respingo
isolado, fechamento tapa buraco interno."

"O gradiente morfológico extrai o contorno das regiões para exibir. O Sobel torna visível a
fronteira entre floresta e corte. E o desvio-padrão local é o descritor de textura que vai
para a etapa de modelo."

"A lógica da ordem: cada filtro sai um passo antes de onde ele atrapalharia. A **ordem** faz
parte da proposta, não é acidente."

## Slide 13 · 3.a — O efeito de cada filtro, na cena real — 1:00

"E aqui estão os filtros rodando de verdade, sobre um recorte da cena real de 2024. Isso não
é ilustração de livro: é a saída do nosso código."

"Em cima, à esquerda, a cor natural. Ao lado, o índice NBR bruto: o amarelo é solo exposto, o
verde é vegetação. O índice já separa bem — mas olhem o granulado. Aquilo é ruído do sensor,
e é exatamente o que estragaria a limiarização."

"O terceiro painel é o gaussiano 5 por 5. Comparem com o do lado: o granulado sumiu e a
estrutura continua lá. Embaixo à esquerda, a mediana, que faz um trabalho parecido por outro
caminho."

"E os dois últimos são o realce de borda e a textura. O Sobel acende no contorno do corte e no
rio. O desvio-padrão local responde ao mesmo contorno, mas por variação local em vez de
derivada."

"O enunciado pede que o resultado dos filtros seja apresentado **e analisado**. É isso que
este slide faz: cada painel tem uma razão de estar na cadeia, e dá para ver o efeito."

## Slide 14 · 3.a — A ordem não é indiferente — 1:00

"Duas coisas para fechar a proposta."

"A primeira é a **ordem**. Pode parecer indiferente suavizar antes ou depois do limiar, e não
é. Suavizar depois estaria operando sobre uma máscara binária — aquilo já seria morfologia,
não filtragem — e não recupera a informação que o limiar destruiu. O ruído tem que ser
atenuado enquanto o dado ainda é contínuo."

"E o efeito de pular esse passo é mensurável: a máscara sai esburacada e a contagem de
componentes conexos explode. Voltamos ao capítulo 1: a análise por região era um requisito
ecológico, e ela morre se a máscara estiver cheia de buraco."

"A segunda é **por que a gente implementou os filtros**. Primeiro porque o enunciado exige, na
página 3. Mas tem uma razão prática que a gente sentiu: uma chamada a `cv2.GaussianBlur` não
permite responder o que acontece na borda, por que o núcleo é normalizado, ou por que
convolução difere de correlação. Com o código no repositório, cada uma dessas perguntas tem
resposta em uma linha."

"E a restrição é **verificável**, não é promessa: dentro da pasta `pdi` a única dependência
permitida é o NumPy, e a ausência de `cv2`, `skimage`, `scipy` e `PIL` é conferida por
inspeção."

## Slide 15 · O que vem na Fase Intermediária II — 35 s

"Fechando: esta qualificação entrega o que precisa estar decidido **antes** do desenvolvimento
prático."

"O capítulo 1 definiu o problema como bi-temporal, mostrou por que ele importa e — o que talvez
seja o mais útil — mostrou que a análise precisa ser por **região**, não só por área total. O
capítulo 2 fixou os conceitos de filtragem. E o 3.a escolheu quais filtros entram, em que
ordem, e por quê."

"O que vem na Fase II é a execução: segmentação, quantificação em hectares, preparação dos
recortes rotulados, e o modelo com a avaliação."

"Obrigado. Estamos à disposição para perguntas — e qualquer um de nós responde sobre qualquer
parte."

---

# Slide 16 · Reserva — só se pedirem · Isabel Da Silva

> **Não apresentar por padrão.** Este slide existe para o caso de sobrar tempo ou de alguém
> pedir para ver o programa. A demonstração completa é da Fase II.

"O protótipo já existe e já aplica esses filtros. Aqui está a aba de etapas do processamento."

"À esquerda o índice bruto, no meio o gaussiano 5 por 5, à direita o Sobel. É a mesma sequência
que a gente acabou de descrever, rodando."

"Os painéis de baixo já são segmentação, que é conteúdo da próxima fase — estou mostrando só
para situar onde a filtragem entra na cadeia."

---

# Checklist antes da apresentação

- [ ] `entrega/apresentacao-qualificacao.pptx` aberto no modo apresentador, com as notas
      visíveis
- [ ] Ensaio cronometrado uma vez, do slide 1 ao 15 — sem o slide de reserva
- [ ] Se o slide 16 for usado: `sentinela app` **já aberto** no navegador antes de começar,
      na aba *Etapas do processamento*. Não subir o servidor ao vivo
- [ ] Plano B do slide 16 testado: `sentinela demo --tamanho 200 --area 80`
- [ ] **Cada integrante consegue responder as perguntas abaixo sem ler**

# Perguntas prováveis — e onde está a resposta

| Pergunta | Resposta curta | Onde mostrar |
|----------|----------------|--------------|
| Vocês usaram OpenCV? | Não. `pdi/` só importa NumPy, e a ausência de `cv2`, `skimage`, `scipy` e `PIL` é conferida por inspeção. | `src/sentinela/pdi/filtros.py` |
| Qual a diferença entre convolução e correlação? | Convolução inverte os índices do núcleo. Igual para núcleo simétrico; muda o sinal no Sobel. | `pdi/nucleo.py` — `convoluir` e `correlacionar` |
| O que acontece no pixel da borda? | A imagem é estendida por reflexão antes de convoluir. Preencher com zero criaria falso desmatamento na margem. | `pdi/nucleo.py` — `aplicar_borda` |
| Por que gaussiano e não média? | A média borra a borda com o mesmo peso com que borra o ruído. O gaussiano decai com a distância. | slide 9 |
| Por que não usar só a mediana? | Ela preserva a borda melhor, mas é mais cara e não é separável. O gaussiano basta para o ruído do sensor. | cap. 2.e.iii |
| A separabilidade é uma aproximação? | Não. É identidade algébrica: o núcleo 2D é o produto externo de dois 1D. A diferença medida foi de 10⁻⁶. | slide 10 |
| Por que Sobel e não Prewitt? | O peso 2 central do Sobel é suavização perpendicular, o que o torna menos sensível a ruído. Os dois estão implementados. | `pdi/filtros.py` — `gradiente` |
| Para que serve o laplaciano aqui? | Realce de nitidez e caso de teste analítico: ele anula região constante e rampa linear. | slide 11 |
| A textura ajuda? | **Ainda não sabemos.** É hipótese da literatura, declarada como não validada. | cap. 2.e.iii, fim |
| Por que MODIS e não Sentinel-2? | Não exige cadastro — qualquer um reproduz. O custo é a resolução, e ele é discutido na Fase II. | `data/raw/FONTES.md` |
| Por que NBR e não NDMI? | Mesma conta, SWIR diferente. O GIBS traz a banda 7 do MODIS, que é SWIR 2 — isso dá o NBR. O NDMI precisa da banda 6. | `pdi/cor.py` — `nbr` |
| Já tem código pronto? | Sim, o protótipo roda. Mas o conteúdo desta fase é o que precisa estar decidido antes do desenvolvimento. | slide 16, se pedirem |

# O que **não** dizer

- Nenhum resultado de detecção, área em hectares ou métrica de modelo — é conteúdo da Fase II.
- "A textura melhora a classificação." — não foi medido.
- Qualquer número de desmatamento da Amazônia que não seja um dos dois conferidos
  (INPE, 2026 e SEEG, 2025).
- "Os filtros são os do OpenCV, só que reescritos." — eles foram implementados a partir das
  definições de Gonzalez e Woods (2018), e validados contra casos analíticos.
