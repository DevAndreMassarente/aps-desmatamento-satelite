# 002 — Imagens de satélite não vão para o Git

**Status:** Aceita
**Contexto:** Bootstrap do projeto

## Contexto

O projeto precisa de imagens reais (enunciado p.3, item 3.a). Cenas Sentinel-2 e Landsat são
grandes: uma cena Sentinel-2 completa passa de 500 MB, e mesmo recortes de trabalho ficam na
casa de dezenas de MB cada. O repositório é privado no GitHub, que tem limite prático de
100 MB por arquivo e degrada com histórico pesado.

## Decisão

`data/raw/`, `data/interim/` e `data/processed/` ficam no `.gitignore`.

Em vez dos dados, o repositório versiona:

1. `data/raw/FONTES.md` — de onde cada imagem veio (satélite, data, coordenadas, produto,
   licença), de forma que qualquer integrante reproduza o download.
2. `scripts/baixar_dados.py` — utilitário de download, quando a fonte permitir automação.
3. Amostras pequenas usadas em teste, se necessárias, em `tests/fixtures/` — geradas por código
   sempre que possível, em vez de commitadas.

Os **resultados** que entram no trabalho escrito (imagem de saída de cada etapa, gráficos,
screenshots) vão versionados em `docs/evidence/`, porque são pequenos e são a evidência
exigida pelos requisitos R015 e R033.

## Justificativa

- Mantém o clone rápido para todos os integrantes.
- Evita estourar limite do GitHub no meio do semestre, com o histórico já sujo.
- Licenciamento: dados Copernicus/INPE são abertos, mas redistribuir cena inteira em repositório
  acadêmico é desnecessário quando a origem é pública e estável.

## Consequências

- **Positiva:** repositório leve; histórico limpo.
- **Negativa:** um integrante que clone o repositório não roda nada até baixar as imagens.
  Mitigado pelo `FONTES.md` e pelo README, que descrevem o passo explicitamente.
- **Atenção:** a reprodutibilidade do resultado depende de as fontes continuarem no ar. Por isso
  `docs/evidence/results/` guarda as saídas que sustentam o trabalho escrito — se a fonte sair
  do ar, a evidência do que foi feito permanece.
