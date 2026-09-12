"""Testes das funções puras do script de aquisição.

Nada aqui toca a rede: o que se verifica é a lógica que decide se uma cena presta e a
transformação que prepara a composição para o pipeline. Foram justamente essas duas que
falharam na primeira tentativa de usar imagem real, e é por isso que têm teste.
"""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

_caminho = Path(__file__).resolve().parents[1] / "scripts" / "baixar_imagens.py"
_spec = importlib.util.spec_from_file_location("baixar_imagens", _caminho)
aquisicao = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(aquisicao)


class TestComposicaoParaAnalise:
    """O GIBS entrega (SWIR, NIR, vermelho); o núcleo espera o vermelho no canal 0."""

    def test_inverte_a_ordem_das_bandas(self):
        bands721 = np.zeros((4, 4, 3), dtype=np.uint8)
        bands721[:, :, 0] = 10  # banda 7 — SWIR
        bands721[:, :, 1] = 20  # banda 2 — NIR
        bands721[:, :, 2] = 30  # banda 1 — vermelho

        analise = aquisicao.composicao_para_analise(bands721)

        assert (analise[:, :, 0] == 30).all(), "canal 0 precisa ser o vermelho"
        assert (analise[:, :, 1] == 20).all(), "canal 1 precisa ser o NIR"
        assert (analise[:, :, 2] == 10).all(), "canal 2 precisa ser o SWIR"

    def test_nao_altera_nenhum_valor(self):
        original = np.random.default_rng(0).integers(0, 255, (8, 8, 3), dtype=np.uint8)
        analise = aquisicao.composicao_para_analise(original)

        assert sorted(np.unique(analise).tolist()) == sorted(np.unique(original).tolist())

    def test_devolve_copia_independente(self):
        original = np.ones((4, 4, 3), dtype=np.uint8)
        analise = aquisicao.composicao_para_analise(original)
        analise[0, 0, 0] = 99

        assert original[0, 0, 2] == 1


class TestQualidade:
    @staticmethod
    def _cena(valor, forma=(20, 20, 3)):
        return np.full(forma, valor, dtype=np.uint8)

    def test_detecta_area_sem_dado(self):
        cena = self._cena(120)
        cena[:10] = 0  # metade sem granulo

        medida = aquisicao.avaliar_qualidade(cena, cena)
        assert medida["ausente"] == pytest.approx(0.5)

    def test_detecta_nuvem(self):
        cena = self._cena(120)
        cena[:5] = 240  # clara nas tres bandas

        medida = aquisicao.avaliar_qualidade(cena, cena)
        assert medida["nuvem"] == pytest.approx(0.25)

    def test_bruma_e_medida_na_composicao_visivel(self):
        """A lição que custou uma rodada: o SWIR atravessa fumaça.

        A cena de análise (Bands721) parece limpa mesmo sob fumaça, porque a banda 7 a
        atravessa. A bruma tem que ser medida na visível, onde o espalhamento aparece.
        """
        analise_limpa = self._cena(120)
        visivel_com_fumaca = self._cena(120)
        visivel_com_fumaca[:, :, 2] = 200  # azul levantado por espalhamento

        medida = aquisicao.avaliar_qualidade(visivel_com_fumaca, analise_limpa)

        assert medida["nuvem"] == 0.0, "a composição de análise passa no teste de nuvem"
        assert medida["bruma_p05_azul"] > aquisicao.BRUMA_SUSPEITA

    def test_cena_limpa_passa_nos_tres_criterios(self):
        gerador = np.random.default_rng(1)
        cena = gerador.integers(5, 150, (40, 40, 3), dtype=np.uint8)

        medida = aquisicao.avaliar_qualidade(cena, cena)

        assert medida["ausente"] < 0.01
        assert medida["nuvem"] == 0.0
        assert medida["bruma_p05_azul"] < aquisicao.BRUMA_SUSPEITA


class TestResolucao:
    def test_recorte_de_um_grau_em_440_pixels(self):
        """1° de latitude ≈ 111.320 m; em 440 px dá ~253 m/px."""
        metros = aquisicao.metros_por_pixel((-7.0, -52.5, -6.0, -51.5), 440)
        assert metros == pytest.approx(253.0, abs=0.5)

    def test_mais_pixels_no_mesmo_recorte_aumenta_a_resolucao(self):
        bbox = (-7.0, -52.5, -6.0, -51.5)
        assert aquisicao.metros_por_pixel(bbox, 880) < aquisicao.metros_por_pixel(bbox, 440)


class TestRegioes:
    def test_toda_regiao_tem_bbox_e_as_duas_datas(self):
        for nome, config in aquisicao.REGIOES.items():
            assert len(config["bbox"]) == 4, nome
            assert config["antes"] < config["depois"], nome
            assert config["descricao"], nome

    def test_as_datas_sao_da_mesma_estacao(self):
        """Comparar julho com janeiro mediria estação, não desmatamento."""
        for nome, config in aquisicao.REGIOES.items():
            mes_antes = int(config["antes"].split("-")[1])
            mes_depois = int(config["depois"].split("-")[1])
            assert abs(mes_antes - mes_depois) <= 1, nome

    def test_nenhuma_data_cai_no_pico_das_queimadas(self):
        """Agosto e setembro na Amazônia: fumaça derruba o NDVI da cena inteira."""
        for nome, config in aquisicao.REGIOES.items():
            for rotulo in ("antes", "depois"):
                mes = int(config[rotulo].split("-")[1])
                assert mes not in (8, 9), f"{nome}/{rotulo} cai na estação de queimadas"
