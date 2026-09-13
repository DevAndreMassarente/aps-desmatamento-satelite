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

---

## Marco 2 — programa completo, imagem real, trabalho escrito e apresentação

_Commits `4d1d672` a `317fc3e`._

### Decisões

| # | Decisão | Onde está o raciocínio |
|---|---------|------------------------|
| D8 | Detecção não confiável **não reporta área**: o resumo devolve vazio em vez de um número | `pipeline/deteccao.py` |
| D9 | Recortes ambíguos descartados na rotulagem, não arredondados para a classe majoritária | `pipeline/amostras.py` |
| D10 | Divisão treino/teste por **blocos espaciais**, nunca por sorteio de recorte | `decisions/004` |
| D11 | Floresta aleatória em vez de rede convolucional, pela defesa oral | `modelo/classificador.py` |
| D12 | Vermelho e NIR do **mesmo** produto do GIBS: os realces de 8 bits diferem entre produtos | `data/raw/FONTES.md` |
| D13 | Resultado negativo em imagem real mantido; o limiar **não** foi ajustado para a cena passar | `decisions/005` |
| D14 | NDMI e NBR fora do modo automático; sobre MODIS via GIBS o índice correto é o NBR | `pdi/cor.py` |
| D15 | Bibliografia só com fontes lidas; o que não pôde ser lido saiu do texto | `trabalho-escrito/BIBLIOGRAFIA.md` |

### Aprendizados

**Resolução de 250 m não sustenta detecção por limiar global numa frente de desmatamento.**
Pixel misto: as distribuições das duas datas se sobrepõem e o vale entre as classes é raso.
O sistema recusou-se a quantificar — e estava certo. Testadas antes de concluir: outro índice
(melhora, não basta), limiarizar a diferença (piora), resolução (confirmado).

**Fumaça de queimada passou no controle de nuvem medido sobre a composição com SWIR.** A cena
de agosto foi aprovada com 0% de nuvem e inverteu a comparação entre as datas. Bruma passou a
ser medida no azul da composição visível. Regra prática: não escolher datas de agosto e
setembro na Amazônia.

**Nome de índice é afirmação de fato.** O índice NIR − SWIR sobre a banda 7 do MODIS é o NBR,
não o NDMI (que exige a banda 6). A conta estava certa e o nome errado por várias rodadas;
só apareceu ao conferir as definições oficiais para a bibliografia.

**Descrever um gráfico sem desenhá-lo gera exagero.** O texto dizia "unimodal, sem vale"; o
histograma desenhado mostrou vale raso. Corrigido em 11 documentos.

**Toda afirmação técnica "óbvia" pediu fonte e várias caíram**: "NDVI satura em dossel
denso", "ExG é mais sensível à iluminação", "PRODES usa Landsat a 20–30 m" (a nota do INPE de
2025 diz Sentinel-2 e Sentinel-1). Também: o SWIR do MODIS tem 500 m nativos, não 250 m; o do
Sentinel-2 tem 20 m, não 10 m.

**Escala do índice.** O pipeline mapeia `[-1,1]` para `[0,1]`, o que divide diferenças pela
metade; relatar sempre na escala nativa.

**Interface e evidência:** o servidor Streamlit mantém os módulos do pacote importados e
serve código antigo mesmo com os testes passando — reiniciar antes de capturar telas.
Emoji como ícone vira quadrado sem fonte de emoji. O screenshot achou um bug que a suíte não
pegava: aviso de "desempenho perfeito" com teste de uma classe só.

**Operação:** `pkill -f <padrão>` casou com o próprio shell que o executava; ancorar o padrão
no início da linha de comando.

### Testes

301 testes. Além dos casos analíticos: cadeia completa contra verdade de terreno sintética
(erro 0,0%), controle negativo que exige a recusa, prova por enumeração de que treino e teste
não compartilham pixel, equivalência dos filtros separáveis inclusive nas bordas, teste de
fumaça da interface e do gerador de apêndice. Evidência sintética é sempre rotulada como tal.

### Riscos

