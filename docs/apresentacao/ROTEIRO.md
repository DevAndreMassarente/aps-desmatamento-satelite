# Roteiro da apresentação

> Enunciado, seção III: sessão de **10 a 15 minutos**, com **explicação do problema e
> contexto**, **demonstração da aplicação** e **discussão dos resultados**. O grupo deve
> estar preparado para **perguntas da turma e dos professores**.

## Como a apresentação é avaliada (30% da nota)

| Critério | Peso | O que isso exige na prática |
|----------|------|-----------------------------|
| Participação de todos os membros | 20% | cada integrante apresenta um bloco — e responde perguntas sobre **qualquer** bloco |
| Qualidade do projeto prático e teórico | 50% | mostrar o programa funcionando e defender as decisões |
| Clareza e estrutura | 30% | seguir a ordem abaixo, sem voltar atrás, dentro do tempo |

> **Integrantes ainda não definidos (Q7).** Os blocos estão atribuídos a papéis A, B, C e
> D. Com menos de quatro pessoas, juntar blocos adjacentes.

---

## Estrutura — 13 minutos, com 2 de folga

| # | Bloco | Quem | Tempo | Parte exigida pelo enunciado |
|---|-------|------|------:|------------------------------|
| 1 | O problema | A | 2:00 | problema e contexto |
| 2 | O objetivo e a abordagem | A | 1:30 | problema e contexto |
| 3 | Como o sistema funciona | B | 3:00 | problema e contexto |
| 4 | Demonstração ao vivo | C | 4:00 | **demonstração da aplicação** |
| 5 | Resultado em imagem real | D | 2:00 | **discussão dos resultados** |
| 6 | O que aprendemos e o que falta | D | 0:30 | **discussão dos resultados** |
| | **Total** | | **13:00** | |

---

## Bloco 1 — O problema · A · 2:00

**Mensagem:** desmatamento não se descobre olhando uma imagem; se descobre comparando duas.

- Mostrar `figuras/comparativo-real.png`: São Félix do Xingu (PA), 2002 × 2024.
- Uma cena só não distingue pasto de 30 anos de desmatamento do mês passado. A informação
  está na **diferença entre duas datas**.
- Por que importa: fiscalização precisa saber **onde olhar**. Detecção automática
  transforma vigilância impossível em priorização.
- Custo de errar nas duas direções: falso positivo pune quem não desmatou; falso negativo
  deixa passar. Guardar essa frase — ela volta no Bloco 5.

> Não citar número de área desmatada sem a fonte do PRODES em mãos
> (`docs/trabalho-escrito/BIBLIOGRAFIA.md`, B1).

## Bloco 2 — O objetivo e a abordagem · A · 1:30

**Mensagem:** o processamento de imagens aqui é preparação de dados, não o fim.

- Ler a frase do objetivo do enunciado: PDI para **alimentar um modelo de visão
  computacional**.
- As cinco etapas: aquisição → manipulação → filtragem → segmentação → modelo.
- A máscara de segmentação vira **rótulo** dos recortes que treinam o classificador.
- **Todos os filtros foram implementados pelo grupo**, com NumPy apenas.

## Bloco 3 — Como o sistema funciona · B · 3:00

**Mensagem:** três decisões determinam o resultado.

1. **Suavizar antes de limiarizar.** Sem o gaussiano o ruído atravessa o limiar pixel a
   pixel e a máscara sai esburacada — centenas de "regiões" onde existe uma.
2. **Um limiar único para as duas datas.** Otsu em cada data dá réguas diferentes; a
   comparação passaria a medir a diferença entre os limiares, não o terreno. Solução:
   Otsu sobre o histograma **conjunto**.
3. **O sistema sabe quando não sabe.** Otsu sempre devolve um número, mesmo sem duas
   classes. Antes de usar o limiar, o sistema mede o tamanho de efeito entre as classes;
   abaixo de 4,0, **recusa-se a reportar área**.

Opcional, se sobrar tempo: gaussiano separável — `exp(−(x²+y²)) = exp(−x²)·exp(−y²)`,
até 9,4× mais rápido com o mesmo resultado.

## Bloco 4 — Demonstração ao vivo · C · 4:00

**Preparar antes de subir ao palco** — ver *Checklist* abaixo. A interface roda em
`localhost` e **não precisa de internet**.

| Passo | Ação na tela | O que dizer |
|------:|--------------|-------------|
| 1 | Abrir `http://localhost:8501`, fonte **Cena sintética** | "Cena construída com área desmatada de tamanho conhecido — é sintética, e está marcado na tela." |
| 2 | Mostrar as métricas no topo | "20×20 = 400 pixels construídos; o sistema detecta 400. A 10 m/pixel, 4 hectares." |
| 3 | Aba **Etapas** — índice bruto × gaussiano × Sobel | "Filtros nossos. Aqui está o efeito da suavização, e o Sobel realçando a borda do corte." |
| 4 | Aba **Etapas** — mapa de mudança | "Vermelho é perda. O limiar é o mesmo para as duas datas." |
| 5 | Barra lateral: **Lado da área desmatada = 0** | "Agora duas datas de floresta intacta." |
| 6 | Apontar a caixa vermelha de recusa | "**O sistema se recusa a dar número.** Sem duas classes, o limiar cortaria o ruído ao meio e inventaria desmatamento." |
| 7 | Voltar a área para 60, tamanho da cena 200; aba **Modelo** | "Os recortes rotulados pela máscara treinam uma floresta aleatória." |
| 8 | Apontar o aviso de desempenho perfeito | "F1 igual a 1. **Não vale nada**, e o próprio programa avisa: a separação foi construída." |

### Plano B — se a interface não abrir

