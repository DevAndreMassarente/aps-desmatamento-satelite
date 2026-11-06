"""Testes da fronteira de entrada e saída.

O que importa verificar aqui não é o Pillow — é que a conversão de faixa acontece na
fronteira e que entrada inválida produz erro explicável, não exceção crua vazando de
uma biblioteca (R036).
"""

import numpy as np
import pytest

from sentinela.dataio import imagem as io
from sentinela.dataio import visual
from sentinela.dataio.imagem import ErroArquivo
from sentinela.dataio.sintetico import cena_sintetica, par_bitemporal


@pytest.fixture
def cena(tmp_path):
    rgb, _ = cena_sintetica(7, corte=(slice(10, 30), slice(10, 30)))
    caminho = tmp_path / "cena.png"
    io.salvar(caminho, rgb)
    return caminho, rgb


class TestCarregar:
    def test_ida_e_volta_preserva_a_imagem(self, cena):
        caminho, original = cena
        recarregada = io.carregar(caminho)

        assert recarregada.shape == original.shape
        assert recarregada.dtype == np.float32
        # Tolerância de meio passo de quantização: uint8 tem 1/255 de resolução.
        assert np.abs(recarregada - original).max() < 1.0 / 255

    def test_carrega_na_faixa_unitaria(self, cena):
        recarregada = io.carregar(cena[0])
        assert recarregada.min() >= 0.0
        assert recarregada.max() <= 1.0

    def test_cinza_devolve_duas_dimensoes(self, cena):
        assert io.carregar(cena[0], cinza=True).ndim == 2

    def test_arquivo_inexistente_tem_mensagem_util(self, tmp_path):
        with pytest.raises(ErroArquivo, match="não encontrado"):
            io.carregar(tmp_path / "nao-existe.png")

    def test_arquivo_que_nao_e_imagem(self, tmp_path):
        falso = tmp_path / "texto.png"
        falso.write_text("isto não é uma imagem")

        with pytest.raises(ErroArquivo, match="não é uma imagem"):
            io.carregar(falso)

    def test_diretorio_no_lugar_de_arquivo(self, tmp_path):
        with pytest.raises(ErroArquivo, match="não é um arquivo"):
            io.carregar(tmp_path)


class TestCarregarComInfravermelho:
    def test_quarta_banda_vira_infravermelho(self, tmp_path):
        from PIL import Image

        rgba = np.zeros((6, 5, 4), dtype=np.uint8)
        rgba[..., 0], rgba[..., 3] = 51, 204
        caminho = tmp_path / "data.png"
        Image.fromarray(rgba, "RGBA").save(caminho)

        rgb, nir = io.carregar_com_infravermelho(caminho)
        assert rgb.shape == (6, 5, 3) and nir.shape == (6, 5)
        assert np.allclose(rgb[..., 0], 0.2) and np.allclose(nir, 0.8)

    def test_tres_bandas_nao_tem_infravermelho(self, cena):
        caminho, _ = cena
        rgb, nir = io.carregar_com_infravermelho(caminho)
        assert rgb.ndim == 3 and nir is None


class TestCarregarPar:
    def test_recortes_diferentes_sao_recusados(self, tmp_path):
        io.salvar(tmp_path / "a.png", cena_sintetica(1, tamanho=(40, 40))[0])
        io.salvar(tmp_path / "b.png", cena_sintetica(2, tamanho=(60, 60))[0])

        with pytest.raises(ErroArquivo, match="mesmo recorte"):
            io.carregar_par(tmp_path / "a.png", tmp_path / "b.png")

    def test_par_valido_passa(self, tmp_path):
        io.salvar(tmp_path / "a.png", cena_sintetica(1)[0])
        io.salvar(tmp_path / "b.png", cena_sintetica(2)[0])

        antes, depois = io.carregar_par(tmp_path / "a.png", tmp_path / "b.png")
        assert antes.shape == depois.shape


class TestSalvar:
    def test_cria_o_diretorio_de_destino(self, tmp_path):
        destino = tmp_path / "fundo" / "do" / "poco" / "m.png"
        io.salvar(destino, np.zeros((10, 10), dtype=np.float32))
        assert destino.exists()

    def test_mascara_booleana_vira_preto_e_branco(self, tmp_path):
        mascara = np.zeros((10, 10), dtype=bool)
        mascara[2:5, 2:5] = True

        recarregada = io.carregar(io.salvar(tmp_path / "m.png", mascara), cinza=True)
        assert recarregada[3, 3] == pytest.approx(1.0)
        assert recarregada[8, 8] == pytest.approx(0.0)

    def test_numero_de_bandas_invalido_e_recusado(self, tmp_path):
        with pytest.raises(ErroArquivo, match="bandas"):
            io.salvar(tmp_path / "x.png", np.zeros((8, 8, 5), dtype=np.float32))


