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
| R001 | Cap. 1.a — Descrição do Problema: definição clara e relevância ambiental | MUST | PDF p.3, item 1.a | `docs/trabalho-escrito/01-introducao.md` §1.a | rascunho completo | IN_PROGRESS |
| R002 | Cap. 1.b — Contexto: importância da resolução, impacto ecológico, implicações sociais | MUST | PDF p.3, item 1.b | `docs/trabalho-escrito/01-introducao.md` §1.b | rascunho completo | IN_PROGRESS |
| R003 | Cap. 1.c — Objetivos principais da solução proposta | MUST | PDF p.3, item 1.c | `docs/trabalho-escrito/01-introducao.md` §1.c | rascunho completo | IN_PROGRESS |
| R004 | Cap. 2 — Descrição **formal** do problema computacional | MUST | PDF p.3, item 2.d | `docs/trabalho-escrito/02-referencial-teorico.md` §2.d | rascunho completo | IN_PROGRESS |
| R005 | Cap. 2 — Conceito de **Aquisição** | MUST | PDF p.3, item 2.e.i | `sentinela/dataio/` | `tests/test_dataio.py` | IN_PROGRESS |
| R006 | Cap. 2 — Conceito de **Manipulação das imagens** | MUST | PDF p.3, item 2.e.ii | `sentinela/pdi/cor.py` | `tests/test_cor.py` | IN_PROGRESS |
| R007 | Cap. 2 — Conceito de **Filtragem** | MUST | PDF p.3, item 2.e.iii | `pdi/filtros.py` + `02-referencial-teorico.md` §2.e.iii | `tests/test_filtros.py` — seção escrita | IN_PROGRESS |
| R008 | Cap. 2 — Conceito de **Segmentação** | MUST | PDF p.3, item 2.e.iv | `sentinela/pdi/{limiar,morfologia,segmentacao}.py` | `tests/test_segmentacao.py` | IN_PROGRESS |
| R009 | Cap. 2 — Proposta **teórica** do modelo adequado de visão computacional | MUST | PDF p.3, item 2.e.v | `docs/` | — | NOT_STARTED |
| R010 | Cap. 3.a — Proposta de PDI: escolha de filtros que apoiem a solução | MUST | PDF p.3, item 3.a | `docs/trabalho-escrito/03-proposta.md` §3.a | `docs/evidence/results/` | IN_PROGRESS |
| R011 | Cap. 3.b — Proposta de modelagem + escolha de algoritmos de inteligência | MUST | PDF p.3, item 3.b | `sentinela/modelo/` | `docs/decisions/004-divisao-espacial.md` | IN_PROGRESS |
| R012 | Cap. 4.a — Descrever como os métodos foram implantados | MUST | PDF p.3, item 4.a | `docs/trabalho-escrito/04-desenvolvimento.md` §4.a | rascunho completo | IN_PROGRESS |
| R013 | Cap. 4.b — Listar as ferramentas utilizadas | MUST | PDF p.3, item 4.b | `docs/trabalho-escrito/04-desenvolvimento.md` §4.b | versões conferidas no ambiente | IN_PROGRESS |
| R014 | Cap. 4.c — Descrever como foram feitos os testes | MUST | PDF p.3, item 4.c | `docs/trabalho-escrito/04-desenvolvimento.md` §4.c | `tests/` — 301 testes | IN_PROGRESS |
| R015 | Cap. 4.d — Mostrar os resultados obtidos | MUST | PDF p.3, item 4.d | `docs/trabalho-escrito/04-desenvolvimento.md` §4.d | `docs/evidence/` | IN_PROGRESS |
| R016 | Cap. 5 — Conclusão | MUST | PDF p.3, item 5 | `docs/trabalho-escrito/05-conclusao.md` | rascunho completo | IN_PROGRESS |
| R017 | Cap. 6 — Bibliografia (fontes reais, ABNT) | MUST | PDF p.3, item 6 | `docs/trabalho-escrito/BIBLIOGRAFIA.md` | 13 pendências mapeadas, nenhuma inventada | IN_PROGRESS |
| R018 | Cap. 7 — Apêndice com o código-fonte do programa | MUST | PDF p.3, item 7 | `sentinela apendice` → `07-apendice.md` | `tests/test_cli.py` | IMPLEMENTED |
| R019 | Cap. 8 — Ficha de Atividades Práticas Supervisionadas | MUST | PDF p.4, item 8 | — | — | NOT_STARTED |

## B. Formatação e entrega

