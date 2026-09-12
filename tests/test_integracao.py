"""Teste de integração da cadeia completa de processamento.

As cenas aqui são **sintéticas** e servem apenas para verificar que as etapas se
encaixam e que a área detectada bate com a área que foi construída de propósito.
Nenhuma imagem gerada aqui pode aparecer no trabalho escrito como se fosse real —
ver `AGENTS.md` §11.

A validação sobre imagens reais é requisito à parte (R032) e depende do download das
cenas registradas em `data/raw/FONTES.md`.
"""

import numpy as np
import pytest

from sentinela.dataio.sintetico import cena_sintetica
from sentinela.pdi import cor, filtros, limiar, morfologia, segmentacao


def indice_suavizado(rgb, nir=None):
    """Índice de vegetação normalizado e suavizado — etapas 2 e 3 do pipeline."""
    indice, metodo = cor.indice_vegetacao(rgb, nir, metodo="auto")
    assert metodo == ("ndvi" if nir is not None else "vari")
    return filtros.gaussiano(cor.para_faixa_unitaria(indice), tamanho=5)


def segmentar_par(indice_antes, indice_depois):
    """Segmenta as duas datas com um limiar **único**, calculado sobre as duas juntas.

    Usar Otsu separadamente em cada data daria a cada uma uma régua diferente, e a
    diferença entre as máscaras mediria a diferença entre os limiares, não a mudança no
    terreno — ver ``limiar.otsu_conjunto``.

    Devolve ``(vegetacao_antes, vegetacao_depois, confiavel, metricas)``.
    """
    valor, confiavel, metricas = limiar.limiar_confiavel(indice_antes, indice_depois)

    limpar = lambda m: morfologia.fechamento(morfologia.abertura(m))
    return (
        limpar(limiar.binarizar(indice_antes, valor)),
        limpar(limiar.binarizar(indice_depois, valor)),
        confiavel,
        metricas,
    )


CORTE = (slice(30, 50), slice(30, 50))  # 20x20 = 400 pixels


