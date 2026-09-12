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

import sys
from pathlib import Path

import numpy as np
import streamlit as st

# Permite `streamlit run src/sentinela/app/principal.py` sem instalar o pacote.
RAIZ_SRC = Path(__file__).resolve().parents[2]
if str(RAIZ_SRC) not in sys.path:
    sys.path.insert(0, str(RAIZ_SRC))

from sentinela.dataio import (  # noqa: E402
    ErroArquivo,
    carregar,
    indice_em_falsa_cor,
    mapa_de_mudanca,
    par_bitemporal,
    resolucao_do_satelite,
    sobrepor_mascara,
)
from sentinela.pdi import filtros  # noqa: E402
from sentinela.pdi.nucleo import ErroImagem, para_uint8  # noqa: E402
from sentinela.pipeline import (  # noqa: E402
    detectar_desmatamento,
    equilibrar,
    extrair_amostras,
)

st.set_page_config(page_title="Sentinela — detecção de desmatamento", layout="wide")


def mostrar(imagem: np.ndarray, legenda: str) -> None:
    """Exibe um array como imagem, convertendo para ``uint8`` na fronteira."""
    if imagem.dtype == np.bool_:
        imagem = imagem.astype(np.float32)
    st.image(para_uint8(imagem), caption=legenda, width="stretch")


def ler_upload(arquivo, *, cinza: bool = False) -> np.ndarray | None:
    """Carrega um arquivo enviado pelo navegador, gravando num temporário."""
    if arquivo is None:
        return None

    destino = Path(st.session_state["_temporarios"]) / arquivo.name
    destino.write_bytes(arquivo.getbuffer())
    return carregar(destino, cinza=cinza)


def barra_lateral() -> dict:
    """Monta os controles e devolve as escolhas do usuário."""
    st.sidebar.title("Sentinela")
    st.sidebar.caption("APS — Processamento de Imagens e Visão Computacional · UNIP 2026/2")

    fonte = st.sidebar.radio(
        "Fonte das imagens",
        ("Cena sintética (demonstração)", "Enviar imagens"),
        help="A cena sintética serve para demonstrar o programa; ela não é evidência.",
    )

    st.sidebar.subheader("Parâmetros do processamento")
    metodo = st.sidebar.selectbox(
        "Índice de vegetação",
        ("auto", "ndvi", "vari", "exg"),
        help="auto usa NDVI quando há banda infravermelha e VARI quando só há o visível.",
    )
    suavizacao = st.sidebar.slider(
        "Suavização gaussiana (lado do kernel)", 1, 15, 5, step=2,
        help="Aplicada antes da limiarização. Sem ela, o ruído do sensor esburaca a máscara.",
    )
    area_minima = st.sidebar.slider(
        "Área mínima da região (pixels)", 0, 400, 25,
        help="Descarta fragmentos residuais da segmentação.",
    )

    st.sidebar.subheader("Escala espacial")
    satelite = st.sidebar.selectbox(
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
            "**Cena sintética.** Floresta simulada com uma área de corte de tamanho "
            "conhecido, usada para demonstrar o programa e conferir a quantificação. "
            "Não é imagem de satélite e não entra no trabalho escrito como evidência.",
            icon="🧪",
        )
        col1, col2 = st.columns(2)
        lado = col1.slider("Tamanho da cena (pixels)", 40, 200, 80, step=20)
        area = col2.slider("Lado da área desmatada (pixels)", 0, 60, 20, step=5)

        corte = None
        if area > 0:
            inicio = (lado - area) // 2
            corte = (slice(inicio, inicio + area), slice(inicio, inicio + area))

        par = par_bitemporal(corte=corte, tamanho=(lado, lado))
        st.session_state["area_esperada"] = par["area_esperada"]
        return par

    st.session_state.pop("area_esperada", None)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Data 1 — antes**")
        rgb_antes = st.file_uploader("RGB antes", type=["png", "jpg", "jpeg", "tif"])
        nir_antes = st.file_uploader("Infravermelho antes (opcional)",
                                     type=["png", "jpg", "jpeg", "tif"])
    with col2:
        st.markdown("**Data 2 — depois**")
        rgb_depois = st.file_uploader("RGB depois", type=["png", "jpg", "jpeg", "tif"])
        nir_depois = st.file_uploader("Infravermelho depois (opcional)",
                                      type=["png", "jpg", "jpeg", "tif"])

    if rgb_antes is None or rgb_depois is None:
        st.warning(
            "Envie as duas datas da **mesma área**, recortadas sobre o mesmo extent. "
            "Sem infravermelho o sistema usa VARI, que trabalha só com o visível.",
            icon="📂",
        )
        return None

    return {
        "rgb_antes": ler_upload(rgb_antes),
        "nir_antes": ler_upload(nir_antes, cinza=True),
        "rgb_depois": ler_upload(rgb_depois),
        "nir_depois": ler_upload(nir_depois, cinza=True),
    }


