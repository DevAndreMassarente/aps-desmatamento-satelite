# Sentinela — detecção de desmatamento em imagens de satélite

APS de Processamento de Imagens e Visão Computacional — Ciência da Computação, UNIP, 2026/2.

O programa compara a mesma área em duas datas, segmenta a perda de vegetação e prepara recortes
rotulados para um modelo de visão computacional. Os filtros foram escritos pelo grupo, só com
NumPy.

**Status:** em desenvolvimento. O programa funciona na cena sintética. Nas imagens reais testadas
(MODIS e Sentinel-2), ele recusou quantificar a área.

## Onde está cada coisa

| Pasta ou arquivo | Conteúdo |
|------------------|----------|
| `entrega/` | Apresentações, falas e trabalho escrito |
| `src/` | Código do programa |
| `tests/` | Testes automatizados |
| `pyproject.toml`, `requirements.txt` | Dependências |
| `_interno/` | Enunciado, fontes do trabalho, dados, resultados, scripts e registros do projeto |
| `AGENTS.md`, `CLAUDE.md` | Instruções do assistente de IA, não versionadas no Git |

## Como executar

```bash
python -m venv .venv
.venv/bin/pip install -e ".[app]"
.venv/bin/sentinela app
```

Sem interface: `.venv/bin/sentinela demo`. Testes: `.venv/bin/python -m pytest`.

Detalhes completos: `_interno/docs/README-completo.md`.
