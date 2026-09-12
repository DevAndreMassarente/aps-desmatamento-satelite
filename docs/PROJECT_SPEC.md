# Project Specification — APS 2026/2

> Este documento **não substitui** o enunciado oficial
> (`docs/enunciado/ManualAPS-5oe6oCCI-PI-2026.pdf`). Em qualquer divergência, o PDF prevalece.

Legenda de confiabilidade usada ao longo do documento:

| Marca | Significado |
|-------|-------------|
| `CONFIRMED` | Está escrito no enunciado oficial |
| `INFERRED`  | Decisão técnica da equipe, derivada do enunciado |
| `UNKNOWN`   | Precisa de confirmação com o professor |

---

## Academic Context

| Campo | Valor | Fonte |
|-------|-------|-------|
| Instituição | Universidade Paulista (UNIP) | `CONFIRMED` — p.4 (site de entrega) |
| Curso | Ciência da Computação (CC) | `CONFIRMED` — p.1 |
| Semestre-alvo | 5º / 6º | `CONFIRMED` — p.1 |
| Período letivo | 2026/2 | `CONFIRMED` — p.1 |
| Disciplina orientadora | Processamento de Imagens e Visão Computacional | `CONFIRMED` — p.2 |
| Tamanho do grupo | Até 4 alunos | `CONFIRMED` — p.4, item III.4 |
| Integrantes | — | `UNKNOWN` |
| Professor supervisor | — | `UNKNOWN` |
| Datas (P1 / P2 / apresentação) | Seguem calendário escolar | `UNKNOWN` — p.5 |

---

## Theme

`CONFIRMED` — p.2:

> "APLICAÇÃO DE TÉCNICAS DE PROCESSAMENTO DIGITAL DE IMAGENS E VISÃO COMPUTACIONAL
> PARA RESOLVER PROBLEMAS DE SUSTENTABILIDADE AMBIENTAL"

### Problema escolhido pelo grupo

`INFERRED` (escolha da equipe dentro dos exemplos do enunciado — p.2, primeiro bullet:
"Tratamento de imagens de desmatamento via satélite"):

**Detecção e quantificação de áreas desmatadas em imagens de satélite.**

O sistema recebe recortes de imagens orbitais (Sentinel-2 / Landsat) de uma mesma região em
duas datas, aplica uma cadeia de processamento digital de imagens implementada pelo grupo e
produz:

1. uma **máscara binária** das áreas com perda de cobertura vegetal;
2. a **quantificação** dessas áreas (pixels e, quando houver metadados geográficos, hectares);
3. **recortes (patches) rotulados e normalizados** prontos para alimentar um modelo de visão
   computacional.

---

## Objective

`CONFIRMED` — p.2. O enunciado pede, literalmente:

> "Desenvolver uma aplicação computacional que utilize técnicas de processamento digital de
> imagens para resolver um problema real relacionado à sustentabilidade ambiental. O grupo
> deverá identificar um problema dentro do tema, propor uma solução baseada em processamento
> de imagens **para preparação dos dados, de modo que a posteriori, estes possam alimentar
> modelos de visão computacional**, e desenvolver uma aplicação para implementar essa solução."

Ponto de atenção que direciona toda a arquitetura: o PDI aqui é **preparação de dados**, não um
fim em si. A aplicação precisa terminar entregando dado pronto para o modelo, e não apenas
imagens filtradas na tela.

---

## Mandatory Requirements

Detalhamento com IDs rastreáveis em [`REQUIREMENTS.md`](./REQUIREMENTS.md).

### Parte I — Pesquisa e produção de conteúdo acadêmico (`CONFIRMED` — p.3/p.4)

Texto acadêmico com exatamente estes capítulos:

1. **Introdução** — a) Descrição do Problema; b) Contexto; c) Objetivos
2. **Referencial teórico** — descrição formal do problema computacional; conceitos de
   Aquisição, Manipulação, Filtragem, Segmentação e proposta teórica do modelo de visão
   computacional
3. **Proposta** — a) Processamento digital de imagens (filtros próprios); b) Modelagem
4. **Desenvolvimento** — a) como os métodos foram implantados; b) ferramentas; c) como os
   testes foram feitos; d) resultados obtidos
5. **Conclusão**
6. **Bibliografia**
7. **Apêndice** (código-fonte)
8. **Ficha de Atividades Práticas Supervisionadas**

### Parte II — Programa (`CONFIRMED` — p.4)

- Sistema que implementa as soluções propostas no item 3 da seção I.
- O enunciado avisa explicitamente que **nível de refinamento, funcionalidade, tratamento de
  erros, funções extras e complexidade da técnica escolhida têm impacto direto na nota**.

