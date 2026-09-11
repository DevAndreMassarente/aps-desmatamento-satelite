"""Limiarização — primeira etapa da segmentação.

Cobre parte da etapa "Segmentação" do enunciado (p.3, item 2.e.iv). O objetivo aqui é
converter o índice de vegetação contínuo em uma máscara binária: vegetação × não-vegetação.
"""

from __future__ import annotations

import numpy as np

from .nucleo import ErroImagem, histograma, janela_deslizante, validar_imagem


def binarizar(imagem: np.ndarray, limiar: float, inverter: bool = False) -> np.ndarray:
    """Aplica um limiar fixo, devolvendo máscara booleana.

    Com ``inverter=False`` marca ``imagem > limiar``. Na detecção de desmatamento o
    interessante costuma ser o inverso — o que ficou **abaixo** do limiar de vegetação.
    """
    imagem = validar_imagem(imagem, bandas_aceitas=(2,))

    if not np.isfinite(limiar):
        raise ErroImagem(f"limiar deve ser um número finito, recebido {limiar}")

    mascara = imagem <= limiar if inverter else imagem > limiar
    return mascara


# Piso teórico da distinguibilidade: cortar uma distribuição normal única no ponto ótimo
# produz duas meias-normais com médias em ±0,798σ e desvio 0,603σ, logo
# d = 1,596σ / 0,603σ ≈ 2,65. Ou seja, QUALQUER imagem unimodal — uma cena inteiramente
# florestada, por exemplo — atinge d ≈ 2,65 sem ter duas classes de verdade.
DISTINGUIBILIDADE_UNIMODAL = 2.65

# Acima deste valor o limiar está separando duas classes reais, não partindo ruído ao meio.
# Medido nas cenas sintéticas de `tests/test_integracao.py`: cena homogênea fica em
# d ≈ 2,69 (os três índices), e cena com corte raso detectável vai de 7,3 (VARI/ExG) a
# 12,0 (NDVI). O corte foi posto na folga. Reavaliar contra as imagens reais (R032).
DISTINGUIBILIDADE_MINIMA = 4.0


