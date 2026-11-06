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
| `exemplos/` | Par de imagens Sentinel-2 para testar o programa |
| `instalar.sh` | Instala tudo depois do `git clone` |
| `_interno/` | Enunciado, fontes do trabalho, dados, resultados, scripts e registros do projeto |
| `AGENTS.md`, `CLAUDE.md` | Instruções do assistente de IA, não versionadas no Git |

## Como executar

Depois do `git clone`, na pasta do projeto:

```bash
./instalar.sh
.venv/bin/sentinela app
```

O `instalar.sh` cria o ambiente `.venv`, instala as dependências e roda os testes. Usa o `uv`
se estiver instalado; sem ele, precisa de Python 3.10 a 3.13. A interface abre em
`http://localhost:8501` e só aceita conexões desta máquina.

Para testar, envie as imagens da pasta `exemplos/`: a de 2018 em **Imagem antes** e a de 2024
em **Imagem depois**.

Sem interface: `.venv/bin/sentinela demo`. Testes: `.venv/bin/python -m pytest`.

Detalhes completos: `_interno/docs/README-completo.md`.
