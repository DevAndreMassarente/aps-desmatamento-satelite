# Project State

_Atualizado em marcos, não a cada alteração. Última atualização: etapa de modelo._

## Current Phase

**Cinco etapas implementadas.** A cadeia roda de ponta a ponta, incluindo o
classificador: aquisição → manipulação → filtragem → segmentação → modelo. Nenhum módulo
do `src/` continua vazio. O que falta no programa não é código: são **imagens reais**
(R032).

Próxima fase: Fase Intermediária I — Qualificação (R040), que o enunciado manda concluir
**antes** do desenvolvimento prático pesado, em paralelo com a aquisição das cenas.

## Completed

- Enunciado oficial lido integralmente e movido para `docs/enunciado/` (hash verificado).
- Transcrição do PDF gerada (`docs/enunciado/TRANSCRICAO.md`) — o PDF original quebra
  `pdftotext` por usar `ToUnicode` por fonte.
- 50 requisitos extraídos e rastreados em `docs/REQUIREMENTS.md`.
- Problema definido: detecção e quantificação de desmatamento em imagens de satélite.
- Arquitetura definida espelhando as cinco etapas nomeadas pelo enunciado.
- Núcleo de PDI implementado com NumPy puro: convolução, filtros, limiarização,
  morfologia, segmentação e índices de vegetação.
- Achado metodológico: Otsu por data usa réguas diferentes, e a separabilidade η do
  artigo original não detecta cena homogênea. Resolvido com limiar conjunto e tamanho de
  efeito padronizado (`docs/decisions/003-limiar-bitemporal.md`).
- **`dataio/`** — leitura e escrita de imagem (Pillow), metadado geográfico opcional
  (rasterio), cena sintética determinística e composição visual dos resultados.
- **`pipeline/`** — orquestração das cinco etapas (`deteccao.py`) e extração de recortes
  rotulados para o modelo (`amostras.py`), que é o objetivo literal do enunciado (p.2).
- **`app/`** — interface Streamlit com as etapas lado a lado, quantificação em pixels e
  hectares, tabela de regiões e amostras para o modelo.
- **`cli.py`** — `sentinela app`, `sentinela detectar` e `sentinela demo`. A geração de
  evidência passa a ser reproduzível por comando, não por cliques numa tela.
- **`modelo/`** — `caracteristicas.py` extrai 15 descritores por recorte, todos vindos
  do núcleo de PDI do grupo; `classificador.py` treina uma floresta aleatória e relata
  precisão, revocação, F1 e matriz de confusão com os avisos que o número sozinho esconde.
- Divisão treino/teste **por blocos espaciais**, não por sorteio de recorte
  (`docs/decisions/004-divisao-espacial.md`). Os recortes se sobrepõem; sortear
  individualmente mediria memorização, não generalização.
- Suíte de testes: **241 passando**, incluindo os caminhos de erro, um teste de fumaça da
  interface e a verificação por força bruta de que treino e teste não compartilham pixel.
- Verificado que `pdi/` não importa `cv2`, `skimage`, `scipy` nem `PIL`, e não depende de
  nenhuma camada superior — a restrição central do enunciado continua de pé.
- Graphify preparado e validado sob Security Gate.

## In Progress

- Nada em andamento. Aguardando definição de integrantes e resposta às perguntas em aberto.

## Next

Em ordem de prioridade:

1. **Levar as perguntas Q1–Q8 ao professor** (`docs/PROJECT_SPEC.md` → Open Questions).
   Q5 (modelo treinado vs. proposta teórica) muda o escopo e trava o planejamento.
2. **Selecionar a região de estudo e baixar o par bi-temporal real** — é o bloqueio que
   segura R032, e por consequência R033, R034, R037, R044 e R050. Registrar em
   `data/raw/FONTES.md`.
3. Rodar `sentinela detectar` nas imagens reais e gerar as evidências em
   `docs/evidence/results/`.
4. Reavaliar `DISTINGUIBILIDADE_MINIMA` em cena real — hoje está calibrada só em
   sintética (B5).
