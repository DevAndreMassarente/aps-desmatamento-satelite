# Falas — Fase Intermediária II (Defesa)

Enunciado, seção III: sessão de **10 a 15 minutos** (nesta turma, **10 minutos** por grupo), com **explicação do problema e
contexto**, **demonstração da aplicação** e **discussão dos resultados**. O grupo deve
estar preparado para **perguntas da turma e dos professores**.

> **Esta é a apresentação da Fase Intermediária II — a defesa**, entregue junto com o
> protótipo. A apresentação da Fase Intermediária I (qualificação) está em
> `FALAS-QUALIFICACAO.md`.

Este é o texto impresso das falas. As mesmas falas estão nas **notas do apresentador** de
cada slide de `entrega/apresentacao-defesa.pptx` — no PowerPoint, *Exibir → Modo de Exibição do
Apresentador*.

> As falas abaixo são um guia, não um texto para ler em voz alta. A regra do projeto vale
> aqui: se o integrante não consegue explicar com as próprias palavras, o trecho ainda não
> está pronto.

## Como a apresentação é avaliada

| Critério | Peso | O que isso exige na prática |
|----------|------|-----------------------------|
| Participação de todos os membros | 20% | cada integrante apresenta um bloco — e responde perguntas sobre **qualquer** bloco |
| Qualidade do projeto prático e teórico | 50% | mostrar o programa funcionando e defender as decisões |
| Clareza e estrutura | 30% | seguir a ordem abaixo, sem voltar atrás, dentro do tempo |

## Divisão — cerca de 9 minutos, com 1 de folga

| Slides | Bloco | Quem | Tempo | Parte exigida pelo enunciado |
|--------|-------|------|------:|------------------------------|
| 1–2 | Abertura e recapitulação da Fase I | Isabel Da Silva | 1:15 | problema e contexto |
| 3–5 | Como o sistema funciona | Enzo Consani | 2:30 | problema e contexto |
| 6 | Demonstração ao vivo | André Massarente | 3:00 | **demonstração da aplicação** |
| 7–9 | Resultados e encerramento | Jonathan Aparecido X Martins | 2:20 | **discussão dos resultados** |
| | **Total** | | **≈9:05** | |

Os slides 10 e 11 ficam depois do encerramento, como reserva. Só entram se a demonstração
ao vivo falhar.

---

# Isabel Da Silva — slides 1 e 2

## Slide 1 · Capa — 20 s

"Boa noite. Nós somos o grupo do tema de sustentabilidade ambiental: detecção e
quantificação de desmatamento em imagens de satélite."

"Eu sou a Isabel, e comigo estão o André, o Enzo e o Jonathan. Cada um de nós apresenta uma
parte, e todos respondem perguntas sobre qualquer parte."

"São dez minutos: o problema, como o sistema funciona, o programa rodando ao vivo
e os resultados — inclusive um resultado que foi uma recusa, e vamos explicar por quê."

## Slide 2 · Relembrando a Fase I — 1:00

"Antes de mostrar o que é novo, uma revisão rápida do que apresentamos na qualificação."

"O problema: olhando uma imagem só, não dá para saber o que é pasto antigo e o que é corte
recente. O desmatamento aparece quando comparamos a mesma área em duas datas, como nestas
imagens de 2002 e 2024."

"O objetivo, pelo enunciado: o processamento de imagens prepara os dados que depois
alimentam um modelo de visão computacional. Ele não é o produto final."

"Os filtros foram escritos por nós, só com NumPy, como o enunciado exige."

"E o que mudou desde então: o protótipo ficou pronto, o modelo é treinado, e testamos o
programa numa imagem de satélite de 10 metros, comparando com o mapeamento oficial do INPE.
O Enzo mostra agora como o sistema funciona por dentro."

**→ passa para o Enzo.**

---

# Enzo Consani — slides 3 a 5

## Slide 3 · As cinco etapas — 40 s

"O programa tem cinco etapas, e elas não são invenção nossa: é a sequência que o próprio
enunciado nomeia. A gente espelhou isso na organização das pastas do código, então cada
etapa tem um lugar e dá para apontar onde ela está."

"Aquisição baixa o par de datas. Manipulação calcula os índices de vegetação. Filtragem
aplica os filtros espaciais. Segmentação decide o que é perda e o que não é. E o modelo
pega o resultado e treina o classificador."

"Um detalhe de implementação que importa para a demonstração: o programa guarda **todos**
os resultados intermediários. Não é uma caixa que entra imagem e sai número — o André vai
mostrar etapa por etapa na tela."

## Slide 4 · Os filtros são nossos — 50 s

