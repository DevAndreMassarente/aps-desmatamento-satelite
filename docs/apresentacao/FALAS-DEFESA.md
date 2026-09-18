# Falas — Fase Intermediária II (Defesa)

Enunciado, seção III: sessão de **10 a 15 minutos**, com **explicação do problema e
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

## Divisão — 13 minutos, com 2 de folga

| Slides | Bloco | Quem | Tempo | Parte exigida pelo enunciado |
|--------|-------|------|------:|------------------------------|
| 1–2 | Abertura e roteiro | André Massarente | 0:45 | — |
| 3–4 | O problema e o objetivo | André Massarente | 3:00 | problema e contexto |
| 5–9 | Como o sistema funciona | Enzo Consani | 4:30 | problema e contexto |
| 10–12 | Demonstração ao vivo | Isabel Da Silva | 3:55 | **demonstração da aplicação** |
| 13–16 | Resultados e encerramento | Jonathan Aparecido X Martins | 3:15 | **discussão dos resultados** |
| | **Total** | | **≈13:00** | |

---

# André Massarente — slides 1 a 4

## Slide 1 · Capa — 20 s

"Boa noite. Nós somos o grupo do tema de sustentabilidade ambiental: detecção e
quantificação de desmatamento em imagens de satélite."

"Eu sou o André, e comigo estão o Enzo, a Isabel e o Jonathan. Cada um de nós apresenta uma
parte, e todos respondem perguntas sobre qualquer parte."

"São treze minutos: o problema, como o sistema funciona, o programa rodando ao vivo e os
resultados — inclusive um resultado que foi uma recusa, e vamos explicar por quê."

## Slide 2 · O que vamos mostrar — 25 s

"A apresentação segue exatamente as três partes pedidas no manual da APS."

"Primeiro o problema e o contexto — eu começo e o Enzo continua explicando como o sistema
funciona por dentro. Depois a Isabel mostra o programa rodando. No fim o Jonathan discute
os resultados."

"Guardem uma frase: o resultado mais importante deste trabalho foi o programa se recusar a
dar um número. No final a gente explica por que isso é um acerto."

## Slide 3 · O problema — 2:00

"Esta é a mesma região da Amazônia em duas datas: 2002 em cima à esquerda, 2024 à direita.
Embaixo, o mesmo recorte no índice NBR, em falsa cor — o verde escuro é vegetação densa, o
amarelo é solo exposto."

"Olhando só a imagem de 2024, eu não sei o que é pasto antigo e o que é corte recente. As
duas coisas são claras na imagem. A informação de desmatamento não está numa imagem: está
na **diferença** entre duas datas. É daí que sai todo o desenho do sistema."

"As imagens são reais, do satélite Terra da NASA, obtidas pelo serviço GIBS. São de domínio
público e a procedência está registrada no trabalho escrito: produto, data, coordenadas,
licença e URL."

"Por que isso importa: fiscalizar a Amazônia inteira a olho é impossível. Detecção
automática não substitui o fiscal — ela diz onde olhar primeiro."

"E errar custa caro dos dois lados. Se o sistema aponta desmatamento onde não houve, alguém
é punido injustamente. Se deixa passar, a floresta não volta. Guardem essa frase, porque
ela volta no final da apresentação."

> Não citar número de área desmatada da Amazônia sem a fonte do PRODES em mãos.

## Slide 4 · O objetivo — 1:00

"Essa frase é do enunciado, e ela decide o projeto inteiro: o processamento de imagens aqui
é **preparação de dados**. Ele não é o produto final."

"Na prática: o PDI compara as duas datas e produz uma máscara de perda de vegetação. Essa
máscara vira o **rótulo** dos recortes de imagem. Os recortes rotulados treinam um
classificador, que depois consegue olhar um recorte novo sem precisar do par de datas. O
modelo só existe porque a etapa de PDI gerou o rótulo."

"E uma restrição que vale a pena registrar agora: o enunciado exige que os filtros sejam
desenvolvidos pelo grupo. Então dentro do nosso núcleo de processamento a única biblioteca
é o NumPy. Não tem OpenCV, não tem scikit-image, não tem scipy. O Enzo vai mostrar os
filtros funcionando no próximo slide."

**→ passa para o Enzo.**

---

# Enzo Consani — slides 5 a 9

## Slide 5 · As cinco etapas — 40 s

"O programa tem cinco etapas, e elas não são invenção nossa: é a sequência que o próprio
enunciado nomeia. A gente espelhou isso na organização das pastas do código, então cada
etapa tem um lugar e dá para apontar onde ela está."