def painel_resultado(resultado, opcoes: dict) -> None:
    """Cabeçalho com o número que interessa — ou a recusa em produzi-lo."""
    resumo = resultado.resumo()

    if not resultado.confiavel:
        st.error(
            f"**Detecção não confiável — nenhuma área é reportada.**\n\n"
            f"A distinguibilidade entre as duas classes ficou em "
            f"`{resumo['distinguibilidade']}`, abaixo do mínimo de `4.0`. Isso acontece "
            f"quando a cena é homogênea: sem duas classes reais para separar, o limiar "
            f"automático corta o ruído do dossel ao meio e produziria desmatamento onde "
            f"não houve. Recusar o número é a resposta correta.",
            icon="🚫",
        )
    else:
        colunas = st.columns(4)
        colunas[0].metric("Área desmatada", f"{resumo['area_pixels']} px")
        colunas[1].metric(
            "Em hectares",
            f"{resumo['area_hectares']:.2f} ha"
            if resumo["area_hectares"] is not None
            else "—",
            help="Requer resolução espacial conhecida.",
        )
        colunas[2].metric("Regiões detectadas", resumo["regioes_detectadas"])
        colunas[3].metric("Da cena", f"{resumo['proporcao_da_cena'] * 100:.2f}%")

        esperada = st.session_state.get("area_esperada")
        if esperada:
            erro = abs(resumo["area_pixels"] - esperada) / esperada * 100
            st.caption(
                f"Verdade de terreno da cena sintética: **{esperada} px**. "
                f"Detectado: **{resumo['area_pixels']} px** — erro de {erro:.1f}%."
            )

    if resultado.alerta_de_registro:
        st.warning(
            "**Ganho de vegetação alto demais.** As duas datas podem não estar "
            "alinhadas, ou a diferença pode ser sazonal e não desmatamento. "
            "Inspecione o mapa de mudança antes de usar este resultado.",
            icon="⚠️",
        )


