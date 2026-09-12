# Demonstração — cena SINTÉTICA

> ## ⚠️ Estas imagens NÃO são de satélite.
>
> Foram geradas por `src/sentinela/dataio/sintetico.py`. **Não podem ser usadas como
> evidência no trabalho escrito** e não atendem ao requisito R032, que exige a aplicação
> dos filtros em imagens reais do problema escolhido.
>
> `AGENTS.md` §11 proíbe apresentar imagem fabricada como real.

## Para que servem

Verificar a cadeia de processamento contra uma verdade de terreno **conhecida**: a área
desmatada foi construída com tamanho exato, então o erro da detecção é mensurável.

## Como foram geradas

```bash
sentinela demo --saida docs/evidence/demo-sintetica --tamanho 120 --area 30
```

Reproduzível: a cena é determinística por semente.

## Resultado

| | |
|---|---|
| Verdade de terreno | 900 pixels (corte de 30×30) |
| Detectado | ver `resumo.json` |
| Resolução assumida | 10 m/pixel (Sentinel-2) |

## Arquivos

| Arquivo | Etapa do enunciado |
|---------|--------------------|
| `01-antes.png`, `02-depois.png` | 1 — Aquisição |
| `03-indice-antes.png`, `04-indice-depois.png` | 2 — Manipulação (índice de vegetação) |
| `05-vegetacao-antes.png`, `06-vegetacao-depois.png` | 4 — Segmentação (limiar de Otsu) |
| `07-mapa-mudanca.png` | 4 — Segmentação (comparação bi-temporal) |
| `08-perda-detectada.png` | 4 — Segmentação (após filtro de área) |
| `09-sobreposicao.png` | Apresentação do resultado |
| `resumo.json` | Métricas da execução |

O efeito da **filtragem** (etapa 3) é visível comparando o índice bruto com o suavizado
na interface (`sentinela app`), aba *Etapas do processamento*.
