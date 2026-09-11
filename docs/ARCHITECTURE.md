# Architecture

## Princípio de organização

O enunciado (p.3, item 2.e) nomeia explicitamente cinco conceitos que o trabalho escrito deve
apresentar:

```text
Aquisição → Manipulação → Filtragem → Segmentação → Modelo de visão computacional
```

O código é organizado **nessa mesma ordem**. Não é coincidência: quando o professor perguntar
"onde está a segmentação?", a resposta é um arquivo, não uma explicação. Isso atende ao
requisito de rastreabilidade (R005–R009) sem custo arquitetural nenhum.

---

## Componentes

```text
┌─────────────────────────────────────────────────────────────────┐
│  sentinela/app/           Interface Streamlit                   │
│                           (demonstração, sliders, comparações)  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  sentinela/pipeline/       Orquestração das etapas              │
│                           encadeia PDI → produz dado para modelo│
└───┬─────────────────────────────────────────────┬───────────────┘
    │                                             │
┌───▼──────────────────────┐         ┌────────────▼───────────────┐
│ sentinela/dataio/        │         │ sentinela/modelo/          │
│ AQUISIÇÃO                │         │ MODELO                     │
│ leitura PNG/JPEG/GeoTIFF │         │ features + classificador   │
│ metadados geográficos    │         │ (scikit-learn)             │
└───┬──────────────────────┘         └────────────────────────────┘
    │
┌───▼─────────────────────────────────────────────────────────────┐
│  sentinela/pdi/           NÚCLEO — implementado pelo grupo       │
│                                                                  │
│   nucleo.py       convolução, padding, normalização              │
│   cor.py          MANIPULAÇÃO: RGB→cinza, RGB→HSV, índices       │
│   filtros.py      FILTRAGEM: gaussiano, mediana, Sobel, ...      │
│   limiar.py       SEGMENTAÇÃO: Otsu, limiar adaptativo           │
│   morfologia.py   SEGMENTAÇÃO: erosão, dilatação, abertura...    │
│   segmentacao.py  SEGMENTAÇÃO: componentes conexos, região       │
│                                                                  │
│   Dependência permitida aqui: SOMENTE numpy.                     │
└──────────────────────────────────────────────────────────────────┘
```

### Regra de dependência

As setas apontam sempre para baixo. `pdi/` não conhece `pipeline/`, `app/` nem `dataio/` —
recebe e devolve arrays NumPy puros. Isso é o que torna cada filtro testável isoladamente
(R014, R030) e reaproveitável no notebook de análise do trabalho escrito.

---

## Responsabilidades

| Módulo | Responsabilidade | Não faz |
|--------|------------------|---------|
| `pdi/nucleo.py` | Convolução 2D, estratégias de borda, normalização, conversão de faixa | Não lê arquivo, não decide parâmetro |
| `pdi/cor.py` | Espaços de cor e índices de vegetação | Não filtra |
| `pdi/filtros.py` | Filtros espaciais construídos sobre `nucleo.py` | Não segmenta |
| `pdi/limiar.py` | Cálculo de limiares e binarização | Não aplica morfologia |
| `pdi/morfologia.py` | Operadores morfológicos sobre máscaras binárias | Não rotula regiões |
| `pdi/segmentacao.py` | Rotulagem de componentes conexos, filtro por área | Não classifica |
| `dataio/` | Abrir imagem, ler metadado geográfico, salvar resultado | Não processa pixel |
| `pipeline/` | Encadear as etapas, registrar cada saída intermediária | Não implementa algoritmo |
| `modelo/` | Extrair features dos patches, treinar e aplicar classificador | Não faz PDI |
| `app/` | Apresentar, receber parâmetros, exibir comparações | Não contém lógica de domínio |

---

## Fluxo principal

