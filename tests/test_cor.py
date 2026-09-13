"""Testes de conversão de espaço de cor e índices de vegetação."""

import numpy as np
import pytest

from sentinela.pdi import cor
from sentinela.pdi.nucleo import ErroImagem


def pixel(r, g, b):
    """Imagem 1x1 com a cor informada, para checar conversões contra valores conhecidos."""
    return np.array([[[r, g, b]]], dtype=np.float32)


class TestEscalaDeCinza:
    def test_branco_vira_um_e_preto_vira_zero(self):
        assert cor.para_cinza(pixel(1, 1, 1))[0, 0] == pytest.approx(1.0)
        assert cor.para_cinza(pixel(0, 0, 0))[0, 0] == pytest.approx(0.0)

    def test_usa_os_pesos_de_luminancia(self):
        """Verde puro deve resultar em 0,587 — o coeficiente ITU-R BT.601."""
        assert cor.para_cinza(pixel(0, 1, 0))[0, 0] == pytest.approx(0.587, abs=1e-3)
        assert cor.para_cinza(pixel(1, 0, 0))[0, 0] == pytest.approx(0.299, abs=1e-3)
        assert cor.para_cinza(pixel(0, 0, 1))[0, 0] == pytest.approx(0.114, abs=1e-3)

    def test_saida_perde_o_eixo_de_bandas(self):
        assert cor.para_cinza(np.ones((8, 6, 3), dtype=np.float32)).shape == (8, 6)

    def test_pesos_customizados_sao_normalizados(self):
        """Pesos que não somam 1 não podem estourar a faixa."""
        saida = cor.para_cinza(pixel(1, 1, 1), pesos=(2.0, 2.0, 2.0))
        assert saida[0, 0] == pytest.approx(1.0)

    def test_imagem_cinza_e_rejeitada(self):
        with pytest.raises(ErroImagem, match="dimensões"):
            cor.para_cinza(np.ones((5, 5), dtype=np.float32))


class TestHSV:
    def test_vermelho_puro(self):
        h, s, v = cor.para_hsv(pixel(1, 0, 0))[0, 0]
        assert h == pytest.approx(0.0, abs=1e-4)
        assert s == pytest.approx(1.0)
        assert v == pytest.approx(1.0)

    def test_verde_puro_fica_em_um_terco(self):
        """120° / 360° = 1/3."""
        h, s, v = cor.para_hsv(pixel(0, 1, 0))[0, 0]
        assert h == pytest.approx(1 / 3, abs=1e-4)
        assert s == pytest.approx(1.0)

    def test_azul_puro_fica_em_dois_tercos(self):
        h, _, _ = cor.para_hsv(pixel(0, 0, 1))[0, 0]
        assert h == pytest.approx(2 / 3, abs=1e-4)

    def test_cinza_tem_saturacao_zero(self):
        _, s, v = cor.para_hsv(pixel(0.5, 0.5, 0.5))[0, 0]
        assert s == pytest.approx(0.0)
        assert v == pytest.approx(0.5)

    def test_preto_nao_divide_por_zero(self):
        h, s, v = cor.para_hsv(pixel(0, 0, 0))[0, 0]
        assert np.isfinite([h, s, v]).all()
        assert v == pytest.approx(0.0)

    def test_valor_e_o_maximo_das_bandas(self):
        gerador = np.random.default_rng(43)
        imagem = gerador.random((10, 10, 3)).astype(np.float32)
        hsv = cor.para_hsv(imagem)
        assert np.allclose(hsv[:, :, 2], imagem.max(axis=2), atol=1e-6)


