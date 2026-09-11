"""Testes de limiarização, morfologia e rotulagem de regiões.

Aqui os casos são construídos com a resposta conhecida de antemão: uma imagem com
duas regiões separadas tem que produzir exatamente dois rótulos; um quadrado 5×5 tem
área 25 pixels; um buraco cercado tem que ser preenchido.
"""

import numpy as np
import pytest

from sentinela.pdi import limiar, morfologia, segmentacao
from sentinela.pdi.nucleo import ErroImagem


@pytest.fixture
def bimodal():
    """Histograma com dois modos bem separados: 0,2 e 0,8.

    É o caso ideal para Otsu, e aproxima o histograma de um índice de vegetação numa
    cena com floresta e área desmatada.
    """
    gerador = np.random.default_rng(23)
    escuro = gerador.normal(0.2, 0.04, 2000)
    claro = gerador.normal(0.8, 0.04, 2000)
    return np.clip(np.concatenate([escuro, claro]).reshape(40, 100), 0, 1).astype(np.float32)


@pytest.fixture
def duas_regioes():
    """Máscara com dois quadrados isolados: 3×3 e 5×5."""
    mascara = np.zeros((20, 20), dtype=bool)
    mascara[2:5, 2:5] = True
    mascara[10:15, 10:15] = True
    return mascara


class TestOtsu:
    def test_limiar_cai_entre_os_dois_modos(self, bimodal):
        assert 0.3 < limiar.otsu(bimodal) < 0.7

    def test_binarizacao_separa_as_duas_metades(self, bimodal):
        mascara, valor = limiar.otsu_binarizar(bimodal)
        proporcao = mascara.mean()
        assert 0.4 < proporcao < 0.6
        assert 0.3 < valor < 0.7

    def test_inverter_troca_a_classe_selecionada(self, bimodal):
        normal, _ = limiar.otsu_binarizar(bimodal, inverter=False)
        invertida, _ = limiar.otsu_binarizar(bimodal, inverter=True)
        assert np.array_equal(normal, ~invertida)

    def test_imagem_constante_falha_com_mensagem_clara(self):
        """Cena homogênea não tem limiar significativo — falhar é melhor que inventar."""
        with pytest.raises(ErroImagem, match="constante"):
            limiar.otsu(np.full((20, 20), 0.5, dtype=np.float32))

    def test_poucas_faixas_e_rejeitado(self, bimodal):
        with pytest.raises(ErroImagem, match="faixas"):
            limiar.otsu(bimodal, faixas=1)


class TestLimiarConjunto:
    def test_combina_os_histogramas_das_duas_imagens(self, bimodal):
        """Metades separadas devem produzir o mesmo limiar que a imagem inteira."""
        metade_escura = bimodal[:20]
        metade_clara = bimodal[20:]
        conjunto, _ = limiar.otsu_conjunto(metade_escura, metade_clara)
        assert conjunto == pytest.approx(limiar.otsu(bimodal), abs=0.02)

    def test_uma_imagem_bimodal_basta_para_definir_o_limiar(self):
        """O ponto do limiar conjunto: uma cena homogênea não estraga o par.

        A asserção é sobre a classificação resultante, não sobre o valor do limiar:
        com um vão vazio entre os modos, toda uma faixa de limiares é igualmente ótima.
        """
        gerador = np.random.default_rng(53)
        homogenea = np.clip(gerador.normal(0.8, 0.03, (40, 40)), 0, 1).astype(np.float32)
        bimodal = np.clip(
            np.concatenate(
                [gerador.normal(0.2, 0.03, 800), gerador.normal(0.8, 0.03, 800)]
            ).reshape(40, 40),
            0,
            1,
        ).astype(np.float32)

        conjunto, _ = limiar.otsu_conjunto(homogenea, bimodal)

        assert 0.2 < conjunto < 0.8
        assert (bimodal > conjunto).mean() == pytest.approx(0.5, abs=0.02)
        assert (homogenea > conjunto).mean() == pytest.approx(1.0, abs=0.01)

    def test_limiar_fica_centrado_no_vao_entre_os_modos(self):
        """Com um vão vazio, todo limiar dentro dele é igualmente ótimo.

        Escolher o centro do platô, em vez do primeiro valor que `argmax` encontraria,
        deixa margem equilibrada para os dois modos — mais robusto a cauda larga em
        imagem real.
        """
        gerador = np.random.default_rng(71)
        imagem = np.clip(
            np.concatenate(
                [gerador.normal(0.2, 0.02, 800), gerador.normal(0.8, 0.02, 800)]
            ).reshape(40, 40),
            0,
            1,
        ).astype(np.float32)

        valor = limiar.otsu(imagem)
        margem_inferior = valor - imagem[imagem < 0.5].max()
        margem_superior = imagem[imagem > 0.5].min() - valor

        assert margem_inferior > 0 and margem_superior > 0
        assert margem_inferior == pytest.approx(margem_superior, abs=0.05)

    def test_sem_imagem_falha(self):
        with pytest.raises(ErroImagem, match="ao menos uma imagem"):
            limiar.otsu_conjunto()


