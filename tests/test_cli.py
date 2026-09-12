"""Testes da linha de comando.

Foco no gerador de apêndice: ele produz um entregável acadêmico (Capítulo 7, R018) e
precisa corresponder exatamente ao código que está no repositório.
"""

from pathlib import Path

import pytest

from sentinela import cli

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def apendice(tmp_path):
    destino = tmp_path / "apendice.md"
    assert cli.main(["apendice", "--saida", str(destino)]) == 0
    return destino, destino.read_text(encoding="utf-8")


class TestApendice:
    def test_gera_o_arquivo(self, apendice):
        destino, texto = apendice
        assert destino.exists()
        assert texto.startswith("# 7. Apêndice")

    def test_inclui_todo_o_nucleo_de_pdi(self, apendice):
        """O núcleo é o que o enunciado exige que seja do grupo: não pode faltar."""
        _, texto = apendice
        for modulo in ("nucleo", "cor", "filtros", "limiar", "morfologia", "segmentacao"):
            assert f"sentinela/pdi/{modulo}.py" in texto, modulo

    def test_o_codigo_no_apendice_e_o_codigo_do_repositorio(self, apendice):
        """A razão de o apêndice ser gerado e não copiado."""
        _, texto = apendice
        fonte = (RAIZ / "src" / "sentinela" / "pdi" / "filtros.py").read_text(
            encoding="utf-8"
        )
        # uma assinatura distintiva, que só existe se o conteúdo real foi embutido
        assert "def kernel_gaussiano_1d(" in fonte
        assert "def kernel_gaussiano_1d(" in texto

    def test_o_nucleo_vem_antes_de_quem_o_consome(self, apendice):
        """Ordem de leitura: quem for ler o apêndice começa pela base."""
        _, texto = apendice
        assert texto.index("## `sentinela/pdi/nucleo.py`") < texto.index(
            "## `sentinela/pipeline/deteccao.py`"
        )

    def test_declara_a_contagem_de_arquivos_e_linhas(self, apendice):
        _, texto = apendice
        assert "**Total:" in texto and "arquivos," in texto

    def test_avisa_para_nao_editar_a_mao(self, apendice):
        _, texto = apendice
        assert "Não editar à mão" in texto

    def test_nao_inclui_arquivo_de_cache(self, apendice):
        """Nenhum arquivo compilado entra como seção.

        A verificação é sobre os **cabeçalhos de seção**, não sobre o texto inteiro: a
        palavra `__pycache__` aparece legitimamente no corpo, porque o próprio `cli.py`
        contém a linha que filtra esses diretórios.
        """
        _, texto = apendice
        secoes = [l for l in texto.splitlines() if l.startswith("## `sentinela/")]

        assert secoes
        for secao in secoes:
            assert "__pycache__" not in secao
            assert secao.endswith('.py`')


class TestParser:
    def test_todo_subcomando_tem_funcao(self):
        parser = cli.construir_parser()
        acoes = [a for a in parser._actions if hasattr(a, "choices") and a.choices]
        assert acoes, "nenhum subcomando registrado"
        for nome, sub in acoes[0].choices.items():
            assert sub.get_default("funcao") is not None, nome

    def test_comando_desconhecido_falha(self):
        with pytest.raises(SystemExit):
            cli.main(["inexistente"])
