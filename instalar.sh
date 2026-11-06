#!/usr/bin/env bash
# Prepara o Sentinela depois do `git clone`: cria o ambiente .venv, instala as dependências
# e roda os testes. Ao terminar, abra a interface com:
#
#     .venv/bin/sentinela app
#
# Uso:  ./instalar.sh              instala e testa
#       ./instalar.sh --sem-testes instala sem rodar os testes
#
# Usa o uv, se estiver instalado, para criar o ambiente com Python 3.12. Sem o uv, usa o
# Python do sistema (3.10 a 3.13). Nada é instalado fora da pasta do projeto.

set -euo pipefail
cd "$(dirname "$0")"

RODAR_TESTES=1
[[ "${1:-}" == "--sem-testes" ]] && RODAR_TESTES=0

passo() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
falha() { printf '\n\033[31mErro:\033[0m %s\n' "$1" >&2; exit 1; }

if [[ -d .venv ]]; then
  passo "Já existe um ambiente .venv; ele será reaproveitado"
fi

if command -v uv >/dev/null 2>&1 && [[ -z "${SENTINELA_SEM_UV:-}" ]]; then
  passo "Criando o ambiente com uv (Python 3.12)"
  [[ -d .venv ]] || uv venv --python 3.12 .venv
  passo "Instalando as dependências"
  uv pip install --python .venv/bin/python -e ".[app,modelo,dev]"
else
  PYTHON=""
  for candidato in python3.12 python3.13 python3.11 python3.10 python3; do
    if command -v "$candidato" >/dev/null 2>&1; then
      versao=$("$candidato" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
      menor=${versao#3.}
      if [[ ${versao%%.*} == 3 && $menor -ge 10 && $menor -le 13 ]]; then
        PYTHON=$candidato
        break
      fi
    fi
  done
  if [[ -z "$PYTHON" ]]; then
    falha "não encontrei Python 3.10 a 3.13. No Garuda/Arch, instale o uv (sudo pacman -S uv) e rode este script de novo: ele baixa o Python 3.12 só para o projeto."
  fi
  passo "Criando o ambiente com $PYTHON ($versao)"
  [[ -d .venv ]] || "$PYTHON" -m venv .venv
  passo "Instalando as dependências"
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -e ".[app,modelo,dev]"
fi

if [[ $RODAR_TESTES == 1 ]]; then
  passo "Rodando os testes"
  .venv/bin/python -m pytest -q -p no:cacheprovider || falha "os testes falharam; veja a saída acima."
fi

passo "Pronto"
cat <<'FIM'
Para abrir a interface:

    .venv/bin/sentinela app

Ela abre em http://localhost:8501. Para testar, envie as imagens da pasta exemplos/:
a de 2018 em "Imagem antes" e a de 2024 em "Imagem depois".
FIM