"Aqui estão os filtros rodando sobre a cena real de 2024. Em cima: a cor natural, o índice
NBR bruto e o mesmo índice depois do gaussiano 5 por 5 — repara que o ruído sumiu e a
estrutura ficou. Embaixo: a mediana, o Sobel realçando as bordas, e o desvio-padrão local,
que é a nossa medida de textura."

"Tudo isso é código nosso. A base é uma função de convolução genérica com tratamento de
borda; todo filtro linear é só um núcleo diferente passado para ela."

"Uma otimização que vale citar: o gaussiano é separável. Em vez de uma janela 2D, a gente
roda dois passes 1D — porque *e* elevado a menos *x*² menos *y*² é igual ao produto dos
dois. Numa janela 21 por 21 isso deu 9,4 vezes mais rápido, e a diferença entre os dois
caminhos é da ordem de 10⁻⁶, que é arredondamento de ponto flutuante."

"E os testes: 364 no total. Eles não comparam com OpenCV — comparam com casos analíticos.
Convolução com núcleo identidade devolve a imagem original; Sobel numa rampa linear devolve
gradiente constante; Otsu numa imagem bimodal cai entre os dois modos."

## Slide 5 · O sistema sabe quando não sabe — 1:10

"O método de Otsu **sempre** devolve um número. Você pode dar a ele uma foto de uma parede
branca e ele devolve um limiar. Se a cena é homogênea — floresta intacta nas duas datas —
ele vai cortar o ruído do dossel no meio e metade da cena vira 'desmatamento'."

"Então antes de usar o limiar, o programa mede o tamanho de efeito entre as duas classes
que ele acabou de separar: a distância entre as médias dividida pelo desvio combinado. É
uma medida padrão de separação entre distribuições."

"Os três números: 2,65 é o piso — é mais ou menos o que uma imagem **sem** classes produz,
porque Otsu sempre acha alguma coisa. 4,0 é o mínimo que a gente exige para reportar área.
E 3,51 foi o que a cena real de satélite deu: abaixo do mínimo, então recusado."

"O ponto importante: esses dois limites foram fixados **antes** de rodar a imagem real, e
não foram mexidos depois. O Jonathan volta nisso no final."

**→ passa para o André.**

---

# André Massarente — slide 6 · demonstração ao vivo

> Antes de começar: app aberto no navegador em `localhost:8501` (ele abre em **Enviar
> imagens**) e os dois arquivos `*_cor-e-infravermelho.png` numa pasta fácil de achar.
> **Não subir o servidor ao vivo.**

## Slide 6 · Demonstração ao vivo — 3:00

**Alt+Tab para o navegador.** O app já abre em **Enviar imagens**.

**Arrastar `2018-07-03_cor-e-infravermelho.png` para o quadro Imagem antes e
`2024-07-16_cor-e-infravermelho.png` para o quadro Imagem depois (30 s).** A prévia aparece em
cada quadro.
"Estas são imagens reais do satélite Sentinel-2, da mesma área do Pará em julho de 2018 e
julho de 2024. Cada arquivo traz a cor e o infravermelho, que separa floresta de solo."

**Clicar em Processar imagens, no painel da esquerda. Leva cerca de 15 s.**
"O programa roda agora as cinco etapas sobre 2,25 milhões de pixels. O painel mostra cada uma
terminando e o que ela mediu: o NDVI médio caiu de 0,77 para 0,63, e a vegetação passou de 76%
para 42% da cena."

**Arrastar a linha da comparação de um lado para o outro (30 s).**
"Dá para ver a floresta virar pasto."

**Em Etapas do processamento, abrir 3 Filtragem e 4 Segmentação (50 s).**
"Aqui está cada etapa. Na filtragem, o gaussiano tirando o ruído e o Sobel marcando a borda.
Na segmentação, o mesmo limiar nas duas datas e o mapa de mudança."

**Apontar a tabela Decisão do limiar, na aba 4.**
"E aqui a decisão: a separação ficou em 3,88, abaixo do mínimo de 4,0. Por isso o programa
não calculou a área. O Jonathan explica esse resultado."

**Cena sintética no painel da esquerda. Tamanho da cena em 200, lado da área desmatada em 60,
depois a aba 5 Modelo (40 s).**
"Para conferir a conta, uma cena em que nós desenhamos o corte: 400 pixels construídos e 400
detectados. E aqui está o modelo: a máscara vira rótulo dos recortes, e os recortes treinam o
classificador. O próprio programa avisa que, numa cena sintética, essa métrica não valida o
modelo."

**Alt+Tab para o PowerPoint e avançar o slide. → passa para o Jonathan.**

### Plano B — se o app travar ou não abrir

