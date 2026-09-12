"""Testes dos filtros espaciais.

Cada filtro é validado por uma propriedade matemática que ele tem que satisfazer,
independente da implementação.
"""

import numpy as np
import pytest

from sentinela.pdi import filtros
from sentinela.pdi.nucleo import ErroImagem


@pytest.fixture
def rampa():
    """Rampa horizontal: gradiente constante e analiticamente conhecido."""
    return np.tile(np.linspace(0.0, 1.0, 20, dtype=np.float32), (20, 1))


@pytest.fixture
def degrau():
    """Metade escura, metade clara — borda vertical única e nítida."""
    imagem = np.zeros((20, 20), dtype=np.float32)
    imagem[:, 10:] = 1.0
    return imagem


@pytest.fixture
def ruido_sal_pimenta():
    """Campo uniforme com pixels extremos isolados."""
    imagem = np.full((21, 21), 0.5, dtype=np.float32)
    imagem[5, 5] = 1.0
    imagem[10, 12] = 0.0
    imagem[15, 3] = 1.0
    return imagem


class TestKernels:
    def test_gaussiano_soma_um(self):
        """Se não somasse 1, o filtro alteraria o brilho médio da imagem."""
        for tamanho in (3, 5, 7, 9):
            assert filtros.kernel_gaussiano(tamanho).sum() == pytest.approx(1.0, abs=1e-6)

    def test_gaussiano_e_simetrico(self):
        kernel = filtros.kernel_gaussiano(7)
        assert np.allclose(kernel, kernel.T, atol=1e-7)
        assert np.allclose(kernel, kernel[::-1, :], atol=1e-7)

    def test_gaussiano_tem_maximo_no_centro(self):
        kernel = filtros.kernel_gaussiano(5)
        assert kernel[2, 2] == kernel.max()

    def test_sigma_maior_achata_o_kernel(self):
        estreito = filtros.kernel_gaussiano(9, sigma=0.8)
        largo = filtros.kernel_gaussiano(9, sigma=3.0)
        assert estreito[4, 4] > largo[4, 4]

    def test_media_soma_um(self):
        assert filtros.kernel_media(5).sum() == pytest.approx(1.0, abs=1e-6)

    def test_sobel_soma_zero(self):
        """Operador de derivada precisa anular região constante."""
        assert filtros.SOBEL_X.sum() == pytest.approx(0.0)
        assert filtros.SOBEL_Y.sum() == pytest.approx(0.0)

    def test_laplaciano_soma_zero(self):
        assert filtros.LAPLACIANO_4.sum() == pytest.approx(0.0)
        assert filtros.LAPLACIANO_8.sum() == pytest.approx(0.0)

    def test_tamanho_par_e_rejeitado(self):
        with pytest.raises(ErroImagem, match="ímpar"):
            filtros.kernel_gaussiano(4)

    def test_sigma_negativo_e_rejeitado(self):
        with pytest.raises(ErroImagem, match="sigma"):
            filtros.kernel_gaussiano(5, sigma=-1.0)


class TestSuavizacao:
    def test_gaussiano_preserva_regiao_constante(self):
        imagem = np.full((20, 20), 0.6, dtype=np.float32)
        saida = filtros.gaussiano(imagem, 5)
        assert np.allclose(saida, 0.6, atol=1e-5)

    def test_gaussiano_reduz_a_variancia(self):
        gerador = np.random.default_rng(3)
        imagem = gerador.random((30, 30)).astype(np.float32)
        assert filtros.gaussiano(imagem, 5).var() < imagem.var()

    def test_media_preserva_regiao_constante(self):
        imagem = np.full((20, 20), 0.25, dtype=np.float32)
        assert np.allclose(filtros.media(imagem, 3), 0.25, atol=1e-6)

    def test_mediana_remove_ruido_impulsivo(self, ruido_sal_pimenta):
        """É o ponto do filtro: outlier isolado some, o fundo não muda."""
        saida = filtros.mediana(ruido_sal_pimenta, 3)
        assert saida[5, 5] == pytest.approx(0.5)
        assert saida[10, 12] == pytest.approx(0.5)
        assert saida[15, 3] == pytest.approx(0.5)

    def test_mediana_preserva_a_borda_melhor_que_gaussiano(self, degrau):
        """A vantagem da mediana sobre o gaussiano, medida na transição."""
        gerador = np.random.default_rng(5)
        ruidoso = np.clip(degrau + gerador.normal(0, 0.05, degrau.shape), 0, 1).astype(
            np.float32
        )
        med = filtros.mediana(ruidoso, 3)
        gauss = filtros.gaussiano(ruidoso, 3)
        salto_mediana = abs(med[10, 10] - med[10, 9])
        salto_gaussiano = abs(gauss[10, 10] - gauss[10, 9])
        assert salto_mediana > salto_gaussiano

    def test_mediana_aceita_multibanda(self):
        imagem = np.full((10, 10, 3), 0.5, dtype=np.float32)
        imagem[5, 5, 0] = 1.0
        saida = filtros.mediana(imagem, 3)
        assert saida.shape == (10, 10, 3)
        assert saida[5, 5, 0] == pytest.approx(0.5)


