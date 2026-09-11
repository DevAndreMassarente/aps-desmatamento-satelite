# Sentinela — detecção de desmatamento em imagens de satélite

Atividades Práticas Supervisionadas (APS) — 5º/6º semestre de Ciência da Computação — UNIP —
2026/2.

## Sobre

Aplicação em Python que detecta e quantifica áreas desmatadas em imagens de satélite usando
processamento digital de imagens. O sistema compara a mesma região em duas datas, segmenta a
perda de cobertura vegetal e prepara os dados resultantes para alimentar um modelo de visão
computacional.

**Todos os filtros são implementados pelo grupo**, com NumPy puro — nenhuma chamada a
`cv2`, `skimage` ou equivalente. É uma exigência explícita do enunciado
([decisão 001](docs/decisions/001-filtros-proprios.md)).

## Contexto acadêmico

| | |
|---|---|
| Disciplina orientadora | Processamento de Imagens e Visão Computacional |
| Tema | Aplicação de técnicas de PDI e visão computacional para resolver problemas de sustentabilidade ambiental |
| Documento oficial | [`docs/enunciado/`](docs/enunciado/) |
| Avaliação | 35% trabalho escrito · 35% programa · 30% apresentação |

## Objetivo

Detectar e quantificar perda de cobertura vegetal em imagens orbitais, produzindo:

1. máscara binária das áreas desmatadas;
2. quantificação em pixels e — havendo metadados geográficos — em hectares;
3. recortes rotulados e normalizados, prontos para treinar um modelo de visão computacional.

O processamento de imagens aqui é **preparação de dados**, conforme a redação do objetivo no
enunciado, e não um fim em si.

## Requisitos principais

- Filtros desenvolvidos pelo grupo, aplicados em imagens reais de satélite.
- Cobertura das cinco etapas nomeadas pelo enunciado: aquisição, manipulação, filtragem,
  segmentação e modelo de visão computacional.
- Rastreabilidade: [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) liga cada exigência do
  enunciado ao código e à evidência.

## Stack

| Camada | Ferramenta |
|--------|-----------|
| Linguagem | Python 3.12 |
| Núcleo de PDI | NumPy — **somente** |
| I/O de imagem | Pillow (PNG/JPEG), rasterio (GeoTIFF, opcional) |
| Modelo | scikit-learn |
| Interface | Streamlit |
| Gráficos | matplotlib |
| Testes | pytest |

## Estrutura

```text
src/sentinela/
├── pdi/              núcleo de processamento — só NumPy
│   ├── nucleo.py         convolução, borda, normalização, histograma
│   ├── cor.py            espaços de cor, NDVI, ExG, VARI
│   ├── filtros.py        gaussiano, média, mediana, Sobel, Prewitt, Laplaciano, nitidez
│   ├── limiar.py         Otsu, limiar adaptativo, histerese
│   ├── morfologia.py     erosão, dilatação, abertura, fechamento, preenchimento
│   └── segmentacao.py    componentes conexos, análise de regiões, mudança bi-temporal
├── dataio/           aquisição e persistência          (a implementar)
├── pipeline/         orquestração das etapas           (a implementar)
├── modelo/           features e classificador          (a implementar)
└── app/              interface Streamlit                (a implementar)

tests/                134 testes contra casos analíticos
docs/                 enunciado, especificação, requisitos, arquitetura, decisões, evidências
data/                 imagens (não versionadas — ver docs/decisions/002)
```

Detalhes em [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Pré-requisitos

- Python 3.10 ou superior
- `python3-venv` instalado no sistema

> No Ubuntu/WSL, se `python3 -m venv` reclamar de `ensurepip`:
> `sudo apt install python3-venv`

## Como executar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[app,modelo,dev]"
```

O núcleo de PDI já está utilizável:

```python
from sentinela.pdi import cor, filtros, limiar, morfologia, segmentacao

# índice de vegetação a partir de RGB + infravermelho
indice, metodo = cor.indice_vegetacao(imagem_rgb, banda_nir)

# suavizar antes de segmentar, para não gerar máscara esburacada
suave = filtros.gaussiano(cor.para_faixa_unitaria(indice), tamanho=5)

# limiar automático separando vegetação de solo exposto
vegetacao, valor_do_limiar = limiar.otsu_binarizar(suave)

# limpar a máscara
limpa = morfologia.fechamento(morfologia.abertura(vegetacao))

# comparar duas datas: 'perda' é a máscara de desmatamento
mudanca = segmentacao.mudanca_entre_mascaras(vegetacao_t1, vegetacao_t2)
```

A interface Streamlit e o pipeline de linha de comando ainda não estão implementados —
ver [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md).

## Como testar

```bash
pytest
```

Os filtros são validados contra **casos analíticos conhecidos**, não contra a saída de outra
biblioteca: convolução com kernel identidade devolve a imagem original, gaussiano preserva
região constante, Laplaciano anula rampa linear, Otsu cai entre os modos de um histograma
bimodal, abertura e fechamento são idempotentes, uma forma em "U" é rotulada como uma única
região.

## Documentação

| Documento | Conteúdo |
|-----------|----------|
| [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md) | Requisitos extraídos do enunciado, decisões técnicas, perguntas em aberto |
| [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) | Matriz de rastreabilidade — 50 requisitos |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Componentes, fluxo, decisões arquiteturais |
| [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) | Estado atual, próximos passos, bloqueios |
| [`docs/decisions/`](docs/decisions/) | Registros de decisão arquitetural |
| [`docs/enunciado/`](docs/enunciado/) | Documento oficial e transcrição |
| [`AGENTS.md`](AGENTS.md) | Regras do projeto para agentes de IA |

## Status

**Em desenvolvimento.** Bootstrap concluído.

| Etapa | Situação |
|-------|----------|
| Estrutura e documentação | Concluído |
| Núcleo de PDI (filtros próprios) | Implementado, 134 testes passando |
| Aquisição de imagens reais | Não iniciado |
| Pipeline de orquestração | Não iniciado |
| Interface Streamlit | Não iniciado |
| Modelo de visão computacional | Não iniciado — depende da pergunta Q5 |
| Trabalho escrito | Não iniciado |

Oito perguntas aguardam confirmação do professor — ver
[`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md), seção *Open Questions*.