class TestDistinguibilidade:
    def test_classes_bem_separadas_dao_efeito_alto(self, bimodal):
        assert limiar.distinguibilidade(bimodal, limiar.otsu(bimodal)) > 8.0

    def test_distribuicao_unimodal_fica_no_piso_teorico(self):
        """Partir uma normal no ponto ótimo dá d ≈ 2,65, independente da escala.

        É esse piso que impede usar d cru como prova de bimodalidade.
        """
        gerador = np.random.default_rng(59)
        unimodal = np.clip(gerador.normal(0.5, 0.05, (60, 60)), 0, 1).astype(np.float32)
        efeito = limiar.distinguibilidade(unimodal, limiar.otsu(unimodal))
        assert efeito == pytest.approx(limiar.DISTINGUIBILIDADE_UNIMODAL, abs=0.3)

    def test_piso_nao_depende_da_escala_da_distribuicao(self):
        gerador = np.random.default_rng(61)
        estreita = np.clip(gerador.normal(0.5, 0.01, (60, 60)), 0, 1).astype(np.float32)
        larga = np.clip(gerador.normal(0.5, 0.12, (60, 60)), 0, 1).astype(np.float32)
        assert limiar.distinguibilidade(estreita, limiar.otsu(estreita)) == pytest.approx(
            limiar.distinguibilidade(larga, limiar.otsu(larga)), abs=0.3
        )

    def test_classe_vazia_devolve_zero(self, bimodal):
        assert limiar.distinguibilidade(bimodal, 5.0) == 0.0

    def test_limiar_confiavel_aprova_caso_bimodal(self, bimodal):
        _, confiavel, metricas = limiar.limiar_confiavel(bimodal)
        assert confiavel
        assert metricas["distinguibilidade"] >= limiar.DISTINGUIBILIDADE_MINIMA
        assert "separabilidade" in metricas

    def test_limiar_confiavel_reprova_caso_unimodal(self):
        gerador = np.random.default_rng(67)
        unimodal = np.clip(gerador.normal(0.6, 0.04, (50, 50)), 0, 1).astype(np.float32)
        _, confiavel, _ = limiar.limiar_confiavel(unimodal)
        assert not confiavel