class TestGradiente:
    def test_sobel_anula_regiao_constante(self):
        imagem = np.full((20, 20), 0.7, dtype=np.float32)
        gx, gy = filtros.gradiente(imagem, "sobel")
        assert np.allclose(gx, 0.0, atol=1e-6)
        assert np.allclose(gy, 0.0, atol=1e-6)

    def test_sobel_em_rampa_da_gradiente_constante(self, rampa):
        """Caso analítico: rampa linear tem derivada constante.

        Passo da rampa = 1/19. O kernel Sobel_x soma 8 unidades de peso positivo
        distribuídas sobre um deslocamento de 2 colunas, logo gx = 8 * passo / 2 * 2.
        Basta verificar a constância no miolo, longe do efeito de borda.
        """
        gx, _ = filtros.gradiente(rampa, "sobel")
        miolo = gx[5:-5, 5:-5]
        assert miolo.std() < 1e-5
        assert miolo.mean() > 0

    def test_gradiente_horizontal_nao_responde_a_variacao_horizontal(self, rampa):
        """Rampa só varia em x, então gy tem que ser nulo."""
        _, gy = filtros.gradiente(rampa, "sobel")
        assert np.allclose(gy[2:-2, 2:-2], 0.0, atol=1e-6)

    def test_magnitude_maxima_fica_na_borda(self, degrau):
        mag = filtros.magnitude_gradiente(degrau, "sobel")
        coluna_da_borda = int(np.argmax(mag.sum(axis=0)))
        assert coluna_da_borda in (9, 10)

    def test_prewitt_concorda_com_sobel_na_posicao_da_borda(self, degrau):
        """Os operadores diferem na ponderação, não em onde detectam a borda."""
        mag_sobel = filtros.magnitude_gradiente(degrau, "sobel")
        mag_prewitt = filtros.magnitude_gradiente(degrau, "prewitt")
        assert np.argmax(mag_sobel.sum(axis=0)) == np.argmax(mag_prewitt.sum(axis=0))

    def test_direcao_de_borda_vertical_e_horizontal(self, degrau):
        """Borda vertical tem gradiente apontando na horizontal (ângulo ≈ 0)."""
        direcao = filtros.direcao_gradiente(degrau, "sobel")
        na_borda = direcao[5:-5, 9:11]
        assert np.allclose(np.abs(na_borda), 0.0, atol=0.2)

    def test_operador_desconhecido_falha(self, rampa):
        with pytest.raises(ErroImagem, match="operador"):
            filtros.gradiente(rampa, "inexistente")


class TestRealce:
    def test_laplaciano_anula_regiao_constante(self):
        imagem = np.full((15, 15), 0.4, dtype=np.float32)
        assert np.allclose(filtros.laplaciano(imagem), 0.0, atol=1e-6)

    def test_laplaciano_anula_rampa_linear(self, rampa):
        """Derivada segunda de função linear é zero — no miolo, sem efeito de borda."""
        assert np.allclose(filtros.laplaciano(rampa)[3:-3, 3:-3], 0.0, atol=1e-5)

    def test_conectividade_invalida_falha(self, rampa):
        with pytest.raises(ErroImagem, match="conectividade"):
            filtros.laplaciano(rampa, conectividade=6)

    def test_nitidez_aumenta_o_contraste_local(self, degrau):
        """A medição precisa ser feita nas colunas que ladeiam a transição.

        Alguns pixels adiante o gaussiano já saturou em 0 e 1: ali o salto vale 1,0
        antes do realce e o recorte em [0,1] impede que cresça, o que mediria o
        recorte em vez do realce.
        """
        gauss = filtros.gaussiano(degrau, 5)
        realcada = filtros.nitidez(gauss, intensidade=1.5, tamanho=5)
        salto_antes = abs(gauss[10, 10] - gauss[10, 9])
        salto_depois = abs(realcada[10, 10] - realcada[10, 9])
        assert salto_depois > salto_antes

    def test_nitidez_com_intensidade_zero_nao_altera(self, degrau):
        assert np.allclose(filtros.nitidez(degrau, intensidade=0.0), degrau, atol=1e-6)

    def test_nitidez_mantem_a_faixa_valida(self, degrau):
        saida = filtros.nitidez(degrau, intensidade=5.0)
        assert saida.min() >= 0.0 and saida.max() <= 1.0

    def test_intensidade_negativa_e_rejeitada(self, degrau):
        with pytest.raises(ErroImagem, match="intensidade"):
            filtros.nitidez(degrau, intensidade=-1.0)


