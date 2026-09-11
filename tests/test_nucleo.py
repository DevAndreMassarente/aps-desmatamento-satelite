"""Testes do núcleo de PDI.

Estratégia: validar contra **casos analíticos conhecidos**, nunca contra a saída de
outra biblioteca. Um teste que compara com `cv2` só provaria que copiamos o `cv2`;
um teste que verifica que a convolução com kernel identidade devolve a imagem original
prova que a convolução está certa.
"""

import numpy as np
import pytest

from sentinela.pdi import nucleo
from sentinela.pdi.nucleo import ErroImagem


@pytest.fixture
def rampa():
    """Rampa horizontal linear: cada coluna vale col/9. Gradiente conhecido e constante."""
    return np.tile(np.linspace(0.0, 1.0, 10, dtype=np.float32), (10, 1))


@pytest.fixture
def aleatoria():
    gerador = np.random.default_rng(42)
    return gerador.random((12, 15)).astype(np.float32)


class TestConversaoDeFaixa:
    def test_uint8_vira_zero_um(self):
        entrada = np.array([[0, 128, 255]], dtype=np.uint8)
        saida = nucleo.para_float(entrada)
        assert saida.dtype == np.float32
        assert saida[0, 0] == pytest.approx(0.0)
        assert saida[0, 2] == pytest.approx(1.0)
        assert saida[0, 1] == pytest.approx(128 / 255, abs=1e-6)

    def test_uint16_usa_o_maximo_do_tipo(self):
        """Sentinel-2 entrega uint16 — dividir por 255 estouraria a faixa."""
        entrada = np.array([[0, 65535]], dtype=np.uint16)
        saida = nucleo.para_float(entrada)
        assert saida[0, 1] == pytest.approx(1.0)

    def test_ida_e_volta_uint8_preserva_valores(self):
        entrada = np.array([[0, 1, 127, 128, 254, 255]], dtype=np.uint8)
        assert np.array_equal(nucleo.para_uint8(nucleo.para_float(entrada)), entrada)

    def test_float_fora_da_faixa_e_recortado(self):
        entrada = np.array([[-0.5, 0.5, 1.5]], dtype=np.float32)
        saida = nucleo.para_float(entrada)
        assert saida.min() >= 0.0 and saida.max() <= 1.0


class TestBorda:
    def test_reflete_espelha(self):
        imagem = np.array([[1.0, 2.0, 3.0]], dtype=np.float32)
        saida = nucleo.aplicar_borda(imagem, (0, 2), "reflete")
        assert np.allclose(saida[0], [3.0, 2.0, 1.0, 2.0, 3.0, 2.0, 1.0])

    def test_replica_repete_a_borda(self):
        imagem = np.array([[1.0, 2.0, 3.0]], dtype=np.float32)
        saida = nucleo.aplicar_borda(imagem, (0, 2), "replica")
        assert np.allclose(saida[0], [1.0, 1.0, 1.0, 2.0, 3.0, 3.0, 3.0])

    def test_zero_preenche_com_zero(self):
        imagem = np.ones((1, 3), dtype=np.float32)
        saida = nucleo.aplicar_borda(imagem, (0, 1), "zero")
        assert saida[0, 0] == 0.0 and saida[0, -1] == 0.0

    def test_multibanda_nao_estende_o_eixo_de_bandas(self):
        imagem = np.ones((4, 4, 3), dtype=np.float32)
        saida = nucleo.aplicar_borda(imagem, (1, 1), "reflete")
        assert saida.shape == (6, 6, 3)

    def test_modo_desconhecido_falha(self):
        with pytest.raises(ErroImagem, match="modo de borda"):
            nucleo.aplicar_borda(np.ones((3, 3), dtype=np.float32), (1, 1), "inexistente")


