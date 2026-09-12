"""Testes da orquestração.

A cadeia já é verificada peça a peça em `test_filtros`, `test_segmentacao` e
`test_integracao`. O que se verifica aqui é o que só o pipeline pode errar: a ordem das
etapas, a propagação dos parâmetros, a recusa a reportar área quando a detecção não é
confiável, e a validação de entradas incompatíveis.

As cenas são **sintéticas** — ver `dataio/sintetico.py`.
"""

import numpy as np
import pytest

from sentinela.dataio.sintetico import cena_sintetica, par_bitemporal
from sentinela.pdi.nucleo import ErroImagem
from sentinela.pipeline import amostras as am
from sentinela.pipeline.deteccao import detectar_desmatamento, preparar_indice

CORTE = (slice(30, 50), slice(30, 50))  # 400 pixels


@pytest.fixture
def resultado():
    par = par_bitemporal(corte=CORTE)
    return detectar_desmatamento(
        par["rgb_antes"], par["rgb_depois"], par["nir_antes"], par["nir_depois"],
        metros_por_pixel=10.0,
    )


class TestDeteccao:
    def test_quantifica_a_area_construida(self, resultado):
        assert resultado.confiavel
        assert resultado.area_pixels == pytest.approx(400, rel=0.10)

    def test_converte_para_hectares(self, resultado):
        """400 px a 10 m/px = 40.000 m² = 4 ha."""
        assert resultado.area_hectares == pytest.approx(4.0, rel=0.10)

    def test_sem_resolucao_nao_ha_hectares(self):
        par = par_bitemporal(corte=CORTE)
        sem_escala = detectar_desmatamento(
            par["rgb_antes"], par["rgb_depois"], par["nir_antes"], par["nir_depois"]
        )
        assert sem_escala.area_hectares is None
        assert sem_escala.resumo()["area_hectares"] is None
        assert sem_escala.area_pixels > 0  # a medida em pixels continua válida

    def test_a_perda_fica_onde_o_corte_foi_construido(self, resultado):
        assert resultado.perda[35:45, 35:45].mean() > 0.9
        assert resultado.perda[5:15, 5:15].mean() < 0.05

    def test_usa_ndvi_com_infravermelho_e_vari_sem(self):
        par = par_bitemporal(corte=CORTE)
        com = detectar_desmatamento(
            par["rgb_antes"], par["rgb_depois"], par["nir_antes"], par["nir_depois"]
        )
        sem = detectar_desmatamento(par["rgb_antes"], par["rgb_depois"])

        assert com.metodo_indice == "ndvi"
        assert sem.metodo_indice == "vari"
        assert sem.confiavel  # degradação para o visível continua detectando

    def test_ndmi_quantifica_a_mesma_area_que_o_ndvi(self):
        """Índices diferentes, mesma verdade de terreno."""
        par = par_bitemporal(corte=CORTE)
        com_ndmi = detectar_desmatamento(
            par["rgb_antes"], par["rgb_depois"], par["nir_antes"], par["nir_depois"],
            swir_antes=par["swir_antes"], swir_depois=par["swir_depois"],
            metodo="ndmi", metros_por_pixel=10.0,
        )

        assert com_ndmi.metodo_indice == "ndmi"
        assert com_ndmi.confiavel
        assert com_ndmi.area_pixels == pytest.approx(400, rel=0.10)

    def test_o_limiar_e_unico_para_as_duas_datas(self, resultado):
        """A régua única é o que torna as duas máscaras comparáveis."""
        from sentinela.pdi import limiar

        separado = limiar.otsu(resultado.indice_antes)
        assert abs(separado - resultado.valor_limiar) > 0.05
        # E o mesmo valor governa as duas máscaras:
        assert (resultado.vegetacao_antes == (resultado.indice_antes > resultado.valor_limiar)).mean() > 0.98

    def test_regioes_vem_ordenadas_da_maior_para_a_menor(self):
        par = par_bitemporal(corte=None)
        duplo = par["rgb_depois"].copy()
        nir_duplo = par["nir_depois"].copy()
        for fatia, tamanho in (((slice(10, 30), slice(10, 30)), 20),
                               ((slice(50, 58), slice(50, 58)), 8)):
            duplo[fatia] = cena_sintetica(1, corte=fatia)[0][fatia]
            nir_duplo[fatia] = cena_sintetica(1, corte=fatia)[1][fatia]

        resultado = detectar_desmatamento(
            par["rgb_antes"], duplo, par["nir_antes"], nir_duplo, area_minima=10
        )
        areas = [r.area_pixels for r in resultado.regioes]
        assert areas == sorted(areas, reverse=True)
        assert len(areas) >= 2

    def test_area_minima_descarta_fragmentos(self):
        par = par_bitemporal(corte=(slice(30, 34), slice(30, 34)))  # 16 px
        com_filtro = detectar_desmatamento(
            par["rgb_antes"], par["rgb_depois"], par["nir_antes"], par["nir_depois"],
            area_minima=100,
        )
        assert com_filtro.area_pixels == 0

    def test_parametros_ficam_registrados_no_resultado(self, resultado):
        """Sem os parâmetros gravados, o resultado não é reproduzível."""
        assert resultado.parametros["suavizacao"] == 5
        assert resultado.parametros["area_minima"] == 25