def aba_etapas(imagens: dict, resultado, opcoes: dict) -> None:
    """As cinco etapas do enunciado, uma seção cada."""
    st.subheader("1 · Aquisição")
    col1, col2 = st.columns(2)
    with col1:
        mostrar(imagens["rgb_antes"], "Data 1 — antes")
    with col2:
        mostrar(imagens["rgb_depois"], "Data 2 — depois")

    st.subheader("2 · Manipulação — índice de vegetação")
    st.caption(
        f"Índice em uso: **{resultado.metodo_indice.upper()}**. "
        "Verde = vegetação densa, marrom = solo exposto."
    )
    col1, col2 = st.columns(2)
    with col1:
        mostrar(indice_em_falsa_cor(resultado.indice_antes), "Índice — antes")
    with col2:
        mostrar(indice_em_falsa_cor(resultado.indice_depois), "Índice — depois")

    st.subheader("3 · Filtragem")
    st.caption(
        "Filtros implementados pelo grupo, com NumPy puro — exigência do enunciado "
        "(p.3, item 3.a). Nenhuma chamada a OpenCV ou scikit-image."
    )
    col1, col2, col3 = st.columns(3)
    bruto, _ = _indice_sem_suavizar(imagens, opcoes)
    with col1:
        mostrar(bruto, "Índice bruto")
    with col2:
        mostrar(resultado.indice_depois, f"Gaussiano {opcoes['suavizacao']}×{opcoes['suavizacao']}")
    with col3:
        mostrar(filtros.magnitude_gradiente(resultado.indice_depois), "Sobel — magnitude do gradiente")

    st.subheader("4 · Segmentação")
    st.caption(
        f"Limiar de Otsu **único** para as duas datas: `{resultado.valor_limiar:.4f}`. "
        "Calcular um limiar por data daria réguas diferentes, e a comparação mediria a "
        "diferença entre os limiares, não a mudança no terreno."
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        mostrar(resultado.vegetacao_antes, "Vegetação — antes")
    with col2:
        mostrar(resultado.vegetacao_depois, "Vegetação — depois")
    with col3:
        mostrar(mapa_de_mudanca(resultado.mudanca), "Mapa de mudança")

    st.markdown(
        "<small>🟥 perda de vegetação &nbsp;·&nbsp; 🟩 ganho &nbsp;·&nbsp; "
        "🌲 vegetação estável &nbsp;·&nbsp; ⬜ solo exposto nas duas datas</small>",
        unsafe_allow_html=True,
    )


def _indice_sem_suavizar(imagens: dict, opcoes: dict):
    """Índice cru da segunda data, para a comparação lado a lado da filtragem."""
    from sentinela.pipeline import preparar_indice

    return preparar_indice(
        imagens["rgb_depois"],
        imagens.get("nir_depois"),
        metodo=opcoes["metodo"],
        suavizacao=1,
    )


def aba_deteccao(imagens: dict, resultado) -> None:
    """Sobreposição e tabela de regiões."""
    if not resultado.confiavel:
        st.info(
            "A máscara abaixo é exibida para inspeção, mas **não deve ser usada como "
            "resultado** enquanto a detecção estiver marcada como não confiável.",
            icon="ℹ️",
        )

    col1, col2 = st.columns([3, 2])
    with col1:
        mostrar(
            sobrepor_mascara(imagens["rgb_depois"], resultado.perda),
            "Áreas desmatadas sobre a imagem de depois",
        )
    with col2:
        if resultado.regioes:
            st.markdown("**Regiões detectadas**")
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
                        "Área (px)": regiao.area_pixels,
                        "Área (ha)": round(area_ha, 3) if area_ha is not None else "—",
                        "Centro (lin, col)": (
                            f"{regiao.centroide[0]:.0f}, {regiao.centroide[1]:.0f}"
                        ),
                    }
                )
            st.dataframe(linhas, width="stretch", hide_index=True)
            if len(resultado.regioes) > 15:
                st.caption(f"Mostrando as 15 maiores de {len(resultado.regioes)} regiões.")
        else:
            st.success("Nenhuma região de desmatamento acima da área mínima.", icon="🌳")

    with st.expander("Métricas de decisão do limiar"):
        st.json(resultado.resumo())


def aba_amostras(imagens: dict, resultado) -> None:
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
        st.error(f"Não foi possível extrair amostras: {erro}", icon="🚫")
        return

    equilibrado = equilibrar(conjunto)

    colunas = st.columns(4)
    colunas[0].metric("Amostras extraídas", len(conjunto))
    colunas[1].metric("Intacto", conjunto.contagem_por_classe[0])
    colunas[2].metric("Desmatado", conjunto.contagem_por_classe[1])
    colunas[3].metric(
        "Equilíbrio", f"{conjunto.equilibrio:.2f}",
        help="Razão entre a classe minoritária e a majoritária. Perto de 0 = desbalanceado.",
    )

    st.caption(
        f"{conjunto.descartados_ambiguos} recortes ambíguos foram **descartados** — "
        "eles pegam parte de floresta e parte de corte. Rotulá-los pela classe "
        "majoritária ensinaria o classificador a responder pela vizinhança."
    )

    if len(equilibrado):
        st.markdown(f"**Conjunto equilibrado por subamostragem — {len(equilibrado)} amostras**")
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
            icon="ℹ️",
        )