"Aquisição baixa o par de datas. Manipulação calcula os índices de vegetação. Filtragem
aplica os filtros espaciais. Segmentação decide o que é perda e o que não é. E o modelo
pega o resultado e treina o classificador."

"Um detalhe de implementação que importa para a demonstração: o programa guarda **todos**
os resultados intermediários. Não é uma caixa que entra imagem e sai número — a Isabel vai
mostrar etapa por etapa na tela."

## Slide 6 · Os filtros são nossos — 50 s

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

"E os testes: 340 no total. Eles não comparam com OpenCV — comparam com casos analíticos.
Convolução com núcleo identidade devolve a imagem original; Sobel numa rampa linear devolve
gradiente constante; Otsu numa imagem bimodal cai entre os dois modos."

## Slide 7 · Duas decisões que mudam o resultado — 1:00

"Duas decisões de projeto que mudam o resultado, e que a gente consegue defender."

"Primeira: suavizar **antes** de limiarizar. O limiar é uma comparação pixel a pixel. Se a
imagem chega com ruído, cada pixel de ruído que passa do corte vira um ponto isolado na
máscara. O programa então rotula centenas de regiõezinhas onde na verdade existe uma área
só. E não adianta suavizar depois — depois de binarizar a informação já se perdeu."

"Segunda: um limiar único para as duas datas. Isso parece detalhe e não é. Se a gente roda
Otsu separado em 2002 e em 2024, cada data ganha uma régua própria. Aí a comparação entre
as duas máscaras passa a medir a diferença entre as **regras**, não a diferença no terreno.
A solução foi juntar os dois histogramas e calcular um limiar só, aplicado dos dois lados."

## Slide 8 · O sistema sabe quando não sabe — 1:10

"Essa é a decisão da qual a gente mais se orgulha, e é a que mais rende pergunta."

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

## Slide 9 · Da máscara ao modelo — 50 s

"Essa é a ponte entre as duas metades do trabalho. A máscara que o PDI produziu vira o
rótulo do conjunto de treino."

"A cena é recortada em pedaços de 16 por 16. Cada recorte olha quanto da sua área está
marcada na máscara: mais de 60 por cento, é desmatado; menos de 5 por cento, é intacto. O
que cai no meio a gente joga fora de propósito — rótulo duvidoso ensina coisa errada."

"De cada recorte saem quinze descritores, e todos são calculados pelo nosso código de PDI.
Se o professor perguntar de onde vem a textura, a resposta é desvio-padrão local, e o
algoritmo está no repositório. O scikit-learn entra só no algoritmo de aprendizado, que é o
que o enunciado permite."

"E o detalhe embaixo, que é o erro mais comum nesse tipo de trabalho: a divisão entre treino
e teste é **por bloco** da imagem, não por sorteio. Como os recortes se sobrepõem, sortear
um a um colocaria o mesmo pedaço de terreno nos dois lados. A acurácia ficaria linda e seria
vazamento."

**→ passa para a Isabel.**

---

# Isabel Da Silva — slides 10 a 12 · demonstração ao vivo

> **Antes de subir ao palco:** o navegador já precisa estar aberto em `localhost:8501`,
> com a cena sintética carregada, tamanho da cena em 80 e lado da área desmatada em 20.
> **Não subir o servidor ao vivo.** A interface roda local e não precisa de internet.

## Slide 10 · Abertura da demonstração — 25 s

"Agora o programa rodando. Ele é uma aplicação local, roda no navegador e não precisa de
internet — o que a gente mostra aqui funciona offline."

"O roteiro é esse: começo pela cena sintética, mostro as cinco etapas por dentro, mostro a
quantificação batendo com a verdade de terreno, depois mostro o programa se recusando a
responder, e termino no modelo."

"Por que cena sintética e não a imagem de satélite: porque na cena sintética eu **sei** qual
é a resposta certa. É assim que a gente confere se a quantificação funciona. A imagem real
vem no bloco do Jonathan."

**→ trocar para o navegador.**

## Slide 11 · Etapa por etapa, na tela — 1:30

Aba **Etapas do processamento**:

"Etapa 1, aquisição: as duas datas lado a lado. Etapa 2, o índice de vegetação — o verde é
vegetação densa e o amarelo é solo exposto. Já dá para ver o corte na segunda data."

"Etapa 3 é a filtragem, e aqui é onde aparece o trabalho da disciplina. À esquerda o índice
bruto, com o ruído. No meio, depois do gaussiano 5 por 5 — o ruído sumiu e a borda do corte
continuou lá. À direita o Sobel, que é a magnitude do gradiente: ele acende exatamente no
contorno da área cortada."