class TestLimiarizacao:
    def test_limiar_fixo(self):
        imagem = np.array([[0.1, 0.5, 0.9]], dtype=np.float32)
        assert np.array_equal(limiar.binarizar(imagem, 0.5), [[False, False, True]])

    def test_limiar_adaptativo_acompanha_iluminacao_variavel(self):
        """O caso em que o limiar global erra: fundo com gradiente de iluminação.

        Dois alvos de mesmo contraste local, um na região clara e outro na escura.
        Otsu global pegaria só um; o adaptativo pega os dois.
        """
        fundo = np.tile(np.linspace(0.1, 0.9, 60, dtype=np.float32), (60, 1))
        imagem = fundo.copy()
        imagem[20:26, 8:14] += 0.08
        imagem[20:26, 46:52] += 0.08
        imagem = np.clip(imagem, 0, 1)

        adaptativo = limiar.limiar_adaptativo(imagem, tamanho=15, deslocamento=0.01)
        assert adaptativo[20:26, 8:14].mean() > 0.5
        assert adaptativo[20:26, 46:52].mean() > 0.5

    def test_janela_par_e_rejeitada(self, bimodal):
        with pytest.raises(ErroImagem, match="ímpar"):
            limiar.limiar_adaptativo(bimodal, tamanho=10)

    def test_limiar_duplo_separa_fortes_e_fracos(self):
        imagem = np.array([[0.1, 0.5, 0.9]], dtype=np.float32)
        fortes, fracos = limiar.limiar_duplo(imagem, 0.4, 0.8)
        assert np.array_equal(fortes, [[False, False, True]])
        assert np.array_equal(fracos, [[False, True, False]])

    def test_limiares_invertidos_falham(self, bimodal):
        with pytest.raises(ErroImagem, match="menor"):
            limiar.limiar_duplo(bimodal, 0.8, 0.2)


class TestMorfologia:
    def test_erosao_encolhe_o_quadrado(self):
        mascara = np.zeros((11, 11), dtype=bool)
        mascara[3:8, 3:8] = True  # 5x5 = 25 pixels
        erodida = morfologia.erosao(mascara, morfologia.elemento_quadrado(3))
        assert erodida.sum() == 9  # 3x3

    def test_dilatacao_expande_o_quadrado(self):
        mascara = np.zeros((11, 11), dtype=bool)
        mascara[4:7, 4:7] = True  # 3x3 = 9 pixels
        dilatada = morfologia.dilatacao(mascara, morfologia.elemento_quadrado(3))
        assert dilatada.sum() == 25  # 5x5

    def test_erosao_apaga_pixel_isolado(self):
        mascara = np.zeros((9, 9), dtype=bool)
        mascara[4, 4] = True
        assert morfologia.erosao(mascara).sum() == 0

    def test_abertura_remove_ruido_e_preserva_o_objeto(self):
        """A propriedade central da abertura, no caso que motiva seu uso no pipeline."""
        mascara = np.zeros((25, 25), dtype=bool)
        mascara[5:15, 5:15] = True  # objeto grande
        mascara[20, 20] = True  # respingo isolado
        aberta = morfologia.abertura(mascara, morfologia.elemento_quadrado(3))
        assert not aberta[20, 20]
        assert aberta[8:12, 8:12].all()

    def test_fechamento_tapa_buraco_pequeno(self):
        mascara = np.zeros((20, 20), dtype=bool)
        mascara[5:15, 5:15] = True
        mascara[9, 9] = False
        assert morfologia.fechamento(mascara, morfologia.elemento_quadrado(3))[9, 9]

    def test_abertura_e_idempotente(self):
        """Propriedade matemática: abrir duas vezes é o mesmo que abrir uma."""
        gerador = np.random.default_rng(29)
        mascara = gerador.random((30, 30)) > 0.5
        uma = morfologia.abertura(mascara)
        assert np.array_equal(morfologia.abertura(uma), uma)

    def test_fechamento_e_idempotente(self):
        gerador = np.random.default_rng(31)
        mascara = gerador.random((30, 30)) > 0.5
        uma = morfologia.fechamento(mascara)
        assert np.array_equal(morfologia.fechamento(uma), uma)

    def test_erosao_e_extensiva_para_dentro(self):
        """Erosão nunca acrescenta pixel; dilatação nunca remove."""
        gerador = np.random.default_rng(37)
        mascara = gerador.random((25, 25)) > 0.4
        assert np.all(morfologia.erosao(mascara) <= mascara)
        assert np.all(morfologia.dilatacao(mascara) >= mascara)

    def test_gradiente_morfologico_da_o_contorno(self):
        mascara = np.zeros((15, 15), dtype=bool)
        mascara[5:10, 5:10] = True
        contorno = morfologia.gradiente_morfologico(mascara)
        assert not contorno[7, 7]  # centro vazio
        assert contorno[5, 5]  # borda marcada

    def test_preencher_buracos_fecha_cavidade_grande(self):
        """Diferente do fechamento, não tem limite de tamanho de buraco."""
        mascara = np.zeros((30, 30), dtype=bool)
        mascara[5:25, 5:25] = True
        mascara[10:20, 10:20] = False
        preenchida = morfologia.preencher_buracos(mascara)
        assert preenchida[15, 15]
        assert preenchida[5:25, 5:25].all()

    def test_preencher_buracos_nao_fecha_baia_aberta(self):
        """Cavidade conectada à borda é fundo, não buraco."""
        mascara = np.zeros((20, 20), dtype=bool)
        mascara[5:15, 5:15] = True
        mascara[8:12, 5:10] = False  # fenda que abre para fora? não — cercada
        mascara[8:12, 0:10] = False  # agora conecta à borda esquerda
        preenchida = morfologia.preencher_buracos(mascara)
        assert not preenchida[10, 2]

    def test_elemento_estruturante_par_e_rejeitado(self, duas_regioes):
        with pytest.raises(ErroImagem, match="ímpares"):
            morfologia.erosao(duas_regioes, np.ones((2, 2), dtype=bool))

    def test_elemento_cruz_tem_a_forma_certa(self):
        cruz = morfologia.elemento_cruz(3)
        assert cruz.sum() == 5
        assert not cruz[0, 0]

    def test_elemento_disco_e_aproximadamente_circular(self):
        disco = morfologia.elemento_disco(3)
        assert disco.shape == (7, 7)
        assert disco[3, 3]
        assert not disco[0, 0]