class TestRecusaHonesta:
    """O caso que mais gera falso positivo em campo: cena homogênea."""

    @pytest.fixture
    def homogenea(self):
        par = par_bitemporal(corte=None)
        return detectar_desmatamento(
            par["rgb_antes"], par["rgb_depois"], par["nir_antes"], par["nir_depois"],
            metros_por_pixel=10.0,
        )

    def test_floresta_intacta_e_marcada_nao_confiavel(self, homogenea):
        assert not homogenea.confiavel

    def test_resumo_omite_a_area_quando_nao_confiavel(self, homogenea):
        resumo = homogenea.resumo()
        assert resumo["area_pixels"] is None
        assert resumo["area_hectares"] is None
        assert resumo["regioes_detectadas"] is None

    def test_a_mascara_continua_disponivel_para_inspecao(self, homogenea):
        """Recusar o número não é o mesmo que esconder o que o algoritmo fez."""
        assert homogenea.perda is not None
        assert homogenea.mudanca["perda"].shape == (80, 80)

    def test_ganho_desproporcional_levanta_alerta_de_registro(self, homogenea):
        assert homogenea.alerta_de_registro


class TestValidacaoDeEntrada:
    def test_recortes_de_tamanhos_diferentes(self):
        a, _ = cena_sintetica(1, tamanho=(40, 40))
        b, _ = cena_sintetica(2, tamanho=(60, 60))
        with pytest.raises(ErroImagem, match="mesmo recorte"):
            detectar_desmatamento(a, b)

    def test_infravermelho_em_apenas_uma_data(self):
        par = par_bitemporal(corte=CORTE)
        with pytest.raises(ErroImagem, match="nas duas datas ou em nenhuma"):
            detectar_desmatamento(par["rgb_antes"], par["rgb_depois"], par["nir_antes"])

    def test_infravermelho_com_formato_incompativel(self):
        par = par_bitemporal(corte=CORTE)
        with pytest.raises(ErroImagem, match="diferente do RGB"):
            detectar_desmatamento(
                par["rgb_antes"], par["rgb_depois"],
                np.zeros((10, 10), np.float32), np.zeros((10, 10), np.float32),
            )

    def test_swir_em_apenas_uma_data(self):
        par = par_bitemporal(corte=CORTE)
        with pytest.raises(ErroImagem, match="SWIR precisa estar"):
            detectar_desmatamento(
                par["rgb_antes"], par["rgb_depois"], par["nir_antes"], par["nir_depois"],
                swir_antes=par["nir_antes"],
            )

    def test_swir_com_formato_incompativel(self):
        par = par_bitemporal(corte=CORTE)
        errado = np.zeros((10, 10), np.float32)
        with pytest.raises(ErroImagem, match="diferente do RGB"):
            detectar_desmatamento(
                par["rgb_antes"], par["rgb_depois"], par["nir_antes"], par["nir_depois"],
                swir_antes=errado, swir_depois=errado,
            )

    def test_ndmi_sem_swir_e_recusado_com_explicacao(self):
        par = par_bitemporal(corte=CORTE)
        with pytest.raises(ErroImagem, match="SWIR"):
            detectar_desmatamento(
                par["rgb_antes"], par["rgb_depois"], par["nir_antes"], par["nir_depois"],
                metodo="ndmi",
            )

    def test_imagem_em_tons_de_cinza_e_recusada(self):
        """O índice de vegetação precisa de bandas separadas."""
        cinza = np.zeros((40, 40), dtype=np.float32)
        with pytest.raises(ErroImagem, match="dimensões"):
            detectar_desmatamento(cinza, cinza)

    def test_area_minima_negativa(self):
        par = par_bitemporal(corte=CORTE)
        with pytest.raises(ErroImagem, match="area_minima"):
            detectar_desmatamento(par["rgb_antes"], par["rgb_depois"], area_minima=-1)

    def test_resolucao_nao_positiva(self):
        par = par_bitemporal(corte=CORTE)
        with pytest.raises(ErroImagem, match="metros_por_pixel"):
            detectar_desmatamento(
                par["rgb_antes"], par["rgb_depois"], metros_por_pixel=0
            )