5. Escrever Capítulo 1 + a parte de filtragem dos Capítulos 2 e 3 (**Fase Intermediária I**).
6. Reavaliar as features de textura em imagem real — na cena sintética elas não
   separam as classes, porque o gerador aplica o mesmo ruído às duas (limitação
   declarada em `modelo/caracteristicas.py`).

## Blockers

| # | Bloqueio | Impacto |
|---|----------|---------|
| B1 | Integrantes do grupo não definidos (Q7) | Ficha de APS e capa |
| B2 | Escopo do modelo indefinido (Q5) | Mitigado: `modelo/` foi implementado pela leitura conservadora do `AGENTS.md` §14 |
| B3 | Datas de P1/P2 desconhecidas (Q3) | Sem cronograma real |
| B4 | **Nenhuma imagem real baixada** | Segura R032 e mais cinco requisitos atrás dele |
| B5 | `DISTINGUIBILIDADE_MINIMA` calibrada só em cena sintética | Precisa ser reavaliada em imagem real antes de ir para o trabalho escrito |

## Known Issues

- O `python3-venv` desta máquina veio sem `ensurepip`, então `python3 -m venv` cria um
  ambiente sem `pip`. Contornado com `venv --without-pip` + `get-pip.py`. A correção
  definitiva é `sudo apt install python3-venv`, que precisa da senha do usuário.
- `rasterio` continua **não instalado** (dependência nativa GDAL). O sistema degrada para
  PNG/JPEG: a resolução espacial passa a ser informada à mão na interface ou por
  `--metros-por-pixel`. Instalar só se as cenas reais vierem em GeoTIFF.
- A convolução é `O(H·W·k²)` com laço sobre o kernel. Suficiente para os recortes usados
  na demonstração; pode ficar lenta em cena Sentinel-2 completa.
- **As features de textura não separam as classes na cena sintética**, porque o gerador
  aplica o mesmo desvio de ruído às duas. Elas continuam no vetor porque devem separar em
  imagem real — hipótese da literatura, ainda não medida. Não apresentar como validadas.
- **F1 = 1,0 na cena sintética não valida o modelo.** A separação radiométrica foi
  construída; o número prova que o encanamento funciona, não que o classificador serve.
  O próprio código emite esse aviso.

## Important Decisions

| # | Decisão | Onde |
|---|---------|------|
| D1 | Filtros implementados do zero, só com NumPy | `docs/decisions/001-filtros-proprios.md` |
| D2 | Imagens não versionadas no Git | `docs/decisions/002-dados-nao-versionados.md` |
| D3 | Abordagem bi-temporal (duas datas da mesma área) em vez de imagem única | `docs/ARCHITECTURE.md` |
| D4 | Streamlit para a interface, pela demonstração ao vivo | `docs/PROJECT_SPEC.md` |
| D5 | Representação interna `float32` em `[0,1]` | `docs/ARCHITECTURE.md` |
| D6 | Limiar único para as duas datas + confiabilidade por tamanho de efeito | `docs/decisions/003-limiar-bitemporal.md` |
| D7 | Graphify como contexto de código local, nunca versionado | `AGENTS.md` §17 |
| D8 | Detecção não confiável **não reporta área** — `resumo()` devolve `None` em vez de um número inventado | `pipeline/deteccao.py` |
| D9 | Recortes ambíguos são descartados na rotulagem, não arredondados para a classe majoritária | `pipeline/amostras.py` |
| D10 | Divisão treino/teste por blocos espaciais, nunca por sorteio de recorte | `docs/decisions/004-divisao-espacial.md` |
| D11 | Floresta aleatória em vez de rede convolucional, pela explicabilidade na banca | `modelo/classificador.py` |

## Graphify

| Campo | Valor |
|-------|-------|
| Estado | `STALE` |
| Grafo | `graphify-out/graph.json` — 433 nós, 726 arestas |
| Validado em | commit `64f6dec` |
| Baseline | `~/.local/state/graphify-baseline/aps-desmatamento-satelite/` |

Marcado `STALE` porque `dataio/`, `pipeline/`, `app/` e `cli.py` foram adicionados depois
da última extração. Regenerar pelo procedimento do `AGENTS.md` §17 antes de confiar em
consulta ao grafo. Data do arquivo não comprova atualidade.
