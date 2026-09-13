# AGENTS.md — aps-desmatamento-satelite

Regras locais deste projeto. Complementa o `AGENTS.md` global em
`/home/vader/Dev/pessoal/faculdade/AGENTS.md`.

---

## 1. Identidade

| Campo | Valor |
|-------|-------|
| Projeto | Detecção e quantificação de desmatamento em imagens de satélite |
| Disciplina orientadora | Processamento de Imagens e Visão Computacional |
| Curso | Ciência da Computação — UNIP |
| Semestre | 5º / 6º — 2026/2 |
| Tipo | APS (Atividades Práticas Supervisionadas) |
| Documento oficial | `docs/enunciado/ManualAPS-5oe6oCCI-PI-2026.pdf` |
| Transcrição | `docs/enunciado/TRANSCRICAO.md` |

---

## 2. Hierarquia de autoridade

```text
1. Instruções explícitas atuais do usuário
2. docs/enunciado/ManualAPS-5oe6oCCI-PI-2026.pdf   ← documento oficial
3. Orientações adicionais do professor
4. Este AGENTS.md
5. docs/PROJECT_SPEC.md e docs/REQUIREMENTS.md
6. docs/ARCHITECTURE.md e docs/decisions/
7. README.md
8. Código existente
9. Conhecimento geral do agente
```

O PDF prevalece sobre a transcrição, sobre este arquivo e sobre qualquer projeto anterior.

---

## 3. Objetivo

Desenvolver aplicação em Python que aplique processamento digital de imagens sobre imagens
reais de satélite para **detectar e quantificar áreas desmatadas**, produzindo dados preparados
que possam alimentar um modelo de visão computacional.

O PDI aqui é **preparação de dados**, não o produto final. Toda decisão deve ser avaliada contra
essa frase — ela é a redação literal do objetivo no enunciado (p.2).

---

## 4. Escopo

**Dentro:** aquisição de imagens orbitais, manipulação (espaços de cor, índices de vegetação),
filtragem espacial, segmentação, extração de patches rotulados, modelo de classificação,
quantificação de área, interface de demonstração.

**Fora:** serviço web em produção, autenticação, banco de dados, processamento de cena completa
em escala operacional, detecção em tempo real, deploy em nuvem.

---

## 5. Restrição central — filtros próprios

> **Os filtros devem ser desenvolvidos pelo grupo.** (enunciado p.3, item 3.a)

### Dentro de `src/sentinela/pdi/` a única dependência permitida é `numpy`.

**Proibido em `pdi/`:**

```text
opencv-python (cv2)
scikit-image (skimage)
scipy.ndimage
PIL.ImageFilter
qualquer biblioteca que forneça o filtro pronto
```

Antes de escrever qualquer coisa em `pdi/`, verificar: o algoritmo está sendo implementado aqui,
ou apenas chamado de outro lugar? Se for chamado, está errado.

**Permitido fora de `pdi/`:**

| Biblioteca | Onde | Para quê |
|-----------|------|----------|
| `Pillow` | `dataio/` | Abrir e salvar PNG/JPEG — **I/O apenas** |
| `rasterio` | `dataio/` | Ler GeoTIFF e metadado geográfico — opcional |
| `scikit-learn` | `modelo/` | Classificador da etapa de modelagem — **só o algoritmo de aprendizado**; as features saem de `pdi/` |
| `matplotlib` | `app/`, scripts | Histogramas e gráficos |
| `streamlit` | `app/` | Interface |

Raciocínio completo em `docs/decisions/001-filtros-proprios.md`.

As 15 features de `modelo/caracteristicas.py` são calculadas com `pdi.cor` e
`pdi.filtros`. Se o professor perguntar de onde vem a textura, a resposta é
`pdi.filtros.desvio_padrao_local`, e o algoritmo está no repositório.

---

## 6. Stack

- Python 3.12
- `numpy` — base numérica do núcleo de PDI
- `Pillow` — I/O de imagem
- `rasterio` — GeoTIFF (opcional; o sistema degrada sem ele)
- `scikit-learn` — modelo
- `streamlit` — interface
- `matplotlib` — gráficos
- `pytest` — testes

