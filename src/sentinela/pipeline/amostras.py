"""Extração de amostras rotuladas — a etapa que o objetivo do enunciado nomeia.

> "produzindo dados preparados que possam alimentar um modelo de visão computacional"
> — enunciado, p.2

É aqui que o PDI deixa de ser um fim e vira **preparação de dados** (R034). A máscara
de desmatamento produzida por ``deteccao`` serve de rótulo: cada recorte da imagem
recebe a classe da região que ele cobre, e o conjunto resultante é o que alimenta o
classificador em ``modelo/``.

Recortes ambíguos — que pegam parte de área desmatada e parte de floresta — são
**descartados**, não arredondados para a classe majoritária. Rotular a borda de um
corte como "desmatado" ensina o classificador a responder pela vizinhança em vez de
pelo conteúdo, e o erro só aparece depois, na matriz de confusão.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..pdi.nucleo import ErroImagem, validar_imagem

INTACTO = 0
DESMATADO = 1

# Um recorte só é rotulado quando é majoritariamente de uma classe. Entre os dois
# limites fica a zona ambígua, descartada.
COBERTURA_PARA_DESMATADO = 0.60
COBERTURA_PARA_INTACTO = 0.05


@dataclass(frozen=True)
class ConjuntoDeAmostras:
    """Recortes rotulados, prontos para o classificador.

    ``recortes`` tem formato ``[N, lado, lado, bandas]``; ``rotulos`` tem ``[N]``, com
    ``INTACTO``/``DESMATADO``. ``posicoes`` guarda o canto superior esquerdo de cada
    recorte na imagem original, para que qualquer amostra possa ser reencontrada na
    cena — sem isso não há como auditar um erro do modelo.
    """

    recortes: np.ndarray
    rotulos: np.ndarray
    posicoes: list[tuple[int, int]]
    descartados_ambiguos: int

    def __len__(self) -> int:
        return int(self.rotulos.size)

    @property
    def contagem_por_classe(self) -> dict[int, int]:
        return {
            INTACTO: int((self.rotulos == INTACTO).sum()),
            DESMATADO: int((self.rotulos == DESMATADO).sum()),
        }

    @property
    def equilibrio(self) -> float:
        """Razão entre a classe minoritária e a majoritária, em ``[0, 1]``.

        Perto de 0 significa conjunto desbalanceado: um classificador que responde
        sempre a classe majoritária teria acurácia alta e utilidade nenhuma.
        """
        contagens = list(self.contagem_por_classe.values())
        if max(contagens) == 0:
            return 0.0
        return min(contagens) / max(contagens)

    def resumo(self) -> dict[str, object]:
        contagens = self.contagem_por_classe
        return {
            "total": len(self),
            "intacto": contagens[INTACTO],
            "desmatado": contagens[DESMATADO],
            "equilibrio": round(self.equilibrio, 3),
            "descartados_ambiguos": self.descartados_ambiguos,
            "formato_do_recorte": tuple(self.recortes.shape[1:])
            if len(self)
            else None,
        }


def extrair_amostras(
    imagem: np.ndarray,
    mascara_desmatamento: np.ndarray,
    *,
    lado: int = 16,
    passo: int | None = None,
    cobertura_desmatado: float = COBERTURA_PARA_DESMATADO,
    cobertura_intacto: float = COBERTURA_PARA_INTACTO,
) -> ConjuntoDeAmostras:
    """Varre a imagem em janelas e rotula cada recorte pela máscara de desmatamento.

    ``passo`` menor que ``lado`` faz as janelas se sobreporem, o que aumenta a
    quantidade de amostras sem precisar de mais cena — útil porque um par bi-temporal
    de uma área pequena rende poucas janelas disjuntas. O padrão é ``lado // 2``.
    """
    imagem = validar_imagem(imagem)
    mascara = np.asarray(mascara_desmatamento) > 0.5

    if imagem.ndim == 2:
        imagem = imagem[:, :, None]

    if mascara.shape != imagem.shape[:2]:
        raise ErroImagem(
            f"máscara {mascara.shape} não corresponde à imagem {imagem.shape[:2]}"
        )
    if lado < 2:
        raise ErroImagem(f"lado do recorte deve ser ao menos 2, recebido {lado}")

    altura, largura = imagem.shape[:2]
    if lado > altura or lado > largura:
        raise ErroImagem(
            f"recorte de {lado}x{lado} não cabe numa imagem de {altura}x{largura}"
        )

    if not 0.0 <= cobertura_intacto < cobertura_desmatado <= 1.0:
        raise ErroImagem(
            "limiares de cobertura inválidos: é preciso "
            f"0 <= intacto ({cobertura_intacto}) < desmatado ({cobertura_desmatado}) <= 1"
        )

    passo = lado // 2 if passo is None else passo
    if passo < 1:
        raise ErroImagem(f"passo deve ser ao menos 1, recebido {passo}")

    recortes: list[np.ndarray] = []
    rotulos: list[int] = []
    posicoes: list[tuple[int, int]] = []
    ambiguos = 0

    for linha in range(0, altura - lado + 1, passo):
        for coluna in range(0, largura - lado + 1, passo):
            janela = mascara[linha : linha + lado, coluna : coluna + lado]
            cobertura = float(janela.mean())

            if cobertura >= cobertura_desmatado:
                rotulo = DESMATADO
            elif cobertura <= cobertura_intacto:
                rotulo = INTACTO
            else:
                ambiguos += 1
                continue

            recortes.append(imagem[linha : linha + lado, coluna : coluna + lado])
            rotulos.append(rotulo)
            posicoes.append((linha, coluna))

    if not recortes:
        return ConjuntoDeAmostras(
            recortes=np.empty((0, lado, lado, imagem.shape[2]), dtype=np.float32),
            rotulos=np.empty(0, dtype=np.int64),
            posicoes=[],
            descartados_ambiguos=ambiguos,
        )

    return ConjuntoDeAmostras(
        recortes=np.stack(recortes).astype(np.float32),
        rotulos=np.array(rotulos, dtype=np.int64),
        posicoes=posicoes,
        descartados_ambiguos=ambiguos,
    )


def equilibrar(
    conjunto: ConjuntoDeAmostras, *, semente: int = 0
) -> ConjuntoDeAmostras:
    """Reduz a classe majoritária ao tamanho da minoritária, por sorteio.

    Numa cena típica a floresta domina — 95% de amostras intactas não é incomum. Sem
    equilibrar, o classificador aprende a responder "intacto" sempre e acerta 95%,
    métrica que não significa nada. A subamostragem é o tratamento mais simples e o
    único que não inventa dado novo.
    """
    contagens = conjunto.contagem_por_classe
    alvo = min(contagens.values())

    if alvo == 0 or len(conjunto) == 0:
        return conjunto

    gerador = np.random.default_rng(semente)
    escolhidos: list[int] = []

    for classe in (INTACTO, DESMATADO):
        indices = np.nonzero(conjunto.rotulos == classe)[0]
        escolhidos.extend(gerador.choice(indices, size=alvo, replace=False).tolist())

    escolhidos.sort()
    return ConjuntoDeAmostras(
        recortes=conjunto.recortes[escolhidos],
        rotulos=conjunto.rotulos[escolhidos],
        posicoes=[conjunto.posicoes[i] for i in escolhidos],
        descartados_ambiguos=conjunto.descartados_ambiguos,
    )
