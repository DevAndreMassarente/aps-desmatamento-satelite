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
| `scikit-learn` | `modelo/` | Classificador da etapa de modelagem |
| `matplotlib` | `app/`, scripts | Histogramas e gráficos |
| `streamlit` | `app/` | Interface |

Raciocínio completo em `docs/decisions/001-filtros-proprios.md`.

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
dataio/      pdi/cor.py   pdi/filtros.py  pdi/limiar.py    modelo/
                                          pdi/morfologia.py
                                          pdi/segmentacao.py
```

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
- **Nunca fabricar imagem de satélite e apresentar como real.** Imagem sintética é permitida em
  teste, desde que rotulada como sintética no código e no trabalho escrito.
- Resultados que entram no trabalho escrito vão em `docs/evidence/`.

---

## 12. Integridade acadêmica

- Nunca inventar resultado, métrica, teste, screenshot ou referência bibliográfica.
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
| T1 | Nenhuma imagem real baixada — pipeline ainda não rodou em dado verdadeiro | Antes da Fase Intermediária I |
| T2 | Interface Streamlit ainda não construída | Antes da Fase Intermediária II |
| T3 | Etapa de modelo ainda não implementada | Depende de Q5 |
| T4 | Convolução é `O(H·W·k²)` com laço sobre o kernel — suficiente para recortes, pode ficar lenta em cena grande | Só se a demonstração exigir |