| # | Risco | Mitigação |
|---|-------|-----------|
| R1 | `DISTINGUIBILIDADE_MINIMA = 4.0` calibrada em cena sintética; em imagem real ficou provado que precisa de recalibração | Só por procedimento independente (controles negativo e positivo), nunca ajustando para uma cena |
| R3 | Quantificação em imagem real bloqueada pela resolução | Exige Sentinel-2 ou Landsat — cadastro de um integrante |
| R6 | Desempenho do classificador medido só em cena sintética (F1 = 1,0 não valida nada) | O próprio programa emite o aviso |
| R7 | Documento final ABNT inexistente; margens superior e inferior indefinidas (Q4) | Gerar por comando com as margens como parâmetro explícito |
| R8 | Texto acadêmico escrito com apoio de IA; política institucional desconhecida (Q8) | O grupo precisa revisar e assumir cada parágrafo antes da arguição |

### Próximos passos

1. Grupo: definir integrantes (Q7), revisar o texto, ensaiar a apresentação.
2. Professor: Q1–Q8, em especial Q4 (margens), Q5 (escopo do modelo) e Q8 (uso de IA).
3. Cadastro no Copernicus ou USGS para obter imagem de 10–30 m.
4. Montar o documento final formatado e preencher a ficha de APS.

---

## Marco 3 — bibliografia verificada, auditoria e documento final

_Commits `317fc3e` a este._

### Decisões

| # | Decisão | Onde |
|---|---------|------|
| D15 | Bibliografia só com fontes lidas; dez obras descartadas com motivo | `trabalho-escrito/BIBLIOGRAFIA.md` |
| D16 | Documento `.docx` gerado por comando só com biblioteca padrão; saída fora do Git | `scripts/montar_documento.py` |
| D17 | Margens superior/inferior pela NBR 14724 (conferida no tutorial da Biblioteca da PUC-SP), registradas como suposição até Q4 | idem |

### Aprendizados

**Buscar fonte é verificação, não formatação.** Resolver as referências corrigiu três fatos
do projeto (NDMI × NBR, sensor do PRODES, resolução nativa das bandas) e derrubou quatro
afirmações "óbvias" sem sustentação. Resumo de busca não conta como fonte: só o documento lido.

**Contornos de acesso sem dependência nova:** metadados pelo Crossref, resumos pelo OpenAlex,
PDFs por `curl` com o extrator próprio do projeto. Páginas de editores bloqueiam; APIs abertas
não.

**Matriz de requisitos envelhece em silêncio.** A auditoria achou quatro estados desatualizados
— trabalho feito e não refletido. Rodar a auditoria depois de cada bloco grande.

**Testar o gerador achou dois defeitos antes de qualquer pessoa abrir o documento:** linha de
continuação de referência que começa com ano ("2018. ISBN") lida como lista numerada, e o ano
apagado da capa numa edição de seção. Módulo com `@dataclass` carregado por caminho precisa ser
registrado em `sys.modules`.

**`set -e` não protege cadeias neste ambiente.** O executor roda cada comando como
`eval '…' && …`, e o bash desliga o `errexit` para tudo o que está do lado esquerdo de um
`&&`. Uma edição falhou, o script saiu com código 1 e o commit aconteceu mesmo assim, com um
parágrafo desatualizado no `AGENTS.md` (corrigido no commit seguinte). Reproduzido: em `bash -c`
novo o `set -e` interrompe; no shell da sessão, não. Usar `|| exit 1` explícito em todo passo
que deve cancelar os seguintes.


### Riscos

| # | Risco | Mitigação |
|---|-------|-----------|
| R9 | O `.docx` nunca foi aberto no Word nesta máquina | Testes garantem estrutura e formatação de base; conferência no Word é passo obrigatório antes de postar |
| R10 | Numeração dos títulos diverge da NBR 14724 (Q2) | Aviso emitido pelo gerador a cada execução |

### Próximos passos

1. Grupo: Q7 (integrantes) → `capa.json`; gerar, abrir no Word, atualizar o sumário.
2. Professor: Q2, Q4, Q5, Q8.
3. Imagem de 10–30 m (cadastro Copernicus ou USGS) para a quantificação.
