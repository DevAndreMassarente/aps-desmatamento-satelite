# 003 — Limiar único para as duas datas, e como julgar se ele é confiável

**Status:** Aceita
**Contexto:** Descoberto ao escrever o teste de integração do bootstrap

## Contexto

O pipeline bi-temporal segmenta a vegetação em duas datas e compara as máscaras: onde
havia vegetação em T1 e não há em T2, houve desmatamento.

A implementação óbvia é aplicar Otsu em cada data separadamente. Ela está **errada**, e o
teste de integração expôs isso.

## Problema 1 — Otsu por data usa réguas diferentes

Medição nas cenas sintéticas de `tests/test_integracao.py`:

| Cena | Faixa do índice | Limiar de Otsu | Fração marcada como vegetação |
|------|-----------------|----------------|-------------------------------|
| T1 — floresta intacta | 0,897 – 0,942 | 0,9160 | 57% |
| T2 — floresta + corte raso | 0,519 – 0,938 | 0,7129 | 94% |

T1 é inteiramente floresta. Seu histograma tem **um modo só**, e Otsu — que por construção
sempre devolve algum limiar — corta no meio do ruído do dossel, classificando 43% da
floresta intacta como não-vegetação.

Comparar essa máscara com a de T2 não mede mudança no terreno. Mede a diferença entre
0,9160 e 0,7129.

### Decisão 1

Calcular **um limiar único** sobre o histograma combinado das duas datas
(`limiar.otsu_conjunto`). Basta que uma das datas contenha as duas classes para o limiar
ficar bem definido, e as duas máscaras passam a ser medidas pela mesma régua.

Verificado em `test_limiar_conjunto_e_o_mesmo_para_as_duas_datas`: os limiares por data
diferem em mais de 0,15, enquanto o conjunto fica a menos de 0,05 do limiar da data
informativa.

## Problema 2 — a separabilidade η de Otsu não detecta cena homogênea

Resolvido o problema 1, resta a pergunta: e se **nenhuma** das duas datas tiver
desmatamento? O limiar continua sendo devolvido, e continua sem significado.

O artigo original de Otsu define uma medida de separabilidade
`η = σ²_entre / σ²_total`. A hipótese inicial foi usá-la como critério de confiança.
Medição:

| Caso | Índice | η | Tamanho de efeito (d) |
|------|--------|-----|----------------------|
| Homogênea (floresta + floresta) | NDVI | 0,650 | 2,69 |
| Homogênea (floresta + floresta) | VARI | 0,634 | 2,68 |
| **Real** (floresta + corte) | NDVI | 0,963 | 12,03 |
| **Real** (floresta + corte) | VARI | **0,575** | 7,30 |
| **Real** (floresta + corte) | ExG | **0,614** | 7,54 |

η **inverte a ordem**: a cena homogênea (0,650) pontua *mais alto* que a cena com
desmatamento real detectado corretamente pelo VARI (0,575). Nenhum corte global em η
separa os dois casos.

### Causa

`σ²_entre` carrega o fator `ω·(1−ω)`, o produto das frações das duas classes:

- cena homogênea — Otsu parte 50/50 → `ω(1−ω) = 0,25`
- área desmatada ocupando 6% da cena → `ω(1−ω) = 0,056`

O fator derruba η por **desbalanceamento de classe**, não por má separação. E desmatamento
é, por natureza, a classe minoritária da cena — justamente o caso que interessa.

### Decisão 2

Julgar a confiabilidade pelo **tamanho de efeito padronizado** entre as duas classes:

```text
d = |μ_baixa − μ_alta| / sqrt[(σ²_baixa + σ²_alta) / 2]
```

Não contém o fator `ω(1−ω)`, logo é invariante ao tamanho relativo das classes.
Implementado em `limiar.distinguibilidade`; `limiar.limiar_confiavel` devolve o limiar,
o veredito e as duas métricas.

### Calibração do corte

O piso tem base teórica, não é arbitrário. Cortar uma distribuição normal única no ponto
ótimo produz duas meias-normais com médias em ±0,798σ e desvio 0,603σ:

```text
d_unimodal = 1,596σ / 0,603σ ≈ 2,65
```

Qualquer imagem unimodal atinge esse valor. O medido nas cenas homogêneas foi 2,68–2,69,
nos três índices — batendo com a previsão.

Como as cenas com desmatamento detectável ficaram entre 7,3 e 12,0, o corte foi posto em
**`DISTINGUIBILIDADE_MINIMA = 4.0`**, na folga entre os dois regimes.

> **Pendência:** reavaliar esse corte contra as imagens reais (requisito R032). A folga em
> dado real tende a ser menor que em cena sintética.

## Problema 3 — platô de limiares equivalentes

Quando não há pixel algum entre os dois modos, todo limiar dentro do vão produz a mesma
partição e portanto o mesmo `σ²_entre`. `np.argmax` devolve o primeiro do platô, encostando
o limiar na cauda do modo inferior — medido a 3,6σ de um modo e 16,4σ do outro.

### Decisão 3

Tomar o **centro do platô** de máximo. A partição resultante é idêntica no caso sintético,
mas a margem fica equilibrada para os dois lados, o que é mais robusto a cauda larga em
imagem real. Verificado em `test_limiar_fica_centrado_no_vao_entre_os_modos`.

## Consequências

- **Positiva:** o sistema recusa produzir máscara em floresta intacta, em vez de inventar
  desmatamento. É o falso positivo mais grave que este tipo de aplicação pode cometer.
- **Positiva:** dá ao grupo uma resposta concreta e mensurada para "como vocês sabem que o
  resultado é confiável?" na apresentação.
- **Negativa:** mais uma constante a justificar. Mitigado pelo piso teórico de 2,65.
- **Atenção:** os três valores (`DISTINGUIBILIDADE_MINIMA`, e a decisão de usar limiar
  conjunto) foram calibrados em **cena sintética**. Nenhum deles pode ir para o trabalho
  escrito como validado até rodar em imagem real.