class TestPrepararIndice:
    def test_suavizacao_reduz_a_variacao_local(self):
        rgb, nir = cena_sintetica(21)
        bruto, _ = preparar_indice(rgb, nir, suavizacao=1)
        suave, _ = preparar_indice(rgb, nir, suavizacao=5)

        assert suave.std() < bruto.std()

    def test_indice_sai_na_faixa_unitaria(self):
        rgb, nir = cena_sintetica(22, corte=CORTE)
        indice, _ = preparar_indice(rgb, nir)
        assert indice.min() >= 0.0 and indice.max() <= 1.0


class TestAmostras:
    @pytest.fixture
    def conjunto(self, resultado):
        par = par_bitemporal(corte=CORTE)
        return am.extrair_amostras(par["rgb_depois"], resultado.perda, lado=16, passo=8)

    def test_extrai_as_duas_classes(self, conjunto):
        contagens = conjunto.contagem_por_classe
        assert contagens[am.DESMATADO] > 0
        assert contagens[am.INTACTO] > 0

    def test_recortes_tem_o_formato_pedido(self, conjunto):
        assert conjunto.recortes.shape[1:] == (16, 16, 3)

    def test_recortes_ambiguos_sao_descartados(self, conjunto):
        """Rotular a borda do corte ensinaria o modelo a olhar a vizinhança."""
        assert conjunto.descartados_ambiguos > 0

    def test_amostra_desmatada_tem_ndvi_menor(self, conjunto):
        """O rótulo tem que corresponder ao conteúdo do recorte, não só à posição."""
        desmatados = conjunto.recortes[conjunto.rotulos == am.DESMATADO]
        intactos = conjunto.recortes[conjunto.rotulos == am.INTACTO]
        # No solo exposto o vermelho sobe; na floresta ele é baixo.
        assert desmatados[:, :, :, 0].mean() > intactos[:, :, :, 0].mean() + 0.1

    def test_posicoes_permitem_reencontrar_a_amostra(self, conjunto):
        assert len(conjunto.posicoes) == len(conjunto)
        linha, coluna = conjunto.posicoes[0]
        assert 0 <= linha <= 80 - 16 and 0 <= coluna <= 80 - 16

    def test_equilibrar_iguala_as_classes(self, conjunto):
        equilibrado = am.equilibrar(conjunto)
        contagens = equilibrado.contagem_por_classe
        assert contagens[am.INTACTO] == contagens[am.DESMATADO]
        assert equilibrado.equilibrio == 1.0

    def test_equilibrar_nao_inventa_amostra(self, conjunto):
        equilibrado = am.equilibrar(conjunto)
        assert len(equilibrado) <= len(conjunto)
        assert set(equilibrado.posicoes).issubset(set(conjunto.posicoes))

    def test_equilibrar_com_uma_classe_so_devolve_o_conjunto(self):
        par = par_bitemporal(corte=None)
        vazio = am.extrair_amostras(par["rgb_depois"], np.zeros((80, 80), bool))
        assert am.equilibrar(vazio).contagem_por_classe[am.DESMATADO] == 0

    def test_mascara_incompativel_e_recusada(self):
        rgb, _ = cena_sintetica(31)
        with pytest.raises(ErroImagem, match="não corresponde"):
            am.extrair_amostras(rgb, np.zeros((10, 10), bool))

    def test_recorte_maior_que_a_imagem(self):
        rgb, _ = cena_sintetica(32, tamanho=(40, 40))
        with pytest.raises(ErroImagem, match="não cabe"):
            am.extrair_amostras(rgb, np.zeros((40, 40), bool), lado=64)

    def test_limiares_de_cobertura_invertidos(self):
        rgb, _ = cena_sintetica(33)
        with pytest.raises(ErroImagem, match="cobertura"):
            am.extrair_amostras(
                rgb, np.zeros((80, 80), bool),
                cobertura_desmatado=0.1, cobertura_intacto=0.9,
            )