class TestRotulagem:
    def test_conta_as_regioes_corretamente(self, duas_regioes):
        _, quantidade = segmentacao.rotular(duas_regioes)
        assert quantidade == 2

    def test_mascara_vazia_devolve_zero_regioes(self):
        rotulos, quantidade = segmentacao.rotular(np.zeros((10, 10), dtype=bool))
        assert quantidade == 0
        assert rotulos.max() == 0

    def test_areas_medidas_batem_com_as_construidas(self, duas_regioes):
        rotulos, quantidade = segmentacao.rotular(duas_regioes)
        areas = sorted(r.area_pixels for r in segmentacao.descrever_regioes(rotulos, quantidade))
        assert areas == [9, 25]

    def test_forma_em_u_e_uma_regiao_so(self):
        """Caso que quebra rotulagem ingênua de passo único.

        Os dois braços do U recebem etiquetas diferentes no primeiro passo e só se
        revelam conectados na base — a união-busca tem que resolver isso.
        """
        mascara = np.zeros((10, 10), dtype=bool)
        mascara[2:8, 2] = True
        mascara[2:8, 7] = True
        mascara[7, 2:8] = True
        _, quantidade = segmentacao.rotular(mascara)
        assert quantidade == 1

    def test_conectividade_4_separa_o_que_a_8_une(self):
        """Dois pixels em diagonal: uma região com conectividade 8, duas com 4."""
        mascara = np.zeros((6, 6), dtype=bool)
        mascara[2, 2] = True
        mascara[3, 3] = True
        assert segmentacao.rotular(mascara, conectividade=8)[1] == 1
        assert segmentacao.rotular(mascara, conectividade=4)[1] == 2

    def test_centroide_do_quadrado_fica_no_centro(self):
        mascara = np.zeros((20, 20), dtype=bool)
        mascara[4:9, 10:15] = True
        rotulos, quantidade = segmentacao.rotular(mascara)
        regiao = segmentacao.descrever_regioes(rotulos, quantidade)[0]
        assert regiao.centroide == pytest.approx((6.0, 12.0))

    def test_caixa_delimitadora(self):
        mascara = np.zeros((20, 20), dtype=bool)
        mascara[4:9, 10:15] = True
        rotulos, quantidade = segmentacao.rotular(mascara)
        assert segmentacao.descrever_regioes(rotulos, quantidade)[0].caixa == (4, 10, 9, 15)

    def test_conversao_para_hectares(self):
        """Sentinel-2 tem 10 m/pixel, logo 100 pixels = 10.000 m² = 1 ha."""
        regiao = segmentacao.Regiao(1, 100, (0.0, 0.0), (0, 0, 10, 10))
        assert regiao.area_hectares(10.0) == pytest.approx(1.0)

    def test_hectares_com_resolucao_invalida_falha(self):
        regiao = segmentacao.Regiao(1, 100, (0.0, 0.0), (0, 0, 10, 10))
        with pytest.raises(ValueError, match="positivo"):
            regiao.area_hectares(0.0)


