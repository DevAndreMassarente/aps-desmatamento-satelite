"""Metadado geográfico — resolução espacial para converter pixels em hectares.

`rasterio` é **opcional**: ele arrasta o GDAL como dependência nativa e falha de
instalar em máquina sem as bibliotecas de sistema. Sem ele o programa continua
funcionando com PNG/JPEG, perdendo apenas a conversão automática para hectares,
que passa a depender da resolução informada à mão.

Degradação explícita, nunca silenciosa: quem chama recebe ``None`` e sabe por quê.
"""

from __future__ import annotations

from pathlib import Path

try:  # pragma: no cover - depende do ambiente, não da lógica
    import rasterio

    RASTERIO_DISPONIVEL = True
except ImportError:  # pragma: no cover
    rasterio = None
    RASTERIO_DISPONIVEL = False

# Resoluções nominais das bandas ópticas mais usadas em detecção de desmatamento.
RESOLUCOES_CONHECIDAS = {
    "sentinel-2": 10.0,  # bandas B02, B03, B04, B08
    "landsat-8": 30.0,
    "landsat-9": 30.0,
    "cbers-4a": 8.0,  # câmera WPM multiespectral
}


def metros_por_pixel(caminho: str | Path) -> float | None:
    """Lê a resolução espacial do GeoTIFF, em metros por pixel.

    Devolve ``None`` quando `rasterio` não está instalado, quando o arquivo não é
    georreferenciado, ou quando o CRS não é métrico — caso em que o valor do
    transform está em graus e usá-lo como metro daria uma área errada por ordens
    de grandeza.
    """
    if not RASTERIO_DISPONIVEL:
        return None

    caminho = Path(caminho)
    if not caminho.exists():
        return None

    try:
        with rasterio.open(caminho) as cena:
            if cena.crs is None or not cena.crs.is_projected:
                return None
            return float(abs(cena.transform.a))
    except Exception:  # rasterio levanta uma família grande de erros de formato
        return None


def resolucao_do_satelite(nome: str) -> float | None:
    """Resolução nominal de um satélite conhecido, para quando não há GeoTIFF.

    Usado pela interface quando o usuário sobe PNG recortado de um visualizador:
    o pixel continua tendo tamanho real, ele só não está gravado no arquivo.
    """
    return RESOLUCOES_CONHECIDAS.get(nome.strip().lower())


def descrever_origem_da_resolucao(
    metros: float | None, veio_do_arquivo: bool
) -> str:
    """Frase curta dizendo de onde saiu a resolução, para aparecer na evidência.

    Área em hectares sem origem declarada é número solto: na banca, "de onde veio o
    tamanho do pixel?" é pergunta certa.
    """
    if metros is None:
        return "resolução desconhecida — área reportada apenas em pixels"
    if veio_do_arquivo:
        return f"{metros:.2f} m/pixel lidos do metadado geográfico do arquivo"
    return f"{metros:.2f} m/pixel informados manualmente"
