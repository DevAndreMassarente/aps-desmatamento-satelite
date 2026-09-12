"""Testes da etapa de modelo.

O que mais importa aqui não é a acurácia — em cena sintética ela é alta por construção e
não prova nada. O que se verifica é o que torna a métrica **honesta**: que treino e teste
não compartilham um único pixel, que o classificador se recusa a operar fora das
condições válidas, e que métrica frágil vem acompanhada de aviso.

As cenas são **sintéticas** — ver `dataio/sintetico.py`.
"""

import numpy as np
import pytest

from sentinela.dataio.sintetico import cena_sintetica, par_bitemporal
from sentinela.pdi.nucleo import ErroImagem
from sentinela.pipeline import detectar_desmatamento, extrair_amostras
from sentinela.pipeline.amostras import DESMATADO, INTACTO, ConjuntoDeAmostras
from sentinela.modelo import caracteristicas as carac
from sentinela.modelo import classificador as clf

LADO = 16


@pytest.fixture(scope="module")
def conjunto():
    """Cena grande o bastante para render vários blocos na divisão espacial."""
    par = par_bitemporal(corte=(slice(60, 140), slice(60, 140)), tamanho=(200, 200))
    resultado = detectar_desmatamento(
        par["rgb_antes"], par["rgb_depois"], par["nir_antes"], par["nir_depois"]
    )
    return extrair_amostras(par["rgb_depois"], resultado.perda, lado=LADO, passo=8)


class TestCaracteristicas:
    def test_um_vetor_por_recorte(self, conjunto):
        matriz = carac.extrair_caracteristicas(conjunto.recortes)
        assert matriz.shape == (len(conjunto), len(carac.NOMES_DAS_FEATURES))

    def test_conjunto_vazio_mantem_as_colunas(self):
        vazio = np.empty((0, LADO, LADO, 3), dtype=np.float32)
        assert carac.extrair_caracteristicas(vazio).shape == (
            0,
            len(carac.NOMES_DAS_FEATURES),
        )

    def test_indices_de_vegetacao_separam_floresta_de_solo_exposto(self):
        floresta, solo = self._par_de_recortes()

        for nome in ("media_exg", "media_vari"):
            indice = carac.NOMES_DAS_FEATURES.index(nome)
            assert floresta[indice] > solo[indice] + 0.2, nome

    def test_brilho_separa_floresta_de_solo_exposto(self):
        floresta, solo = self._par_de_recortes()
        indice = carac.NOMES_DAS_FEATURES.index("brilho_mediana")
        assert solo[indice] > floresta[indice] + 0.15

    def test_textura_nao_separa_as_classes_na_cena_sintetica(self):
        """Limitação declarada, não defeito.

        O gerador sintético aplica o **mesmo** desvio de ruído às duas classes, então o
        desvio local é igual nas duas e a textura não carrega informação aqui. Em imagem
        real ela deveria separar — dossel fechado é irregular, solo exposto é liso — mas
        isso é hipótese da literatura, e só pode ser medido depois de R032.

        O teste existe para impedir que alguém apresente a textura como validada por
        esta suíte. Se ele começar a falhar, o gerador mudou e este comentário também
        precisa mudar.
        """
        floresta, solo = self._par_de_recortes()
        indice = carac.NOMES_DAS_FEATURES.index("textura_media")

        assert abs(floresta[indice] - solo[indice]) < 0.005

    @staticmethod
    def _par_de_recortes():
        floresta, _ = cena_sintetica(41, tamanho=(LADO, LADO))
        solo, _ = cena_sintetica(
            42, corte=(slice(0, LADO), slice(0, LADO)), tamanho=(LADO, LADO)
        )
        return carac.descrever_recorte(floresta), carac.descrever_recorte(solo)

    def test_nao_produz_nan(self, conjunto):
        """Divisão por zero nos índices de vegetação envenenaria o treino."""
        matriz = carac.extrair_caracteristicas(conjunto.recortes)
        assert np.isfinite(matriz).all()

    def test_recorte_sem_tres_bandas_e_recusado(self):
        with pytest.raises(ErroImagem, match="RGB"):
            carac.extrair_caracteristicas(np.zeros((2, LADO, LADO, 1), dtype=np.float32))

    def test_formato_errado_e_recusado(self):
        with pytest.raises(ErroImagem, match="formato"):
            carac.extrair_caracteristicas(np.zeros((LADO, LADO, 3), dtype=np.float32))


