"""Orquestração das cinco etapas do enunciado (p.3, item 2.e).

```text
Aquisição  →  Manipulação  →  Filtragem  →  Segmentação  →  Modelo
dataio/       pdi/cor       pdi/filtros    pdi/limiar        modelo/
                                           pdi/morfologia
                                           pdi/segmentacao
```

Este módulo não implementa nenhum algoritmo: ele encadeia os que estão em ``pdi/`` e
guarda **todos os intermediários**, porque a interface precisa exibir etapa por etapa e
o trabalho escrito precisa mostrar o efeito de cada filtro (R033).

A decisão que mais importa aqui está em ``docs/decisions/003-limiar-bitemporal.md``: o
limiar é **único** para as duas datas. Otsu por data daria a cada uma uma régua
diferente, e a diferença entre as máscaras mediria a diferença entre os limiares, não a
mudança no terreno.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..pdi import cor, filtros, limiar, morfologia, segmentacao
from ..pdi.nucleo import ErroImagem, validar_imagem
from ..pdi.segmentacao import Regiao

# Acima desta razão ganho/perda, as duas datas provavelmente não estão alinhadas, ou a
# variação sazonal está sendo lida como mudança real. Regeneração de vegetação existe,
# mas no intervalo de meses de um par bi-temporal ela não compete em área com o corte.
PROPORCAO_GANHO_SUSPEITA = 0.5

# Fragmentos abaixo disto são resíduo de segmentação, não evento. A 10 m/pixel do
# Sentinel-2, 25 pixels = 2.500 m² = 0,25 ha.
AREA_MINIMA_PADRAO = 25


@dataclass(frozen=True)
class ResultadoDeteccao:
    """Saída completa de uma detecção, com todos os intermediários preservados.

    ``perda`` é a máscara de desmatamento já filtrada por área. Ela **existe mesmo
    quando ``confiavel`` é falso** — descartá-la esconderia do usuário o que o
    algoritmo fez. Mas nesse caso a área não deve ser reportada como resultado: ver
    ``resumo()``, que devolve ``None`` no lugar do número.
    """

    metodo_indice: str
    valor_limiar: float
    confiavel: bool
    metricas: dict[str, float]

    indice_antes: np.ndarray
    indice_depois: np.ndarray
    vegetacao_antes: np.ndarray
    vegetacao_depois: np.ndarray
    mudanca: dict[str, np.ndarray]
    perda: np.ndarray
    rotulos: np.ndarray
    regioes: list[Regiao]

    metros_por_pixel: float | None = None
    parametros: dict[str, object] = field(default_factory=dict)

    @property
    def area_pixels(self) -> int:
        """Área desmatada total, em pixels."""
        return int(self.perda.sum())

    @property
    def area_hectares(self) -> float | None:
        """Área desmatada em hectares, ou ``None`` sem resolução espacial conhecida."""
        if self.metros_por_pixel is None:
            return None
        return self.area_pixels * (self.metros_por_pixel**2) / 10_000.0

    @property
    def proporcao_da_cena(self) -> float:
        """Fração da cena classificada como desmatamento, em ``[0, 1]``."""
        return float(self.perda.sum() / self.perda.size)

    @property
    def alerta_de_registro(self) -> bool:
        """Verdadeiro quando o ganho de vegetação é alto demais para ser plausível.

        Controle de sanidade: as duas datas podem estar desalinhadas, ou a diferença
        pode ser sazonal. Não invalida o resultado sozinho — pede inspeção visual.
        """
        perdidos = float(self.mudanca["perda"].sum())
        if perdidos == 0:
            return bool(self.mudanca["ganho"].sum() > 0)
        return float(self.mudanca["ganho"].sum()) / perdidos > PROPORCAO_GANHO_SUSPEITA

    def resumo(self) -> dict[str, object]:
        """Números prontos para relatório — sem área quando a detecção não é confiável.

        Cena homogênea não tem duas classes para separar: o limiar automático corta o
        ruído do dossel ao meio e produziria uma área de desmatamento inexistente.
        Devolver ``None`` ali é a resposta correta, não uma falha.
        """
        reportavel = self.confiavel
        return {
            "confiavel": self.confiavel,
            "metodo_indice": self.metodo_indice,
            "limiar": round(self.valor_limiar, 4),
            "distinguibilidade": round(self.metricas["distinguibilidade"], 3),
            "separabilidade_otsu": round(self.metricas["separabilidade"], 4),
            "area_pixels": self.area_pixels if reportavel else None,
            "area_hectares": (
                round(self.area_hectares, 3)
                if reportavel and self.area_hectares is not None
                else None
            ),
            "proporcao_da_cena": round(self.proporcao_da_cena, 5) if reportavel else None,
            "regioes_detectadas": len(self.regioes) if reportavel else None,
            "alerta_de_registro": self.alerta_de_registro,
        }


def preparar_indice(
    rgb: np.ndarray,
    infravermelho: np.ndarray | None = None,
    *,
    metodo: str = "auto",
    suavizacao: int = 5,
    swir: np.ndarray | None = None,
) -> tuple[np.ndarray, str]:
    """Etapas 2 e 3: índice de vegetação, normalizado para ``[0, 1]`` e suavizado.

    A suavização vem **antes** da limiarização de propósito. Sem ela, o ruído do sensor
    atravessa o limiar pixel a pixel e a máscara sai esburacada, o que multiplica
    regiões conexas e inviabiliza a contagem por área.

    Devolve ``(indice_suavizado, nome_do_metodo)``.
    """
    indice, nome = cor.indice_vegetacao(rgb, infravermelho, metodo=metodo, swir=swir)
    unitario = cor.para_faixa_unitaria(indice)

    if suavizacao <= 1:
        return unitario, nome

    return filtros.gaussiano(unitario, tamanho=suavizacao), nome


def detectar_desmatamento(
    rgb_antes: np.ndarray,
    rgb_depois: np.ndarray,
    nir_antes: np.ndarray | None = None,
    nir_depois: np.ndarray | None = None,
    *,
    swir_antes: np.ndarray | None = None,
    swir_depois: np.ndarray | None = None,
    metodo: str = "auto",
    suavizacao: int = 5,
    area_minima: int = AREA_MINIMA_PADRAO,
    metros_por_pixel: float | None = None,
    limpar_mascara: bool = True,
) -> ResultadoDeteccao:
    """Executa a cadeia completa sobre um par bi-temporal da mesma área.

    ``rgb_antes`` e ``rgb_depois`` são a mesma região em duas datas, já recortadas sobre
    o mesmo extent. As bandas infravermelhas são opcionais: havendo as duas, usa-se
    NDVI; faltando, o sistema degrada para VARI, que trabalha só com o visível.

    Levanta ``ErroImagem`` quando as entradas são incompatíveis — checar aqui é o que
    evita um mapa de desmatamento sem sentido lá na frente (R036).
    """
    rgb_antes = validar_imagem(rgb_antes, bandas_aceitas=(3,))
    rgb_depois = validar_imagem(rgb_depois, bandas_aceitas=(3,))

    if rgb_antes.shape != rgb_depois.shape:
        raise ErroImagem(
            f"as duas datas precisam ter o mesmo recorte: antes {rgb_antes.shape[:2]}, "
            f"depois {rgb_depois.shape[:2]}"
        )

    if (nir_antes is None) != (nir_depois is None):
        raise ErroImagem(
            "infravermelho precisa estar presente nas duas datas ou em nenhuma: "
            "usar NDVI numa data e VARI na outra compara índices de escalas diferentes"
        )

    if (swir_antes is None) != (swir_depois is None):
        raise ErroImagem(
            "SWIR precisa estar presente nas duas datas ou em nenhuma: o índice com SWIR de uma "
            "data não é comparável ao NDVI da outra"
        )

    for nome, banda in (
        ("nir_antes", nir_antes),
        ("nir_depois", nir_depois),
        ("swir_antes", swir_antes),
        ("swir_depois", swir_depois),
    ):
        if banda is not None and banda.shape[:2] != rgb_antes.shape[:2]:
            raise ErroImagem(
                f"'{nome}' tem formato {banda.shape[:2]}, diferente do RGB "
                f"{rgb_antes.shape[:2]}"
            )

    if area_minima < 0:
        raise ErroImagem(f"area_minima não pode ser negativa, recebido {area_minima}")
    if metros_por_pixel is not None and metros_por_pixel <= 0:
        raise ErroImagem(
            f"metros_por_pixel deve ser positivo, recebido {metros_por_pixel}"
        )

    # Etapas 2 e 3 — manipulação e filtragem.
    indice_antes, nome_metodo = preparar_indice(
        rgb_antes, nir_antes, metodo=metodo, suavizacao=suavizacao, swir=swir_antes
    )
    indice_depois, _ = preparar_indice(
        rgb_depois, nir_depois, metodo=metodo, suavizacao=suavizacao, swir=swir_depois
    )

    # Etapa 4 — segmentação, com régua única para as duas datas.
    valor, confiavel, metricas = limiar.limiar_confiavel(indice_antes, indice_depois)

    vegetacao_antes = limiar.binarizar(indice_antes, valor)
    vegetacao_depois = limiar.binarizar(indice_depois, valor)

    if limpar_mascara:
        limpar = lambda m: morfologia.fechamento(morfologia.abertura(m))
        vegetacao_antes = limpar(vegetacao_antes)
        vegetacao_depois = limpar(vegetacao_depois)

    mudanca = segmentacao.mudanca_entre_mascaras(vegetacao_antes, vegetacao_depois)
    perda = segmentacao.filtrar_por_area(mudanca["perda"], area_minima=area_minima)

    rotulos, quantidade = segmentacao.rotular(perda)
    regioes = sorted(
        segmentacao.descrever_regioes(rotulos, quantidade),
        key=lambda regiao: regiao.area_pixels,
        reverse=True,
    )

    return ResultadoDeteccao(
        metodo_indice=nome_metodo,
        valor_limiar=valor,
        confiavel=confiavel,
        metricas=metricas,
        indice_antes=indice_antes,
        indice_depois=indice_depois,
        vegetacao_antes=vegetacao_antes,
        vegetacao_depois=vegetacao_depois,
        mudanca=mudanca,
        perda=perda,
        rotulos=rotulos,
        regioes=regioes,
        metros_por_pixel=metros_por_pixel,
        parametros={
            "metodo": metodo,
            "suavizacao": suavizacao,
            "area_minima": area_minima,
            "limpar_mascara": limpar_mascara,
        },
    )