"Etapa 4, segmentação. O limiar separa vegetação de solo exposto, e o mapa de mudança
compara as duas máscaras. Atenção na legenda: vermelho é **perda**, verde é ganho,
verde-escuro é vegetação que ficou de pé e cinza é solo exposto nas duas datas."

"E uma coisa que costuma confundir: esse mapa não é a subtração de uma imagem pela outra. É
a comparação entre duas máscaras calculadas com o **mesmo** limiar, que é a decisão que o
Enzo explicou."

## Slide 12 · Quantificação e recusa — 2:00

Aba **Detecção**:

"Agora a quantificação. A cena foi construída com um corte de 20 por 20 pixels, o que dá
400 pixels. O programa detectou 400. Erro de zero por cento. E o próprio programa mostra a
verdade de terreno ali embaixo, para dar para conferir."

"Ao lado, os 400 pixels convertidos em hectares. Isso depende da resolução: a 10 metros por
pixel, que é o Sentinel-2, dá 4 hectares. A escala é escolhida ali na barra lateral, e é
assim que se sai de pixel para área de verdade."

"Mas eu preciso ser honesta sobre o que esse número prova: ele prova que a **cadeia**
funciona de ponta a ponta. Ele não prova desempenho no mundo real, porque quem construiu a
separação entre floresta e corte foi o gerador da cena. Por isso a tela avisa em azul que a
imagem é sintética."

**Ao vivo:** arrastar *Lado da área desmatada* para **0**.

"Agora eu zerei a área desmatada: são duas datas de floresta intacta, sem corte nenhum.
Olhem o que acontece."

**Apontar a caixa vermelha.**

"O programa **se recusa** a dar um número, e explica: a distinguibilidade ficou em 2,66,
abaixo do mínimo de 4,0. Sem duas classes reais, o limiar cortaria o ruído ao meio e
inventaria desmatamento onde não houve. Recusar é a resposta certa."

**Ao vivo:** voltar a área para 60, tamanho da cena para 200, abrir a aba **Modelo**.

"E no modelo: os recortes rotulados pela máscara treinam a floresta aleatória. O F1 dá 1,000
— e o programa avisa, em amarelo, que esse número **não** vale como validação, porque em
cena sintética a separação foi construída. O Jonathan explica agora o que aconteceu quando a
gente rodou isso em imagem de satélite de verdade."

**→ passa para o Jonathan.**

### Plano B — se a interface não abrir

```bash
sentinela demo --tamanho 200 --area 80 --modelo
```

e mostrar os slides 11 e 12, que já trazem as mesmas telas. Treinar o plano B uma vez.

---

# Jonathan Aparecido X Martins — slides 13 a 16

## Slide 13 · Resultado em cena sintética — 45 s

"Resumindo o que a Isabel mostrou, em números. A quantificação errou zero por cento nos dois
tamanhos de corte que a gente testou: 400 pixels e 6.400 pixels. A 10 metros por pixel, os
6.400 viram 64 hectares. E a cadeia inteira roda em cerca de 730 milissegundos numa cena de
440 por 440."

"O classificador deu 1,000 em precisão, revocação e F1. E eu quero ser muito claro sobre
isso, porque é o tipo de número que engana: ele **não** valida o modelo."

"Numa cena sintética quem construiu a separação entre as classes foi o nosso gerador.
Acertar tudo era o resultado esperado, não uma conquista. Tanto que o próprio programa emite
esse aviso em amarelo, junto da métrica — ele não depende de alguém lembrar de ler a
ressalva no relatório."

"O que esse número mostra de verdade é que a preparação de dados funciona de ponta a ponta:
a máscara vira rótulo, o rótulo vira conjunto de treino, e o treino acontece."

## Slide 14 · Resultado em imagem real — 1:15

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

"A causa é a resolução. A 253 metros por pixel, cada pixel mistura floresta, pasto,
regeneração e estrada num valor só. Tudo vira um cinza intermediário."

"E a gente não chutou isso. Testou três hipóteses: primeiro, será que era o índice errado?
Trocamos NDVI por NBR: melhorou de 2,99 para 3,51 e continuou abaixo de 4. Segundo, será que
era a abordagem? Limiarizar a imagem de diferença deu 2,79, ainda pior. Terceiro, a
resolução — é a única que sobrou, e é a que explica tudo."

## Slide 15 · A decisão metodológica — 45 s

> Este é o slide mais importante da apresentação. Falar devagar.