class TestSintetico:
    def test_area_esperada_bate_com_o_corte_construido(self):
        par = par_bitemporal(corte=(slice(10, 30), slice(5, 25)))
        assert par["area_esperada"] == 400

    def test_sem_corte_nao_ha_area(self):
        assert par_bitemporal(corte=None)["area_esperada"] == 0

    def test_floresta_reflete_mais_no_infravermelho_que_no_vermelho(self):
        """Premissa radiométrica que torna o NDVI significativo."""
        rgb, nir = cena_sintetica(3)
        assert nir.mean() > rgb[:, :, 0].mean()

    def test_a_area_cortada_tem_ndvi_menor_que_a_floresta(self):
        corte = (slice(20, 40), slice(20, 40))
        rgb, nir = cena_sintetica(4, corte=corte)
        ndvi = (nir - rgb[:, :, 0]) / (nir + rgb[:, :, 0])

        assert ndvi[25:35, 25:35].mean() < ndvi[5:15, 5:15].mean() - 0.3

    def test_o_par_traz_a_banda_swir(self):
        par = par_bitemporal()
        assert par["swir_antes"].shape == par["nir_antes"].shape
        assert par["swir_depois"].shape == par["nir_depois"].shape

    def test_swir_inverte_o_comportamento_do_nir(self):
        """Dossel absorve no SWIR; solo exposto reflete. É o oposto do NIR."""
        from sentinela.dataio.sintetico import banda_swir

        corte = (slice(20, 40), slice(20, 40))
        swir = banda_swir(5, corte=corte)
        _, nir = cena_sintetica(5, corte=corte)

        assert swir[25:35, 25:35].mean() > swir[5:15, 5:15].mean()
        assert nir[25:35, 25:35].mean() < nir[5:15, 5:15].mean()

    def test_o_swir_nao_altera_a_cena_existente(self):
        """`cena_sintetica` é verdade de terreno em dezenas de testes: não pode mudar."""
        antes = cena_sintetica(77)
        par_bitemporal(semente=77)
        depois = cena_sintetica(77)

        assert np.array_equal(antes[0], depois[0])
        assert np.array_equal(antes[1], depois[1])

    def test_a_mesma_semente_produz_a_mesma_cena(self):
        assert np.array_equal(cena_sintetica(9)[0], cena_sintetica(9)[0])


class TestVisual:
    def test_sobreposicao_pinta_dentro_e_preserva_fora(self):
        rgb, _ = cena_sintetica(11)
        mascara = np.zeros((80, 80), dtype=bool)
        mascara[30:50, 30:50] = True

        composta = visual.sobrepor_mascara(rgb, mascara, cor=(1.0, 0.0, 0.0))

        dentro = composta[35:45, 35:45]
        assert dentro[:, :, 0].mean() > dentro[:, :, 1].mean() + 0.3
        # Fora da máscara a cena continua sendo vegetação: verde acima de vermelho.
        fora = composta[5:15, 5:15]
        assert fora[:, :, 1].mean() > fora[:, :, 0].mean()

    def test_sobreposicao_recusa_mascara_de_tamanho_errado(self):
        rgb, _ = cena_sintetica(12)
        with pytest.raises(ValueError, match="não corresponde"):
            visual.sobrepor_mascara(rgb, np.zeros((10, 10), dtype=bool))

    def test_intensidade_fora_da_faixa_e_recusada(self):
        rgb, _ = cena_sintetica(13)
        with pytest.raises(ValueError, match="intensidade"):
            visual.sobrepor_mascara(rgb, np.zeros((80, 80), bool), intensidade=1.5)

    def test_mapa_de_mudanca_usa_uma_cor_por_classe(self):
        forma = (20, 20)
        mudanca = {
            "perda": np.zeros(forma, bool),
            "ganho": np.zeros(forma, bool),
            "estavel_vegetado": np.zeros(forma, bool),
            "estavel_nao_vegetado": np.ones(forma, bool),
        }
        mudanca["perda"][0:5, :] = True
        mudanca["estavel_nao_vegetado"][0:5, :] = False

        mapa = visual.mapa_de_mudanca(mudanca)
        assert tuple(mapa[2, 2]) == pytest.approx(visual.COR_PERDA)
        assert tuple(mapa[15, 2]) == pytest.approx(visual.COR_ESTAVEL_EXPOSTO)

    def test_mapa_de_mudanca_exige_as_quatro_classes(self):
        with pytest.raises(ValueError, match="faltam as classes"):
            visual.mapa_de_mudanca({"perda": np.zeros((4, 4), bool)})

    def test_falsa_cor_vai_de_marrom_a_verde(self):
        rampa = np.linspace(0, 1, 100, dtype=np.float32).reshape(10, 10)
        colorido = visual.indice_em_falsa_cor(rampa)

        baixo, alto = colorido[0, 0], colorido[9, 9]
        assert baixo[0] > baixo[1]  # marrom: vermelho acima de verde
        assert alto[1] > alto[0]  # verde: verde acima de vermelho


class TestRealcarPar:
    def test_mesma_regua_para_as_duas_datas(self):
        antes = np.full((4, 4, 3), 0.1, dtype=np.float32)
        depois = np.full((4, 4, 3), 0.3, dtype=np.float32)
        a, b = visual.realcar_par(antes, depois, percentis=(0.0, 100.0))
        assert np.allclose(a, 0.0) and np.allclose(b, 1.0)

    def test_saida_na_faixa_unitaria(self):
        rng = np.random.default_rng(0)
        a, b = visual.realcar_par(rng.random((8, 8, 3)) * 0.4, rng.random((8, 8, 3)) * 0.4)
        assert a.min() >= 0 and b.max() <= 1