Antes de adicionar qualquer dependência nova: verificar se o enunciado permite, se há
alternativa nativa, e se o grupo consegue explicar o que ela faz. Pedir aprovação do usuário.

---

## 7. Arquitetura

Espelha as cinco etapas nomeadas pelo enunciado (p.3, item 2.e):

```text
Aquisição → Manipulação → Filtragem → Segmentação → Modelo
dataio/      pdi/cor.py   pdi/filtros.py  pdi/limiar.py    pipeline/amostras.py
                                          pdi/morfologia.py  modelo/
                                          pdi/segmentacao.py
```

`pipeline/deteccao.py` encadeia as cinco etapas e guarda **todos** os intermediários —
a interface precisa exibir etapa por etapa e o trabalho escrito precisa mostrar o efeito
de cada filtro. `app/principal.py` e `cli.py` só consomem o resultado; nenhum algoritmo
de PDI mora neles.

Regra de dependência: `pdi/` não importa de `pipeline/`, `app/`, `dataio/` nem `modelo/`.
Recebe e devolve arrays NumPy puros.

Detalhe em `docs/ARCHITECTURE.md`.

---

## 8. Convenções de código

- Representação interna: `float32`, faixa `[0, 1]`, formato `[H, W]` (cinza) ou `[H, W, C]`
  (multibanda). Conversão para `uint8` só na fronteira de saída.
- Nomes de módulos, funções e variáveis em **português** — o trabalho escrito é em português e
  o apêndice traz o código-fonte; código e texto precisam usar o mesmo vocabulário.
- Docstring em cada função pública de `pdi/`, indicando o que faz e a referência do algoritmo
  quando houver. Essas docstrings alimentam o capítulo 4.a do trabalho escrito.
- Sem comentário que apenas repete o código.
- Type hints nas funções públicas.

---

## 9. Testes

```bash
pytest
```

Os filtros são validados contra **casos analíticos conhecidos**, não contra output de
biblioteca. Exemplos: convolução com kernel identidade devolve a imagem original; gaussiano
preserva a soma de intensidade; Sobel numa rampa linear devolve gradiente constante; Otsu numa
imagem bimodal sintética cai entre os dois modos.

Ao implementar um filtro novo, escrever o teste **junto**. Um filtro sem teste não pode ser
marcado `VERIFIED` na matriz de requisitos.

A suíte tem **301 testes**. `tests/test_app.py` usa o `AppTest` do Streamlit e é pulado
automaticamente quando o extra `app` não está instalado.

---

## 10. Rastreabilidade

`docs/REQUIREMENTS.md` é a matriz. Ao implementar algo que atende a um requisito:

1. preencher a coluna **Implementação** com o caminho do arquivo;
2. preencher **Evidência/Teste**;
3. atualizar o **Status**.

Só marcar `VERIFIED` com teste passando ou evidência real em `docs/evidence/`. Compilar e rodar
não é verificar.

---

## 11. Dados

- `data/` não é versionado (`docs/decisions/002-dados-nao-versionados.md`).
- Toda imagem baixada deve ser registrada em `data/raw/FONTES.md`: satélite, produto, data,
  coordenadas, licença, URL.
- Imagens reais baixadas com `scripts/baixar_imagens.py`; procedência obrigatória em
  `data/raw/FONTES.md`, incluindo licença e URL exata.
- **Nunca fabricar imagem de satélite e apresentar como real.** Imagem sintética é permitida em
  teste, desde que rotulada como sintética no código e no trabalho escrito.
- Resultados que entram no trabalho escrito vão em `docs/evidence/`.

---

## 12. Integridade acadêmica

- Nunca inventar resultado, métrica, teste, screenshot ou referência bibliográfica.
- O trabalho escrito fica em `docs/trabalho-escrito/`. Toda lacuna de fonte é marcada
  com `[NEEDS_SOURCE: ...]` dizendo o que buscar e onde. Marcador pendente é aceitável
  em rascunho; citação inventada, nunca. Pendências em `BIBLIOGRAFIA.md`.