class TestDivisaoEspacial:
    """A parte metodologicamente crítica: sem isolamento, a métrica é fantasia."""

    def test_nenhum_pixel_e_compartilhado_entre_treino_e_teste(self, conjunto):
        treino, teste = clf.dividir_espacialmente(conjunto)

        def pixels(amostras):
            ocupados = set()
            for linha, coluna in amostras.posicoes:
                for i in range(linha, linha + LADO):
                    for j in range(coluna, coluna + LADO):
                        ocupados.add((i, j))
            return ocupados

        assert not (pixels(treino) & pixels(teste))

    def test_as_duas_classes_aparecem_nos_dois_lados(self, conjunto):
        """Um corte único deixaria a área desmatada inteira de um lado só."""
        treino, teste = clf.dividir_espacialmente(conjunto)

        for parte in (treino, teste):
            contagens = parte.contagem_por_classe
            assert contagens[INTACTO] > 0
            assert contagens[DESMATADO] > 0

    def test_a_divisao_e_deterministica(self, conjunto):
        primeira = clf.dividir_espacialmente(conjunto, semente=3)[1].posicoes
        segunda = clf.dividir_espacialmente(conjunto, semente=3)[1].posicoes
        assert primeira == segunda

    def test_sementes_diferentes_escolhem_blocos_diferentes(self, conjunto):
        um = clf.dividir_espacialmente(conjunto, semente=1)[1].posicoes
        outro = clf.dividir_espacialmente(conjunto, semente=7)[1].posicoes
        assert um != outro

    def test_cena_pequena_demais_e_recusada_com_explicacao(self):
        """Um bloco só significa treino e teste no mesmo terreno: melhor recusar."""
        par = par_bitemporal(corte=(slice(20, 44), slice(20, 44)), tamanho=(64, 64))
        resultado = detectar_desmatamento(
            par["rgb_antes"], par["rgb_depois"], par["nir_antes"], par["nir_depois"]
        )
        pequeno = extrair_amostras(par["rgb_depois"], resultado.perda, lado=16, passo=8)
        assert len(pequeno) > 0  # há amostras; o problema é não haver blocos suficientes

        with pytest.raises(clf.ErroModelo, match="bloco"):
            clf.dividir_espacialmente(pequeno, tamanho_bloco=128)

    def test_proporcao_invalida(self, conjunto):
        with pytest.raises(clf.ErroModelo, match="proporcao_teste"):
            clf.dividir_espacialmente(conjunto, proporcao_teste=1.5)

    def test_bloco_menor_que_o_recorte(self, conjunto):
        with pytest.raises(clf.ErroModelo, match="tamanho_bloco"):
            clf.dividir_espacialmente(conjunto, tamanho_bloco=4)


class TestClassificador:
    def test_treina_e_classifica(self, conjunto):
        modelo, avaliacao = clf.treinar_e_avaliar(conjunto)

        assert modelo.treinado
        assert avaliacao.total_teste > 0
        # Em cena sintética a separação foi construída; exigir menos que isso seria
        # aceitar que o encanamento está quebrado.
        assert avaliacao.f1 > 0.8

    def test_probabilidade_fica_na_faixa_valida(self, conjunto):
        modelo, _ = clf.treinar_e_avaliar(conjunto)
        probabilidades = modelo.probabilidade_de_desmatamento(conjunto.recortes[:10])

        assert probabilidades.shape == (10,)
        assert ((probabilidades >= 0) & (probabilidades <= 1)).all()

    def test_importancia_cobre_todas_as_features(self, conjunto):
        modelo, _ = clf.treinar_e_avaliar(conjunto)
        importancias = modelo.importancia_das_features()

        assert len(importancias) == len(carac.NOMES_DAS_FEATURES)
        assert [nome for nome, _ in importancias] != list(carac.NOMES_DAS_FEATURES)
        pesos = [peso for _, peso in importancias]
        assert pesos == sorted(pesos, reverse=True)
        assert sum(pesos) == pytest.approx(1.0, abs=1e-6)

    def test_prever_antes_de_treinar_e_recusado(self, conjunto):
        with pytest.raises(clf.ErroModelo, match="treinado"):
            clf.ClassificadorDesmatamento().prever(conjunto.recortes)

    def test_avaliar_antes_de_treinar_e_recusado(self, conjunto):
        with pytest.raises(clf.ErroModelo, match="treinado"):
            clf.ClassificadorDesmatamento().avaliar(conjunto)

    def test_treino_com_uma_classe_so_e_recusado(self, conjunto):
        indices = np.nonzero(conjunto.rotulos == INTACTO)[0]
        so_intacto = ConjuntoDeAmostras(
            recortes=conjunto.recortes[indices],
            rotulos=conjunto.rotulos[indices],
            posicoes=[conjunto.posicoes[i] for i in indices],
            descartados_ambiguos=0,
        )

        with pytest.raises(clf.ErroModelo, match="duas classes"):
            clf.ClassificadorDesmatamento().treinar(so_intacto)

    def test_treino_sem_amostra_e_recusado(self):
        vazio = ConjuntoDeAmostras(
            recortes=np.empty((0, LADO, LADO, 3), dtype=np.float32),
            rotulos=np.empty(0, dtype=np.int64),
            posicoes=[],
            descartados_ambiguos=0,
        )
        with pytest.raises(clf.ErroModelo, match="não há amostras"):
            clf.ClassificadorDesmatamento().treinar(vazio)


class TestAvisosDaAvaliacao:
    """Métrica sem aviso engana. Estes testes garantem que o aviso aparece."""

    def test_desempenho_perfeito_vem_com_ressalva(self, conjunto):
        _, avaliacao = clf.treinar_e_avaliar(conjunto)
        if avaliacao.acuracia == 1.0:
            assert any("perfeito" in aviso for aviso in avaliacao.avisos)

    def test_conjunto_desbalanceado_manda_ler_o_f1(self, conjunto):
        _, avaliacao = clf.treinar_e_avaliar(conjunto)
        if avaliacao.total_teste and conjunto.equilibrio < 0.3:
            assert any("desbalanceado" in aviso for aviso in avaliacao.avisos)

    def test_matriz_de_confusao_nomeia_os_dois_tipos_de_erro(self, conjunto):
        _, avaliacao = clf.treinar_e_avaliar(conjunto)
        matriz = avaliacao.resumo()["matriz_confusao"]

        assert "falso_alarme" in matriz
        assert "desmatamento_perdido" in matriz
        assert sum(matriz.values()) == avaliacao.total_teste
