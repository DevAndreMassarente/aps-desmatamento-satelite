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
| 6 | Bibliografia | `BIBLIOGRAFIA.md` | 28 referências conferidas na fonte; nenhuma pendência |
| 7 | Apêndice — código-fonte | `07-apendice.md` | **Gerado automaticamente** por `sentinela apendice` |
| 8 | Ficha de APS | — | Bloqueado por Q7 (integrantes) |

## O que ainda falta

| Pendência | Bloqueio |
|-----------|----------|
| Revisão do texto pelo grupo | Nenhum — mas é obrigatória antes da entrega |
| 22 referências bibliográficas | Precisam ser localizadas e conferidas |
| Capítulo 8 — Ficha de APS | Q7: integrantes não definidos |
| Capa, folha de rosto, sumário | Q7 |
| Conferência do `.docx` gerado no Word | Q2 (numeração dos títulos), Q4 (margens), Q7 (capa) |

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

## Documento final (.docx)

```bash
python scripts/montar_documento.py                  # saidas/trabalho-escrito.docx
python scripts/montar_documento.py --sem-apendice   # versão leve, para revisão
```

Monta o trabalho a partir destes arquivos, **só com a biblioteca padrão do Python**. A saída
fica em `saidas/`, fora do Git: o que se versiona é o texto, e o documento se regera.

| Aspecto | Como sai | Origem |
|---------|----------|--------|
| Fonte e tamanho | Arial 12 | enunciado, p.4, III.5 |
| Espaçamento | 1,5, justificado | enunciado, p.4, III.5 |
| Papel | A4 | enunciado, p.4, III.5 |
| Margens laterais | 2,5 cm | enunciado, p.4, III.5 |
| Margens superior e inferior | 3 cm e 2 cm — **suposição até Q4** | ABNT NBR 14724, conferida no tutorial da Biblioteca da PUC-SP |
| Recuo de parágrafo | 1,25 cm | idem |
| Paginação | contada a partir da folha de rosto; número visível a partir da Introdução | idem |
| Capa e folha de rosto | a partir de `capa.json` — **marcadores até Q7** | — |
| Sumário | campo do Word — **atualizar ao abrir (F9)** | — |
| Referências | só a seção de referências de `BIBLIOGRAFIA.md` | — |
| Ficha de APS | página reservada | enunciado, p.4, III.6 |

O gerador lista, a cada execução, o que ainda está provisório. **Conferir o documento no Word
antes de postar** — os testes garantem estrutura e formatação de base, não a renderização,
porque não há Word nesta máquina.

Uma divergência fica para o professor (Q2): a NBR 14724 pede o número da seção sem pontuação
antes do título ("1 INTRODUÇÃO"), e os capítulos seguem a numeração do próprio enunciado
("1. Introdução", "1.a.").

## Regra de ouro

Toda afirmação sobre o programa neste texto precisa ser verificável no repositório. Se o
texto disser que algo funciona, tem que haver teste ou evidência. Se o resultado foi
negativo, o texto diz que foi negativo.
