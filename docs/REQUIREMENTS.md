# Requirements Matrix

Rastreabilidade entre o enunciado oficial, a implementação e a evidência.

**Fonte única:** `docs/enunciado/ManualAPS-5oe6oCCI-PI-2026.pdf`
(transcrição em `docs/enunciado/TRANSCRICAO.md`).

## Convenções

**Tipo:** `MUST` obrigatório · `SHOULD` forte impacto na nota · `MAY` opcional ·
`FORBIDDEN` proibido · `UNKNOWN` precisa de confirmação

**Status:** `NOT_STARTED` · `IN_PROGRESS` · `IMPLEMENTED` (código existe) ·
`VERIFIED` (código existe **e** há teste/evidência) · `BLOCKED` · `NOT_APPLICABLE`

> Regra: só marcar `VERIFIED` quando houver teste automatizado passando ou evidência real em
> `docs/evidence/`. Compilar/rodar não é verificação.

---

## A. Produto acadêmico — trabalho escrito (35% da nota)

| ID | Requisito | Tipo | Fonte | Implementação | Evidência/Teste | Status |
|----|-----------|------|-------|---------------|-----------------|--------|
| R001 | Cap. 1.a — Descrição do Problema: definição clara e relevância ambiental | MUST | PDF p.3, item 1.a | — | — | NOT_STARTED |
| R002 | Cap. 1.b — Contexto: importância da resolução, impacto ecológico, implicações sociais | MUST | PDF p.3, item 1.b | — | — | NOT_STARTED |
| R003 | Cap. 1.c — Objetivos principais da solução proposta | MUST | PDF p.3, item 1.c | — | — | NOT_STARTED |
| R004 | Cap. 2 — Descrição **formal** do problema computacional | MUST | PDF p.3, item 2.d | — | — | NOT_STARTED |
| R005 | Cap. 2 — Conceito de **Aquisição** | MUST | PDF p.3, item 2.e.i | `sentinela/dataio/` | `tests/test_dataio.py` | IN_PROGRESS |
| R006 | Cap. 2 — Conceito de **Manipulação das imagens** | MUST | PDF p.3, item 2.e.ii | `sentinela/pdi/cor.py` | `tests/test_cor.py` | IN_PROGRESS |
| R007 | Cap. 2 — Conceito de **Filtragem** | MUST | PDF p.3, item 2.e.iii | `sentinela/pdi/filtros.py` | `tests/test_filtros.py` | IN_PROGRESS |
| R008 | Cap. 2 — Conceito de **Segmentação** | MUST | PDF p.3, item 2.e.iv | `sentinela/pdi/{limiar,morfologia,segmentacao}.py` | `tests/test_segmentacao.py` | IN_PROGRESS |
| R009 | Cap. 2 — Proposta **teórica** do modelo adequado de visão computacional | MUST | PDF p.3, item 2.e.v | `docs/` | — | NOT_STARTED |
| R010 | Cap. 3.a — Proposta de PDI: escolha de filtros que apoiem a solução | MUST | PDF p.3, item 3.a | `sentinela/pipeline/` | — | NOT_STARTED |
| R011 | Cap. 3.b — Proposta de modelagem + escolha de algoritmos de inteligência | MUST | PDF p.3, item 3.b | `sentinela/modelo/` | — | NOT_STARTED |
| R012 | Cap. 4.a — Descrever como os métodos foram implantados | MUST | PDF p.3, item 4.a | — | — | NOT_STARTED |
| R013 | Cap. 4.b — Listar as ferramentas utilizadas | MUST | PDF p.3, item 4.b | — | — | NOT_STARTED |
| R014 | Cap. 4.c — Descrever como foram feitos os testes | MUST | PDF p.3, item 4.c | `tests/` | — | NOT_STARTED |
| R015 | Cap. 4.d — Mostrar os resultados obtidos | MUST | PDF p.3, item 4.d | `docs/evidence/results/` | — | NOT_STARTED |
| R016 | Cap. 5 — Conclusão | MUST | PDF p.3, item 5 | — | — | NOT_STARTED |
| R017 | Cap. 6 — Bibliografia (fontes reais, ABNT) | MUST | PDF p.3, item 6 | — | — | NOT_STARTED |
| R018 | Cap. 7 — Apêndice com o código-fonte do programa | MUST | PDF p.3, item 7 | gerado de `src/` | — | NOT_STARTED |
| R019 | Cap. 8 — Ficha de Atividades Práticas Supervisionadas | MUST | PDF p.4, item 8 | — | — | NOT_STARTED |