class TestFiltroDeArea:
    def test_descarta_regiao_menor_que_o_minimo(self, duas_regioes):
        filtrada = segmentacao.filtrar_por_area(duas_regioes, area_minima=10)
        assert filtrada.sum() == 25
        assert not filtrada[3, 3]

    def test_descarta_regiao_maior_que_o_maximo(self, duas_regioes):
        filtrada = segmentacao.filtrar_por_area(duas_regioes, area_maxima=10)
        assert filtrada.sum() == 9

    def test_sem_limites_preserva_tudo(self, duas_regioes):
        filtrada = segmentacao.filtrar_por_area(duas_regioes)
        assert np.array_equal(filtrada, duas_regioes)

    def test_faixa_invertida_falha(self, duas_regioes):
        with pytest.raises(ValueError, match="area_maxima"):
            segmentacao.filtrar_por_area(duas_regioes, area_minima=50, area_maxima=10)


class TestReconstrucao:
    def test_mantem_apenas_regiao_com_marcador(self, duas_regioes):
        """A histerese: região sem marcador forte é descartada inteira."""
        marcadores = np.zeros((20, 20), dtype=bool)
        marcadores[12, 12] = True  # cai só dentro do quadrado grande
        reconstruida = segmentacao.reconstruir_por_conexao(marcadores, duas_regioes)
        assert reconstruida.sum() == 25
        assert not reconstruida[3, 3]

    def test_sem_marcador_devolve_vazio(self, duas_regioes):
        vazio = np.zeros((20, 20), dtype=bool)
        assert segmentacao.reconstruir_por_conexao(vazio, duas_regioes).sum() == 0

    def test_formatos_incompativeis_falham(self, duas_regioes):
        with pytest.raises(ValueError, match="incompatíveis"):
            segmentacao.reconstruir_por_conexao(np.zeros((10, 10), dtype=bool), duas_regioes)


class TestMudancaBiTemporal:
    def test_identifica_perda_de_vegetacao(self):
        """O cálculo que define o resultado do projeto."""
        antes = np.zeros((10, 10), dtype=bool)
        antes[2:8, 2:8] = True
        depois = antes.copy()
        depois[4:6, 4:6] = False  # área desmatada entre as duas datas

        mudanca = segmentacao.mudanca_entre_mascaras(antes, depois)
        assert mudanca["perda"].sum() == 4
        assert mudanca["ganho"].sum() == 0
        assert mudanca["estavel_vegetado"].sum() == 32

    def test_as_quatro_classes_particionam_a_imagem(self):
        gerador = np.random.default_rng(41)
        antes = gerador.random((20, 20)) > 0.5
        depois = gerador.random((20, 20)) > 0.5
        mudanca = segmentacao.mudanca_entre_mascaras(antes, depois)
        assert sum(m.sum() for m in mudanca.values()) == 400

    def test_recortes_de_tamanhos_diferentes_falham(self):
        with pytest.raises(ValueError, match="mesmo recorte"):
            segmentacao.mudanca_entre_mascaras(
                np.zeros((10, 10), dtype=bool), np.zeros((12, 12), dtype=bool)
            )