### Parte III — Apresentação (`CONFIRMED` — p.4)

- Sessão de 10 a 15 minutos em sala.
- Deve incluir: explicação do problema e contexto; demonstração da aplicação; discussão dos
  resultados.
- Grupo preparado para perguntas da turma e dos professores.

### Formatação do trabalho escrito (`CONFIRMED` — p.4, item III.5)

| Item | Exigência |
|------|-----------|
| Fonte | ARIAL 12 |
| Espaçamento | 1,5 |
| Margem direita | 2,5 cm |
| Margem esquerda | 2,5 cm |
| Papel | A4 |
| Norma | ABNT |

> Margens superior e inferior não são especificadas no enunciado → `UNKNOWN`; na ABNT
> (NBR 14724) o usual é 3 cm superior e 2 cm inferior.

### Entrega (`CONFIRMED` — p.4, item III.8)

- Postagem obrigatória da versão final em `http://trabalhosacademicos.unip.br/entrega/`.
- **A não postagem implica reprovação automática.**
- Entrega acompanhada da ficha padrão de APS, preenchida cronologicamente.

---

## Restrictions

| # | Restrição | Tipo | Fonte |
|---|-----------|------|-------|
| 1 | Os filtros **devem ser desenvolvidos pelo grupo** | `CONFIRMED` | p.3, item 3.a |
| 2 | Preferencialmente em linguagem **Python** | `CONFIRMED` | p.3, item 3.a |
| 3 | Filtros aplicados em **imagens reais** do problema escolhido | `CONFIRMED` | p.3, item 3.a |
| 4 | Resultado deve ser **apresentado e analisado** | `CONFIRMED` | p.3, item 3.a |
| 5 | Sugestão de usar Python para o sistema | `CONFIRMED` | p.2 |
| 6 | Grupo de até 4 alunos | `CONFIRMED` | p.4 |
| 7 | Apresentação entre 10 e 15 minutos | `CONFIRMED` | p.4 |

### Consequência técnica da restrição #1

`INFERRED` — a leitura da equipe é que "filtros desenvolvidos pelo grupo" **exclui** chamar
prontos de biblioteca (`cv2.GaussianBlur`, `skimage.filters.sobel`, `PIL.ImageFilter`) para o
núcleo de PDI. Portanto:

- **Permitido no núcleo de PDI:** `numpy` (álgebra de arrays — é base numérica, não biblioteca
  de processamento de imagens).
- **Proibido no núcleo de PDI:** `opencv-python`, `scikit-image`, filtros do `Pillow`,
  `scipy.ndimage`.
- `Pillow` fica restrito a **I/O** (abrir/salvar PNG/JPEG).
- Bibliotecas de modelagem (`scikit-learn`) são permitidas na etapa de **modelo**, que o
  enunciado não exige implementar do zero — ele pede "escolha de algoritmos de inteligência
  adequados" (p.3, item 3.b).

Registrado como decisão em [`decisions/001-filtros-proprios.md`](./decisions/001-filtros-proprios.md).

---

## Optional Features

`INFERRED` — não exigidas, mas o enunciado pontua "funções extras" (p.4, item II.2):

- Quantificação em hectares via metadados geográficos do GeoTIFF.
- Comparação bi-temporal (mesma área em duas datas) com mapa de diferença.
- Exportação de relatório com as métricas e imagens de cada etapa.
- Benchmark dos filtros próprios contra implementação de referência, para **validar corretude**
  (nunca para substituir a implementação própria).
- Histogramas e curvas de limiar interativos na interface.

---

## Deliverables

| # | Entregável | Onde | Status |
|---|-----------|------|--------|
| D1 | Trabalho escrito (ABNT, 8 capítulos) | `docs/trabalho-escrito/` + postagem no site UNIP | IN_PROGRESS — caps. 1 a 5 em rascunho completo; 22 referências pendentes; documento ABNT final não montado |
| D2 | Programa (aplicação Python) | `src/` | IN_PROGRESS — cinco etapas implementadas; quantificação em imagem real bloqueada pela resolução |
| D3 | Apresentação (10–15 min) | `docs/apresentacao/` | NOT_STARTED |
| D4 | Ficha de APS preenchida | `docs/` | NOT_STARTED — bloqueado por Q7 |
| D5 | Código-fonte como Apêndice do trabalho | `docs/trabalho-escrito/07-apendice.md`, gerado por `sentinela apendice` | IMPLEMENTED |

### Etapas intermediárias (`CONFIRMED` — p.5)