Não tentar consertar ao vivo. Se o envio demorar mais de 30 s, trocar para a cena
sintética e seguir dela. Se o app travar, voltar ao PowerPoint, ir até os slides 10 e 11
(depois do encerramento) e narrar a mesma sequência pelos prints. Depois voltar ao slide 7.

---

# Jonathan Aparecido X Martins — slides 7 a 9

## Slide 7 · Resultado em imagem real — 1:00

"Agora o resultado principal, que é o que aconteceu com a imagem de satélite de verdade: o
sistema se recusou a quantificar."

"Este gráfico é a distribuição do índice nas duas datas. À esquerda o NDVI, à direita o NBR.
Azul é 2002, laranja é 2024, e a linha vertical é o limiar de Otsu."

"Tem perda de vegetação: a mediana do NDVI caiu de 0,944 para 0,794, e a do NBR de 0,799
para 0,504 — isso na escala nativa do índice, que vai de −1 a +1."

"E tem vale entre os montes — no NDVI de 2024 dá para ver dois montes. Só que o vale é
**raso**. Nenhum corte ali separa as classes com o tamanho de efeito que a gente exige."

> Se alguém perguntar "não tem vale?": a figura mostra que tem. O problema não é ausência de
> vale, é profundidade do vale. Não dizer que os histogramas são unimodais.

"Nossa hipótese principal aqui foi a resolução. A 253 metros por pixel, cada pixel mistura
floresta, pasto, regeneração e estrada num valor só."

"Testamos outras explicações: trocamos NDVI por NBR, que melhorou de 2,99 para 3,51 e
continuou abaixo de 4. Limiarizar a imagem de diferença deu 2,79, ainda pior. Faltava testar
a resolução de verdade, e a gente fez isso: já vou mostrar."

"E uma decisão: bastava baixar o critério de 4 para 3 e teríamos um número. Não fizemos
isso. **Escolher a régua depois de ver a medida não é medir.**"

## Slide 8 · O teste a 10 metros — 1:00

"Baixamos imagem Sentinel-2, de 10 metros por pixel. Agora os talhões aparecem claramente.
Mesmo assim, o sistema recusou: deu 3,97, e o critério é 4,0. E a gente manteve o critério."

"Então a resolução explicava só parte do problema. Para medir o resto, usamos o PRODES, o
mapeamento de desmatamento do INPE, como referência independente."

"Olhando a máscara só como diagnóstico, ela marca cerca de 7.975 hectares, e o PRODES cerca
de 4.125. Ela acerta boa parte do que o PRODES marca, mas marca muito além disso. Pasto e
rebrota podem pesar, mas a gente não mediu quanto."

"Isso não é a área desmatada do recorte. É a medida de quanto o método ainda erra."

"Com o NBR, as janelas intactas ficaram bem abaixo das janelas com desmatamento. Isso sugere
que dá para melhorar a recusa, mas com poucos controles e um único tile. Fica como hipótese,
não como resultado."

## Slide 9 · Encerramento — 30 s

"Fechando: o que funciona são as cinco etapas de processamento, todas escritas por nós com
NumPy; a quantificação exata quando existe verdade de terreno; a preparação de dados
alimentando um classificador de verdade; e 364 testes automatizados."

"O que a gente aprendeu foi na marra. A primeira cena real que baixamos estava tomada de
fumaça de queimada, e passou no nosso controle de nuvem — porque o infravermelho de ondas
curtas atravessa fumaça. Quem apontou o problema foi o próprio sistema, recusando a
detecção. A gente foi investigar a recusa e achou a fumaça. Hoje o controle de qualidade
mede bruma no canal azul."

"E o que falta: separar floresta de pasto e rebrota, recalibrar o critério com mais
controles, validar os descritores de textura, e tratar registro geométrico quando as duas
datas vierem de origens diferentes."

"Obrigado. Estamos à disposição para as perguntas — e qualquer um de nós responde sobre
qualquer parte."

---

# Checklist antes da apresentação

- [ ] App aberto no navegador antes de começar, em Enviar imagens. Não subir o servidor ao
      vivo
- [ ] Os dois arquivos `*_cor-e-infravermelho.png` numa pasta fácil de achar, e um envio de
      teste feito antes da aula
- [ ] Zoom do navegador em 125%, conferido no projetor
- [ ] `entrega/apresentacao-defesa.pptx` aberto no modo apresentador, com as notas visíveis
- [ ] Notificações do Windows desligadas e notebook na tomada
- [ ] Ensaio cronometrado: até 9 minutos. Se passar, encurtar a fala do slide 4
- [ ] **Cada integrante consegue responder as perguntas abaixo sem ler**

# Perguntas prováveis — e onde está a resposta