class TestEstatisticaLocal:
    def test_minimo_local_nunca_supera_a_imagem(self):
        gerador = np.random.default_rng(13)
        imagem = gerador.random((20, 20)).astype(np.float32)
        assert np.all(filtros.minimo_local(imagem, 3) <= imagem + 1e-6)

    def test_maximo_local_nunca_fica_abaixo_da_imagem(self):
        gerador = np.random.default_rng(17)
        imagem = gerador.random((20, 20)).astype(np.float32)
        assert np.all(filtros.maximo_local(imagem, 3) >= imagem - 1e-6)

    def test_desvio_local_e_zero_em_regiao_homogenea(self):
        imagem = np.full((20, 20), 0.5, dtype=np.float32)
        assert np.allclose(filtros.desvio_padrao_local(imagem, 5), 0.0, atol=1e-6)

    def test_desvio_local_separa_textura_de_area_lisa(self):
        """Base da feature de textura usada na etapa de modelo.

        Metade lisa (pasto/solo exposto), metade texturizada (dossel de floresta).
        """
        gerador = np.random.default_rng(19)
        imagem = np.full((30, 30), 0.5, dtype=np.float32)
        imagem[:, 15:] += gerador.normal(0, 0.15, (30, 15)).astype(np.float32)
        desvio = filtros.desvio_padrao_local(imagem, 5)
        assert desvio[10:20, 2:12].mean() < desvio[10:20, 18:28].mean()


class TestSeparabilidadeDoGaussiano:
    """A separabilidade é uma identidade algébrica, não uma aproximação.

    ``exp(-(x²+y²)/2σ²) = exp(-x²/2σ²)·exp(-y²/2σ²)`` — o expoente de uma soma vira
    produto de exponenciais. Estes testes fixam essa igualdade no código, porque é dela
    que vem o ganho de desempenho.
    """

    def test_kernel_1d_soma_um(self):
        for tamanho in (3, 5, 9, 15):
            assert filtros.kernel_gaussiano_1d(tamanho).sum() == pytest.approx(1.0)

    def test_produto_externo_reconstroi_o_kernel_2d(self):
        """A prova da separabilidade, em uma linha."""
        for tamanho in (3, 5, 9):
            linha = filtros.kernel_gaussiano_1d(tamanho).ravel()
            reconstruido = np.outer(linha, linha)
            assert reconstruido == pytest.approx(
                filtros.kernel_gaussiano(tamanho), abs=1e-6
            )

    def test_os_dois_caminhos_dao_o_mesmo_resultado(self):
        gerador = np.random.default_rng(3)
        imagem = gerador.random((60, 60)).astype(np.float32)

        for tamanho in (3, 5, 9, 15):
            direto = filtros.gaussiano(imagem, tamanho=tamanho, separavel=False)
            separado = filtros.gaussiano(imagem, tamanho=tamanho, separavel=True)
            assert separado == pytest.approx(direto, abs=1e-5), tamanho

    def test_equivalencia_vale_tambem_na_borda(self):
        """Onde a equivalência poderia falhar: o tratamento de borda de cada passe."""
        gerador = np.random.default_rng(4)
        imagem = gerador.random((40, 40)).astype(np.float32)

        for modo in ("reflete", "replica", "zero", "circular"):
            direto = filtros.gaussiano(imagem, tamanho=9, modo_borda=modo, separavel=False)
            separado = filtros.gaussiano(imagem, tamanho=9, modo_borda=modo, separavel=True)
            assert separado[:5, :] == pytest.approx(direto[:5, :], abs=1e-5), modo
            assert separado[:, :5] == pytest.approx(direto[:, :5], abs=1e-5), modo

    def test_equivalencia_vale_em_imagem_multibanda(self):
        gerador = np.random.default_rng(5)
        imagem = gerador.random((30, 30, 3)).astype(np.float32)

        direto = filtros.gaussiano(imagem, tamanho=5, separavel=False)
        separado = filtros.gaussiano(imagem, tamanho=5, separavel=True)
        assert separado == pytest.approx(direto, abs=1e-5)

    def test_sigma_explicito_tambem_e_separavel(self):
        gerador = np.random.default_rng(6)
        imagem = gerador.random((30, 30)).astype(np.float32)

        direto = filtros.gaussiano(imagem, tamanho=9, sigma=2.5, separavel=False)
        separado = filtros.gaussiano(imagem, tamanho=9, sigma=2.5, separavel=True)
        assert separado == pytest.approx(direto, abs=1e-5)

    def test_tamanho_par_e_recusado(self):
        with pytest.raises(ErroImagem, match="ímpar"):
            filtros.kernel_gaussiano_1d(4)

    def test_sigma_nao_positivo_e_recusado(self):
        with pytest.raises(ErroImagem, match="sigma"):
            filtros.kernel_gaussiano_1d(5, sigma=0)