def _otsu_do_histograma(
    contagens: np.ndarray, centros: np.ndarray
) -> tuple[float, float]:
    """Núcleo do método de Otsu sobre um histograma já montado.

    Otsu varre todos os limiares possíveis e escolhe o que **maximiza a variância entre
    as duas classes** resultantes — equivalente a minimizar a variância dentro delas.
    A intuição: o melhor corte é o que deixa os dois grupos mais separados um do outro
    e mais compactos internamente.

    Para o peso ``ω`` e a média ``μ`` acumulados até cada faixa::

        σ²_entre(t) = [μ_total · ω(t) − μ(t)]² / [ω(t) · (1 − ω(t))]

    A formulação acumulada evita recalcular as médias das duas classes a cada limiar,
    reduzindo o método a uma varredura única sobre o histograma.

    Devolve ``(limiar, separabilidade)``. A separabilidade é a medida ``η = σ²_entre /
    σ²_total`` definida no artigo original: vale 1 quando as duas classes são
    perfeitamente distintas e tende a 0 quando o histograma tem um modo só.

    Referência: Otsu, N. (1979). "A Threshold Selection Method from Gray-Level Histograms".
    IEEE Transactions on Systems, Man, and Cybernetics, 9(1), 62–66.
    """
    total = contagens.sum()
    if total == 0:
        raise ErroImagem("histograma vazio — imagem sem pixels válidos")

    probabilidade = contagens.astype(np.float64) / total
    centros = centros.astype(np.float64)

    peso = np.cumsum(probabilidade)
    media_acumulada = np.cumsum(probabilidade * centros)
    media_total = media_acumulada[-1]

    denominador = peso * (1.0 - peso)
    # Limiares degenerados (uma das classes vazia) são descartados, não ajustados.
    valido = denominador > 1e-12

    if not valido.any():
        raise ErroImagem(
            "não foi possível calcular o limiar de Otsu: a imagem parece ter "
            "intensidade constante"
        )

    variancia_entre = np.zeros_like(denominador)
    variancia_entre[valido] = (
        (media_total * peso[valido] - media_acumulada[valido]) ** 2 / denominador[valido]
    )

    # Quando não há pixel algum entre os dois modos, todo limiar dentro do vão produz a
    # mesma partição e portanto a mesma variância entre classes. `argmax` devolveria o
    # primeiro desse platô, encostando o limiar na cauda do modo inferior. Tomar o centro
    # do platô deixa a margem equilibrada para os dois lados, que é mais robusto a ruído
    # na imagem real sem alterar a partição no caso sintético.
    maximo = variancia_entre.max()
    no_platô = np.flatnonzero(variancia_entre >= maximo * (1.0 - 1e-9))
    melhor = int(no_platô[len(no_platô) // 2])

    variancia_total = float((probabilidade * (centros - media_total) ** 2).sum())

    separabilidade = (
        float(variancia_entre[melhor] / variancia_total) if variancia_total > 1e-15 else 0.0
    )

    return float(centros[melhor]), separabilidade


def otsu(imagem: np.ndarray, faixas: int = 256) -> float:
    """Limiar ótimo de Otsu para a imagem.

    Funciona quando o histograma é bimodal — o caso de um índice de vegetação numa cena
    que tem floresta **e** área desmatada. Numa cena homogênea o valor devolvido não tem
    significado; use ``otsu_com_separabilidade`` para saber se dá para confiar nele.
    """
    return otsu_com_separabilidade(imagem, faixas)[0]


def otsu_com_separabilidade(imagem: np.ndarray, faixas: int = 256) -> tuple[float, float]:
    """Como ``otsu``, mas devolve também a separabilidade ``η`` do histograma.

    Usar quando a imagem pode não ter duas classes — por exemplo uma cena inteiramente
    florestada, em que qualquer limiar automático vai partir o ruído ao meio e inventar
    desmatamento onde não há. Comparar ``η`` com ``SEPARABILIDADE_MINIMA``.
    """
    imagem = validar_imagem(imagem, bandas_aceitas=(2,))

    if faixas < 2:
        raise ErroImagem(f"são necessárias ao menos 2 faixas, recebido {faixas}")

    contagens, centros = histograma(imagem, faixas)
    return _otsu_do_histograma(contagens, centros)


def distinguibilidade(imagem: np.ndarray, valor: float) -> float:
    """Tamanho de efeito padronizado entre as duas classes produzidas por um limiar.

    ``d = |μ_baixa − μ_alta| / sqrt[(σ²_baixa + σ²_alta) / 2]``

    Mede a distância entre as médias das duas classes em unidades do espalhamento
    interno delas. É o critério para decidir se o limiar encontrado separa duas
    populações reais ou apenas partiu uma população única ao meio.

    **Por que não usar a separabilidade η de Otsu para isso.** η vale
    ``σ²_entre / σ²_total``, e ``σ²_entre`` carrega o fator ``ω·(1−ω)`` — o produto das
    frações das duas classes. Uma área desmatada pequena (digamos 6% da cena) dá
    ``ω(1−ω) = 0,056``, contra ``0,25`` de uma partição meio a meio. Isso derruba η
    mecanicamente, por desbalanceamento, sem nenhuma relação com a qualidade da
    separação. Na prática η chega a ficar **mais alto** numa cena homogênea (onde Otsu
    corta 50/50) do que numa cena com desmatamento real pequeno — exatamente ao
    contrário do que se precisa.

    O tamanho de efeito não tem esse fator e é invariante ao tamanho relativo das classes.

    Ver ``DISTINGUIBILIDADE_UNIMODAL`` para o piso que qualquer imagem atinge.
    """
    imagem = validar_imagem(imagem, bandas_aceitas=(2,))

    baixa = imagem[imagem <= valor]
    alta = imagem[imagem > valor]

    if baixa.size < 2 or alta.size < 2:
        return 0.0

    espalhamento = np.sqrt((float(baixa.var()) + float(alta.var())) / 2.0)
    if espalhamento < 1e-12:
        return float("inf")

    return float(abs(float(baixa.mean()) - float(alta.mean())) / espalhamento)


def limiar_confiavel(
    *imagens: np.ndarray, faixas: int = 256
) -> tuple[float, bool, dict[str, float]]:
    """Calcula o limiar conjunto e avalia se ele é confiável.

    Devolve ``(valor, confiavel, metricas)``. ``metricas`` traz ``separabilidade``
    (o η do artigo de Otsu, útil para o relatório) e ``distinguibilidade`` (o critério
    efetivo de decisão).

    Usar isto, e não ``otsu`` cru, sempre que a cena puder não conter desmatamento:
    marcar ``confiavel=False`` e não emitir máscara é a resposta correta para uma
    floresta intacta. Emitir uma máscara ali seria inventar desmatamento.
    """
    valor, separabilidade = otsu_conjunto(*imagens, faixas=faixas)
    efeito = max(distinguibilidade(imagem, valor) for imagem in imagens)

    return (
        valor,
        efeito >= DISTINGUIBILIDADE_MINIMA,
        {"separabilidade": separabilidade, "distinguibilidade": efeito},
    )


def otsu_conjunto(*imagens: np.ndarray, faixas: int = 256) -> tuple[float, float]:
    """Limiar **único** de Otsu calculado sobre o histograma combinado das imagens.

    É o que a análise bi-temporal exige. Calcular Otsu separadamente em cada data dá a
    cada uma um limiar diferente — réguas diferentes — e a comparação entre as máscaras
    deixa de significar mudança no terreno: passa a medir a diferença entre os dois
    limiares.

    O caso que expõe o erro: se T1 é floresta intacta, o histograma de T1 sozinho é
    unimodal e o Otsu corta no meio do ruído do dossel, marcando metade da floresta como
    não-vegetação. A comparação com T2 acusaria desmatamento massivo inexistente.

    Com o histograma combinado, as duas datas são medidas pela mesma régua, e basta que
    **uma** delas contenha as duas classes para que o limiar seja bem definido.

    Devolve ``(limiar, separabilidade)``.
    """
    if not imagens:
        raise ErroImagem("é necessária ao menos uma imagem")

    if faixas < 2:
        raise ErroImagem(f"são necessárias ao menos 2 faixas, recebido {faixas}")

    validadas = [validar_imagem(img, bandas_aceitas=(2,)) for img in imagens]

    total_contagens = np.zeros(faixas, dtype=np.int64)
    centros = None
    for imagem in validadas:
        contagens, centros = histograma(imagem, faixas)
        total_contagens += contagens

    return _otsu_do_histograma(total_contagens, centros)


def otsu_binarizar(
    imagem: np.ndarray, faixas: int = 256, inverter: bool = False
) -> tuple[np.ndarray, float]:
    """Conveniência: calcula o limiar de Otsu e já aplica.

    Devolve ``(mascara, limiar)`` — o limiar é propagado para que apareça no relatório
    e na interface, já que "qual limiar vocês usaram?" é pergunta certa na banca.
    """
    limiar = otsu(imagem, faixas)
    return binarizar(imagem, limiar, inverter), limiar


def limiar_adaptativo(
    imagem: np.ndarray,
    tamanho: int = 31,
    deslocamento: float = 0.02,
    inverter: bool = False,
    modo_borda: str = "reflete",
) -> np.ndarray:
    """Limiarização adaptativa pela média local.

    Cada pixel é comparado à média da sua vizinhança, menos um deslocamento. Diferente
    do Otsu, que escolhe **um** limiar para a imagem inteira, este acompanha variações
    graduais de iluminação — sombra de nuvem, gradiente atmosférico, relevo sombreado —
    que fariam um limiar global errar sistematicamente num lado da cena.

    O custo é sensibilidade a ruído: em região homogênea a média local fica próxima do
    próprio pixel e o resultado vira textura aleatória. Suavizar antes, ou usar
    ``deslocamento`` maior.
    """
    imagem = validar_imagem(imagem, bandas_aceitas=(2,))

    if tamanho < 3 or tamanho % 2 == 0:
        raise ErroImagem(f"tamanho da janela deve ser ímpar e >= 3, recebido {tamanho}")

    media_local = janela_deslizante(imagem, tamanho, modo_borda).mean(axis=0)
    referencia = media_local - deslocamento

    return imagem <= referencia if inverter else imagem > referencia


def limiar_duplo(
    imagem: np.ndarray, limiar_baixo: float, limiar_alto: float
) -> tuple[np.ndarray, np.ndarray]:
    """Histerese: separa pixels fortes dos fracos.

    Devolve ``(fortes, fracos)``. Pixels acima de ``limiar_alto`` são seguramente da
    classe; os entre os dois limiares são candidatos, aceitos só se conectados a um
    forte — conexão resolvida em ``segmentacao.reconstruir_por_conexao``.

    É o mecanismo do detector de Canny e vale para reduzir falso positivo isolado na
    máscara de desmatamento.
    """
    imagem = validar_imagem(imagem, bandas_aceitas=(2,))

    if limiar_baixo >= limiar_alto:
        raise ErroImagem(
            f"limiar_baixo ({limiar_baixo}) deve ser menor que limiar_alto ({limiar_alto})"
        )

    fortes = imagem >= limiar_alto
    fracos = (imagem >= limiar_baixo) & ~fortes
    return fortes, fracos
