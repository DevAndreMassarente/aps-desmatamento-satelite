# Memória do agente — aps-desmatamento-satelite

Conhecimento acumulado entre sessões. Mantido em marcos relevantes, não a cada alteração.

**Regra de conteúdo (`AGENTS.md` global §55):** só o que for útil — Decisões, Aprendizados,
Testes, Riscos e Próximos passos. Sem código, diffs, logs, transcrições, dumps de grafo ou
secrets. Revisar antes de versionar.

---

## Marco 1 — Bootstrap + núcleo de PDI

_Commits `64f6dec`, `a3bd361`._

### Decisões

| # | Decisão | Onde está o raciocínio |
|---|---------|------------------------|
| D1 | Filtros implementados do zero, só com NumPy. `cv2`/`skimage`/`scipy.ndimage`/`PIL.ImageFilter` proibidos em `pdi/` | `decisions/001` |
| D2 | Imagens de satélite fora do Git; só as fontes registradas | `decisions/002` |
| D3 | Abordagem **bi-temporal** (duas datas da mesma área) em vez de imagem única | `ARCHITECTURE.md` |
| D4 | Streamlit para a interface — comparação antes/depois ao vivo, offline na sala | `PROJECT_SPEC.md` |
| D5 | Representação interna `float32` em `[0,1]` | `ARCHITECTURE.md` |
| D6 | Limiar único para as duas datas + confiabilidade por tamanho de efeito | `decisions/003` |
| D7 | Graphify como contexto local do agente, nunca versionado | `AGENTS.md` §17 |

### Aprendizados

**Detecção em imagem única é mal-posta.** Solo exposto natural, afloramento rochoso e área
agrícola antiga têm assinatura espectral parecida com corte raso recente. Só a comparação
entre datas transforma o problema em "onde houve **perda** de vegetação". Isso também dá ao
grupo a resposta para "por que essa abordagem?" na banca.

**Otsu aplicado por data estava errado.** Numa cena de floresta intacta o histograma é
unimodal; o Otsu, que sempre devolve algum limiar, corta no meio do ruído do dossel e
classificou 43% de floresta intacta como não-vegetação. Cada data ganhava uma régua
diferente, e a comparação media a diferença entre limiares, não mudança no terreno. Corrigido
com limiar único sobre o histograma combinado.

**A separabilidade η do artigo original do Otsu não serve como critério de confiança.**
Ela carrega o fator `ω·(1−ω)`, que é deprimido por desbalanceamento de classe — e
desmatamento é sempre a classe minoritária. Medido: cena homogênea deu η = 0,650 e cena com
desmatamento real detectado pelo VARI deu η = 0,575. **Ordena ao contrário.** Substituído por
tamanho de efeito padronizado, que não tem esse fator.

**O piso de 2,65 tem base teórica, não é chute.** Cortar uma normal única no ponto ótimo
produz duas meias-normais com médias em ±0,798σ e desvio 0,603σ, logo d ≈ 2,65. Qualquer
imagem unimodal atinge isso. O medido nas cenas homogêneas foi 2,68–2,69, nos três índices.

**Índices só-visíveis são instáveis em floresta escura.** VARI e ExG detectaram o corte
corretamente, mas com desvio interno 5× maior que o NDVI, porque o denominador em pixel de
floresta é minúsculo (refletância visível baixa). Funciona, mas com margem menor.

**O PDF do enunciado quebra `pdftotext`.** Usa `ToUnicode` por fonte; leitores comuns
devolvem texto cifrado. Extrator próprio em `scripts/extrair_enunciado.py`.

### Testes

154 testes, validados contra **casos analíticos conhecidos**, nunca contra saída de outra
biblioteca — comparar com `cv2` só provaria que copiamos o `cv2`. Exemplos: kernel identidade
preserva a imagem; Laplaciano anula rampa linear; abertura e fechamento são idempotentes;
forma em "U" é uma única região conexa; conectividade 4 separa o que a 8 une.

Um teste de nitidez falhou por medir longe da transição, onde o gaussiano já saturou e o
recorte em `[0,1]` limita o resultado — o teste media o recorte, não o realce.

### Riscos

| # | Risco | Mitigação |
|---|-------|-----------|
| R1 | `DISTINGUIBILIDADE_MINIMA = 4.0` calibrada só em **cena sintética** | Reavaliar contra imagem real antes de citar no trabalho escrito |
| R2 | Escopo do modelo indefinido (Q5) — dimensiona metade do programa | Leitura conservadora adotada: implementar de fato |
| R3 | Nenhuma imagem real baixada; R032 parado | Fontes registradas em `data/raw/FONTES.md` |
| R4 | `python3-venv` desta máquina sem `ensurepip` | Contornado com `venv --without-pip` + `get-pip.py` |
| R5 | Regra global pode mudar após o bootstrap, como já ocorreu com o §55 | Auditar o `AGENTS.md` global ao retomar |

### Próximos passos

1. Levar Q1–Q8 ao professor. **Q5 destrava o planejamento.**
2. Baixar o par bi-temporal real (Copernicus/INPE) e registrar em `FONTES.md`.
3. Rodar o pipeline em imagem real e recalibrar R1.
4. Fase Intermediária I: Cap. 1 + filtragem dos Caps. 2 e 3.
5. Interface Streamlit; depois a etapa de modelo.