class TestNDVI:
    def test_vegetacao_sadia_da_valor_alto(self):
        """NIR alto e vermelho baixo é a assinatura espectral de vegetação."""
        vermelho = np.array([[0.05]], dtype=np.float32)
        nir = np.array([[0.60]], dtype=np.float32)
        assert cor.ndvi(vermelho, nir)[0, 0] > 0.8

    def test_solo_exposto_da_valor_proximo_de_zero(self):
        """A assinatura do desmatamento: NIR e vermelho parecidos."""
        vermelho = np.array([[0.30]], dtype=np.float32)
        nir = np.array([[0.35]], dtype=np.float32)
        assert abs(cor.ndvi(vermelho, nir)[0, 0]) < 0.15

    def test_agua_da_valor_negativo(self):
        vermelho = np.array([[0.20]], dtype=np.float32)
        nir = np.array([[0.05]], dtype=np.float32)
        assert cor.ndvi(vermelho, nir)[0, 0] < 0

    def test_resultado_fica_na_faixa_menos_um_a_um(self):
        gerador = np.random.default_rng(47)
        vermelho = gerador.random((20, 20)).astype(np.float32)
        nir = gerador.random((20, 20)).astype(np.float32)
        resultado = cor.ndvi(vermelho, nir)
        assert resultado.min() >= -1.0 and resultado.max() <= 1.0

    def test_pixel_nulo_devolve_zero_em_vez_de_nan(self):
        """Sombra profunda zera as duas bandas; nan se propagaria até a segmentação."""
        zeros = np.zeros((5, 5), dtype=np.float32)
        resultado = cor.ndvi(zeros, zeros)
        assert np.all(np.isfinite(resultado))
        assert np.allclose(resultado, 0.0)

    def test_bandas_de_formatos_diferentes_falham(self):
        with pytest.raises(ErroImagem, match="formatos diferentes"):
            cor.ndvi(np.zeros((5, 5), dtype=np.float32), np.zeros((6, 6), dtype=np.float32))


class TestIndicesVisiveis:
    def test_exg_positivo_para_vegetacao(self):
        assert cor.exg(pixel(0.2, 0.6, 0.2))[0, 0] > 0

    def test_exg_negativo_para_solo_avermelhado(self):
        """Latossolo exposto, cor típica de área desmatada na Amazônia."""
        assert cor.exg(pixel(0.6, 0.4, 0.3))[0, 0] < 0

    def test_exg_zero_para_cinza(self):
        assert cor.exg(pixel(0.5, 0.5, 0.5))[0, 0] == pytest.approx(0.0, abs=1e-6)

    def test_vari_positivo_para_vegetacao(self):
        assert cor.vari(pixel(0.2, 0.6, 0.2))[0, 0] > 0

    def test_vari_negativo_para_solo(self):
        assert cor.vari(pixel(0.6, 0.4, 0.3))[0, 0] < 0

    def test_indices_nao_geram_nan_em_pixel_preto(self):
        preto = pixel(0, 0, 0)
        assert np.all(np.isfinite(cor.exg(preto)))
        assert np.all(np.isfinite(cor.vari(preto)))


class TestSelecaoDeIndice:
    def test_auto_usa_ndvi_quando_ha_infravermelho(self):
        imagem = np.full((5, 5, 3), 0.3, dtype=np.float32)
        nir = np.full((5, 5), 0.7, dtype=np.float32)
        _, metodo = cor.indice_vegetacao(imagem, nir, metodo="auto")
        assert metodo == "ndvi"

    def test_auto_cai_para_vari_sem_infravermelho(self):
        imagem = np.full((5, 5, 3), 0.3, dtype=np.float32)
        _, metodo = cor.indice_vegetacao(imagem, None, metodo="auto")
        assert metodo == "vari"

    def test_ndvi_sem_infravermelho_falha_com_orientacao(self):
        imagem = np.full((5, 5, 3), 0.3, dtype=np.float32)
        with pytest.raises(ErroImagem, match="B08"):
            cor.indice_vegetacao(imagem, None, metodo="ndvi")

    def test_metodo_desconhecido_falha(self):
        imagem = np.full((5, 5, 3), 0.3, dtype=np.float32)
        with pytest.raises(ErroImagem, match="desconhecido"):
            cor.indice_vegetacao(imagem, None, metodo="inexistente")

    def test_conversao_para_faixa_unitaria_preserva_a_ordem(self):
        indice = np.array([[-1.0, -0.5, 0.0, 0.5, 1.0]], dtype=np.float32)
        convertido = cor.para_faixa_unitaria(indice)
        assert convertido[0, 0] == pytest.approx(0.0)
        assert convertido[0, 2] == pytest.approx(0.5)
        assert convertido[0, 4] == pytest.approx(1.0)
        assert np.all(np.diff(convertido[0]) > 0)