| ID | Requisito | Tipo | Fonte | Implementação | Evidência/Teste | Status |
|----|-----------|------|-------|---------------|-----------------|--------|
| R020 | Fonte ARIAL 12 | MUST | PDF p.4, item III.5 | — | — | NOT_STARTED |
| R021 | Espaçamento 1,5 | MUST | PDF p.4, item III.5 | — | — | NOT_STARTED |
| R022 | Margem direita 2,5 cm e esquerda 2,5 cm | MUST | PDF p.4, item III.5 | — | — | NOT_STARTED |
| R023 | Páginas em formato A4 | MUST | PDF p.4, item III.5 | — | — | NOT_STARTED |
| R024 | Seguir formato de trabalho acadêmico (normas ABNT) | MUST | PDF p.4, item III.5 | — | — | NOT_STARTED |
| R025 | Contemplar todos os tópicos do item I do enunciado | MUST | PDF p.4, item III.5 | `docs/trabalho-escrito/` — caps. 1 a 5 e 7 | `docs/trabalho-escrito/README.md` | IN_PROGRESS |
| R026 | Entregar junto com a ficha padrão de APS, cronologicamente preenchida | MUST | PDF p.4, item III.6 | — | — | NOT_STARTED |
| R027 | **Postar versão final em `trabalhosacademicos.unip.br/entrega/`** — a não postagem implica reprovação automática | MUST | PDF p.4, item III.8 | — | — | NOT_STARTED |
| R028 | Desenvolver o trabalho **em etapas** | MUST | PDF p.4, item III.7 | R040, R041 | — | IN_PROGRESS |

## C. Programa (35% da nota)

| ID | Requisito | Tipo | Fonte | Implementação | Evidência/Teste | Status |
|----|-----------|------|-------|---------------|-----------------|--------|
| R029 | Sistema que implementa as soluções propostas no item 3 da seção I | MUST | PDF p.4, item II.1 | `src/sentinela/` + `cli.py` + `scripts/` | `tests/` — 301 testes | IN_PROGRESS |
| R030 | **Filtros desenvolvidos pelo próprio grupo** (não usar prontos de biblioteca) | MUST | PDF p.3, item 3.a | `sentinela/pdi/` | `tests/test_filtros.py`, `test_nucleo.py` — 154 testes | VERIFIED |
| R031 | Filtros preferencialmente em linguagem Python | SHOULD | PDF p.3, item 3.a | Python 3.12 | — | IMPLEMENTED |
| R032 | Filtros aplicados em **imagens reais** do problema escolhido | MUST | PDF p.3, item 3.a | `scripts/baixar_imagens.py` | `docs/evidence/results/` — MODIS real, 2002 e 2024 | IMPLEMENTED |
| R033 | Resultado dos filtros apresentado **e analisado** | MUST | PDF p.3, item 3.a | `sentinela/app/principal.py` | `docs/evidence/results/README.md` — análise da recusa | IN_PROGRESS |
| R034 | PDI usado como **preparação de dados** para alimentar modelo de visão computacional | MUST | PDF p.2 (Objetivo) | `pipeline/amostras.py` → `modelo/` | `tests/test_pipeline.py`, `test_modelo.py` | IN_PROGRESS |
| R035 | Processo de modelagem + algoritmos de inteligência adequados para imagens | MUST | PDF p.3, item 3.b | `modelo/caracteristicas.py`, `modelo/classificador.py` | `tests/test_modelo.py` — 25 testes | IN_PROGRESS |
| R036 | **Tratamento de erros** — citado como fator de impacto direto na nota | SHOULD | PDF p.4, item II.2 | `dataio/imagem.py`, `pipeline/deteccao.py` | `test_dataio.py`, `TestValidacaoDeEntrada` — 18 casos | VERIFIED |
| R037 | Nível de refinamento e funcionalidade do sistema | SHOULD | PDF p.4, item II.2 | `sentinela/app/`, `sentinela/cli.py` | `tests/test_app.py` | IN_PROGRESS |
| R038 | Funções extras implementadas | MAY | PDF p.4, item II.2 | — | — | NOT_STARTED |
| R039 | Complexidade da técnica escolhida | SHOULD | PDF p.4, item II.2 | floresta aleatória + divisão espacial por blocos | `docs/decisions/004-divisao-espacial.md` | IN_PROGRESS |

## D. Etapas intermediárias

