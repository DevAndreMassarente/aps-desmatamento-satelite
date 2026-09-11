"""Rotulagem e análise de regiões segmentadas.

Fecha a etapa "Segmentação" do enunciado (p.3, item 2.e.iv). Enquanto ``limiar`` e
``morfologia`` produzem uma máscara, este módulo transforma a máscara em **objetos
contáveis e mensuráveis** — que é o que permite responder "quantos hectares foram
desmatados, e em quantos polígonos distintos?".
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .morfologia import _validar_mascara, dilatacao, elemento_cruz, elemento_quadrado


@dataclass(frozen=True)
class Regiao:
    """Uma região conexa da máscara.

    ``caixa`` é ``(linha_min, coluna_min, linha_max, coluna_max)``, com os limites
    máximos exclusivos, no padrão de fatiamento do NumPy.
    """

    rotulo: int
    area_pixels: int
    centroide: tuple[float, float]
    caixa: tuple[int, int, int, int]

    def area_hectares(self, metros_por_pixel: float) -> float:
        """Converte a área para hectares. 1 ha = 10.000 m²."""
        if metros_por_pixel <= 0:
            raise ValueError(
                f"metros_por_pixel deve ser positivo, recebido {metros_por_pixel}"
            )
        return self.area_pixels * (metros_por_pixel**2) / 10_000.0


class _UnionFind:
    """Estrutura união-busca para equivalência de rótulos.

    Usada pela rotulagem de dois passos: quando duas etiquetas provisórias se revelam
    da mesma região, em vez de reetiquetar a imagem inteira, apenas registra-se que
    elas são equivalentes.
    """

    def __init__(self) -> None:
        self._pai: dict[int, int] = {}

    def criar(self, item: int) -> None:
        self._pai.setdefault(item, item)

    def buscar(self, item: int) -> int:
        raiz = item
        while self._pai[raiz] != raiz:
            raiz = self._pai[raiz]
        # Compressão de caminho: aplana a árvore para acelerar as buscas seguintes.
        while self._pai[item] != raiz:
            self._pai[item], item = raiz, self._pai[item]
        return raiz

    def unir(self, a: int, b: int) -> None:
        raiz_a, raiz_b = self.buscar(a), self.buscar(b)
        if raiz_a != raiz_b:
            self._pai[max(raiz_a, raiz_b)] = min(raiz_a, raiz_b)


def rotular(mascara: np.ndarray, conectividade: int = 8) -> tuple[np.ndarray, int]:
    """Rotula componentes conexos pelo algoritmo de dois passos.

    Devolve ``(rotulos, quantidade)``, onde ``rotulos`` é um array inteiro com 0 no
    fundo e 1..N nas regiões.

    **Primeiro passo:** varre a imagem em ordem de leitura. Para cada pixel marcado,
    olha apenas os vizinhos **já visitados** (acima e à esquerda). Sem vizinho marcado,
    cria etiqueta nova; com um ou mais, adota a menor e registra na união-busca que as
    demais são equivalentes a ela.

    **Segundo passo:** substitui cada etiqueta provisória pela raiz da sua classe de
    equivalência e renumera para 1..N contíguos.

    ``conectividade=4`` considera vizinhos ortogonais; ``8`` inclui as diagonais. Para
    desmatamento, 8 é o padrão razoável — uma área de corte ligada apenas na diagonal
    ainda é a mesma área no terreno.
    """
    mascara = _validar_mascara(mascara) > 0.5

    if conectividade not in (4, 8):
        raise ValueError(f"conectividade deve ser 4 ou 8, recebido {conectividade}")

    altura, largura = mascara.shape
    rotulos = np.zeros((altura, largura), dtype=np.int32)
    conjuntos = _UnionFind()
    proximo = 1

    if conectividade == 4:
        vizinhos = ((-1, 0), (0, -1))
    else:
        vizinhos = ((-1, -1), (-1, 0), (-1, 1), (0, -1))

    for linha in range(altura):
        for coluna in range(largura):
            if not mascara[linha, coluna]:
                continue

            candidatos = []
            for dl, dc in vizinhos:
                vl, vc = linha + dl, coluna + dc
                if 0 <= vl < altura and 0 <= vc < largura and rotulos[vl, vc] != 0:
                    candidatos.append(int(rotulos[vl, vc]))

            if not candidatos:
                conjuntos.criar(proximo)
                rotulos[linha, coluna] = proximo
                proximo += 1
                continue

            menor = min(candidatos)
            rotulos[linha, coluna] = menor
            for outro in candidatos:
                conjuntos.unir(menor, outro)

    if proximo == 1:
        return rotulos, 0

    resolvidos = {etiqueta: conjuntos.buscar(etiqueta) for etiqueta in range(1, proximo)}
    finais = sorted(set(resolvidos.values()))
    renumerado = {raiz: indice for indice, raiz in enumerate(finais, start=1)}

    tabela = np.zeros(proximo, dtype=np.int32)
    for etiqueta, raiz in resolvidos.items():
        tabela[etiqueta] = renumerado[raiz]

    return tabela[rotulos], len(finais)


def descrever_regioes(rotulos: np.ndarray, quantidade: int | None = None) -> list[Regiao]:
    """Extrai área, centroide e caixa delimitadora de cada região rotulada."""
    if rotulos.ndim != 2:
        raise ValueError(f"rótulos devem ser 2D, recebido {rotulos.shape}")

    if quantidade is None:
        quantidade = int(rotulos.max())
    if quantidade == 0:
        return []

    regioes: list[Regiao] = []
    for rotulo in range(1, quantidade + 1):
        linhas, colunas = np.nonzero(rotulos == rotulo)
        if linhas.size == 0:
            continue
        regioes.append(
            Regiao(
                rotulo=rotulo,
                area_pixels=int(linhas.size),
                centroide=(float(linhas.mean()), float(colunas.mean())),
                caixa=(
                    int(linhas.min()),
                    int(colunas.min()),
                    int(linhas.max()) + 1,
                    int(colunas.max()) + 1,
                ),
            )
        )
    return regioes


def filtrar_por_area(
    mascara: np.ndarray,
    area_minima: int = 0,
    area_maxima: int | None = None,
    conectividade: int = 8,
) -> np.ndarray:
    """Descarta regiões fora da faixa de área informada.

    Este é o filtro que separa desmatamento real de ruído residual: uma clareira de
    3 pixels numa imagem Sentinel-2 (10 m/pixel) corresponde a 300 m², abaixo do que
    qualquer sistema de monitoramento considera evento. Filtrar por área é mais honesto
    que erodir repetidamente, porque o critério fica explícito e mensurável.
    """
    if area_minima < 0:
        raise ValueError(f"area_minima não pode ser negativa, recebido {area_minima}")
    if area_maxima is not None and area_maxima < area_minima:
        raise ValueError(
            f"area_maxima ({area_maxima}) não pode ser menor que area_minima ({area_minima})"
        )

    rotulos, quantidade = rotular(mascara, conectividade)
    if quantidade == 0:
        return np.zeros_like(rotulos, dtype=bool)

    resultado = np.zeros_like(rotulos, dtype=bool)
    for regiao in descrever_regioes(rotulos, quantidade):
        if regiao.area_pixels < area_minima:
            continue
        if area_maxima is not None and regiao.area_pixels > area_maxima:
            continue
        resultado |= rotulos == regiao.rotulo

    return resultado


def reconstruir_por_conexao(
    marcadores: np.ndarray, permitido: np.ndarray, conectividade: int = 8
) -> np.ndarray:
    """Reconstrução morfológica: expande os marcadores dentro da máscara permitida.

    Dilata os marcadores repetidamente, mantendo apenas o que cai dentro de
    ``permitido``, até nada mais mudar. O resultado é o conjunto de regiões de
    ``permitido`` que **contêm** ao menos um marcador.

    É assim que a histerese de ``limiar.limiar_duplo`` se completa: os pixels fortes são
    os marcadores, fortes ∪ fracos é o permitido, e só os fracos conectados a algum forte
    sobrevivem.
    """
    marcadores = _validar_mascara(marcadores) > 0.5
    permitido = _validar_mascara(permitido) > 0.5

    if marcadores.shape != permitido.shape:
        raise ValueError(
            f"formatos incompatíveis: marcadores {marcadores.shape}, "
            f"permitido {permitido.shape}"
        )

    elemento = elemento_cruz(3) if conectividade == 4 else elemento_quadrado(3)

    atual = marcadores & permitido
    while True:
        expandido = dilatacao(atual, elemento) & permitido
        if np.array_equal(expandido, atual):
            return atual
        atual = expandido


def mudanca_entre_mascaras(
    antes: np.ndarray, depois: np.ndarray
) -> dict[str, np.ndarray]:
    """Compara duas máscaras de vegetação e classifica a mudança pixel a pixel.

    Coração da abordagem bi-temporal (``docs/ARCHITECTURE.md``): ``perda`` é a máscara de
    desmatamento — onde havia vegetação em T1 e não há mais em T2.

    ``ganho`` (regeneração ou erro de registro) e ``estavel`` acompanham porque servem
    de controle: um ``ganho`` alto demais indica que as duas imagens não estão bem
    alinhadas, ou que a variação sazonal está sendo lida como mudança real.
    """
    antes = _validar_mascara(antes) > 0.5
    depois = _validar_mascara(depois) > 0.5

    if antes.shape != depois.shape:
        raise ValueError(
            f"as duas datas precisam ter o mesmo recorte: antes {antes.shape}, "
            f"depois {depois.shape}"
        )

    return {
        "perda": antes & ~depois,
        "ganho": ~antes & depois,
        "estavel_vegetado": antes & depois,
        "estavel_nao_vegetado": ~antes & ~depois,
    }