- **Atenção à escala ao citar o índice**: internamente o pipeline mapeia `[-1,1]` para
  `[0,1]` antes de limiarizar, o que reduz qualquer diferença à metade. No texto
  acadêmico, usar a escala nativa do índice e dizer qual é.
- Toda métrica no trabalho escrito deve ser reproduzível a partir do código do repositório.
- Screenshots devem vir da versão entregue, não de uma versão anterior.
- Não usar linguagem acadêmica acima do que o grupo consegue defender.
- Evitar abstração sem uso real — arquitetura acima do necessário é sinal de código não
  compreendido.

> Se o grupo não consegue explicar, o projeto não está pronto.

---

## 13. Critérios de aceite

Um requisito obrigatório só está pronto quando:

```text
implementado  +  testado ou com evidência real  +  refletido na matriz  +  o grupo sabe explicar
```

O projeto só está pronto quando, abrindo o enunciado item por item, for possível apontar onde
cada exigência foi atendida, mostrar a implementação e exibir evidência real de que funciona.

---

## 14. Perguntas em aberto

Oito perguntas aguardam o professor (`docs/PROJECT_SPEC.md` → Open Questions). A mais
impactante é **Q5**: o modelo de visão computacional precisa ser treinado e funcional, ou basta
a proposta teórica?

Até haver resposta, o projeto adota a leitura conservadora: **implementar o modelo de fato**.

Não resolver nenhuma dessas perguntas por suposição silenciosa. Se uma decisão depender de uma
delas, registrar a suposição explicitamente.

---

## 15. Git