"A cena real deu 3,51. O nosso critério é 4,0. Bastava baixar o critério para 3,0 e a gente
teria um número de hectares para colocar no trabalho."

*[pausa]*

"A gente não fez isso. **Escolher a régua depois de ver a medida não é medir.**"

"O critério de 4,0 foi calibrado em cena sintética, antes de existir imagem real no projeto.
Mudar ele depois, só para a cena passar, produziria um número bonito e sem significado
nenhum."

"Então o que o sistema entregou foi: o mapa de mudança, as distribuições, a medida de
separação e a recusa — com o motivo explicado na tela. O que ele não entregou foi o número
de hectares."

"E o que falta para entregar esse número não é código. É imagem de 10 a 30 metros por pixel
— Sentinel-2 ou Landsat. Com MODIS, a 253 metros, não dá."

## Slide 16 · Encerramento — 30 s

"Fechando: o que funciona são as cinco etapas de processamento, todas escritas por nós com
NumPy; a quantificação exata quando existe verdade de terreno; a preparação de dados
alimentando um classificador de verdade; e 340 testes automatizados."

"O que a gente aprendeu foi na marra. A primeira cena real que baixamos estava tomada de
fumaça de queimada, e passou no nosso controle de nuvem — porque o infravermelho de ondas
curtas atravessa fumaça. Quem apontou o problema foi o próprio sistema, recusando a
detecção. A gente foi investigar a recusa e achou a fumaça. Hoje o controle de qualidade
mede bruma no canal azul."

"E o que falta: imagem de resolução melhor, validar os descritores de textura, e tratar
registro geométrico quando as duas datas vierem de origens diferentes."

"Obrigado. Estamos à disposição para as perguntas — e qualquer um de nós responde sobre
qualquer parte."

---

# Checklist antes da apresentação

- [ ] `pytest` passando na máquina da apresentação
- [ ] `sentinela app` **reiniciado depois da última alteração no código** e **já aberto** no
      navegador antes de começar — não subir ao vivo. Um servidor antigo mostra código antigo:
      o Streamlit não recarrega os módulos do pacote sozinho
- [ ] Cena sintética carregada, área desmatada em 20, tamanho da cena em 80
- [ ] `entrega/apresentacao-defesa.pptx` aberto no modo apresentador, com as notas visíveis
- [ ] Plano B testado: `sentinela demo --modelo` roda
- [ ] Cronometrar um ensaio completo; cortar a otimização do gaussiano no slide 6 se passar
      de 13 minutos
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
| Por que não sai número na imagem real? | A 253 m o pixel é misto: as classes se sobrepõem e o vale entre elas é raso demais. | cap. 3.a do trabalho escrito |
| Não era só baixar o limiar para 3? | Seria escolher a régua depois da medida. | cap. 3.a do trabalho escrito |
| De onde saiu o 4,0? | Calibrado em cena sintética. **Precisa ser recalibrado** — é limitação declarada. | cap. 5 do trabalho escrito |
| Por que floresta aleatória e não rede neural? | Ela diz quais descritores pesaram. Dá para defender cada decisão. | `modelo/classificador.py` |
| F1 igual a 1 não é suspeito? | É. Cena sintética. O programa emite o aviso. | aba Modelo |
| Como garantem que treino e teste não se misturam? | Sorteio por bloco da imagem; teste confere pixel a pixel. | `modelo/classificador.py` — `dividir_espacialmente` |
| Por que MODIS e não Sentinel-2? | Não exige cadastro — qualquer um reproduz. Custo: resolução. | `data/raw/FONTES.md` |
| A textura ajuda o modelo? | **Não sabemos.** Na cena sintética ela não separa as classes. | `modelo/caracteristicas.py` |
| Como a fumaça passou no controle de nuvem? | Medíamos no infravermelho de ondas curtas, que atravessa fumaça. Hoje medimos no azul. | `scripts/baixar_imagens.py` |
| Por que NBR e não NDMI? | Mesma conta, SWIR diferente. O GIBS só traz a banda 7 do MODIS, que é SWIR 2 — isso dá o NBR. O NDMI precisa da banda 6. Já chamamos de NDMI por engano e corrigimos. | `pdi/cor.py` — `nbr` |

# O que **não** dizer

- "O sistema detectou X hectares de desmatamento em São Félix." — ele se recusou.
- "O modelo tem 100% de acerto." — em cena sintética, e não valida nada.
- "A textura melhora a classificação." — não foi medido.
- "Os histogramas são unimodais, não há vale." — há vale; ele é raso.
- Qualquer número de desmatamento da Amazônia sem a fonte na mão.