| Etapa | Conteúdo | Prazo |
|-------|----------|-------|
| Fase Intermediária I — Qualificação | Capítulo 1 + itens de **filtragem** dos capítulos 2 e 3. "Deve ser concluída antes do desenvolvimento prático." | Aula anterior à **P1** |
| Fase Intermediária II — Defesa | Finalização do plano de projeto + **protótipo** | Aula anterior à **P2** |
| Apresentação | Junto com a entrega da Fase Intermediária II | idem |

---

## Evaluation Criteria

`CONFIRMED` — p.5, seção IV:

| Componente | Peso |
|-----------|------|
| Trabalho escrito | 35% |
| Programa desenvolvido | 35% |
| Apresentação em classe | 30% |

Subdivisão da nota de apresentação (`CONFIRMED` — p.5):

| Critério | Peso dentro da apresentação |
|----------|------------------------------|
| Participação de todos os membros | 20% |
| Qualidade do projeto prático e teórico | 50% |
| Clareza e estrutura da apresentação | 30% |

O enunciado também cita (p.2) que o projeto será avaliado com base em **clareza da proposta,
inovação da solução e qualidade da implementação**.

---

## Documentation Requirements

Ver "Formatação do trabalho escrito" acima. Resumo operacional:
ARIAL 12 · espaçamento 1,5 · margens laterais 2,5 cm · A4 · ABNT · os 8 capítulos na ordem do
enunciado · ficha de APS anexada · código-fonte no apêndice.

---

## Technical Decisions

Todas `INFERRED` — escolhas da equipe, compatíveis com o enunciado.

| Área | Decisão | Justificativa |
|------|---------|---------------|
| Linguagem | Python 3.12 | Sugerida pelo enunciado (p.2, p.3) |
| Base numérica | `numpy` | Permite implementar convolução e morfologia do zero com desempenho aceitável, sem usar biblioteca de PDI |
| I/O de imagem | `Pillow` (PNG/JPEG), `rasterio` (GeoTIFF, opcional) | `rasterio` dá o metadado geográfico para converter pixels em hectares; o sistema degrada para PNG/JPEG se ele não estiver instalado |
| Interface | `streamlit` | A demonstração exige comparar antes/depois e mexer em limiares ao vivo; roda em `localhost`, sem internet na sala |
| Modelagem | `scikit-learn` | Classificador clássico sobre features de textura/índice — explicável pelo grupo em 15 min |
| Gráficos | `matplotlib` | Histogramas e curvas para o trabalho escrito |
| Testes | `pytest` | Validação dos filtros contra casos analíticos conhecidos |

Arquitetura detalhada em [`ARCHITECTURE.md`](./ARCHITECTURE.md).

---

## Open Questions

Itens a confirmar com o professor. **Nenhum destes deve ser resolvido por suposição.**

| # | Pergunta | Impacto | Status |
|---|----------|---------|--------|
| Q1 | **O peso da apresentação é 30% ou 35%?** A p.5 traz "Apresentação (35% da Nota Final)" no bloco "ETAPAS DO PROJETO", mas a seção IV logo abaixo lista 35% escrito + 35% programa + 30% apresentação (que soma 100%). | Planejamento de esforço | `UNKNOWN` |
| Q2 | O capítulo 2 (Referencial teórico) começa nos subitens "d)" e "e)" no PDF — a numeração parece continuar a do capítulo 1. Os subitens devem ser renumerados como a) e b)? | Estrutura do trabalho escrito | `UNKNOWN` |
| Q3 | Datas exatas de P1, P2 e da apresentação no calendário escolar. | Cronograma | `UNKNOWN` |
| Q4 | Margens superior e inferior do trabalho escrito (não especificadas). | Formatação | `UNKNOWN` |
| Q5 | O modelo de visão computacional precisa ser **treinado e funcional**, ou basta a "proposta teórica" (p.3, item 2.e.v) mais a modelagem (item 3.b)? | Escopo do programa — grande impacto | `UNKNOWN` |
| Q6 | Há restrição quanto ao uso de bibliotecas para a etapa de **modelo** (a restrição de implementação própria é explícita apenas para os filtros)? | Escopo do programa | `UNKNOWN` |
| Q7 | Nomes e RAs dos integrantes do grupo. | Ficha de APS, capa | `UNKNOWN` |
| Q8 | Existe política institucional sobre uso de IA neste trabalho? | Integridade acadêmica | `UNKNOWN` |

> **Q5 é a mais importante.** A leitura conservadora — e a que o projeto adota até resposta em
> contrário — é implementar o modelo de fato, porque o item II.1 (p.4) manda desenvolver um
> sistema "implementando as soluções propostas no item 3", e o item 3.b é justamente a
> modelagem.