```text
1. AQUISIÇÃO
   imagem T1 (antes)  ─┐
   imagem T2 (depois) ─┴─► dataio.carregar()
                           → array float32 [H,W,C] em [0,1] + metadado geográfico opcional

2. MANIPULAÇÃO
   → cor.para_cinza() / cor.para_hsv()
   → cor.indice_vegetacao()   NDVI se houver banda NIR; senão ExG/VARI sobre RGB
   → nucleo.alongar_contraste() / equalizar_histograma()

3. FILTRAGEM
   → filtros.gaussiano()   suaviza ruído sensor/atmosfera antes de segmentar
   → filtros.mediana()     remove ruído sal-e-pimenta preservando borda
   → filtros.sobel()       realça a fronteira floresta/solo exposto

4. SEGMENTAÇÃO
   → limiar.otsu()                 separa vegetação de não-vegetação
   → morfologia.abertura()         remove respingos isolados
   → morfologia.fechamento()       fecha buracos dentro da área desmatada
   → segmentacao.componentes()     rotula regiões
   → segmentacao.filtrar_area()    descarta região menor que o limiar mínimo

5. PREPARAÇÃO DE DADOS   ← é aqui que o objetivo do enunciado se cumpre
   → pipeline.extrair_patches()    recortes normalizados + rótulo
   → dataio.salvar_dataset()       data/processed/

6. MODELO
   → modelo.features()             estatísticas de cor, textura e índice por patch
   → modelo.treinar() / prever()   classificador
   → quantificação: pixels → hectares (quando houver metadado geográfico)
```

---

## Decisões arquiteturais relevantes

### Por que `float32` em `[0, 1]` como representação interna

Trabalhar em inteiro de 8 bits obriga a saturar a cada operação e destrói precisão em cadeias
longas de filtro (o gradiente de Sobel é naturalmente negativo, por exemplo). A conversão para
`uint8` acontece só na fronteira de saída, em `dataio`/`app`.

### Por que a comparação bi-temporal

Detectar desmatamento em **uma única** imagem é mal-posto: solo exposto natural, afloramento
rochoso e área agrícola antiga têm assinatura parecida com corte raso recente. Comparar a mesma
área em duas datas transforma o problema em "onde houve **perda** de vegetação", que é o que o
enunciado pede em termos de sustentabilidade. Isso também dá ao grupo uma resposta forte na
pergunta "por que essa abordagem?" da banca.

### Por que índice de vegetação e não só RGB

NDVI usa a banda do infravermelho próximo, onde vegetação sadia reflete muito e solo exposto
não — a separação é muito mais limpa que em RGB. Quando a imagem disponível for apenas RGB, o
sistema cai para ExG/VARI, que aproximam o efeito usando só as bandas visíveis. A escolha fica
explícita na interface para que o grupo saiba explicar qual está em uso.

### Por que `rasterio` é opcional

GeoTIFF dá a resolução espacial do pixel, que é o que permite reportar "N hectares" em vez de
"N pixels" — muito mais convincente na apresentação. Mas `rasterio` tem dependência nativa
(GDAL) e pode falhar de instalar na máquina de um integrante. O sistema detecta a ausência e
segue funcionando com PNG/JPEG, apenas sem a conversão para hectares.

---

## Estrutura de diretórios

```text
aps-desmatamento-satelite/
├── src/sentinela/
│   ├── pdi/              núcleo de processamento (só numpy)
│   ├── dataio/           aquisição e persistência
│   ├── pipeline/         orquestração
│   ├── modelo/           visão computacional
│   └── app/              interface Streamlit
├── tests/                pytest — valida os filtros contra casos analíticos
├── docs/
│   ├── enunciado/        documento oficial + transcrição
│   ├── evidence/         screenshots, resultados, benchmarks
│   └── decisions/        ADRs
├── scripts/              utilitários (extração do enunciado, download de dados)
└── data/
    ├── raw/              imagens originais (não versionadas)
    ├── interim/          saídas intermediárias de cada etapa
    └── processed/        dataset pronto para o modelo
```

`data/` não é versionado — ver `docs/decisions/002-dados-nao-versionados.md`.
