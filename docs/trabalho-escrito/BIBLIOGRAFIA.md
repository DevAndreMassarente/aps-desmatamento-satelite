# 6. Bibliografia — pendências

> **Nenhuma referência foi inventada.** Esta lista registra o que **precisa ser localizado
> e conferido** antes da entrega. `AGENTS.md` §12 e `AGENTS.md` global §42: não inventar
> autor, obra, DOI, página, URL ou citação.

## Como usar esta lista

1. Localizar a fonte real.
2. Ler o trecho que sustenta a afirmação — não citar por título.
3. Preencher a referência em ABNT, com data de acesso quando for eletrônica.
4. Substituir o marcador `[NEEDS_SOURCE: ...]` correspondente no capítulo.

**Se a fonte não for encontrada, a afirmação sai do texto.** Afirmação sem fonte não vira
afirmação com fonte genérica.

## Pendências por capítulo

### Capítulo 1 — Introdução

| # | O que precisa de fonte | Onde buscar | Estado |
|---|------------------------|-------------|--------|
| B1 | Área desmatada na Amazônia Legal — taxa anual e acumulado | INPE/PRODES, TerraBrasilis | `NEEDS_SOURCE` |
| B2 | Relação entre desmatamento e emissão de gases de efeito estufa no Brasil | Inventário nacional de emissões / SEEG | `NEEDS_SOURCE` |
| B3 | Conflitos fundiários associados a frentes de desmatamento | Entidades que compilam esses dados — conferir metodologia | `NEEDS_SOURCE` |

### Capítulo 2 — Referencial teórico

| # | O que precisa de fonte | Onde buscar | Estado |
|---|------------------------|-------------|--------|
| B4 | Método de limiarização de Otsu — definição e a métrica de separabilidade η | Artigo original | `NEEDS_SOURCE` |
| B5 | Tamanho de efeito padronizado — definição e interpretação de magnitude | Literatura de estatística | `NEEDS_SOURCE` |
| B6 | Operadores clássicos de PDI: convolução, Sobel, Prewitt, Laplaciano, mediana | Livro-texto consolidado de PDI | `NEEDS_SOURCE` |
| B7 | Proposição original dos operadores de Sobel e de Prewitt | Verificar acessibilidade; se não houver, citar pelo livro-texto e dizer isso | `NEEDS_SOURCE` |
| B8 | NDVI — definição e faixa de valores típicos por cobertura | Literatura de sensoriamento remoto | `NEEDS_SOURCE` |
| B9 | NDMI — definição e aplicação a umidade de dossel | Literatura de sensoriamento remoto | `NEEDS_SOURCE` |
| B10 | Problema do pixel misto e o efeito da resolução espacial | Literatura de sensoriamento remoto | `NEEDS_SOURCE` |

### Capítulo 3 — Proposta

| # | O que precisa de fonte | Onde buscar | Estado |
|---|------------------------|-------------|--------|
| B11 | Metodologia do PRODES e a justificativa da escolha de sensor e resolução | INPE — documentação metodológica | `NEEDS_SOURCE` |
| B12 | Validação cruzada espacial e autocorrelação em dados geoespaciais | Literatura de aprendizado sobre dados espaciais | `NEEDS_SOURCE` |

### Fontes de dados — estas já estão confirmadas

| # | Fonte | Uso | Estado |
|---|-------|-----|--------|
| B13 | NASA GIBS — MODIS/Terra Corrected Reflectance | Imagens do par bi-temporal | `SOURCE_CONFIRMED` — URLs exatas em `data/raw/sao-felix_manifesto.json` |

## Ferramentas a declarar no Capítulo 4.b

Sem necessidade de fonte bibliográfica, mas com **versão** a registrar: Python, NumPy,
Pillow, scikit-learn, Streamlit, Matplotlib e pytest. As versões exatas estão no ambiente
do projeto.
