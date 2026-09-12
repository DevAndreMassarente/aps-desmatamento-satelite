"""Teste de fumaça da interface.

A demonstração ao vivo vale 30% da nota (R044, R050). Uma tela que quebra no seminário
não tem segunda chance, então o mínimo verificado aqui é: o script executa sem exceção,
mostra o número certo quando há desmatamento, e **se recusa** a mostrar número quando a
cena é homogênea.

Não testa aparência — testa que a interface não mente.
"""

from pathlib import Path

import pytest

streamlit_testing = pytest.importorskip(
    "streamlit.testing.v1", reason="interface requer o extra 'app'"
)
AppTest = streamlit_testing.AppTest

# Caminho absoluto: o `pytest` pode ser invocado de qualquer diretório.
CAMINHO = str(
    Path(__file__).resolve().parents[1] / "src" / "sentinela" / "app" / "principal.py"
)


@pytest.fixture
def app():
    teste = AppTest.from_file(CAMINHO, default_timeout=120)
    teste.run()
    return teste


class TestInterface:
    def test_executa_sem_excecao(self, app):
        assert not app.exception, [str(e.value) for e in app.exception]

    def test_apresenta_as_quatro_secoes(self, app):
        assert len(app.tabs) == 4

    def test_mostra_a_area_detectada(self, app):
        metricas = {m.label: m.value for m in app.metric}
        assert metricas["Área desmatada"] == "400 px"
        assert metricas["Em hectares"] == "4.00 ha"

    def test_declara_que_a_cena_e_sintetica(self, app):
        """`AGENTS.md` §11: imagem sintética precisa estar rotulada como tal na tela."""
        avisos = " ".join(i.value for i in app.info)
        assert "sintética" in avisos.lower()

    def test_cena_homogenea_recusa_reportar_area(self, app):
        alvo = next(s for s in app.slider if "desmatada" in s.label)
        alvo.set_value(0).run()

        assert not app.exception, [str(e.value) for e in app.exception]

        mensagens = " ".join(e.value for e in app.error)
        assert "não confiável" in mensagens.lower()

        rotulos = {m.label for m in app.metric}
        assert "Área desmatada" not in rotulos
        assert "Em hectares" not in rotulos

    def test_o_modelo_e_treinado_ou_explica_por_que_nao(self, app):
        """Na cena padrão o classificador roda; se a cena for pequena, avisa."""
        rotulos = {m.label for m in app.metric}
        avisos = " ".join(w.value for w in app.warning)

        assert "F1" in rotulos or "Modelo não treinado" in avisos

    def test_desempenho_perfeito_vem_acompanhado_de_ressalva(self, app):
        """Nunca exibir 1.000 sem dizer que a cena é sintética."""
        metricas = {m.label: m.value for m in app.metric}
        if metricas.get("F1") == "1.000":
            avisos = " ".join(w.value for w in app.warning)
            assert "perfeito" in avisos

    def test_ndmi_funciona_na_cena_sintetica(self, app):
        """A cena sintética traz banda SWIR, então o NDMI é demonstrável na tela."""
        seletor = next(s for s in app.sidebar.selectbox if "Índice" in s.label)
        assert "ndmi" in seletor.options

        seletor.set_value("ndmi").run()

        assert not app.exception, [str(e.value) for e in app.exception]
        assert not app.error, [e.value[:80] for e in app.error]
        assert {m.label for m in app.metric} >= {"Área desmatada", "Em hectares"}

    def test_upload_sem_arquivo_orienta_em_vez_de_quebrar(self, app):
        app.sidebar.radio[0].set_value("Enviar imagens").run()

        assert not app.exception, [str(e.value) for e in app.exception]
        avisos = " ".join(w.value for w in app.warning)
        assert "mesma área" in avisos
