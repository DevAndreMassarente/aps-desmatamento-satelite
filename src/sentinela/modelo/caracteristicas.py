"""Descritores extraídos de cada recorte — a ponte entre o PDI e o classificador.

Etapa 5 do enunciado (p.3, item 2.e.v e 3.b). Cada recorte rotulado por
``pipeline.extrair_amostras`` vira um vetor de números que o classificador consegue
comparar.

**Todas as features saem de `pdi/`**, o núcleo implementado pelo grupo: não há descritor
vindo pronto de biblioteca. Isso mantém a exigência do enunciado de ponta a ponta — se o
professor perguntar de onde vem a textura, a resposta é `pdi.filtros.desvio_padrao_local`,
e o algoritmo está no repositório.

A escolha das features é deliberadamente **explicável**. Um descritor profundo daria
acurácia maior, mas o grupo precisa saber defender por que cada número existe
(`AGENTS.md` §12).

## Limitação conhecida das features de textura

`textura_media` e `textura_maxima` são justificadas pela literatura — dossel fechado é
irregular e produz desvio local alto, solo exposto e pasto são lisos e produzem desvio
baixo. **Na cena sintética isso não é observável**, porque o gerador aplica o mesmo
desvio de ruído às duas classes. Elas continuam no vetor porque devem separar em imagem
real, mas até R032 essa é uma hipótese, não um resultado. Não apresentar como validada.
"""

from __future__ import annotations

import numpy as np

from ..pdi import cor, filtros
from ..pdi.nucleo import ErroImagem, validar_imagem

# Vizinhança das medidas de textura. 5×5 num recorte de 16×16 cobre área suficiente
# para capturar a irregularidade do dossel sem virar estatística da imagem inteira.
JANELA_TEXTURA = 5

NOMES_DAS_FEATURES = (
    "media_vermelho",
    "media_verde",
    "media_azul",
    "desvio_vermelho",
    "desvio_verde",
    "desvio_azul",
    "media_exg",
    "desvio_exg",
    "media_vari",
    "textura_media",
    "textura_maxima",
    "borda_media",
    "brilho_p10",
    "brilho_mediana",
    "brilho_p90",
)


def descrever_recorte(recorte: np.ndarray) -> np.ndarray:
    """Extrai o vetor de características de **um** recorte RGB.

    A ordem dos valores corresponde a ``NOMES_DAS_FEATURES`` — a correspondência importa
    porque é ela que permite dizer, no trabalho escrito, qual medida o classificador
    considerou mais informativa.
    """
    recorte = validar_imagem(recorte, bandas_aceitas=(3,))

    cinza = cor.para_cinza(recorte)
    indice_exg = cor.exg(recorte)
    indice_vari = cor.vari(recorte)

    # Textura: floresta tem dossel irregular e desvio local alto; solo exposto e pasto
    # são homogêneos. Sozinha esta medida já separa razoavelmente as duas classes.
    textura = filtros.desvio_padrao_local(cinza, tamanho=JANELA_TEXTURA)

    # Borda: a fronteira entre floresta e corte produz gradiente forte.
    borda = filtros.magnitude_gradiente(cinza)

    return np.array(
        [
            recorte[:, :, 0].mean(),
            recorte[:, :, 1].mean(),
            recorte[:, :, 2].mean(),
            recorte[:, :, 0].std(),
            recorte[:, :, 1].std(),
            recorte[:, :, 2].std(),
            indice_exg.mean(),
            indice_exg.std(),
            indice_vari.mean(),
            textura.mean(),
            textura.max(),
            borda.mean(),
            np.percentile(cinza, 10),
            np.percentile(cinza, 50),
            np.percentile(cinza, 90),
        ],
        dtype=np.float32,
    )


def extrair_caracteristicas(recortes: np.ndarray) -> np.ndarray:
    """Transforma ``[N, lado, lado, 3]`` em ``[N, 15]``.

    Devolve matriz vazia com a quantidade certa de colunas quando não há recorte
    nenhum — assim quem chama não precisa tratar o caso vazio de forma diferente.
    """
    recortes = np.asarray(recortes)

    if recortes.ndim != 4:
        raise ErroImagem(
            f"esperado [N, lado, lado, bandas], recebido formato {recortes.shape}"
        )
    if recortes.shape[0] == 0:
        return np.empty((0, len(NOMES_DAS_FEATURES)), dtype=np.float32)
    if recortes.shape[3] != 3:
        raise ErroImagem(
            f"as features assumem recorte RGB; recebido {recortes.shape[3]} bandas"
        )

    return np.stack([descrever_recorte(recorte) for recorte in recortes]).astype(
        np.float32
    )
