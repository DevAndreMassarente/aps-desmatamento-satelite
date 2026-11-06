"""Interface de demonstração — o que roda no seminário (R044, R050).

Streamlit foi escolhido porque a apresentação é ao vivo e o enunciado pede demonstração
do programa: uma tela permite trocar parâmetro e mostrar o efeito na hora, coisa que um
script de terminal não faz sem parecer ensaiado.

A interface não decide nada. Ela chama ``pipeline.detectar_desmatamento`` e exibe os
intermediários que o resultado já carrega. Nenhum algoritmo de PDI mora aqui.

Executar com:

```bash
streamlit run src/sentinela/app/principal.py
```
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

import numpy as np
import streamlit as st
import streamlit.components.v1 as components

# Permite `streamlit run src/sentinela/app/principal.py` sem instalar o pacote.
RAIZ_SRC = Path(__file__).resolve().parents[2]
if str(RAIZ_SRC) not in sys.path:
    sys.path.insert(0, str(RAIZ_SRC))

from sentinela.app import comparador, estilo  # noqa: E402
from sentinela.dataio import (  # noqa: E402
    ErroArquivo,
    carregar_com_infravermelho,
    em_data_uri,
    indice_em_falsa_cor,
    mapa_de_mudanca,
    par_bitemporal,
    realcar_par,
    resolucao_do_satelite,
    sobrepor_mascara,
)
from sentinela.pdi import filtros, limiar  # noqa: E402
from sentinela.pdi.nucleo import ErroImagem, para_uint8  # noqa: E402
from sentinela.pipeline import (  # noqa: E402
    detectar_desmatamento,
    equilibrar,
    extrair_amostras,
)

st.set_page_config(
    page_title="Sentinela",
    page_icon=":material/satellite_alt:",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _br(valor: float, casas: int) -> str:
    """Número com vírgula decimal — a apresentação e o trabalho escrito são em português."""
    return f"{valor:.{casas}f}".replace(".", ",")


def _subtitulo(texto: str) -> None:
    st.markdown(f'<p class="subtitulo">{texto}</p>', unsafe_allow_html=True)


def _apresentacao(titulo: str, texto: str) -> None:
    """Abertura de cada etapa: o que ela faz, em uma frase."""
    st.markdown(
        f'<div class="etapa"><h3>{titulo}</h3><p>{texto}</p></div>', unsafe_allow_html=True
    )


def mostrar(imagem: np.ndarray, legenda: str) -> None:
    """Exibe um array como imagem, convertendo para ``uint8`` na fronteira."""
    if imagem.dtype == np.bool_:
        # Máscara toda branca (cena inteira vegetada) desaparece no fundo da página e
        # parece imagem faltando. A moldura cinza delimita a área sem alterar o dado.
        imagem = np.pad(imagem.astype(np.float32), 2, constant_values=0.55)
    st.image(para_uint8(imagem), caption=legenda, width="stretch")


def _gravar_upload(arquivo) -> Path:
    destino = Path(st.session_state["_temporarios"]) / arquivo.name
    destino.write_bytes(arquivo.getbuffer())
    return destino


def controles(coluna) -> dict:
    """Fonte das imagens e ajustes do processamento, no painel de entrada."""
    fonte = coluna.segmented_control(
        "Fonte das imagens",
        ("Enviar imagens", "Cena sintética"),
        default="Enviar imagens",
        label_visibility="collapsed",
    ) or "Enviar imagens"

    ajustes = coluna.popover("Ajustes do processamento", icon=":material/tune:", width="stretch")
    metodo = ajustes.selectbox(
        "Índice de vegetação",
        ("auto", "ndvi", "ndmi", "nbr", "vari", "exg"),
        help=(
            "auto usa NDVI quando há banda infravermelha e VARI quando só há o visível. "
            "NDMI e NBR comparam o infravermelho próximo com o SWIR: o NDMI usa o SWIR 1 "
            "(banda 6 do MODIS), o NBR usa o SWIR 2 (banda 7 do MODIS). As imagens do GIBS "
            "trazem só a banda 7. Para elas, use NBR. Nenhum dos dois entra no automático, "
            "porque trocam a grandeza medida."
        ),
    )
    suavizacao = ajustes.slider(
        "Suavização gaussiana (lado do kernel)", 1, 15, 5, step=2,
        help="Aplicada antes da limiarização. Sem ela, o ruído do sensor esburaca a máscara.",
    )
    area_minima = ajustes.slider(
        "Área mínima da região (pixels)", 0, 400, 25,
        help="Descarta fragmentos residuais da segmentação.",
    )

    satelite = ajustes.selectbox(
        "Resolução", ("Sentinel-2 (10 m/px)", "Landsat-8/9 (30 m/px)",
                      "CBERS-4A (8 m/px)", "Desconhecida"),
    )
    mapa_resolucao = {
        "Sentinel-2 (10 m/px)": resolucao_do_satelite("sentinel-2"),
        "Landsat-8/9 (30 m/px)": resolucao_do_satelite("landsat-8"),
        "CBERS-4A (8 m/px)": resolucao_do_satelite("cbers-4a"),
        "Desconhecida": None,
    }

    return {
        "fonte": fonte,
        "metodo": metodo,
        "suavizacao": suavizacao,
        "area_minima": area_minima,
        "metros_por_pixel": mapa_resolucao[satelite],
    }


def obter_imagens(opcoes: dict) -> dict | None:
    """Resolve a fonte escolhida em quatro arrays (RGB e NIR das duas datas)."""
    if opcoes["fonte"].startswith("Cena sintética"):
        st.info(
            "**Cena sintética.** Floresta simulada com um corte de tamanho conhecido, "
            "para conferir a conta. Não é imagem de satélite.",
            icon=":material/science:",
        )
        lado = st.slider("Tamanho da cena (pixels)", 40, 200, 80, step=20)
        area = st.slider("Lado da área desmatada (pixels)", 0, 60, 20, step=5)

        corte = None
        if area > 0:
            inicio = (lado - area) // 2
            corte = (slice(inicio, inicio + area), slice(inicio, inicio + area))

        par = par_bitemporal(corte=corte, tamanho=(lado, lado))
        st.session_state["area_esperada"] = par["area_esperada"]
        return par

    return None


@st.cache_resource
def _memoria() -> dict:
    """Imagens enviadas e último resultado, guardados no processo do app.

    A sessão do Streamlit some quando a página é recarregada (F5). Como o app roda no
    notebook de quem apresenta, uma pessoa por vez, guardar no processo mantém as imagens
    e o resultado depois de recarregar.
    """
    return {"envio": {}, "resultado": None}


_QUADROS = components.declare_component(
    "quadros_de_envio", path=str(Path(__file__).resolve().parent / "quadros")
)


def quadros_de_envio() -> dict | None:
    """Os dois quadros de envio, antes e depois, com a prévia dentro de cada um.

    As imagens ficam guardadas na sessão: trocar para a cena sintética e voltar não as
    perde. O componente devolve o último evento (arquivo enviado ou removido); o ``id``
    evita aplicar o mesmo evento duas vezes.
    """
    st.session_state.pop("area_esperada", None)
    guardadas = _memoria()["envio"]
    previas = {chave: {"nome": nome, "uri": uri} for chave, (nome, _, _, uri) in guardadas.items()}
    evento = _QUADROS(previas=previas, fontes=estilo.fontes_css(), key="quadros", default=None)

    if evento and evento.get("id") != st.session_state.get("_ultimo_evento"):
        st.session_state["_ultimo_evento"] = evento["id"]
        chave = evento["chave"]
        if evento.get("remover"):
            guardadas.pop(chave, None)
        else:
            destino = Path(st.session_state["_temporarios"]) / f"{chave}-{evento['nome']}"
            destino.write_bytes(base64.b64decode(evento["dados"]))
            try:
                cor, nir = carregar_com_infravermelho(destino)
            except ErroArquivo as erro:
                st.session_state["_erro_envio"] = str(erro)
            else:
                st.session_state.pop("_erro_envio", None)
                previa, _ = realcar_par(cor, cor)
                guardadas[chave] = (evento["nome"], cor, nir, em_data_uri(previa, lado_maximo=720))
        st.rerun()

    if st.session_state.get("_erro_envio"):
        st.error(st.session_state["_erro_envio"], icon=":material/block:")

    if "antes" not in guardadas or "depois" not in guardadas:
        st.caption(
            "Use duas imagens da **mesma área**, em datas diferentes e com o mesmo recorte. "
            "Com o infravermelho na quarta banda do PNG, o programa usa NDVI."
        )
        return None

    _, cor_antes, nir_antes, _ = guardadas["antes"]
    _, cor_depois, nir_depois, _ = guardadas["depois"]
    return {
        "rgb_antes": cor_antes,
        "nir_antes": nir_antes,
        "rgb_depois": cor_depois,
        "nir_depois": nir_depois,
    }


def veredito(resultado) -> None:
    """O número que interessa, ou a recusa em produzi-lo, explicada."""
    resumo = resultado.resumo()

    # Com a detecção recusada não há número a mostrar; a decisão fica na etapa 4.
    if resultado.confiavel:
        colunas = st.columns(4)
        colunas[0].metric("Área desmatada", f"{_inteiro(resumo['area_pixels'])} px")
        colunas[1].metric(
            "Em hectares",
            f"{_br(resumo['area_hectares'], 2)} ha"
            if resumo["area_hectares"] is not None
            else "sem escala",
            help="Requer resolução espacial conhecida.",
        )
        colunas[2].metric("Regiões detectadas", resumo["regioes_detectadas"])
        colunas[3].metric("Da cena", f"{_br(resumo['proporcao_da_cena'] * 100, 2)}%")

        esperada = st.session_state.get("area_esperada")
        if esperada:
            erro = abs(resumo["area_pixels"] - esperada) / esperada * 100
            st.caption(
                f"Verdade de terreno da cena sintética: **{esperada} px**. "
                f"Detectado: **{resumo['area_pixels']} px**. Erro de {_br(erro, 1)}%."
            )

    if resultado.alerta_de_registro:
        st.warning(
            "**Ganho de vegetação alto demais.** As duas datas podem não estar "
            "alinhadas, ou a diferença pode ser sazonal e não desmatamento.",
            icon=":material/warning:",
        )


def etapa_aquisicao(imagens: dict, resultado, opcoes: dict) -> None:
    _apresentacao(
        "Aquisição",
        "As duas datas da mesma área.",
    )
    antes, depois = realcar_par(imagens["rgb_antes"], imagens["rgb_depois"])
    col1, col2 = st.columns(2)
    with col1:
        mostrar(antes, "Antes")
    with col2:
        mostrar(depois, "Depois")
    altura, largura = imagens["rgb_antes"].shape[:2]
    bandas = "cor e infravermelho próximo" if imagens.get("nir_antes") is not None else "só cor"
    escala = (
        f"{_br(resultado.metros_por_pixel, 0)} m por pixel"
        if resultado.metros_por_pixel
        else "desconhecida"
    )
    if imagens.get("nir_depois") is not None:
        _subtitulo("Como cada imagem é montada")
        st.caption("Quatro bandas do mesmo instante: três formam a cor, a quarta é o infravermelho.")
        data = st.segmented_control(
            "Data das bandas", ("Antes", "Depois"), default="Depois", key="data_bandas",
            label_visibility="collapsed",
        ) or "Depois"
        sufixo = "antes" if data == "Antes" else "depois"
        rgb, nir = imagens[f"rgb_{sufixo}"], imagens[f"nir_{sufixo}"]
        # Cada banda pintada na cor que representa; o infravermelho, invisível ao olho,
        # ganha um tom de magenta, convenção comum para mostrar essa banda.
        bandas_vistas = (
            (rgb[..., 0], "Vermelho", (1.0, 0.15, 0.15)),
            (rgb[..., 1], "Verde", (0.2, 1.0, 0.3)),
            (rgb[..., 2], "Azul", (0.25, 0.45, 1.0)),
            (nir, "Infravermelho próximo", (1.0, 0.3, 0.85)),
        )
        for coluna, (banda, nome, tinta) in zip(st.columns(4), bandas_vistas):
            with coluna:
                teto = max(float(np.percentile(banda, 99)), 1e-6)
                intensidade = np.clip(banda / teto, 0, 1)[..., None]
                mostrar(intensidade * np.array(tinta, dtype=np.float32), nome)
        st.caption("A floresta é escura no vermelho e clara no infravermelho. O NDVI mede essa diferença.")

    st.dataframe(
        [
            {"Item": "Tamanho", "Valor": f"{_inteiro(largura)} × {_inteiro(altura)} pixels"},
            {"Item": "Bandas", "Valor": bandas},
            {"Item": "Escala", "Valor": escala},
        ],
        width="stretch",
        hide_index=True,
    )


def etapa_indice(imagens: dict, resultado, opcoes: dict) -> None:
    _apresentacao(
        "Manipulação: índice de vegetação",
        f"{resultado.metodo_indice.upper()}: verde é vegetação densa, amarelo é solo exposto.",
    )
    col1, col2 = st.columns(2)
    with col1:
        mostrar(indice_em_falsa_cor(resultado.indice_antes), "Índice antes")
    with col2:
        mostrar(indice_em_falsa_cor(resultado.indice_depois), "Índice depois")


def etapa_filtragem(imagens: dict, resultado, opcoes: dict) -> None:
    _apresentacao(
        "Filtragem",
        "O gaussiano tira o ruído e o Sobel marca a borda entre mata e corte.",
    )
    data = st.segmented_control(
        "Data", ("Antes", "Depois"), default="Depois", key="data_filtragem",
        label_visibility="collapsed",
    ) or "Depois"
    sufixo = "antes" if data == "Antes" else "depois"
    bruto, _ = _indice_sem_suavizar(imagens, opcoes, sufixo)
    suavizado = getattr(resultado, f"indice_{sufixo}")
    recorte, nota = _recorte_central(bruto.shape, data=data.lower())
    col1, col2, col3 = st.columns(3)
    with col1:
        mostrar(bruto[recorte], "Índice bruto")
    with col2:
        mostrar(suavizado[recorte], f"Gaussiano {opcoes['suavizacao']}×{opcoes['suavizacao']}")
    with col3:
        mostrar(filtros.magnitude_gradiente(suavizado)[recorte], "Sobel: magnitude do gradiente")
    if nota:
        st.caption(nota)


def etapa_segmentacao(imagens: dict, resultado, opcoes: dict) -> None:
    _apresentacao(
        "Segmentação",
        f"Um limiar único ({_br(resultado.valor_limiar, 3)}) separa vegetação (branco) de área "
        "aberta. Vermelho no mapa é o que deixou de ser vegetação.",
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        mostrar(resultado.vegetacao_antes, "Vegetação antes (branco)")
    with col2:
        mostrar(resultado.vegetacao_depois, "Vegetação depois (branco)")
    with col3:
        mostrar(mapa_de_mudanca(resultado.mudanca), "Mapa de mudança")
    st.markdown(_legenda_mudanca(), unsafe_allow_html=True)
    decisao_e_regioes(resultado)


def etapa_modelo(imagens: dict, resultado, opcoes: dict) -> None:
    _apresentacao(
        "Modelo",
        "A máscara rotula recortes da imagem, e os recortes treinam o classificador.",
    )
    if not resultado.confiavel:
        st.markdown(
            '<div class="nota"><b>Sem rótulo confiável, o modelo não foi treinado.</b> '
            "A detecção destas imagens foi recusada, e uma máscara recusada não pode virar "
            "rótulo: o modelo aprenderia com um erro. Para ver o modelo treinando, use a "
            "<b>Cena sintética</b>.</div>",
            unsafe_allow_html=True,
        )
        return
    _subtitulo("Amostras rotuladas")
    amostras(imagens, resultado)
    _subtitulo("Classificador")
    classificador(imagens, resultado)


def _recorte_central(forma: tuple, lado: int = 240, data: str = "depois") -> tuple:
    """Recorte do centro, para o efeito de cada filtro aparecer em imagens grandes."""
    altura, largura = forma[:2]
    if max(altura, largura) <= 2 * lado:
        return (slice(None), slice(None)), ""
    topo, esquerda = (altura - lado) // 2, (largura - lado) // 2
    return (
        (slice(topo, topo + lado), slice(esquerda, esquerda + lado)),
        f"Recorte ampliado de {lado} × {lado} pixels do centro da imagem {data}.",
    )


def _legenda_mudanca() -> str:
    """Legenda do mapa de mudança com as cores exatas usadas em ``mapa_de_mudanca``.

    Amostra de cor desenhada em HTML, não emoji: emoji depende de fonte instalada e, sem
    ela, a legenda vira uma fila de quadrados vazios — exatamente o que um screenshot da
    versão entregue mostraria.
    """
    from sentinela.dataio import visual

    def hexa(cor):
        return "#" + "".join(f"{round(c * 255):02x}" for c in cor)

    itens = (
        (visual.COR_PERDA, "perda de vegetação"),
        (visual.COR_GANHO, "ganho"),
        (visual.COR_ESTAVEL_VEGETADO, "vegetação estável"),
        (visual.COR_ESTAVEL_EXPOSTO, "solo exposto nas duas datas"),
    )
    amostras = " &nbsp;&nbsp; ".join(
        f'<span style="display:inline-block;width:0.8em;height:0.8em;'
        f'background:{hexa(cor)};border-radius:2px;vertical-align:-0.05em"></span> {rotulo}'
        for cor, rotulo in itens
    )
    return f"<small>{amostras}</small>"


def _indice_sem_suavizar(imagens: dict, opcoes: dict, data: str = "depois"):
    """Índice cru de uma das datas, para a comparação lado a lado da filtragem."""
    from sentinela.pipeline import preparar_indice

    return preparar_indice(
        imagens[f"rgb_{data}"],
        imagens.get(f"nir_{data}"),
        metodo=opcoes["metodo"],
        suavizacao=1,
        swir=imagens.get(f"swir_{data}"),
    )


def panorama(imagens: dict, resultado) -> None:
    """Comparador das duas datas, com a opção de pintar a perda sobre a imagem depois."""
    camada = st.segmented_control(
        "Camada sobre a imagem depois",
        ("Imagem", "Perda detectada"),
        default="Imagem",
        key="camada_comparador",
        label_visibility="collapsed",
    ) or "Imagem"
    antes, depois = realcar_par(imagens["rgb_antes"], imagens["rgb_depois"])
    if camada == "Perda detectada":
        depois = sobrepor_mascara(depois, resultado.perda)

    altura, largura = imagens["rgb_antes"].shape[:2]
    components.html(
        comparador.html(em_data_uri(antes), em_data_uri(depois), largura / altura),
        height=comparador.ALTURA,
    )
    legenda = "Arraste a linha para comparar as datas. Brilho realçado só para visualização."
    if camada == "Perda detectada" and not resultado.confiavel:
        legenda += " A detecção foi recusada: a perda em vermelho serve só para inspeção."
    st.caption(legenda)


def _inteiro(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def decisao_e_regioes(resultado) -> None:
    """Como o limiar foi decidido e, se a detecção foi aceita, as regiões encontradas."""
    resumo = resultado.resumo()
    _subtitulo("Decisão do limiar")
    st.dataframe(
        [
            {"Medida": "Índice de vegetação", "Valor": resumo["metodo_indice"].upper()},
            {"Medida": "Limiar de Otsu (escala de 0 a 1)", "Valor": _br(resumo["limiar"], 3)},
            {"Medida": "Separação entre as classes", "Valor": _br(resumo["distinguibilidade"], 3)},
            {"Medida": "Mínimo exigido", "Valor": _br(limiar.DISTINGUIBILIDADE_MINIMA, 1)},
            {"Medida": "Resultado", "Valor": "aceito" if resultado.confiavel else "recusado"},
        ],
        width="stretch",
        hide_index=True,
    )

    if not resultado.confiavel:
        st.caption("Com a detecção recusada, as regiões não são listadas.")
        return

    if not resultado.regioes:
        st.success("Nenhuma região de desmatamento acima da área mínima.", icon=":material/forest:")
        return

    _subtitulo("Regiões detectadas")
    linhas = []
    for ordem, regiao in enumerate(resultado.regioes[:15], start=1):
        area_ha = (
            regiao.area_hectares(resultado.metros_por_pixel)
            if resultado.metros_por_pixel
            else None
        )
        linhas.append(
            {
                "#": ordem,
                "Área (px)": _inteiro(regiao.area_pixels),
                "Área (ha)": _br(area_ha, 2) if area_ha is not None else "sem escala",
                "Centro (linha, coluna)": (
                    f"{regiao.centroide[0]:.0f}, {regiao.centroide[1]:.0f}"
                ),
            }
        )
    st.dataframe(linhas, width="stretch", hide_index=True)
    if len(resultado.regioes) > 15:
        st.caption(f"Mostrando as 15 maiores de {len(resultado.regioes)} regiões.")


def amostras(imagens: dict, resultado) -> None:
    """Preparação de dados para o modelo — o objetivo literal do enunciado."""
    st.caption(
        "O objetivo do enunciado (p.2) é usar o PDI como **preparação de dados** para "
        "alimentar um modelo de visão computacional. A máscara de desmatamento serve "
        "de rótulo: cada recorte recebe a classe da região que cobre."
    )

    col1, col2 = st.columns(2)
    lado = col1.slider("Lado do recorte (pixels)", 8, 48, 16, step=8)
    passo = col2.slider("Passo da varredura (pixels)", 4, 48, 8, step=4)

    try:
        conjunto = extrair_amostras(
            imagens["rgb_depois"], resultado.perda, lado=lado, passo=passo
        )
    except ErroImagem as erro:
        st.error(f"Não foi possível extrair amostras: {erro}", icon=":material/block:")
        return

    equilibrado = equilibrar(conjunto)

    colunas = st.columns(4)
    colunas[0].metric("Amostras extraídas", len(conjunto))
    colunas[1].metric("Intacto", conjunto.contagem_por_classe[0])
    colunas[2].metric("Desmatado", conjunto.contagem_por_classe[1])
    colunas[3].metric(
        "Equilíbrio", _br(conjunto.equilibrio, 2),
        help="Razão entre a classe minoritária e a majoritária. Perto de 0 = desbalanceado.",
    )

    st.caption(
        f"{conjunto.descartados_ambiguos} recortes ambíguos foram **descartados**: "
        "eles pegam parte de floresta e parte de corte. Rotulá-los pela classe "
        "majoritária ensinaria o classificador a responder pela vizinhança."
    )

    if len(equilibrado):
        _subtitulo(f"Conjunto equilibrado por subamostragem: {len(equilibrado)} amostras")
        amostrar = min(8, len(equilibrado))
        colunas = st.columns(amostrar)
        for coluna, indice in zip(colunas, range(amostrar)):
            with coluna:
                mostrar(
                    equilibrado.recortes[indice],
                    "desmatado" if equilibrado.rotulos[indice] == 1 else "intacto",
                )
    else:
        st.info(
            "Sem amostras das duas classes não há conjunto de treino. Aumente a área "
            "desmatada, reduza o lado do recorte ou diminua o passo.",
            icon=":material/info:",
        )


def classificador(imagens: dict, resultado) -> None:
    """Classificador treinado sobre as amostras rotuladas."""
    from sentinela.modelo import ErroModelo, treinar_e_avaliar

    st.caption(
        "Floresta aleatória treinada sobre os recortes rotulados. As **features saem do "
        "núcleo de PDI do grupo** (`pdi.filtros.desvio_padrao_local`, "
        "`pdi.cor.exg`, ...); o scikit-learn entra só no algoritmo de aprendizado, que o "
        "enunciado permite."
    )

    col1, col2, col3 = st.columns(3)
    lado = col1.slider("Lado do recorte", 8, 32, 16, step=8, key="modelo_lado")
    proporcao = col2.slider("Fração para teste", 0.1, 0.5, 0.3, step=0.1)
    semente = col3.number_input("Semente do sorteio de blocos", 0, 999, 0)

    try:
        conjunto = extrair_amostras(
            imagens["rgb_depois"], resultado.perda, lado=lado, passo=lado // 2
        )
    except ErroImagem as erro:
        st.error(f"Não foi possível extrair amostras: {erro}", icon=":material/block:")
        return

    st.info(
        "**Treino e teste são separados por blocos da imagem, não por sorteio de "
        "recorte.** Os recortes se sobrepõem: sortear individualmente colocaria o mesmo "
        "pedaço de terreno nos dois lados e a acurácia medida seria vazamento. Recortes "
        "que cruzam fronteira de bloco são descartados.",
        icon=":material/explore:",
    )

    try:
        modelo, avaliacao = treinar_e_avaliar(
            conjunto, proporcao_teste=proporcao, semente=int(semente)
        )
    except ErroModelo as erro:
        st.warning(f"**Modelo não treinado.** {erro}", icon=":material/warning:")
        return

    resumo = avaliacao.resumo()
    colunas = st.columns(4)
    colunas[0].metric("Acurácia", _br(resumo['acuracia'], 3))
    colunas[1].metric("Precisão", _br(resumo['precisao'], 3))
    colunas[2].metric(
        "Revocação", _br(resumo['revocacao'], 3),
        help="Fração do desmatamento real que o modelo encontrou.",
    )
    colunas[3].metric("F1", _br(resumo['f1'], 3))

    for aviso in avaliacao.avisos:
        st.warning(aviso, icon=":material/warning:")

    col1, col2 = st.columns(2)

    with col1:
        _subtitulo("Matriz de confusão")
        matriz = resumo["matriz_confusao"]
        st.dataframe(
            [
                {"Resultado": "Intacto classificado como intacto",
                 "Amostras": matriz["intacto_correto"]},
                {"Resultado": "Desmatamento encontrado",
                 "Amostras": matriz["desmatamento_correto"]},
                {"Resultado": "Falso alarme", "Amostras": matriz["falso_alarme"]},
                {"Resultado": "Desmatamento perdido",
                 "Amostras": matriz["desmatamento_perdido"]},
            ],
            width="stretch",
            hide_index=True,
        )
        st.caption(
            f"{resumo['amostras_de_teste']} amostras de teste, de blocos que o modelo "
            "não viu no treino."
        )

    with col2:
        _subtitulo("O que pesou na decisão")
        importancias = modelo.importancia_das_features()
        st.dataframe(
            [{"Descritor": nome, "Peso": _br(peso, 3)} for nome, peso in importancias[:8]],
            width="stretch",
            hide_index=True,
        )
        st.caption(
            "Peso de cada descritor na decisão do modelo."
        )


def _assinatura(imagens: dict, opcoes: dict) -> tuple:
    """Identifica as imagens e os parâmetros, para saber se o resultado guardado ainda vale."""
    bandas = tuple(
        (nome, imagem.shape, round(float(imagem.sum()), 3))
        for nome, imagem in sorted(imagens.items())
        if isinstance(imagem, np.ndarray)
    )
    parametros = tuple(sorted((k, str(v)) for k, v in opcoes.items()))
    return bandas, parametros


def _detectar(imagens: dict, opcoes: dict):
    indicador = st.empty()
    feitas = []

    def avisar(etapa: str) -> None:
        feitas.append(etapa)
        indicador.markdown(
            f'<div class="progresso" role="status"><span class="giro" aria-hidden="true"></span>'
            f"<span>Etapa {len(feitas)} de 5: {etapa}</span></div>",
            unsafe_allow_html=True,
        )

    try:
        resultado = detectar_desmatamento(
            imagens["rgb_antes"],
            imagens["rgb_depois"],
            imagens.get("nir_antes"),
            imagens.get("nir_depois"),
            swir_antes=imagens.get("swir_antes"),
            swir_depois=imagens.get("swir_depois"),
            metodo=opcoes["metodo"],
            suavizacao=opcoes["suavizacao"],
            area_minima=opcoes["area_minima"],
            metros_por_pixel=opcoes["metros_por_pixel"],
            progresso=avisar,
        )
    finally:
        indicador.empty()
    return resultado


def _resultado(imagens: dict | None, opcoes: dict):
    """Detecta na hora para a cena sintética; para imagens enviadas, só ao clicar em Processar.

    O resultado das imagens enviadas fica guardado na sessão: trocar de aba ou mexer num
    controle da página não refaz um processamento que leva vários segundos.
    """
    try:
        if not opcoes["fonte"].startswith("Enviar"):
            return _detectar(imagens, opcoes) if imagens is not None else None

        clicou = st.button(
            "Processar imagens", type="primary", icon=":material/play_arrow:",
            width="stretch", disabled=imagens is None,
        )
        if imagens is None:
            st.caption("Envie as duas imagens para liberar o processamento.")
            return None
        assinatura = _assinatura(imagens, opcoes)
        if clicou:
            _memoria()["resultado"] = (assinatura, _detectar(imagens, opcoes))
            # Recarrega para recolher os quadros de envio e abrir espaço para o resultado.
            st.rerun()
    except ErroImagem as erro:
        st.error(f"**Não foi possível processar:** {erro}", icon=":material/block:")
        return None

    guardado = _memoria()["resultado"]
    if guardado is None or guardado[0] != assinatura:
        return None
    return guardado[1]


ETAPAS = (
    ("1  Aquisição", etapa_aquisicao),
    ("2  Índice", etapa_indice),
    ("3  Filtragem", etapa_filtragem),
    ("4  Segmentação", etapa_segmentacao),
    ("5  Modelo", etapa_modelo),
)


def principal() -> None:
    st.html(estilo.folha_de_estilo())
    st.markdown(
        f'<header class="topo">{estilo.MARCA_SVG}<b>Sentinela</b>'
        "<span>Detecção de desmatamento em imagens de satélite</span></header>",
        unsafe_allow_html=True,
    )
    if "_temporarios" not in st.session_state:
        import tempfile

        st.session_state["_temporarios"] = tempfile.mkdtemp(prefix="sentinela-")

    entrada, analise = st.columns([1, 2.5], gap="large")
    painel = entrada.container(key="entrada")
    with painel:
        _subtitulo("Imagens")
        opcoes = controles(st)

    imagens = None
    enviar = opcoes["fonte"].startswith("Enviar")
    try:
        if enviar:
            ja_processado = _memoria()["resultado"] is not None
            with analise:
                local = st.expander("Imagens enviadas") if ja_processado else st.container()
                with local:
                    imagens = quadros_de_envio()
        else:
            with painel:
                imagens = obter_imagens(opcoes)
    except (ErroArquivo, ErroImagem) as erro:
        with painel:
            st.error(str(erro), icon=":material/block:")

    with painel:
        resultado = _resultado(imagens, opcoes)

    if resultado is not None:
        with analise:
            veredito(resultado)
            panorama(imagens, resultado)

    if resultado is None:
        return

    st.markdown('<h2 class="trilho">Etapas do processamento</h2>', unsafe_allow_html=True)
    etapas = ETAPAS if resultado.confiavel else ETAPAS[:4]
    abas = st.tabs([nome for nome, _ in etapas])
    for aba, (_, desenhar) in zip(abas, etapas):
        with aba:
            desenhar(imagens, resultado, opcoes)


if __name__ == "__main__":
    principal()
