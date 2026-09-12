"""Classificador de desmatamento sobre os recortes rotulados.

Etapa 5 — item 3.b do enunciado. Recebe o conjunto produzido por
``pipeline.extrair_amostras``, descreve cada recorte com ``caracteristicas`` e treina um
classificador do scikit-learn.

`scikit-learn` é permitido **aqui** (`AGENTS.md` §5): a restrição de implementação
própria vale para os filtros, não para o algoritmo de aprendizado. As features, essas
sim, saem todas do núcleo do grupo.

Floresta aleatória foi escolhida por ser defensável numa banca: ela informa quais
features pesaram na decisão, o que permite responder "por que o modelo classificou este
recorte como desmatado?" apontando para uma medida concreta. Uma rede convolucional
daria acurácia maior e nenhuma resposta a essa pergunta.

## A divisão espacial

O ponto metodológico que mais afeta o resultado está em ``dividir_espacialmente``. Os
recortes se sobrepõem, porque a varredura usa passo menor que o lado. Uma divisão
aleatória entre treino e teste colocaria **o mesmo pixel nos dois lados**, e a acurácia
medida seria fantasia. A divisão por faixa da imagem, com uma faixa-tampão descartada
entre elas, é o que torna a métrica honesta.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..pipeline.amostras import DESMATADO, INTACTO, ConjuntoDeAmostras
from .caracteristicas import NOMES_DAS_FEATURES, extrair_caracteristicas

# Abaixo disto a métrica de teste é ruído: com 10 amostras, um acerto a mais move a
# acurácia em 10 pontos. O número não é omitido, mas vem acompanhado de aviso.
AMOSTRAS_MINIMAS_PARA_METRICA = 20


class ErroModelo(RuntimeError):
    """Uso inválido do classificador — treino sem dado, previsão sem treino."""


@dataclass(frozen=True)
class Avaliacao:
    """Resultado de uma avaliação, com os avisos que o número sozinho esconde."""

    acuracia: float
    precisao: float
    revocacao: float
    f1: float
    matriz_confusao: np.ndarray
    total_teste: int
    avisos: tuple[str, ...] = ()

    def resumo(self) -> dict[str, object]:
        verdadeiro_negativo, falso_positivo, falso_negativo, verdadeiro_positivo = (
            self.matriz_confusao.ravel()
        )
        return {
            "acuracia": round(self.acuracia, 4),
            "precisao": round(self.precisao, 4),
            "revocacao": round(self.revocacao, 4),
            "f1": round(self.f1, 4),
            "amostras_de_teste": self.total_teste,
            "matriz_confusao": {
                "intacto_correto": int(verdadeiro_negativo),
                "falso_alarme": int(falso_positivo),
                "desmatamento_perdido": int(falso_negativo),
                "desmatamento_correto": int(verdadeiro_positivo),
            },
            "avisos": list(self.avisos),
        }


def dividir_espacialmente(
    conjunto: ConjuntoDeAmostras,
    *,
    proporcao_teste: float = 0.3,
    tamanho_bloco: int | None = None,
    semente: int = 0,
) -> tuple[ConjuntoDeAmostras, ConjuntoDeAmostras]:
    """Separa treino e teste por **blocos da imagem**, não por sorteio de recorte.

    A varredura usa passo menor que o lado do recorte, então recortes vizinhos
    compartilham pixels. Sortear recortes individualmente colocaria o mesmo pedaço de
    terreno nos dois conjuntos, e a acurácia medida seria vazamento, não generalização.

    Aqui a imagem é dividida em blocos quadrados, o **bloco** é sorteado para treino ou
    teste, e só entram recortes que cabem inteiros dentro de um bloco. Como os blocos são
    disjuntos, nenhum recorte de treino compartilha um pixel com um recorte de teste.

    O sorteio por bloco — em vez de um corte único ao meio — importa porque desmatamento
    costuma ser espacialmente concentrado: um corte único tende a deixar toda a área
    desmatada de um lado só, e o conjunto de teste fica com uma classe única.

    Recortes que cruzam fronteira de bloco são descartados. É o preço da separação.
    """
    if not 0.0 < proporcao_teste < 1.0:
        raise ErroModelo(
            f"proporcao_teste deve estar em (0, 1), recebido {proporcao_teste}"
        )
    if len(conjunto) == 0:
        return conjunto, conjunto

    lado = int(conjunto.recortes.shape[1])
    bloco = tamanho_bloco if tamanho_bloco is not None else 3 * lado

    if bloco < lado:
        raise ErroModelo(
            f"tamanho_bloco ({bloco}) precisa ser ao menos o lado do recorte ({lado})"
        )

    # Só entram recortes que cabem inteiros num bloco; os que cruzam fronteira sairiam
    # parcialmente para o outro conjunto e reintroduziriam o vazamento.
    dentro = [
        indice
        for indice, (linha, coluna) in enumerate(conjunto.posicoes)
        if linha % bloco + lado <= bloco and coluna % bloco + lado <= bloco
    ]

    blocos = sorted(
        {
            (conjunto.posicoes[i][0] // bloco, conjunto.posicoes[i][1] // bloco)
            for i in dentro
        }
    )
    if len(blocos) < 2:
        raise ErroModelo(
            f"a cena rende {len(blocos)} bloco(s) de {bloco}x{bloco} px — não dá para "
            "separar treino de teste sem compartilhar terreno. Use uma imagem maior, um "
            "recorte menor, ou reduza tamanho_bloco."
        )

    gerador = np.random.default_rng(semente)
    embaralhados = list(blocos)
    gerador.shuffle(embaralhados)
    quantidade_teste = max(1, round(len(blocos) * proporcao_teste))
    blocos_de_teste = set(map(tuple, embaralhados[:quantidade_teste]))

    def fatiar(indices: list[int]) -> ConjuntoDeAmostras:
        return ConjuntoDeAmostras(
            recortes=conjunto.recortes[indices],
            rotulos=conjunto.rotulos[indices],
            posicoes=[conjunto.posicoes[i] for i in indices],
            descartados_ambiguos=conjunto.descartados_ambiguos,
        )

    def no_teste(indice: int) -> bool:
        linha, coluna = conjunto.posicoes[indice]
        return (linha // bloco, coluna // bloco) in blocos_de_teste

    return (
        fatiar([i for i in dentro if not no_teste(i)]),
        fatiar([i for i in dentro if no_teste(i)]),
    )


class ClassificadorDesmatamento:
    """Envolve o classificador do scikit-learn com as regras deste projeto.

    Mantém a lista de nomes das features junto do modelo treinado, para que a
    importância relatada possa ser lida sem consultar outro arquivo.
    """

    def __init__(self, *, arvores: int = 100, semente: int = 0, profundidade: int | None = None):
        try:
            from sklearn.ensemble import RandomForestClassifier
        except ImportError as erro:  # pragma: no cover - depende do ambiente
            raise ErroModelo(
                "a etapa de modelo requer scikit-learn. Instale o extra:\n"
                '  pip install -e ".[modelo]"'
            ) from erro

        self._modelo = RandomForestClassifier(
            n_estimators=arvores,
            max_depth=profundidade,
            random_state=semente,
            class_weight="balanced",
        )
        self._treinado = False
        self.nomes_das_features = NOMES_DAS_FEATURES

    @property
    def treinado(self) -> bool:
        return self._treinado

    def treinar(self, conjunto: ConjuntoDeAmostras) -> "ClassificadorDesmatamento":
        """Ajusta o modelo. Exige as duas classes presentes."""
        if len(conjunto) == 0:
            raise ErroModelo("não há amostras para treinar")

        contagens = conjunto.contagem_por_classe
        if contagens[INTACTO] == 0 or contagens[DESMATADO] == 0:
            raise ErroModelo(
                f"o treino precisa das duas classes; recebido "
                f"{contagens[INTACTO]} intactas e {contagens[DESMATADO]} desmatadas. "
                "Um classificador treinado numa classe só responde sempre a mesma coisa."
            )

        self._modelo.fit(extrair_caracteristicas(conjunto.recortes), conjunto.rotulos)
        self._treinado = True
        return self

    def prever(self, recortes: np.ndarray) -> np.ndarray:
        """Classe prevista para cada recorte."""
        if not self._treinado:
            raise ErroModelo("o classificador precisa ser treinado antes de prever")
        return self._modelo.predict(extrair_caracteristicas(recortes))

    def probabilidade_de_desmatamento(self, recortes: np.ndarray) -> np.ndarray:
        """Confiança da classe 'desmatado', em ``[0, 1]``.

        Mais útil que a classe crua na apresentação: permite mostrar onde o modelo está
        inseguro em vez de fingir que toda decisão tem o mesmo peso.
        """
        if not self._treinado:
            raise ErroModelo("o classificador precisa ser treinado antes de prever")
        probabilidades = self._modelo.predict_proba(extrair_caracteristicas(recortes))
        indice = list(self._modelo.classes_).index(DESMATADO)
        return probabilidades[:, indice]

    def avaliar(self, conjunto: ConjuntoDeAmostras) -> Avaliacao:
        """Mede o desempenho num conjunto que o modelo não viu.

        Métrica sem aviso é métrica que engana: conjunto pequeno demais ou com uma
        classe só produz número alto que não significa nada, e isso vai declarado.
        """
        if not self._treinado:
            raise ErroModelo("o classificador precisa ser treinado antes de avaliar")
        if len(conjunto) == 0:
            raise ErroModelo("não há amostras para avaliar")

        from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

        previsto = self.prever(conjunto.recortes)
        real = conjunto.rotulos

        precisao, revocacao, f1, _ = precision_recall_fscore_support(
            real, previsto, average="binary", pos_label=DESMATADO, zero_division=0
        )

        avisos: list[str] = []
        if len(conjunto) < AMOSTRAS_MINIMAS_PARA_METRICA:
            avisos.append(
                f"conjunto de teste com {len(conjunto)} amostras — abaixo de "
                f"{AMOSTRAS_MINIMAS_PARA_METRICA}, a métrica é instável"
            )

        acuracia = float((previsto == real).mean())
        if acuracia == 1.0:
            avisos.append(
                "desempenho perfeito — em imagem real isso praticamente não acontece. "
                "Em cena sintética é esperado, porque a separação radiométrica entre as "
                "classes foi construída. Não apresente este número como validação do "
                "modelo sem repetir a medição em imagem real"
            )

        contagens = conjunto.contagem_por_classe
        if contagens[DESMATADO] == 0 or contagens[INTACTO] == 0:
            avisos.append(
                "o conjunto de teste tem uma classe só: a acurácia não distingue um "
                "modelo útil de um que responde sempre a mesma coisa"
            )
        elif conjunto.equilibrio < 0.3:
            avisos.append(
                f"conjunto de teste desbalanceado (equilíbrio {conjunto.equilibrio:.2f}) "
                "— leia a revocação e o F1, não a acurácia"
            )

        return Avaliacao(
            acuracia=acuracia,
            precisao=float(precisao),
            revocacao=float(revocacao),
            f1=float(f1),
            matriz_confusao=confusion_matrix(real, previsto, labels=[INTACTO, DESMATADO]),
            total_teste=len(conjunto),
            avisos=tuple(avisos),
        )

    def importancia_das_features(self) -> list[tuple[str, float]]:
        """Features ordenadas pelo peso que tiveram na decisão, da maior para a menor.

        É o que permite responder "por que o modelo decidiu isso?" na apresentação.
        """
        if not self._treinado:
            raise ErroModelo("o classificador precisa ser treinado antes")
        pares = zip(self.nomes_das_features, self._modelo.feature_importances_)
        return sorted(pares, key=lambda par: par[1], reverse=True)


def treinar_e_avaliar(
    conjunto: ConjuntoDeAmostras,
    *,
    proporcao_teste: float = 0.3,
    semente: int = 0,
) -> tuple[ClassificadorDesmatamento, Avaliacao]:
    """Fluxo completo: divide espacialmente, treina e avalia.

    Devolve ``(classificador, avaliacao)``. A divisão é espacial, nunca aleatória — ver
    ``dividir_espacialmente``.
    """
    treino, teste = dividir_espacialmente(conjunto, proporcao_teste=proporcao_teste)

    if len(treino) == 0 or len(teste) == 0:
        raise ErroModelo(
            f"a divisão espacial deixou treino com {len(treino)} e teste com "
            f"{len(teste)} amostras. A cena é pequena demais para separar as faixas: "
            "use um recorte menor, um passo menor, ou uma imagem maior."
        )

    classificador = ClassificadorDesmatamento(semente=semente).treinar(treino)
    return classificador, classificador.avaliar(teste)