class TestCorrelacaoEConvolucao:
    def test_kernel_identidade_preserva_a_imagem(self, aleatoria):
        identidade = np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]], dtype=np.float32)
        assert np.allclose(nucleo.correlacionar(aleatoria, identidade), aleatoria)

    def test_saida_tem_o_formato_da_entrada(self, aleatoria):
        kernel = np.ones((5, 5), dtype=np.float32) / 25.0
        assert nucleo.correlacionar(aleatoria, kernel).shape == aleatoria.shape

    def test_kernel_que_soma_um_preserva_imagem_constante(self):
        """Propriedade fundamental: filtro normalizado não altera o brilho médio."""
        imagem = np.full((8, 8), 0.42, dtype=np.float32)
        kernel = np.ones((3, 3), dtype=np.float32) / 9.0
        assert np.allclose(nucleo.correlacionar(imagem, kernel), 0.42, atol=1e-6)

    def test_convolucao_inverte_o_kernel_assimetrico(self, rampa):
        """Convolução ≠ correlação quando o kernel não é simétrico."""
        kernel = np.array([[0, 0, 0], [-1, 0, 1], [0, 0, 0]], dtype=np.float32)
        corr = nucleo.correlacionar(rampa, kernel)
        conv = nucleo.convoluir(rampa, kernel)
        assert np.allclose(conv, -corr, atol=1e-6)

    def test_convolucao_iguala_correlacao_em_kernel_simetrico(self, aleatoria):
        kernel = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], dtype=np.float32) / 16.0
        assert np.allclose(
            nucleo.convoluir(aleatoria, kernel),
            nucleo.correlacionar(aleatoria, kernel),
            atol=1e-6,
        )

    def test_multibanda_processa_cada_banda(self):
        imagem = np.zeros((6, 6, 3), dtype=np.float32)
        imagem[:, :, 0] = 1.0
        kernel = np.ones((3, 3), dtype=np.float32) / 9.0
        saida = nucleo.correlacionar(imagem, kernel)
        assert saida.shape == (6, 6, 3)
        assert np.allclose(saida[:, :, 0], 1.0, atol=1e-6)
        assert np.allclose(saida[:, :, 1], 0.0, atol=1e-6)

    def test_kernel_par_e_rejeitado(self, aleatoria):
        with pytest.raises(ErroImagem, match="ímpares"):
            nucleo.correlacionar(aleatoria, np.ones((2, 2), dtype=np.float32))

    def test_kernel_1d_e_rejeitado(self, aleatoria):
        with pytest.raises(ErroImagem, match="2D"):
            nucleo.correlacionar(aleatoria, np.ones(3, dtype=np.float32))


class TestJanelaDeslizante:
    def test_formato_empilhado(self, aleatoria):
        janelas = nucleo.janela_deslizante(aleatoria, 3)
        assert janelas.shape == (9, *aleatoria.shape)

    def test_posicao_central_e_a_propria_imagem(self, aleatoria):
        janelas = nucleo.janela_deslizante(aleatoria, 3)
        assert np.allclose(janelas[4], aleatoria)

    def test_tamanho_par_e_rejeitado(self, aleatoria):
        with pytest.raises(ErroImagem, match="ímpar"):
            nucleo.janela_deslizante(aleatoria, 4)


class TestNormalizacao:
    def test_leva_para_zero_um(self, aleatoria):
        saida = nucleo.normalizar(aleatoria * 7.0 - 3.0)
        assert saida.min() == pytest.approx(0.0)
        assert saida.max() == pytest.approx(1.0)

    def test_imagem_constante_nao_divide_por_zero(self):
        saida = nucleo.normalizar(np.full((5, 5), 0.3, dtype=np.float32))
        assert np.all(np.isfinite(saida))
        assert np.allclose(saida, 0.0)

    def test_alongamento_ignora_valor_extremo_isolado(self):
        """Um pixel saturado não pode comprimir toda a faixa útil."""
        imagem = np.full((10, 10), 0.5, dtype=np.float32)
        imagem[0, 0] = 100.0
        saida = nucleo.alongar_contraste(imagem, 2.0, 98.0)
        assert saida.max() <= 1.0
        assert np.count_nonzero(saida > 0.99) < 5

    def test_percentis_invertidos_falham(self, aleatoria):
        with pytest.raises(ErroImagem, match="percentis inválidos"):
            nucleo.alongar_contraste(aleatoria, 90.0, 10.0)


class TestHistograma:
    def test_contagem_total_bate_com_o_numero_de_pixels(self, aleatoria):
        contagens, centros = nucleo.histograma(aleatoria, 64)
        assert contagens.sum() == aleatoria.size
        assert len(centros) == 64

    def test_equalizacao_espalha_a_faixa(self):
        """Imagem de baixo contraste deve ocupar mais da faixa após equalizar."""
        gerador = np.random.default_rng(7)
        imagem = (gerador.random((40, 40)) * 0.2 + 0.4).astype(np.float32)
        saida = nucleo.equalizar_histograma(imagem)
        assert saida.max() - saida.min() > imagem.max() - imagem.min()

    def test_equalizacao_preserva_a_ordem_dos_pixels(self):
        """Equalização é monotônica: pixel mais claro continua mais claro."""
        gerador = np.random.default_rng(11)
        imagem = gerador.random((20, 20)).astype(np.float32)
        saida = nucleo.equalizar_histograma(imagem)
        ordem_entrada = np.argsort(imagem, axis=None)
        valores = saida.flatten()[ordem_entrada]
        assert np.all(np.diff(valores) >= -1e-6)


class TestValidacao:
    def test_lista_python_e_rejeitada(self):
        with pytest.raises(ErroImagem, match="numpy.ndarray"):
            nucleo.validar_imagem([[1, 2], [3, 4]])

    def test_array_vazio_e_rejeitado(self):
        with pytest.raises(ErroImagem, match="vazia"):
            nucleo.validar_imagem(np.zeros((0, 5), dtype=np.float32))

    def test_4d_e_rejeitado(self):
        with pytest.raises(ErroImagem, match="dimensões"):
            nucleo.validar_imagem(np.zeros((2, 2, 2, 2), dtype=np.float32))
