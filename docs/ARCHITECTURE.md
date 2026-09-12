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
│  sentinela/app/ · sentinela/cli.py                              │
│  Interface Streamlit e linha de comando                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  sentinela/pipeline/       Orquestração das etapas              │
│   deteccao.py  encadeia PDI e guarda os intermediários          │
│   amostras.py  recortes rotulados que alimentam o modelo        │
└───┬─────────────────────────────────────────────┬───────────────┘
    │                                             │
┌───▼──────────────────────┐         ┌────────────▼───────────────┐
│ sentinela/dataio/        │         │ sentinela/modelo/          │
│ AQUISIÇÃO                │         │ MODELO   (a implementar)   │
│ imagem.py  leitura/escrita│        │ features + classificador   │
│ geo.py     GeoTIFF (opc.) │        │ (scikit-learn)             │
│ sintetico.py  demonstração│        │                            │
│ visual.py  sobreposição   │        │                            │
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
| `dataio/imagem.py` | Abrir e salvar imagem; converter faixa na fronteira | Não processa pixel |
| `dataio/geo.py` | Ler resolução espacial do GeoTIFF | Não converte área |
| `dataio/sintetico.py` | Gerar cena de demonstração | Não é fonte de evidência |
| `dataio/visual.py` | Sobreposição, mapa de mudança, falsa cor | Não decide nada |
| `pipeline/deteccao.py` | Encadear as etapas, registrar cada saída intermediária | Não implementa algoritmo |
| `pipeline/amostras.py` | Recortar e rotular amostras para o modelo | Não treina |
| `cli.py` | Expor o pipeline por comando, gravar evidência reproduzível | Não implementa algoritmo |
| `modelo/caracteristicas.py` | Descrever cada recorte com medidas vindas de `pdi/` | Não implementa filtro |
| `modelo/classificador.py` | Dividir espacialmente, treinar, avaliar, relatar importância | Não faz PDI |
| `app/` | Apresentar, receber parâmetros, exibir comparações | Não contém lógica de domínio |

---

## Fluxo principal

Os nomes abaixo são os do código real. `pipeline.detectar_desmatamento()` executa as
etapas 1 a 4 numa chamada e devolve um `ResultadoDeteccao` com todos os intermediários.

```text
1. AQUISIÇÃO
   imagem T1 (antes)  ─┐
   imagem T2 (depois) ─┴─► dataio.carregar_par()
                           → float32 [H,W,3] em [0,1]; recusa recortes de tamanhos diferentes
                           dataio.metros_por_pixel()   resolução do GeoTIFF (opcional)

2. MANIPULAÇÃO
   → cor.indice_vegetacao()      NDVI se houver banda NIR; VARI sobre RGB caso contrário
   → cor.para_faixa_unitaria()   índice assinado [-1,1] → [0,1]

3. FILTRAGEM
   → filtros.gaussiano()             suaviza antes de segmentar; sem isso a máscara
                                     sai esburacada e a contagem por região se perde
   → filtros.magnitude_gradiente()   Sobel — realça a fronteira floresta/solo exposto
                                     (exibido na interface, não entra na decisão)

4. SEGMENTAÇÃO
   → limiar.limiar_confiavel()          limiar ÚNICO para as duas datas + veredito de
                                        confiabilidade por tamanho de efeito
   → limiar.binarizar()                 aplica o mesmo valor nas duas máscaras
   → morfologia.abertura() / fechamento()   remove respingos e fecha buracos
   → segmentacao.mudanca_entre_mascaras()   perda / ganho / estável
   → segmentacao.filtrar_por_area()     descarta fragmentos residuais
   → segmentacao.rotular() + descrever_regioes()   área, centroide e caixa por região

   Quantificação: Regiao.area_hectares(metros_por_pixel), quando a resolução é conhecida.

5. PREPARAÇÃO DE DADOS   ← é aqui que o objetivo do enunciado se cumpre
   → pipeline.extrair_amostras()   recortes + rótulo vindo da máscara de perda;
                                   recortes ambíguos são descartados, não arredondados
   → pipeline.equilibrar()         subamostra a classe majoritária

6. MODELO
   → modelo.extrair_caracteristicas()  15 descritores por recorte, calculados com
                                       pdi.cor e pdi.filtros — nada vem pronto
   → modelo.dividir_espacialmente()    treino/teste por BLOCOS da imagem; sortear
                                       recortes vazaria pixel de um lado para o outro
   → modelo.treinar_e_avaliar()        floresta aleatória + precisão, revocação, F1,
                                       matriz de confusão e avisos sobre a métrica
```

### Saídas

| Consumidor | Como |
|-----------|------|
| Interface | `app/principal.py` — etapas lado a lado, métricas, tabela de regiões |
| Linha de comando | `cli.py` — `sentinela detectar --saida <dir>` grava PNG por etapa + `resumo.json` |
| Biblioteca | `ResultadoDeteccao.resumo()` — dicionário pronto para relatório |

### A recusa deliberada

Quando as duas datas não apresentam classes separáveis, `limiar_confiavel` devolve
`confiavel=False` e `resumo()` põe `None` no lugar da área. A máscara continua acessível
para inspeção, mas o número não é reportado. Produzir uma área ali seria inventar
desmatamento — ver `docs/decisions/003-limiar-bitemporal.md`.

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
│   ├── app/              interface Streamlit
│   └── cli.py            linha de comando
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