- Branch principal: `main`. Branches só quando agregarem valor.
- Commits em português, no padrão `tipo: descrição`
  (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`).
- Rodar `git status` antes de mudanças relevantes.
- Nunca executar `git reset --hard` ou `git clean -fd` sem autorização explícita.
- Repositório é **privado**.

---

## 16. Débito técnico conhecido

| # | Item | Quando resolver |
|---|------|-----------------|
| T1 | **Resolução insuficiente**: o par MODIS (253 m/px) foi processado, mas as classes se sobrepõem — vale raso — e a detecção é recusada. Quantificação exige Sentinel-2/Landsat, que exigem cadastro | Antes da Fase Intermediária I |
| T7 | Features de textura não são separáveis na cena sintética (mesmo ruído nas duas classes); só podem ser validadas em imagem real | Junto com T1 |
| T4 | Convolução genérica continua `O(H·W·k²)`. Gaussiano e média — os filtros separáveis — já usam dois passes 1D. Mediana não é separável e segue `O(H·W·k²)` por natureza | Só se a demonstração exigir |
| T5 | `DISTINGUIBILIDADE_MINIMA = 4.0` foi calibrada em cena sintética. Confirmado em imagem real que precisa de recalibração — por procedimento honesto, **nunca** ajustando para uma cena passar | Junto com T1 |
| T6 | `rasterio` não está instalado; sem ele a resolução espacial é informada à mão | Só se as cenas vierem em GeoTIFF |

> **T2 (interface Streamlit) foi resolvido.** `app/principal.py` está implementado e
> coberto por teste de fumaça em `tests/test_app.py`.
>
> **T8 (NDMI) foi resolvido.** `pdi.cor.ndmi` (SWIR 1) e `pdi.cor.nbr` (SWIR 2) estão
> implementados, expostos na CLI e na interface, e cobertos por teste. **Sobre as imagens do
> GIBS o índice correto é o NBR**: a composição traz a banda 7 do MODIS, que é SWIR 2.
> Nenhum dos dois entra no modo automático.
>
> **T3 (etapa de modelo) foi resolvido.** `modelo/` está implementado pela leitura
> conservadora do §14, com 25 testes. Q5 continua em aberto, mas deixou de bloquear.

---

## 17. Graphify — contexto de código local

Ferramenta **auxiliar do agente**. Não é dependência da aplicação, não é entregável
acadêmico e não entra no trabalho escrito. Regra global em `faculdade/AGENTS.md` §55;
esta seção é autossuficiente, com os caminhos e comandos já validados neste projeto.

### Estado

| Campo | Valor |
|-------|-------|
| Estado | `READY` — regenerado em 2026-09-12 sobre o código com as cinco etapas |
| Grafo | `graphify-out/graph.json` — 863 nós, 1531 arestas, 37 arquivos-fonte |
| Origem dos nós | 863/863 `ast` — zero LLM (`input_tokens=0`, `output_tokens=0`) |
| Ferramenta | `/home/vader/.local/share/uv/tools/graphifyy/bin/graphify` — `graphify 0.9.51` |
| Baseline | `~/.local/state/graphify-baseline/aps-desmatamento-satelite/` (fora do repo) |

### Fronteiras

- Um grafo **deste** projeto apenas. Nunca indexar `faculdade/` ou `projetos/`, nunca
  usar `--global`.
- `graphify-out/` e `.handoff/` estão no `.gitignore` e **nunca** vão para o GitHub,
  Drive, Alpha Brain ou qualquer provedor de IA.
- Somente AST local: sem LLM, sem embeddings, sem rede, sem telemetria.
- **O código-fonte é a autoridade.** O grafo só orienta a busca e pode estar obsoleto —
  confirmar na fonte antes de editar.
- Sem `sudo`, instalação, hooks, MCP, `watch`, cron ou alteração global. Mudança de
  ferramenta, versão, isolamento ou escopo exige novo Security Gate.

### Consultas (da raiz do projeto)

```bash
G=/home/vader/.local/share/uv/tools/graphifyy/bin/graphify

umask 077 && GRAPHIFY_QUERY_LOG_DISABLE=1 unshare -Urn $G \
  query "<símbolo A> calls <símbolo B>" --context call --budget 1200 \
  --graph graphify-out/graph.json

umask 077 && GRAPHIFY_QUERY_LOG_DISABLE=1 unshare -Urn $G \
  explain "<símbolo-ou-ID>" --graph graphify-out/graph.json

umask 077 && GRAPHIFY_QUERY_LOG_DISABLE=1 unshare -Urn $G \
  path "<A>" "<B>" --graph graphify-out/graph.json
```

Um símbolo ou relação por vez. **Guardrail:** acima de 20 nós, ou com aviso de orçamento
excedido, parar e reformular — preferir ID exato em caso de ambiguidade. Nunca compensar
despejando arquivos inteiros.

### Regeneração

Só pelo procedimento revisado, com backup e nova validação:

```bash
umask 077 && unshare -Urn $G extract . --code-only --no-cluster
```

- **`--code-only` é obrigatório.** A ajuda da 0.9.51 descreve `extract` puro como
  "AST + semantic LLM": sem essa flag, dispara extração semântica com LLM.
- `--no-cluster` evita a nomeação de comunidades, que também usa LLM.
- **Nunca** usar `--global`, `--no-gitignore`, `--force`, enriquecimento ou visualização.
- **Não** rodar `graphify update` automaticamente: o piloto identificou mudança de esquema
  `edges`/`links` e alteração semântica de baseline. Migração exige novo Security Gate.

Exclusões em `.graphifyignore` — `.gitignore` sozinho não basta.

Após mudança relevante no código, marcar o grafo como `STALE` em `docs/PROJECT_STATE.md`
até regenerar. Data do arquivo não comprova atualidade.

### Aceite

Só declarar `READY` após verificar: extração bem-sucedida e esquema válido; nenhum caminho
fora da allowlist e nenhum secret; **uma consulta de resposta conhecida confirmada na
fonte**; saída restrita e fora do Git; baseline atualizado.

A validação desta geração: `path treinar_e_avaliar → dividir_espacialmente` devolveu 1 salto,
`calls [EXTRACTED]`, conferido em `modelo/classificador.py` L307 — o arquivo que mudou nesta
extração, o que prova que ele foi relido. A geração anterior foi validada com
`aba_etapas → _legenda_mudanca` (`app/principal.py` L278). Um nó `ndarray` **sem arquivo-fonte**
apareceu nesta extração: referência a tipo externo registrada pelo extrator incremental, não
conteúdo indexado — nenhum nó foi removido. A varredura de secrets usa fronteira de
palavra: uma versão anterior da regex acusou "senha" dentro de "Desenha", falso positivo.
As gerações anteriores (433 e 840 nós) estão em backups verificados por hash no diretório
de baseline.