class TestCadeiaCompleta:
    def test_detecta_area_desmatada_com_area_correta(self):
        """Corte de 400 pixels construído de propósito; a detecção deve bater."""
        antes = indice_suavizado(*cena_sintetica(101))
        depois = indice_suavizado(*cena_sintetica(202, corte=CORTE))

        veg_antes, veg_depois, confiavel, _ = segmentar_par(antes, depois)
        mudanca = segmentacao.mudanca_entre_mascaras(veg_antes, veg_depois)

        assert confiavel
        assert mudanca["perda"].sum() == pytest.approx(400, rel=0.10)
        assert mudanca["ganho"].sum() < 40  # controle: pouco ruído de registro

    def test_a_perda_fica_no_lugar_certo(self):
        antes = indice_suavizado(*cena_sintetica(103))
        depois = indice_suavizado(*cena_sintetica(204, corte=CORTE))

        veg_antes, veg_depois, _, _ = segmentar_par(antes, depois)
        perda = segmentacao.mudanca_entre_mascaras(veg_antes, veg_depois)["perda"]

        assert perda[35:45, 35:45].mean() > 0.9  # dentro do corte
        assert perda[5:15, 5:15].mean() < 0.05  # longe dele

    def test_cena_homogenea_e_sinalizada_como_nao_confiavel(self):
        """Controle negativo — o caso que mais gera falso positivo em campo.

        Duas datas de floresta intacta não têm duas classes para separar. O limiar
        automático vai cortar o ruído do dossel ao meio e acusar desmatamento onde não
        houve. O sistema precisa **detectar** essa situação, não produzir a máscara.
        """
        antes = indice_suavizado(*cena_sintetica(105))
        depois = indice_suavizado(*cena_sintetica(206))

        _, confiavel, metricas = limiar.limiar_confiavel(antes, depois)

        assert not confiavel
        # Fica no piso teórico de partir uma distribuição unimodal ao meio.
        assert metricas["distinguibilidade"] == pytest.approx(
            limiar.DISTINGUIBILIDADE_UNIMODAL, abs=0.3
        )

    def test_a_separabilidade_de_otsu_nao_serve_de_criterio(self):
        """Justifica a escolha da distinguibilidade em vez do η do artigo original.

        Cena homogênea cortada 50/50 tem ω(1−ω) = 0,25; cena com desmatamento pequeno
        e índice só-visível tem ω(1−ω) ≈ 0,06. Esse fator entra em σ²_entre e derruba η
        do caso real **abaixo** do caso homogêneo, invertendo o critério. A
        distinguibilidade, que não carrega o fator, ordena os dois casos corretamente.
        """
        homog_a = indice_suavizado(*cena_sintetica(105))
        homog_b = indice_suavizado(*cena_sintetica(206))

        real_a = indice_suavizado(cena_sintetica(111)[0])  # só RGB -> VARI
        real_b = indice_suavizado(cena_sintetica(212, corte=CORTE)[0])

        _, eta_homogenea = limiar.otsu_conjunto(homog_a, homog_b)
        _, eta_real = limiar.otsu_conjunto(real_a, real_b)

        _, _, m_homogenea = limiar.limiar_confiavel(homog_a, homog_b)
        _, _, m_real = limiar.limiar_confiavel(real_a, real_b)

        # η ordena errado: o caso homogêneo pontua mais que o caso com desmatamento real.
        assert eta_homogenea > eta_real
        # A distinguibilidade ordena certo.
        assert m_real["distinguibilidade"] > m_homogenea["distinguibilidade"]

    def test_limiar_conjunto_e_o_mesmo_para_as_duas_datas(self):
        """A régua única é o que torna as máscaras comparáveis.

        Otsu por data devolveria limiares muito diferentes quando uma das cenas é
        homogênea — a diferença entre eles apareceria como mudança no terreno.
        """
        antes = indice_suavizado(*cena_sintetica(107))
        depois = indice_suavizado(*cena_sintetica(208, corte=CORTE))

        conjunto, _ = limiar.otsu_conjunto(antes, depois)
        separado_antes = limiar.otsu(antes)
        separado_depois = limiar.otsu(depois)

        assert abs(separado_antes - separado_depois) > 0.15
        assert abs(conjunto - separado_depois) < 0.05

    def test_quantificacao_em_hectares(self):
        """400 pixels a 10 m/pixel (Sentinel-2) = 40.000 m² = 4 ha."""
        antes = indice_suavizado(*cena_sintetica(107))
        depois = indice_suavizado(*cena_sintetica(208, corte=CORTE))

        veg_antes, veg_depois, _, _ = segmentar_par(antes, depois)
        perda = segmentacao.mudanca_entre_mascaras(veg_antes, veg_depois)["perda"]

        rotulos, quantidade = segmentacao.rotular(perda)
        maior = max(segmentacao.descrever_regioes(rotulos, quantidade), key=lambda r: r.area_pixels)

        assert maior.area_hectares(metros_por_pixel=10.0) == pytest.approx(4.0, rel=0.10)

    def test_filtro_de_area_elimina_fragmentos_residuais(self):
        antes = indice_suavizado(*cena_sintetica(109))
        depois = indice_suavizado(*cena_sintetica(210, corte=CORTE))

        veg_antes, veg_depois, _, _ = segmentar_par(antes, depois)
        perda = segmentacao.mudanca_entre_mascaras(veg_antes, veg_depois)["perda"]

        filtrada = segmentacao.filtrar_por_area(perda, area_minima=25)
        _, quantidade = segmentacao.rotular(filtrada)

        assert quantidade == 1
        assert filtrada.sum() == pytest.approx(400, rel=0.10)

    def test_cadeia_funciona_sem_infravermelho(self):
        """Degradação para VARI quando só há as bandas visíveis."""
        antes_rgb, _ = cena_sintetica(111)
        depois_rgb, _ = cena_sintetica(212, corte=CORTE)

        antes = indice_suavizado(antes_rgb)
        depois = indice_suavizado(depois_rgb)

        veg_antes, veg_depois, confiavel, _ = segmentar_par(antes, depois)
        perda = segmentacao.mudanca_entre_mascaras(veg_antes, veg_depois)["perda"]

        assert confiavel
        assert perda.sum() == pytest.approx(400, rel=0.25)


class TestRealceDeBordas:
    def test_gradiente_contorna_a_area_desmatada(self):
        """O contorno do corte tem que aparecer no mapa de bordas."""
        rgb, nir = cena_sintetica(113, corte=(slice(30, 50), slice(30, 50)))
        indice = cor.para_faixa_unitaria(cor.ndvi(rgb[:, :, 0], nir))
        suave = filtros.gaussiano(indice, tamanho=5)
        bordas = filtros.magnitude_gradiente(suave, "sobel")

        na_borda = bordas[29:31, 32:48].mean()
        no_interior = bordas[35:45, 35:45].mean()
        assert na_borda > no_interior * 5

    def test_textura_separa_floresta_de_solo_exposto(self):
        """Feature prevista para a etapa de modelo: dossel é texturizado, corte é liso."""
        gerador = np.random.default_rng(115)
        rgb, nir = cena_sintetica(115, corte=(slice(30, 50), slice(30, 50)))
        # Dossel de floresta tem variação espacial bem maior que solo exposto.
        cinza = cor.para_cinza(rgb)
        cinza[:30, :] += gerador.normal(0, 0.05, (30, 80)).astype(np.float32)

        desvio = filtros.desvio_padrao_local(np.clip(cinza, 0, 1), tamanho=5)
        assert desvio[5:25, 5:75].mean() > desvio[35:45, 35:45].mean()
