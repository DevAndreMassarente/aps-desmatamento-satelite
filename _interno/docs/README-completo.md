# Sentinela — detecção de desmatamento em imagens de satélite

Atividades Práticas Supervisionadas (APS) — 5º/6º semestre de Ciência da Computação — UNIP —
2026/2.

## Sobre

Aplicação em Python que detecta e quantifica áreas desmatadas em imagens de satélite usando
processamento digital de imagens. O sistema compara a mesma região em duas datas, segmenta a
perda de cobertura vegetal e prepara os dados resultantes para alimentar um modelo de visão
computacional.

**Todos os filtros são implementados pelo grupo**, com NumPy puro — nenhuma chamada a
`cv2`, `skimage` ou equivalente. É uma exigência explícita do enunciado (p. 3, item 3.a),
e o raciocínio está no capítulo 3.a do trabalho escrito.

## Contexto acadêmico

| | |
|---|---|
| Disciplina orientadora | Processamento de Imagens e Visão Computacional |
| Tema | Aplicação de técnicas de PDI e visão computacional para resolver problemas de sustentabilidade ambiental |
| Documento oficial | [`_interno/docs/enunciado/`](_interno/docs/enunciado/) |
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
- Rastreabilidade: [`_interno/docs/REQUIREMENTS.md`](_interno/docs/REQUIREMENTS.md) liga cada exigência do
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
│   ├── cor.py            espaços de cor, NDVI, NDMI, NBR, ExG, VARI
│   ├── filtros.py        gaussiano e média (separáveis), mediana, Sobel, Prewitt, Laplaciano
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
└── cli.py            linha de comando (app, detectar, demo, apendice)

tests/                363 testes automatizados

entrega/              O QUE SE ENTREGA — tudo gerado por comando
├── trabalho-escrito.docx            capítulos 1 a 8, formatados como o enunciado exige
├── apresentacao-qualificacao.pptx   Fase Intermediária I — cap. 1 e a filtragem dos caps. 2 e 3
├── falas-qualificacao.docx          as falas dessa apresentação, para imprimir
├── apresentacao-defesa.pptx         Fase Intermediária II — protótipo e resultados
└── falas-defesa.docx                as falas da defesa, para imprimir

docs/
├── enunciado/        documento oficial em PDF e a transcrição
├── trabalho-escrito/ os capítulos em Markdown que geram o DOCX
├── apresentacao/     o roteiro das falas e as figuras usadas nos slides
└── resultados/       evidências: saídas do programa sobre imagem real e sintética

data/                 imagens de satélite — não versionadas, ver `_interno/data/raw/FONTES.md`
scripts/              aquisição de imagens, figuras, capturas de tela e os geradores da entrega
```

Regra de dependência: `pdi/` não importa de nenhuma camada acima dele e trabalha só com
arrays NumPy.

> O repositório guarda só o que é entregue e o que produz o que é entregue. A documentação
> de processo — matriz de requisitos, registros de decisão, memória de trabalho — fica na
> máquina de quem desenvolve e está no `.gitignore`.

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
python _interno/scripts/baixar_imagens.py --listar-regioes
python _interno/scripts/baixar_imagens.py --regiao sao-felix
```

Usa o NASA GIBS (MODIS/Terra), que **não exige credencial** — a aquisição é reproduzível
por qualquer integrante do grupo. O script mede ausência de dado, nuvem e bruma, e avisa
quando a cena não presta. Procedência registrada em
[`_interno/data/raw/FONTES.md`](_interno/data/raw/FONTES.md).

### Regerar os três arquivos da entrega

Os arquivos em `entrega/` estão versionados, mas nenhum deles é editado à mão: todos saem
de comando, a partir do texto e das imagens do repositório.

```bash
# 1. as figuras, a partir das imagens de satélite em _interno/data/raw/
python _interno/scripts/gerar_figuras.py

# 2. o apêndice de código-fonte do trabalho escrito
sentinela apendice

# 3. o trabalho escrito — Arial 12, espaçamento 1,5, A4, margens de 2,5 cm
python _interno/scripts/montar_documento.py

# 4. as falas impressas das duas apresentações
python _interno/scripts/montar_documento.py --avulso _interno/docs/apresentacao/FALAS-QUALIFICACAO.md \
                                   --saida entrega/fase-1/falas-qualificacao.docx
python _interno/scripts/montar_documento.py --avulso _interno/docs/apresentacao/FALAS-DEFESA.md \
                                   --saida entrega/falas-defesa.docx

# 5. os slides (precisa do pptxgenjs: npm install pptxgenjs)
node _interno/scripts/montar_apresentacao.mjs              # as duas fases
node _interno/scripts/montar_apresentacao.mjs qualificacao # só a de hoje
```

