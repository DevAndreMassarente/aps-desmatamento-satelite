# Trabalho escrito — 35% da nota

Rascunhos versionados dos capítulos. O documento final vai para o Word/PDF com a
formatação ABNT exigida; aqui ficam o texto e a rastreabilidade.

> ## ⚠️ Leia antes de usar
>
> **Este texto é um rascunho de trabalho, não um documento pronto para entrega.**
>
> 1. **O grupo precisa ler, revisar e assumir cada parágrafo.** O enunciado cobra
>    apresentação oral com arguição: o que ninguém do grupo consegue explicar tem que
>    sair do texto. `AGENTS.md` §12.
> 2. **Nenhuma referência bibliográfica foi inventada.** Onde falta fonte, há um marcador
>    explícito `[NEEDS_SOURCE: ...]` dizendo o que buscar e onde. Esses marcadores
>    **precisam ser resolvidos ou o trecho precisa ser removido** antes da entrega.
>    Entregar com marcador é melhor que entregar com citação falsa — mas as duas coisas
>    são inaceitáveis na versão final.
> 3. **Nenhum número foi estimado.** Toda métrica citada é reproduzível a partir do
>    repositório, ou está marcada como pendente.

## Estrutura exigida pelo enunciado (p.3–4)

| Cap. | Conteúdo | Arquivo | Estado |
|------|----------|---------|--------|
| 1 | Introdução: a) problema, b) contexto, c) objetivos | `01-introducao.md` | Rascunho completo |
| 2 | Referencial teórico: d) descrição formal, e) conceitos (aquisição, manipulação, filtragem, segmentação, modelo) | `02-referencial-teorico.md` | Rascunho completo |
| 3 | Proposta: a) PDI, b) modelagem | `03-proposta.md` | Rascunho completo |
| 4 | Desenvolvimento: a) implantação, b) ferramentas, c) testes, d) resultados | `04-desenvolvimento.md` | Rascunho completo |
| 5 | Conclusão | `05-conclusao.md` | Rascunho completo |
| 6 | Bibliografia | `BIBLIOGRAFIA.md` | Lista de pendências |
| 7 | Apêndice — código-fonte | `07-apendice.md` | **Gerado automaticamente** por `sentinela apendice` |
| 8 | Ficha de APS | — | Bloqueado por Q7 (integrantes) |

## O que ainda falta

| Pendência | Bloqueio |
|-----------|----------|
| Revisão do texto pelo grupo | Nenhum — mas é obrigatória antes da entrega |
| 22 referências bibliográficas | Precisam ser localizadas e conferidas |
| Capítulo 8 — Ficha de APS | Q7: integrantes não definidos |
| Capa, folha de rosto, sumário | Q7 |
| Formatação ABNT no documento final | Q4: margens superior e inferior desconhecidas |

## Fase Intermediária I — Qualificação (R040)

O enunciado (p.5) manda entregar, na aula anterior à P1, o **Capítulo 1 mais os itens de
filtragem dos Capítulos 2 e 3**, antes do desenvolvimento prático pesado.

O que essa fase exige já está escrito:

- Capítulo 1 inteiro — `01-introducao.md`
- Capítulo 2, item e.iii (Filtragem) — `02-referencial-teorico.md`
- Capítulo 3, item a (PDI e escolha de filtros) — `03-proposta.md`

## Formatação exigida (p.4, item III.5)

| Regra | Valor | Requisito |
|-------|-------|-----------|
| Fonte | Arial 12 | R020 |
| Espaçamento | 1,5 | R021 |
| Margens laterais | 2,5 cm de cada lado | R022 |
| Papel | A4 | R023 |
| Normas | ABNT | R024 |

Margens superior e inferior não constam do enunciado — é a pergunta **Q4**, ainda sem
resposta do professor.

## Apêndice de código-fonte

```bash
sentinela apendice
```

Regenera `07-apendice.md` a partir de `src/`, na ordem de leitura — o núcleo de PDI antes
de quem o consome. **Não editar à mão.** Um apêndice copiado diverge do código na primeira
correção feita depois de copiar, e essa divergência é o tipo de coisa que uma banca
encontra. Rodar de novo antes de fechar o documento final.

## Regra de ouro

Toda afirmação sobre o programa neste texto precisa ser verificável no repositório. Se o
texto disser que algo funciona, tem que haver teste ou evidência. Se o resultado foi
negativo, o texto diz que foi negativo.
