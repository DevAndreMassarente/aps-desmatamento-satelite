"""Garante a restrição central do enunciado (p.3, item 3.a): os filtros são do grupo.

Dentro de ``src/sentinela/pdi/`` só são aceitos ``numpy``, módulos da biblioteca
padrão e imports relativos do próprio pacote ``pdi``. Qualquer outro import,
inclusive tardio (dentro de função), faz o teste falhar.
"""

import ast
import sys
from pathlib import Path

import pytest

PDI = Path(__file__).resolve().parents[1] / "src" / "sentinela" / "pdi"
ARQUIVOS = sorted(PDI.glob("*.py"))
PERMITIDOS = {"numpy"} | set(sys.stdlib_module_names)


def _raizes_importadas(arvore: ast.AST) -> list[str]:
    raizes = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            raizes += [alias.name.split(".")[0] for alias in no.names]
        elif isinstance(no, ast.ImportFrom) and no.level == 0:
            raizes.append((no.module or "").split(".")[0])
    return raizes


def test_pdi_tem_arquivos():
    assert ARQUIVOS, f"nenhum módulo encontrado em {PDI}"


@pytest.mark.parametrize("arquivo", ARQUIVOS, ids=lambda a: a.name)
def test_pdi_importa_apenas_numpy(arquivo):
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    proibidos = sorted(set(_raizes_importadas(arvore)) - PERMITIDOS)
    assert not proibidos, f"{arquivo.name} importa fora de numpy: {proibidos}"


@pytest.mark.parametrize("arquivo", ARQUIVOS, ids=lambda a: a.name)
def test_pdi_nao_importa_camadas_superiores(arquivo):
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    for no in ast.walk(arvore):
        if isinstance(no, ast.ImportFrom) and no.level > 1:
            pytest.fail(f"{arquivo.name} sobe além de pdi/ com import relativo")
        if isinstance(no, ast.ImportFrom) and no.level == 0:
            assert not (no.module or "").startswith("sentinela"), (
                f"{arquivo.name} importa de fora de pdi/"
            )