Ao abrir o `.docx` no Word, aceitar a atualização do sumário (ou apertar F9 sobre ele). O
gerador imprime o que ainda é provisório no documento — hoje, as margens superior e inferior,
que o enunciado não especifica, e a página reservada para a ficha de APS.

### Linha de comando

```bash
# demonstração com cena sintética, gravando as imagens de cada etapa
sentinela demo --saida _interno/docs/resultados/cena-sintetica

# incluindo o treino e a avaliação do classificador
sentinela demo --tamanho 200 --area 80 --modelo

# par de imagens reais
sentinela detectar --antes _interno/data/raw/2020.png --depois _interno/data/raw/2024.png \
                   --nir-antes _interno/data/raw/2020_nir.png --nir-depois _interno/data/raw/2024_nir.png \
                   --metros-por-pixel 10 --saida _interno/docs/resultados/imagem-real
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
pixels, e um sorteio individual mediria memorização.

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
| [`entrega/trabalho-escrito.docx`](entrega/trabalho-escrito.docx) | **O trabalho escrito.** Arial 12, espaçamento 1,5, A4, margens de 2,5 cm, capítulos 1 a 8 |
| [`entrega/fase-1/apresentacao-qualificacao.pptx`](entrega/fase-1/apresentacao-qualificacao.pptx) | **Slides da Fase Intermediária I.** 16 slides; as falas estão nas notas do apresentador |
| [`entrega/fase-1/falas-qualificacao.docx`](entrega/fase-1/falas-qualificacao.docx) | **As falas da qualificação**, divididas por integrante, com checklist e perguntas prováveis |
| [`entrega/apresentacao-defesa.pptx`](entrega/apresentacao-defesa.pptx) | **Slides da Fase Intermediária II** — protótipo, demonstração e resultados |
| [`entrega/falas-defesa.docx`](entrega/falas-defesa.docx) | **As falas da defesa**, no mesmo formato |
| [`_interno/docs/trabalho-escrito/`](_interno/docs/trabalho-escrito/) | Os capítulos em Markdown que geram o DOCX, e a bibliografia conferida |
| [`_interno/docs/apresentacao/`](_interno/docs/apresentacao/) | A fonte das falas das duas fases, e o que **não** dizer na banca |
| [`_interno/docs/resultados/`](_interno/docs/resultados/) | Saídas reais do programa, com o comando que as reproduz |
| [`_interno/docs/enunciado/`](_interno/docs/enunciado/) | Documento oficial e transcrição |

## Status

**Em desenvolvimento.** O programa roda de ponta a ponta; o que falta não é código, são
imagens reais.

| Etapa | Situação |
|-------|----------|
| Estrutura e documentação | Concluído |
| Núcleo de PDI (filtros próprios) | Implementado, 363 testes passando |
| Aquisição e I/O de imagem | Implementado |
| Pipeline de orquestração | Implementado |
| Interface Streamlit e linha de comando | Implementado |
| Extração de amostras para o modelo | Implementado |
| Modelo de visão computacional | Implementado — floresta aleatória, 25 testes |
| Aplicação em imagens reais de satélite | Executado — MODIS/Terra, São Félix do Xingu (PA), 2002 e 2024 |
| **Quantificação validada em imagem real** | **Bloqueada pela resolução — exige 10 a 30 m/pixel** |
| Trabalho escrito | Caps. 1 a 7 escritos e montados em `entrega/trabalho-escrito.docx`, com figuras |
| Apresentação do seminário | 16 slides e as falas de cada integrante em `entrega/` |
| Ficha de APS e postagem no site da UNIP | **Pendentes — dependem do grupo, não do código** |

### O resultado em imagem real foi uma recusa

O pipeline já rodou sobre um par bi-temporal real ([`_interno/docs/resultados/imagem-real/`](_interno/docs/resultados/imagem-real/)),
e **o sistema recusou-se a quantificar**: a 253 m/pixel quase todo pixel da frente de
desmatamento é mistura de floresta, pastagem e regeneração, as distribuições das duas
datas se sobrepõem demais — o vale entre as classes é raso — e não existe limiar global
defensável. A recusa é o comportamento
correto — o diagnóstico completo, com as três hipóteses testadas, está na
o capítulo 3.a do trabalho escrito.

Para quantificação validada é preciso Sentinel-2 (10 m) ou Landsat (30 m), que exigem
cadastro gratuito no Copernicus Data Space ou no USGS EarthExplorer.

A evidência de cena sintética ([`_interno/docs/resultados/cena-sintetica/`](_interno/docs/resultados/cena-sintetica/))
serve para demonstrar o programa e conferir a quantificação contra uma verdade de terreno
conhecida, mas **não sustenta requisito acadêmico**.

Duas dúvidas de formatação seguem em aberto com o professor e estão marcadas nos avisos do
gerador do documento: as margens superior e inferior, que o enunciado não especifica (foi
adotado o padrão da NBR 14724), e a numeração dos títulos.
