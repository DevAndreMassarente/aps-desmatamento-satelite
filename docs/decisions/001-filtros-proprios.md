# 001 — Filtros implementados pelo grupo, com NumPy apenas

**Status:** Aceita
**Contexto:** Bootstrap do projeto

## Contexto

O enunciado (p.3, item 3.a) diz:

> "Os filtros devem ser desenvolvidos pelo grupo preferencialmente em linguagem Python e
> aplicados em imagens reais relacionadas ao problema escolhido."

A frase admite duas leituras:

1. **Restritiva:** o grupo escreve o algoritmo do filtro (a convolução, o kernel, o
   varrimento da janela) do zero.
2. **Permissiva:** o grupo "desenvolve" a solução escolhendo e encadeando filtros de
   biblioteca.

## Decisão

Adotar a leitura **restritiva**.

O núcleo de PDI (`src/sentinela/pdi/`) depende **apenas de `numpy`** e implementa do zero:
convolução 2D com tratamento de borda, filtros gaussiano/média/mediana, gradientes de
Sobel/Prewitt, Laplaciano, realce por máscara de nitidez, limiarização de Otsu, operadores
morfológicos e rotulagem de componentes conexos.

Ficam **proibidos dentro de `pdi/`**: `opencv-python`, `scikit-image`, `scipy.ndimage`, e os
filtros do `Pillow` (`PIL.ImageFilter`).

`Pillow` é permitido, mas exclusivamente para **I/O** (abrir e salvar PNG/JPEG), dentro de
`dataio/`.

`scikit-learn` é permitido na etapa de **modelo**, que é um item separado do enunciado
(p.3, item 3.b: "escolha algoritmos de inteligência adequados para imagens") e não carrega a
exigência de implementação própria.

## Justificativa

- É a leitura que satisfaz as duas interpretações ao mesmo tempo: um trabalho que implementa os
  filtros do zero também atende à leitura permissiva. O inverso não é verdade.
- O enunciado premia explicitamente "o nível de complexidade da técnica escolhida" (p.4, item
  II.2). Implementar convolução é matéria da disciplina, não acessório.
- Torna o capítulo 4.a do trabalho escrito ("descrever como foram implantados os métodos")
  possível de escrever com substância real.
- Sustenta a exigência de que o grupo consiga **defender** o que entregou.

## Por que NumPy não viola a decisão

NumPy é biblioteca de **álgebra de arrays**, não de processamento de imagens. Ele fornece
`array`, indexação e aritmética vetorizada — o equivalente a usar `list` e `for`, só que
rápido o bastante para processar uma cena de satélite em tempo de demonstração. Nenhuma
operação de PDI vem pronta dele: `numpy` não tem gaussiano, não tem Sobel, não tem Otsu.

Alternativa considerada e descartada: Python puro com listas aninhadas. Convolução 5×5 numa
imagem 2000×2000 levaria minutos, inviabilizando a demonstração ao vivo, sem nenhum ganho
acadêmico — o algoritmo demonstrado é o mesmo.

## Consequências

- **Positiva:** cada filtro é testável contra um caso analítico conhecido (`tests/`), o que
  alimenta o capítulo 4.c do trabalho escrito.
- **Positiva:** o grupo consegue responder "como esse filtro funciona?" apontando o código.
- **Negativa:** mais código para escrever e manter que a alternativa de biblioteca.
- **Negativa:** risco de bug sutil na implementação própria. Mitigado pelos testes e por um
  benchmark de corretude opcional contra implementação de referência, mantido **fora** de
  `pdi/` e claramente rotulado como validação — nunca como substituto.