## B. Formatação e entrega

| ID | Requisito | Tipo | Fonte | Implementação | Evidência/Teste | Status |
|----|-----------|------|-------|---------------|-----------------|--------|
| R020 | Fonte ARIAL 12 | MUST | PDF p.4, item III.5 | — | — | NOT_STARTED |
| R021 | Espaçamento 1,5 | MUST | PDF p.4, item III.5 | — | — | NOT_STARTED |
| R022 | Margem direita 2,5 cm e esquerda 2,5 cm | MUST | PDF p.4, item III.5 | — | — | NOT_STARTED |
| R023 | Páginas em formato A4 | MUST | PDF p.4, item III.5 | — | — | NOT_STARTED |
| R024 | Seguir formato de trabalho acadêmico (normas ABNT) | MUST | PDF p.4, item III.5 | — | — | NOT_STARTED |
| R025 | Contemplar todos os tópicos do item I do enunciado | MUST | PDF p.4, item III.5 | R001–R019 | — | NOT_STARTED |
| R026 | Entregar junto com a ficha padrão de APS, cronologicamente preenchida | MUST | PDF p.4, item III.6 | — | — | NOT_STARTED |
| R027 | **Postar versão final em `trabalhosacademicos.unip.br/entrega/`** — a não postagem implica reprovação automática | MUST | PDF p.4, item III.8 | — | — | NOT_STARTED |
| R028 | Desenvolver o trabalho **em etapas** | MUST | PDF p.4, item III.7 | R040, R041 | — | IN_PROGRESS |

## C. Programa (35% da nota)

| ID | Requisito | Tipo | Fonte | Implementação | Evidência/Teste | Status |
|----|-----------|------|-------|---------------|-----------------|--------|
| R029 | Sistema que implementa as soluções propostas no item 3 da seção I | MUST | PDF p.4, item II.1 | `src/sentinela/` + `cli.py` | `tests/` — 214 testes | IN_PROGRESS |
| R030 | **Filtros desenvolvidos pelo próprio grupo** (não usar prontos de biblioteca) | MUST | PDF p.3, item 3.a | `sentinela/pdi/` | `tests/test_filtros.py`, `test_nucleo.py` — 154 testes | VERIFIED |
| R031 | Filtros preferencialmente em linguagem Python | SHOULD | PDF p.3, item 3.a | Python 3.12 | — | IMPLEMENTED |
| R032 | Filtros aplicados em **imagens reais** do problema escolhido | MUST | PDF p.3, item 3.a | `data/raw/` | `docs/evidence/results/` | NOT_STARTED |
| R033 | Resultado dos filtros apresentado **e analisado** | MUST | PDF p.3, item 3.a | `sentinela/app/principal.py` | `docs/evidence/demo-sintetica/` (sintética) | IN_PROGRESS |
| R034 | PDI usado como **preparação de dados** para alimentar modelo de visão computacional | MUST | PDF p.2 (Objetivo) | `sentinela/pipeline/amostras.py` | `tests/test_pipeline.py::TestAmostras` | IN_PROGRESS |
| R035 | Processo de modelagem + algoritmos de inteligência adequados para imagens | MUST | PDF p.3, item 3.b | `sentinela/modelo/` | — | NOT_STARTED |
| R036 | **Tratamento de erros** — citado como fator de impacto direto na nota | SHOULD | PDF p.4, item II.2 | `dataio/imagem.py`, `pipeline/deteccao.py` | `test_dataio.py`, `TestValidacaoDeEntrada` — 18 casos | VERIFIED |
| R037 | Nível de refinamento e funcionalidade do sistema | SHOULD | PDF p.4, item II.2 | `sentinela/app/`, `sentinela/cli.py` | `tests/test_app.py` | IN_PROGRESS |
| R038 | Funções extras implementadas | MAY | PDF p.4, item II.2 | — | — | NOT_STARTED |
| R039 | Complexidade da técnica escolhida | SHOULD | PDF p.4, item II.2 | `sentinela/modelo/` | — | NOT_STARTED |

## D. Etapas intermediárias