| ID | Requisito | Tipo | Fonte | Implementação | Evidência/Teste | Status |
|----|-----------|------|-------|---------------|-----------------|--------|
| R040 | Fase Intermediária I (Qualificação): Cap. 1 + itens de **filtragem** dos caps. 2 e 3 — concluída **antes** do desenvolvimento prático. Entrega na aula anterior à P1 | MUST | PDF p.5, item 1 | Cap. 1 + filtragem dos caps. 2 e 3 | `docs/trabalho-escrito/` | IN_PROGRESS |
| R041 | Fase Intermediária II (Defesa): finalização do plano de projeto + **protótipo**. Entrega na aula anterior à P2 | MUST | PDF p.5, item 2 | — | — | NOT_STARTED |

## E. Apresentação (30% da nota — ver Q1)

| ID | Requisito | Tipo | Fonte | Implementação | Evidência/Teste | Status |
|----|-----------|------|-------|---------------|-----------------|--------|
| R042 | Apresentar em sala, sessão de **10 a 15 minutos** | MUST | PDF p.4, item III.1 | `docs/apresentacao/ROTEIRO.md` — 13 min em 6 blocos | ensaio cronometrado pendente | IN_PROGRESS |
| R043 | Apresentação inclui explicação do problema e contexto | MUST | PDF p.4, item III.2 | `ROTEIRO.md` blocos 1–3 | `figuras/comparativo-real.png` | IN_PROGRESS |
| R044 | Apresentação inclui **demonstração da aplicação** | MUST | PDF p.4, item III.2 | `sentinela/app/` + `ROTEIRO.md` bloco 4 | `tests/test_app.py`, `docs/evidence/screenshots/` | IN_PROGRESS |
| R045 | Apresentação inclui discussão dos resultados obtidos | MUST | PDF p.4, item III.2 | `ROTEIRO.md` blocos 5–6 | `figuras/histogramas-ndvi-nbr.png` + tabela | IN_PROGRESS |
| R046 | Grupo preparado para responder perguntas da turma e dos professores | MUST | PDF p.4, item III.3 | `ROTEIRO.md` — 14 perguntas prováveis com resposta e local no código | depende do grupo | IN_PROGRESS |
| R047 | **Participação de todos os membros** na apresentação (20% da nota de apresentação) | MUST | PDF p.5, item 3 | — | — | NOT_STARTED |
| R048 | Clareza e estrutura da apresentação (30% da nota de apresentação) | SHOULD | PDF p.5, item 3 | `ROTEIRO.md` — ordem fixa, tempos por bloco, checklist | ensaio pendente | IN_PROGRESS |
| R049 | Grupo composto de **até 4 alunos** | MUST | PDF p.4, item III.4 | — | — | NOT_STARTED |
| R050 | Demonstração do programa no seminário | MUST | PDF p.4, item III.7 | `sentinela/app/` + plano B `sentinela demo` | `docs/evidence/screenshots/` — 4 telas | IN_PROGRESS |

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
| NOT_STARTED | 13 |
| IN_PROGRESS | 32 |
| IMPLEMENTED | 3 |
| VERIFIED | 2 |
| BLOCKED (perguntas) | 8 |

> **Os Capítulos 1 a 5 e o 7 têm rascunho.** Faltam as seções 2.e.i, 2.e.ii, 2.e.iv,
> 2.e.v e 3.b — sem bloqueio, o conteúdo existe no repositório. O Capítulo 8 depende
> de Q7.

> **Fase Intermediária I (R040) tem rascunho completo.** O enunciado exige, na aula
> anterior à P1, o Capítulo 1 mais os itens de **filtragem** dos Capítulos 2 e 3. Os três
> estão escritos em `docs/trabalho-escrito/`. Segue `IN_PROGRESS` porque o grupo precisa
> revisar e assumir o texto, e porque 13 referências bibliográficas continuam pendentes —
> **nenhuma foi inventada**, todas estão marcadas.

> **R032 está `IMPLEMENTED`, não `VERIFIED`.** Os filtros do grupo foram aplicados a
> imagens reais e a evidência está em `docs/evidence/results/`. Mas o resultado foi uma
> **recusa**: a 253 m/pixel o índice não é bimodal. Quantificação validada depende de
> imagem de 10 a 30 m — `docs/decisions/005-resolucao-espacial.md`.

> R030 está `VERIFIED` quanto à **implementação própria** dos filtros, comprovada por 301
> testes contra casos analíticos.

> **Q5 continua em aberto.** O projeto segue a leitura conservadora do `AGENTS.md` §14: o
> modelo foi implementado de fato.

**Total de requisitos rastreados:** 50 (R001–R050) + 8 perguntas em aberto.
