# Project State

_Atualizado em marcos, não a cada alteração. Última atualização: capítulos 1 a 5 e 7 do trabalho escrito._

## Current Phase

**Primeira execução em imagem real, com resultado negativo documentado.** A cadeia
roda de ponta a ponta e já processou um par bi-temporal MODIS de São Félix do Xingu
(2002 e 2024). O sistema **recusou-se a quantificar**: a 253 m/pixel as classes se
sobrepõem demais — o vale entre elas é raso — e o critério de confiabilidade disparou. A recusa está correta e o
diagnóstico está em `docs/decisions/005-resolucao-espacial.md`.

O bloqueio deixou de ser "não temos imagem real" e passou a ser **"precisamos de 10 a
30 m/pixel"**, o que exige cadastro no Copernicus ou no USGS.

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
- **`scripts/baixar_imagens.py`** — aquisição reproduzível via NASA GIBS (MODIS/Terra),
  sem credencial, com controle de qualidade que mede ausência de dado, nuvem e **bruma**.
- Par bi-temporal real baixado e registrado em `data/raw/FONTES.md` com procedência,
  licença e URLs exatas.
- Dois achados de medição documentados: os dois produtos GIBS realçam a banda 1 de forma
  diferente (média 88 contra 62), e **fumaça de queimada atravessa o SWIR** — o controle
  de qualidade original aprovou uma cena tomada por fumaça, que inverteu a comparação
  entre as datas.
- **NDMI implementado** (`pdi.cor.ndmi`), exposto na CLI (`--metodo ndmi`) e na
  interface; a cena sintética ganhou banda SWIR para que ele seja demonstrável.
- **Trabalho escrito** (`docs/trabalho-escrito/`): Capítulos 1, 3.a, 4 e 5 com rascunho
  completo, Capítulo 2 com a parte de filtragem completa, Capítulo 7 gerado por comando.
  A Fase Intermediária I está coberta. Nenhuma referência inventada: 13 pendências
  mapeadas em `BIBLIOGRAFIA.md`.
- Erro de escala corrigido na documentação: a queda do índice entre as datas tinha sido
  reportada na escala interna `[0,1]` do pipeline (0,06 e 0,11) em vez da escala nativa
  `[-1,1]` do índice (0,150 e 0,295). Corrigido em três documentos.
- **Gaussiano separável**: dois passes 1D em vez do núcleo 2D, explorando uma identidade
  algébrica exata. Medido: 2,2× mais rápido em janela 5×5 e 9,4× em 21×21, com
  diferença máxima de 1e-6 (arredondamento de `float32`). Os números reportados na
  imagem real não mudaram.
- **Apêndice de código-fonte gerado por comando** (`sentinela apendice`), atendendo
  o Capítulo 7 do enunciado. Gerado e não copiado, para não divergir do código
  entregue: 16 arquivos, 3.782 linhas.
- **Média separável**: mesmo tratamento do gaussiano, até 11,3× em janela 21×21.
- **Apresentação preparada** (`docs/apresentacao/`): roteiro de 13 minutos em seis blocos com
  a parte exigida pelo enunciado em cada um, passo a passo da demonstração ao vivo, plano B,
  checklist e 14 perguntas prováveis com onde está a resposta no código.
- **Figuras da apresentação** geradas dos dados reais: comparativo 2002 × 2024 e histogramas
  NDVI/NDMI com tabela equivalente. A paleta foi validada por script (daltonismo e contraste).
- **Screenshots da interface por comando** (`scripts/capturar_telas.mjs`): quatro telas,
  incluindo a recusa. Regerar antes da entrega — o `AGENTS.md` exige telas da versão entregue.
- **Interface revisada** a partir dos screenshots: ícones que dependiam de fonte de emoji
  viravam quadrados, a máscara toda branca sumia no fundo, e os números usavam ponto decimal.
- **Correção de descrição**: o texto dizia que os histogramas reais eram "unimodais" e sem
  vale. O gráfico mostrou vale raso entre as classes. Corrigido em 11 documentos; a
  conclusão e as métricas não mudam.
- **Bug no aviso de "desempenho perfeito"**, achado pelo screenshot: disparava com teste de uma
  classe só, ao lado de precisão, revocação e F1 iguais a zero. Corrigido, com teste de
  regressão.
- Graphify regenerado e validado — `READY`.
- Suíte de testes: **294 passando**, incluindo os caminhos de erro, um teste de fumaça da
  interface e a verificação por força bruta de que treino e teste não compartilham pixel.
- Verificado que `pdi/` não importa `cv2`, `skimage`, `scipy` nem `PIL`, e não depende de
  nenhuma camada superior — a restrição central do enunciado continua de pé.
