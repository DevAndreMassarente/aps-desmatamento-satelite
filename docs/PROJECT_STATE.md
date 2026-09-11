# Project State

_Atualizado em marcos, não a cada alteração. Última atualização: bootstrap._

## Current Phase

**Bootstrap concluído.** Fundação do projeto (estrutura, documentação, núcleo de PDI e testes)
pronta. Próxima fase: Fase Intermediária I — Qualificação (R040), que o enunciado manda concluir
**antes** do desenvolvimento prático pesado.

## Completed

- Enunciado oficial lido integralmente e movido para `docs/enunciado/` (hash verificado).
- Transcrição do PDF gerada (`docs/enunciado/TRANSCRICAO.md`) — o PDF original quebra
  `pdftotext` por usar `ToUnicode` por fonte.
- 50 requisitos extraídos e rastreados em `docs/REQUIREMENTS.md`.
- Problema definido: detecção e quantificação de desmatamento em imagens de satélite.
- Arquitetura definida espelhando as cinco etapas nomeadas pelo enunciado.
- Estrutura de diretórios e configuração de projeto criadas.
- Núcleo de PDI implementado com NumPy puro: convolução, filtros, limiarização, morfologia,
  segmentação e índices de vegetação.
- Suíte de testes cobrindo os filtros contra casos analíticos conhecidos: **154 passando**.
- Achado metodológico durante o teste de integração: Otsu por data usa réguas diferentes, e
  a separabilidade η do artigo original não detecta cena homogênea. Resolvido com limiar
  conjunto e tamanho de efeito padronizado (`docs/decisions/003-limiar-bitemporal.md`).

## In Progress

- Nada em andamento. Aguardando definição de integrantes e resposta às perguntas em aberto.

## Next

Em ordem de prioridade:

1. **Levar as perguntas Q1–Q8 ao professor** (`docs/PROJECT_SPEC.md` → Open Questions).
   Q5 (modelo treinado vs. proposta teórica) muda o escopo do programa e trava o planejamento.
2. Selecionar a região de estudo e baixar o par de imagens bi-temporais reais; registrar em
   `data/raw/FONTES.md`.
3. Rodar o pipeline nas imagens reais e gerar as primeiras evidências em `docs/evidence/`.
4. Escrever Capítulo 1 + a parte de filtragem dos Capítulos 2 e 3 (**Fase Intermediária I**).
5. Construir a interface Streamlit para a demonstração.
6. Implementar a etapa de modelo.

## Blockers

| # | Bloqueio | Impacto |
|---|----------|---------|
| B1 | Integrantes do grupo não definidos (Q7) | Ficha de APS e capa |
| B2 | Escopo do modelo indefinido (Q5) | Dimensiona metade do esforço do programa |
| B3 | Datas de P1/P2 desconhecidas (Q3) | Sem cronograma real |
| B4 | Nenhuma imagem real baixada ainda | R032 não pode avançar |
| B5 | `DISTINGUIBILIDADE_MINIMA` calibrada só em cena sintética | Precisa ser reavaliada em imagem real antes de ir para o trabalho escrito |

## Known Issues

- O `python3-venv` desta máquina veio sem `ensurepip`, então `python3 -m venv` cria um
  ambiente sem `pip`. Contornado com `venv --without-pip` + `get-pip.py`. A correção
  definitiva é `sudo apt install python3-venv`, que precisa da senha do usuário.
  O ambiente atual está funcional com numpy 2.5.3 e pytest 9.1.1.
- `rasterio` é opcional e pode falhar de instalar (dependência nativa GDAL). O sistema degrada
  para PNG/JPEG sem ele, perdendo apenas a conversão de pixels para hectares.

## Important Decisions

| # | Decisão | Onde |
|---|---------|------|
| D1 | Filtros implementados do zero, só com NumPy | `docs/decisions/001-filtros-proprios.md` |
| D2 | Imagens não versionadas no Git | `docs/decisions/002-dados-nao-versionados.md` |
| D3 | Abordagem bi-temporal (duas datas da mesma área) em vez de imagem única | `docs/ARCHITECTURE.md` |
| D4 | Streamlit para a interface, pela demonstração ao vivo | `docs/PROJECT_SPEC.md` |
| D5 | Representação interna `float32` em `[0,1]` | `docs/ARCHITECTURE.md` |
| D6 | Limiar único para as duas datas + confiabilidade por tamanho de efeito | `docs/decisions/003-limiar-bitemporal.md` |
