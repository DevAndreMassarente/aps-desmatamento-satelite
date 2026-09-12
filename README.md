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
│   ├── cor.py            espaços de cor, NDVI, NDMI, ExG, VARI
│   ├── filtros.py        gaussiano (separável), média, mediana, Sobel, Prewitt, Laplaciano
│   ├── limiar.py         Otsu, limiar adaptativo, histerese
│   ├── morfologia.py     erosão, dilatação, abertura, fechamento, preenchimento
│   └── segmentacao.py    componentes conexos, análise de regiões, mudança bi-temporal
├── dataio/           aquisição e persistência
│   ├── imagem.py         leitura e escrita (Pillow) — única fronteira de I/O
│   ├── geo.py            resolução espacial via GeoTIFF (rasterio, opcional)
│   ├── sintetico.py      cena sintética de demonstração — nunca evidência
│   └── visual.py         sobreposição, mapa de mudança, falsa cor
├── pipeline/         orquestração das etapas
│   ├── deteccao.py       encadeia as cinco etapas e guarda os intermediários
│   └── amostras.py       recortes rotulados para o modelo
├── modelo/           etapa de visão computacional
│   ├── caracteristicas.py  15 descritores por recorte, todos vindos de pdi/
│   └── classificador.py    floresta aleatória + divisão espacial por blocos
├── app/principal.py  interface Streamlit
└── cli.py            linha de comando

tests/                279 testes contra casos analíticos
docs/                 enunciado, especificação, requisitos, arquitetura, decisões, evidências
data/                 imagens (não versionadas — ver docs/decisions/002)
```

Regra de dependência: `pdi/` não importa de nenhuma camada acima dele e trabalha só com
arrays NumPy. Detalhes em [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Pré-requisitos

- Python 3.10 ou superior
- `python3-venv` instalado no sistema

> No Ubuntu/WSL, se `python3 -m venv` reclamar de `ensurepip`:
> `sudo apt install python3-venv`

## Como executar

Instalação:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[app,modelo,dev]"
```

### Interface no navegador

```bash
sentinela app
```

Abre em `http://localhost:8501`. A interface parte de uma **cena sintética** de
demonstração — rotulada como tal na tela — e aceita upload de um par de imagens reais.
Mostra as cinco etapas lado a lado, a área desmatada em pixels e hectares, a tabela de
regiões e os recortes rotulados que alimentariam o modelo.

### Baixar imagens reais

```bash
python scripts/baixar_imagens.py --listar-regioes
python scripts/baixar_imagens.py --regiao sao-felix
```

Usa o NASA GIBS (MODIS/Terra), que **não exige credencial** — a aquisição é reproduzível
por qualquer integrante do grupo. O script mede ausência de dado, nuvem e bruma, e avisa
quando a cena não presta. Procedência registrada em
[`data/raw/FONTES.md`](data/raw/FONTES.md).

### Linha de comando

```bash
# demonstração com cena sintética, gravando as imagens de cada etapa
sentinela demo --saida docs/evidence/demo-sintetica

# incluindo o treino e a avaliação do classificador
sentinela demo --tamanho 200 --area 80 --modelo

# par de imagens reais
sentinela detectar --antes data/raw/2020.png --depois data/raw/2024.png \
                   --nir-antes data/raw/2020_nir.png --nir-depois data/raw/2024_nir.png \
                   --metros-por-pixel 10 --saida docs/evidence/results
```

A linha de comando existe porque evidência para o trabalho escrito precisa ser
reproduzível por comando: resultado que só aparece depois de alguém clicar numa tela não
é reproduzível.

### Sobre a métrica do modelo

Em cena sintética o classificador atinge F1 = 1,0. **Isso não valida o modelo** — a
separação entre as classes foi construída pelo gerador. O número prova que o encanamento
funciona; o próprio programa emite esse aviso junto da métrica.

A divisão entre treino e teste é feita **por blocos da imagem**, nunca sorteando
recortes: como a varredura usa passo menor que o lado, recortes vizinhos compartilham
pixels, e um sorteio individual mediria memorização
([decisão 004](docs/decisions/004-divisao-espacial.md)).

### Pela biblioteca

```python
from sentinela.dataio import carregar_par
from sentinela.pipeline import detectar_desmatamento

antes, depois = carregar_par("2020.png", "2024.png")
resultado = detectar_desmatamento(antes, depois, metros_por_pixel=10.0)

print(resultado.resumo())
```

### Quando o sistema se recusa a responder

Se a cena não apresenta duas classes separáveis — floresta intacta nas duas datas — o
limiar automático cortaria o ruído do dossel ao meio e produziria desmatamento onde não
houve. Nesse caso `resumo()` devolve `None` no lugar da área, e a interface exibe a
recusa em vez de um número. **Não é falha: é a resposta correta.**

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
| [`docs/trabalho-escrito/`](docs/trabalho-escrito/) | Rascunhos dos capítulos e pendências de bibliografia |
| [`docs/enunciado/`](docs/enunciado/) | Documento oficial e transcrição |
| [`AGENTS.md`](AGENTS.md) | Regras do projeto para agentes de IA |

## Status

**Em desenvolvimento.** O programa roda de ponta a ponta; o que falta não é código, são
imagens reais.

| Etapa | Situação |
|-------|----------|
| Estrutura e documentação | Concluído |
| Núcleo de PDI (filtros próprios) | Implementado, 279 testes passando |
| Aquisição e I/O de imagem | Implementado |
| Pipeline de orquestração | Implementado |
| Interface Streamlit e linha de comando | Implementado |
| Extração de amostras para o modelo | Implementado |
| Modelo de visão computacional | Implementado — floresta aleatória, 25 testes |
| Aplicação em imagens reais de satélite | Executado — MODIS/Terra, São Félix do Xingu (PA), 2002 e 2024 |
| **Quantificação validada em imagem real** | **Bloqueada pela resolução — exige 10 a 30 m/pixel** |
| Trabalho escrito | Capítulo 1 e seções de filtragem dos caps. 2 e 3 em rascunho |

### O resultado em imagem real foi uma recusa

O pipeline já rodou sobre um par bi-temporal real ([`docs/evidence/results/`](docs/evidence/results/)),
e **o sistema recusou-se a quantificar**: a 253 m/pixel quase todo pixel da frente de
desmatamento é mistura de floresta, pastagem e regeneração, o índice de vegetação sai
contínuo em vez de bimodal, e não existe limiar defensável. A recusa é o comportamento
correto — o diagnóstico completo, com as três hipóteses testadas, está na
[decisão 005](docs/decisions/005-resolucao-espacial.md).

Para quantificação validada é preciso Sentinel-2 (10 m) ou Landsat (30 m), que exigem
cadastro gratuito no Copernicus Data Space ou no USGS EarthExplorer.

A evidência de cena sintética ([`docs/evidence/demo-sintetica/`](docs/evidence/demo-sintetica/))
serve para demonstrar o programa e conferir a quantificação contra uma verdade de terreno
conhecida, mas **não sustenta requisito acadêmico**.

Oito perguntas aguardam confirmação do professor — ver
[`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md), seção *Open Questions*.