def aba_modelo(imagens: dict, resultado) -> None:
    """Etapa 5 — classificador treinado sobre as amostras rotuladas."""
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
        st.error(f"Não foi possível extrair amostras: {erro}", icon="🚫")
        return

    st.info(
        "**Treino e teste são separados por blocos da imagem, não por sorteio de "
        "recorte.** Os recortes se sobrepõem: sortear individualmente colocaria o mesmo "
        "pedaço de terreno nos dois lados e a acurácia medida seria vazamento. Recortes "
        "que cruzam fronteira de bloco são descartados.",
        icon="🧭",
    )

    try:
        classificador, avaliacao = treinar_e_avaliar(
            conjunto, proporcao_teste=proporcao, semente=int(semente)
        )
    except ErroModelo as erro:
        st.warning(f"**Modelo não treinado.** {erro}", icon="⚠️")
        return

    resumo = avaliacao.resumo()
    colunas = st.columns(4)
    colunas[0].metric("Acurácia", f"{resumo['acuracia']:.3f}")
    colunas[1].metric("Precisão", f"{resumo['precisao']:.3f}")
    colunas[2].metric(
        "Revocação", f"{resumo['revocacao']:.3f}",
        help="Fração do desmatamento real que o modelo encontrou.",
    )
    colunas[3].metric("F1", f"{resumo['f1']:.3f}")

    for aviso in avaliacao.avisos:
        st.warning(aviso, icon="⚠️")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Matriz de confusão**")
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
        st.markdown("**O que pesou na decisão**")
        importancias = classificador.importancia_das_features()
        st.dataframe(
            [{"Feature": nome, "Peso": round(peso, 4)} for nome, peso in importancias[:8]],
            width="stretch",
            hide_index=True,
        )
        st.caption(
            "É o que permite responder *por que o modelo classificou assim* na "
            "apresentação."
        )


def principal() -> None:
    st.title("Sentinela — detecção e quantificação de desmatamento")
    st.caption(
        "Compara a mesma região em duas datas, segmenta a perda de cobertura vegetal "
        "e prepara recortes rotulados para um modelo de visão computacional."
    )

    if "_temporarios" not in st.session_state:
        import tempfile

        st.session_state["_temporarios"] = tempfile.mkdtemp(prefix="sentinela-")

    opcoes = barra_lateral()

    try:
        imagens = obter_imagens(opcoes)
    except (ErroArquivo, ErroImagem) as erro:
        st.error(str(erro), icon="🚫")
        return

    if imagens is None:
        return

    try:
        resultado = detectar_desmatamento(
            imagens["rgb_antes"],
            imagens["rgb_depois"],
            imagens.get("nir_antes"),
            imagens.get("nir_depois"),
            metodo=opcoes["metodo"],
            suavizacao=opcoes["suavizacao"],
            area_minima=opcoes["area_minima"],
            metros_por_pixel=opcoes["metros_por_pixel"],
        )
    except ErroImagem as erro:
        st.error(f"**Não foi possível processar:** {erro}", icon="🚫")
        return

    painel_resultado(resultado, opcoes)

    etapas, deteccao, amostras, classificacao = st.tabs(
        ["Etapas do processamento", "Detecção", "Amostras para o modelo", "Modelo"]
    )
    with etapas:
        aba_etapas(imagens, resultado, opcoes)
    with deteccao:
        aba_deteccao(imagens, resultado)
    with amostras:
        aba_amostras(imagens, resultado)
    with classificacao:
        aba_modelo(imagens, resultado)


if __name__ == "__main__":
    principal()