```bash
sentinela demo --tamanho 200 --area 80 --modelo
```

e mostrar as imagens de `docs/evidence/demo-sintetica/`. Treinar o plano B uma vez.

## Bloco 5 — Resultado em imagem real · D · 2:00

**Mensagem:** o resultado principal foi uma recusa — e ela está certa.

- Imagem real: MODIS/Terra, São Félix do Xingu, 2002 × 2024, ≈253 m/pixel.
- A perda é visível a olho nu. **O sistema recusou-se a quantificar.**
- Mostrar `figuras/histogramas-ndvi-nbr.png`: as duas datas **se sobrepõem demais**. Existe
  vale entre as classes — no NDVI de 2024 dá para ver dois montes — mas é **raso**: nenhum
  corte atinge o tamanho de efeito exigido.
- Não dizer que "não há vale": a figura mostra que há, e alguém da banca vai apontar.
- Causa: a 253 m, cada pixel mistura floresta, pasto, regeneração e estrada.
- Três hipóteses testadas antes de concluir:

| Hipótese | Resultado |
|----------|-----------|
| Índice errado? | NBR melhora (3,51 contra 2,99), ainda abaixo de 4,0 |
| Abordagem errada? | Limiarizar a diferença é **pior** (2,79) |
| Resolução? | **Confirmado** |

- **A frase mais importante da apresentação:** "Bastaria baixar o critério para 3,0 e
  teríamos um número. Não fizemos isso — escolher a régua depois de ver a medida não é
  medir."

## Bloco 6 — O que aprendemos e o que falta · D · 0:30

- A primeira cena real estava tomada por **fumaça de queimada**, e passou no controle de
  nuvem: o infravermelho de ondas curtas atravessa fumaça. O sistema recusou a detecção
  e a medição encontrou a causa.
- O que falta para um número defensável não é código: é imagem de 10 a 30 m (Sentinel-2
  ou Landsat).

---

## Checklist antes da apresentação

- [ ] `pytest` passando na máquina da apresentação
- [ ] `sentinela app` **reiniciado depois da última alteração no código** e **já aberto** no
      navegador antes de começar — não subir ao vivo. Um servidor antigo mostra código antigo:
      o Streamlit não recarrega os módulos do pacote sozinho
- [ ] Cena sintética carregada, área desmatada em 20, tamanho da cena em 80
- [ ] Figuras de `docs/apresentacao/figuras/` abertas ou nos slides
- [ ] Plano B testado: `sentinela demo --modelo` roda
- [ ] Cronometrar um ensaio completo; cortar o opcional do Bloco 3 se passar de 13 min
- [ ] **Cada integrante consegue responder as perguntas abaixo sem ler**

---

## Perguntas prováveis — e onde está a resposta

A regra do projeto vale aqui: *se o grupo não consegue explicar, não está pronto.* Estas
respostas precisam ser entendidas, não decoradas.

| Pergunta | Resposta curta | Onde mostrar |
|----------|----------------|--------------|
| Vocês usaram OpenCV? | Não. `pdi/` só importa NumPy. | `src/sentinela/pdi/filtros.py` |
| Qual a diferença entre convolução e correlação? | Convolução gira o núcleo 180°. Igual para núcleo simétrico; muda o sinal no Sobel. | `pdi/nucleo.py` — `convoluir` |
| O que acontece no pixel da borda? | A imagem é estendida por reflexão antes de convoluir. Preencher com zero criaria falso desmatamento na margem. | `pdi/nucleo.py` — `aplicar_borda` |
| Por que um limiar só para as duas datas? | Limiares separados medem a diferença entre histogramas, não o terreno. | `pdi/limiar.py` — `otsu_conjunto` |
| Por que não sai número na imagem real? | A 253 m o pixel é misto: as classes se sobrepõem e o vale entre elas é raso demais. | `docs/decisions/005-resolucao-espacial.md` |
| Não era só baixar o limiar para 3? | Seria escolher a régua depois da medida. | cap. 3.a do trabalho escrito |
| De onde saiu o 4,0? | Calibrado em cena sintética. **Precisa ser recalibrado** — é limitação declarada. | `AGENTS.md` §16, T5 |
| Por que floresta aleatória e não rede neural? | Ela diz quais descritores pesaram. Dá para defender cada decisão. | `modelo/classificador.py` |
| F1 igual a 1 não é suspeito? | É. Cena sintética. O programa emite o aviso. | aba Modelo |
| Como garantem que treino e teste não se misturam? | Sorteio por bloco da imagem; teste confere pixel a pixel. | `modelo/classificador.py` — `dividir_espacialmente` |
| Por que MODIS e não Sentinel-2? | Não exige cadastro — qualquer um reproduz. Custo: resolução. | `data/raw/FONTES.md` |
| A textura ajuda o modelo? | **Não sabemos.** Na cena sintética ela não separa as classes. | `modelo/caracteristicas.py` |
| Como a fumaça passou no controle de nuvem? | Medíamos no infravermelho de ondas curtas, que atravessa fumaça. Hoje medimos no azul. | `scripts/baixar_imagens.py` |
| Por que NBR e não NDMI? | Mesma conta, SWIR diferente. O GIBS só traz a banda 7 do MODIS, que é SWIR 2 — isso dá o NBR. O NDMI precisa da banda 6. Já chamamos de NDMI por engano e corrigimos. | `pdi/cor.py` — `nbr` |

## O que **não** dizer

- ❌ "O sistema detectou X hectares de desmatamento em São Félix." — ele se recusou.
- ❌ "O modelo tem 100% de acerto." — em cena sintética, e não valida nada.
- ❌ "A textura melhora a classificação." — não foi medido.
- ❌ Qualquer número de desmatamento da Amazônia sem a fonte na mão.