| ID | Requisito | Tipo | Fonte | Implementação | Evidência/Teste | Status |
|----|-----------|------|-------|---------------|-----------------|--------|
| R040 | Fase Intermediária I (Qualificação): Cap. 1 + itens de **filtragem** dos caps. 2 e 3 — concluída **antes** do desenvolvimento prático. Entrega na aula anterior à P1 | MUST | PDF p.5, item 1 | R001–R003, R007, R010 | — | NOT_STARTED |
| R041 | Fase Intermediária II (Defesa): finalização do plano de projeto + **protótipo**. Entrega na aula anterior à P2 | MUST | PDF p.5, item 2 | — | — | NOT_STARTED |

## E. Apresentação (30% da nota — ver Q1)

| ID | Requisito | Tipo | Fonte | Implementação | Evidência/Teste | Status |
|----|-----------|------|-------|---------------|-----------------|--------|
| R042 | Apresentar em sala, sessão de **10 a 15 minutos** | MUST | PDF p.4, item III.1 | — | — | NOT_STARTED |
| R043 | Apresentação inclui explicação do problema e contexto | MUST | PDF p.4, item III.2 | — | — | NOT_STARTED |
| R044 | Apresentação inclui **demonstração da aplicação** | MUST | PDF p.4, item III.2 | `sentinela/app/` | `tests/test_app.py` | IN_PROGRESS |
| R045 | Apresentação inclui discussão dos resultados obtidos | MUST | PDF p.4, item III.2 | — | — | NOT_STARTED |
| R046 | Grupo preparado para responder perguntas da turma e dos professores | MUST | PDF p.4, item III.3 | — | — | NOT_STARTED |
| R047 | **Participação de todos os membros** na apresentação (20% da nota de apresentação) | MUST | PDF p.5, item 3 | — | — | NOT_STARTED |
| R048 | Clareza e estrutura da apresentação (30% da nota de apresentação) | SHOULD | PDF p.5, item 3 | — | — | NOT_STARTED |
| R049 | Grupo composto de **até 4 alunos** | MUST | PDF p.4, item III.4 | — | — | NOT_STARTED |
| R050 | Demonstração do programa no seminário | MUST | PDF p.4, item III.7 | `sentinela/app/` | `tests/test_app.py` | IN_PROGRESS |

## F. Pendências de confirmação

| ID | Pergunta | Tipo | Fonte | Status |
|----|----------|------|-------|--------|
| Q1 | Peso da apresentação: 30% (seção IV) ou 35% (bloco ETAPAS)? | UNKNOWN | PDF p.5 | BLOCKED |
| Q2 | Subitens do Cap. 2 aparecem como "d)" e "e)" — renumerar para a) e b)? | UNKNOWN | PDF p.3 | BLOCKED |
| Q3 | Datas exatas de P1, P2 e apresentação | UNKNOWN | PDF p.5 | BLOCKED |
| Q4 | Margens superior e inferior do trabalho escrito | UNKNOWN | PDF p.4 | BLOCKED |
| Q5 | Modelo de visão computacional precisa ser treinado/funcional ou basta proposta teórica? | UNKNOWN | PDF p.3/p.4 | BLOCKED |
| Q6 | Há restrição de bibliotecas para a etapa de modelo? | UNKNOWN | PDF p.3 | BLOCKED |
| Q7 | Integrantes do grupo (nomes e RAs) | UNKNOWN | — | BLOCKED |
| Q8 | Política institucional sobre uso de IA | UNKNOWN | — | BLOCKED |

---

## Resumo

| Status | Qtd |
|--------|-----|
| NOT_STARTED | 36 |
| IN_PROGRESS | 11 |
| IMPLEMENTED | 1 |
| VERIFIED | 2 |
| BLOCKED (perguntas) | 8 |

> R030 está `VERIFIED` quanto à **implementação própria** dos filtros, comprovada por 214
> testes contra casos analíticos. A aplicação em **imagens reais** (R032) é requisito
> separado e continua `NOT_STARTED` — é hoje o bloqueio mais relevante do programa.

> R033, R034, R037, R044 e R050 estão `IN_PROGRESS`, não `VERIFIED`: o código existe e
> tem teste, mas a evidência disponível vem de **cena sintética**
> (`docs/evidence/demo-sintetica/`), que por `AGENTS.md` §11 não pode sustentar requisito
> acadêmico. Eles só avançam depois de R032.

**Total de requisitos rastreados:** 50 (R001–R050) + 8 perguntas em aberto.