class TestNdmi:
    """Índice de umidade — mede água do dossel, não verde.

    O caso que justifica sua existência é o último teste: floresta e pastagem vigorosa
    têm quase o mesmo NDVI, e NDMI bem diferente.
    """

    def test_dossel_umido_da_indice_alto(self):
        """Folha viva reflete no NIR e absorve no SWIR."""
        nir = np.full((8, 8), 0.55, dtype=np.float32)
        swir = np.full((8, 8), 0.10, dtype=np.float32)

        assert cor.ndmi(nir, swir).mean() == pytest.approx(0.692, abs=0.01)

    def test_superficie_seca_da_indice_baixo(self):
        """Solo exposto e pasto seco refletem bem no SWIR."""
        nir = np.full((8, 8), 0.30, dtype=np.float32)
        swir = np.full((8, 8), 0.38, dtype=np.float32)

        assert cor.ndmi(nir, swir).mean() < 0

    def test_fica_na_faixa_valida(self):
        gerador = np.random.default_rng(0)
        nir = gerador.random((32, 32)).astype(np.float32)
        swir = gerador.random((32, 32)).astype(np.float32)

        indice = cor.ndmi(nir, swir)
        assert indice.min() >= -1.0 and indice.max() <= 1.0

    def test_bandas_iguais_zeram_o_indice(self):
        banda = np.full((6, 6), 0.4, dtype=np.float32)
        assert cor.ndmi(banda, banda) == pytest.approx(0.0)

    def test_denominador_zero_nao_produz_nan(self):
        """Sombra e água profunda podem zerar as duas bandas."""
        zeros = np.zeros((5, 5), dtype=np.float32)
        indice = cor.ndmi(zeros, zeros)

        assert np.isfinite(indice).all()
        assert (indice == 0).all()

    def test_formatos_diferentes_sao_recusados(self):
        with pytest.raises(ErroImagem, match="formatos diferentes"):
            cor.ndmi(np.zeros((4, 4), np.float32), np.zeros((5, 5), np.float32))

    def test_separa_floresta_de_pastagem_melhor_que_o_ndvi(self):
        """A razão de existir do NDMI, em números.

        Floresta e pastagem vigorosa são as duas verdes: absorvem no vermelho e refletem
        no NIR, então o NDVI as distingue pouco. A diferença real está na água do dossel,
        que aparece no SWIR — a pastagem reflete muito mais ali.

        Com estas refletâncias o NDVI ainda separa 0,086; o NDMI separa 0,378. O ganho é
        de fator ~4, não uma diferença entre "nada" e "tudo".

        Valores de refletância de ordem de grandeza realista para dossel fechado e para
        capim em início de estação seca.
        """
        floresta = {"vermelho": 0.04, "nir": 0.48, "swir": 0.12}
        pastagem = {"vermelho": 0.06, "nir": 0.44, "swir": 0.28}

        campo = lambda valor: np.full((8, 8), valor, dtype=np.float32)

        ndvi_floresta = cor.ndvi(campo(floresta["vermelho"]), campo(floresta["nir"])).mean()
        ndvi_pastagem = cor.ndvi(campo(pastagem["vermelho"]), campo(pastagem["nir"])).mean()
        ndmi_floresta = cor.ndmi(campo(floresta["nir"]), campo(floresta["swir"])).mean()
        ndmi_pastagem = cor.ndmi(campo(pastagem["nir"]), campo(pastagem["swir"])).mean()

        separacao_ndvi = abs(ndvi_floresta - ndvi_pastagem)
        separacao_ndmi = abs(ndmi_floresta - ndmi_pastagem)

        assert separacao_ndvi < 0.10, "NDVI separa pouco"
        assert separacao_ndmi > 0.30, "NDMI separa bem"
        assert separacao_ndmi > 4 * separacao_ndvi, "o ganho é de fator ~4"