A regra do projeto vale aqui: *se o grupo não consegue explicar, não está pronto.* Estas
respostas precisam ser entendidas, não decoradas.

| Pergunta | Resposta curta | Onde mostrar |
|----------|----------------|--------------|
| Vocês usaram OpenCV? | Não. `pdi/` só importa NumPy. | `src/sentinela/pdi/filtros.py` |
| Qual a diferença entre convolução e correlação? | Convolução gira o núcleo 180°. Igual para núcleo simétrico; muda o sinal no Sobel. | `pdi/nucleo.py` — `convoluir` |
| O que acontece no pixel da borda? | A imagem é estendida por reflexão antes de convoluir. Preencher com zero criaria falso desmatamento na margem. | `pdi/nucleo.py` — `aplicar_borda` |
| Por que um limiar só para as duas datas? | Limiares separados medem a diferença entre histogramas, não o terreno. | `pdi/limiar.py` — `otsu_conjunto` |
| Por que não sai número na imagem real? | O critério recusou nas duas: MODIS (253 m), com pixel misto, e Sentinel-2 (10 m), por pouco. A resolução explica só parte; a máscara ainda marca além do PRODES. | `_interno/docs/resultados/sentinel-2/teste.json` |
| Como o arquivo traz cor e infravermelho? | É um PNG de quatro bandas: vermelho, verde e azul formam a cor, e a quarta é o infravermelho próximo. A etapa 1 mostra cada banda separada. | aba 1 Aquisição; `_interno/scripts/ver_bandas.py` |
| Como o infravermelho ajuda a achar floresta? | Ela fica escura no vermelho, que a clorofila absorve, e clara no infravermelho, que a folha reflete. O NDVI mede essa diferença. | aba 1 Aquisição |
| Vocês validaram contra o quê? | PRODES 2019–2024, referência independente do INPE. Comparamos a máscara só como diagnóstico. | `_interno/scripts/validar_prodes.py` |
| Por que a máscara marca 2× mais que o PRODES? | Hipótese: reage também a pasto e rebrota, e o PRODES tem outra definição. Não medimos quanto cada causa pesa. | `_interno/docs/resultados/sentinel-2/teste.json` |
| O recorte foi escolhido a dedo? | Foi escolhido por um critério fixo, para ter muita perda de floresta. Por isso não representa a região inteira. | `_interno/scripts/baixar_sentinel.py` |
| Não era só baixar o limiar para 3? | Seria escolher a régua depois da medida. | cap. 3.a do trabalho escrito |
| De onde saiu o 4,0? | Calibrado em cena sintética. **Precisa ser recalibrado** — é limitação declarada. | cap. 5 do trabalho escrito |
| Por que floresta aleatória e não rede neural? | Ela diz quais descritores pesaram. Dá para defender cada decisão. | `modelo/classificador.py` |
| F1 igual a 1 não é suspeito? | É. Cena sintética. O programa emite o aviso. | aba Modelo |
| Como garantem que treino e teste não se misturam? | Sorteio por bloco da imagem; teste confere pixel a pixel. | `modelo/classificador.py` — `dividir_espacialmente` |
| Por que usaram MODIS e Sentinel-2? | MODIS cobre 2002, antes do Sentinel-2. Sentinel-2 dá 10 m. Os dois foram baixados sem cadastro. | `_interno/data/raw/FONTES.md` |
| A textura ajuda o modelo? | **Não sabemos.** Na cena sintética ela não separa as classes. | `modelo/caracteristicas.py` |
| Como a fumaça passou no controle de nuvem? | Medíamos no infravermelho de ondas curtas, que atravessa fumaça. Hoje medimos no azul. | `_interno/scripts/baixar_imagens.py` |
| Por que NBR e não NDMI? | Mesma conta, SWIR diferente. O GIBS só traz a banda 7 do MODIS, que é SWIR 2 — isso dá o NBR. O NDMI precisa da banda 6. Já chamamos de NDMI por engano e corrigimos. | `pdi/cor.py` — `nbr` |

# O que **não** dizer

- "O sistema detectou X hectares de desmatamento em São Félix." — ele se recusou.
- "A máscara mediu 7.975 hectares de desmatamento." — é diagnóstico, e fica quase 2× acima do PRODES.
- "O limite certo é 2,8." — é hipótese, com 6 controles em um único tile.
- "A resolução era a causa." — a 10 m a recusa continuou.
- "O modelo tem 100% de acerto." — em cena sintética, e não valida nada.
- "A textura melhora a classificação." — não foi medido.
- "Os histogramas são unimodais, não há vale." — há vale; ele é raso.
- Qualquer número de desmatamento da Amazônia sem a fonte na mão.