- Graphify preparado e validado sob Security Gate.

## In Progress

- Nada em andamento. Aguardando definição de integrantes e resposta às perguntas em aberto.

## Next

Em ordem de prioridade:

1. **Criar conta no Copernicus Data Space ou no USGS EarthExplorer** e baixar um par
   Sentinel-2 (10 m) ou Landsat (30 m) da mesma área. É o único caminho para a
   quantificação validada; o cadastro precisa ser feito por um integrante do grupo.
2. **Levar as perguntas Q1–Q8 ao professor** (`docs/PROJECT_SPEC.md` → Open Questions).
   Q5 (modelo treinado vs. proposta teórica) muda o escopo e trava o planejamento.
3. Recalibrar `DISTINGUIBILIDADE_MINIMA` por procedimento honesto (B5): medir a
   distribuição da métrica em pares de floresta intacta e em pares com desmatamento
   validado pelo PRODES. **Não** ajustar o número para fazer uma cena específica passar.
5. **Revisar o rascunho do trabalho escrito em grupo** e resolver as 13 pendências de
   bibliografia. O texto existe, mas precisa ser assumido por quem vai defendê-lo.
6. Redigir as seções que faltam — 2.e.i, 2.e.ii, 2.e.iv, 2.e.v e 3.b. Sem bloqueio: o
   conteúdo já existe no repositório, falta escrever.
7. Montar o documento final em ABNT e preencher a Ficha de APS (bloqueado por Q7).
6. Reavaliar as features de textura em imagem real — na cena sintética elas não
   separam as classes, porque o gerador aplica o mesmo ruído às duas (limitação
   declarada em `modelo/caracteristicas.py`).

## Blockers

| # | Bloqueio | Impacto |
|---|----------|---------|
| B1 | Integrantes do grupo não definidos (Q7) | Ficha de APS e capa |
| B2 | Escopo do modelo indefinido (Q5) | Mitigado: `modelo/` foi implementado pela leitura conservadora do `AGENTS.md` §14 |
| B3 | Datas de P1/P2 desconhecidas (Q3) | Sem cronograma real — e a Fase Intermediária I tem prazo amarrado à P1 |
| B4 | ~~Nenhuma imagem real baixada~~ — **resolvido**: par MODIS baixado e processado | — |
| B6 | **Resolução de 250 m insuficiente**: classes sobrepostas, vale raso, detecção recusada | Trava a quantificação. Exige Sentinel-2/Landsat, que exigem cadastro |
| B5 | `DISTINGUIBILIDADE_MINIMA` calibrada só em cena sintética | Confirmado em imagem real. Recalibrar por procedimento honesto, nunca ajustando para uma cena passar |

## Known Issues

- O `python3-venv` desta máquina veio sem `ensurepip`, então `python3 -m venv` cria um
  ambiente sem `pip`. Contornado com `venv --without-pip` + `get-pip.py`. A correção
  definitiva é `sudo apt install python3-venv`, que precisa da senha do usuário.
- `rasterio` continua **não instalado** (dependência nativa GDAL). O sistema degrada para
  PNG/JPEG: a resolução espacial passa a ser informada à mão na interface ou por
  `--metros-por-pixel`. Instalar só se as cenas reais vierem em GeoTIFF.
- A convolução **genérica** continua `O(H·W·k²)`. Gaussiano e média já usam a forma
  separável. A mediana não é separável e segue `O(H·W·k²)` por natureza. O pipeline
  completo roda em ~730 ms numa cena de 440×440.
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
| D12 | Vermelho e NIR extraídos do **mesmo** produto GIBS, porque os realces de 8 bits diferem entre produtos | `data/raw/FONTES.md` |
| D13 | Resultado negativo em imagem real mantido como resultado; limiar **não** ajustado para fazê-lo passar | `docs/decisions/005-resolucao-espacial.md` |
| D14 | NDMI disponível mas **fora** do modo automático: ele mede água, não verde | `pdi/cor.py` |

## Graphify

| Campo | Valor |
|-------|-------|
| Estado | `READY` |
| Grafo | `graphify-out/graph.json` — 863 nós, 1531 arestas, 37 fontes, 100% AST |
| Consulta de aceite | `treinar_e_avaliar → dividir_espacialmente`, conferida em `modelo/classificador.py` L307 — o arquivo alterado por último |
| Baseline | `~/.local/state/graphify-baseline/aps-desmatamento-satelite/` |

Marcar `STALE` de novo após mudança relevante no código, até regenerar pelo procedimento do
`AGENTS.md` §17. Data do arquivo não comprova atualidade.