class TestNdmiPorIndiceVegetacao:
    def test_precisa_das_duas_bandas(self):
        imagem = np.zeros((8, 8, 3), dtype=np.float32)
        banda = np.zeros((8, 8), dtype=np.float32)

        with pytest.raises(ErroImagem, match="SWIR"):
            cor.indice_vegetacao(imagem, banda, metodo="ndmi")
        with pytest.raises(ErroImagem, match="infravermelho"):
            cor.indice_vegetacao(imagem, None, metodo="ndmi", swir=banda)

    def test_devolve_o_nome_do_metodo(self):
        imagem = np.zeros((8, 8, 3), dtype=np.float32)
        banda = np.full((8, 8), 0.5, dtype=np.float32)

        _, metodo = cor.indice_vegetacao(imagem, banda, metodo="ndmi", swir=banda)
        assert metodo == "ndmi"

    def test_automatico_nunca_escolhe_ndmi(self):
        """Trocar a grandeza medida sem o usuário pedir mudaria a interpretação."""
        imagem = np.zeros((8, 8, 3), dtype=np.float32)
        banda = np.full((8, 8), 0.5, dtype=np.float32)

        _, metodo = cor.indice_vegetacao(imagem, banda, metodo="auto", swir=banda)
        assert metodo == "ndvi"


class TestNbr:
    """NBR: a mesma conta do NDMI, com o SWIR 2 — outro índice, outro nome."""

    def test_tem_a_mesma_matematica_do_ndmi(self):
        """O que muda entre os dois é qual banda entra, não a fórmula."""
        gerador = np.random.default_rng(11)
        nir = gerador.random((16, 16)).astype(np.float32)
        swir = gerador.random((16, 16)).astype(np.float32)
        assert cor.nbr(nir, swir) == pytest.approx(cor.ndmi(nir, swir))

    def test_fica_na_faixa_valida_e_sem_nan(self):
        zeros = np.zeros((5, 5), dtype=np.float32)
        assert np.isfinite(cor.nbr(zeros, zeros)).all()

    def test_formatos_diferentes_sao_recusados(self):
        with pytest.raises(ErroImagem, match="formatos diferentes"):
            cor.nbr(np.zeros((4, 4), np.float32), np.zeros((5, 5), np.float32))

    def test_indice_vegetacao_devolve_o_nome_nbr(self):
        imagem = np.zeros((8, 8, 3), dtype=np.float32)
        banda = np.full((8, 8), 0.5, dtype=np.float32)
        _, metodo = cor.indice_vegetacao(imagem, banda, metodo="nbr", swir=banda)
        assert metodo == "nbr"

    def test_mensagem_de_erro_aponta_a_banda_certa_do_modis(self):
        """A versão anterior dizia que o SWIR do NDMI no MODIS era a banda 7 — errado."""
        imagem = np.zeros((8, 8, 3), dtype=np.float32)
        banda = np.zeros((8, 8), dtype=np.float32)
        with pytest.raises(ErroImagem, match="banda 6 no MODIS"):
            cor.indice_vegetacao(imagem, banda, metodo="ndmi")
        with pytest.raises(ErroImagem, match="banda 7 no MODIS"):
            cor.indice_vegetacao(imagem, banda, metodo="nbr")

    def test_automatico_nunca_escolhe_nbr(self):
        imagem = np.zeros((8, 8, 3), dtype=np.float32)
        banda = np.full((8, 8), 0.5, dtype=np.float32)
        _, metodo = cor.indice_vegetacao(imagem, banda, metodo="auto", swir=banda)
        assert metodo == "ndvi"
