"""Leitura e escrita de imagens — a fronteira entre o disco e os arrays de ``pdi``.

Este é o único lugar do projeto autorizado a usar Pillow. O núcleo de PDI trabalha
exclusivamente com arrays NumPy e não sabe o que é um arquivo — ver `AGENTS.md` §5.

Convenção de fronteira: tudo que **entra** vira ``float32`` em ``[0, 1]``; tudo que
**sai** volta para ``uint8``. A conversão acontece aqui e em nenhum outro lugar.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

from ..pdi.nucleo import ErroImagem, para_float, para_uint8, validar_imagem

EXTENSOES_SUPORTADAS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")


class ErroArquivo(ErroImagem):
    """Falha ao ler ou escrever um arquivo de imagem.

    Herda de ``ErroImagem`` para que a interface possa capturar um tipo só e ainda
    assim distinguir o caso quando precisar.
    """


def carregar(caminho: str | Path, *, cinza: bool = False) -> np.ndarray:
    """Carrega uma imagem do disco como ``float32`` em ``[0, 1]``.

    Devolve ``[H, W]`` com ``cinza=True`` e ``[H, W, 3]`` caso contrário. Canal alfa é
    descartado: transparência não tem significado radiométrico numa cena orbital.

    Levanta ``ErroArquivo`` com mensagem explicativa em vez de deixar vazar o erro do
    Pillow — o enunciado pontua tratamento de erros (p.4, item II.2).
    """
    caminho = Path(caminho)

    if not caminho.exists():
        raise ErroArquivo(f"arquivo não encontrado: {caminho}")
    if not caminho.is_file():
        raise ErroArquivo(f"caminho não é um arquivo: {caminho}")

    try:
        with Image.open(caminho) as arquivo:
            arquivo = arquivo.convert("L" if cinza else "RGB")
            dados = np.array(arquivo)
    except UnidentifiedImageError as erro:
        raise ErroArquivo(
            f"'{caminho.name}' não é uma imagem que o Pillow reconheça. "
            f"Formatos suportados: {', '.join(EXTENSOES_SUPORTADAS)}."
        ) from erro
    except OSError as erro:
        raise ErroArquivo(f"falha ao ler '{caminho}': {erro}") from erro

    if dados.size == 0:
        raise ErroArquivo(f"'{caminho.name}' está vazia (0 pixels)")

    return para_float(dados)


def carregar_com_infravermelho(caminho: str | Path) -> tuple[np.ndarray, np.ndarray | None]:
    """Carrega uma imagem que pode trazer o infravermelho próximo como quarta banda.

    Com quatro bandas, as três primeiras são a cor e a quarta é o infravermelho próximo:
    assim cada data cabe num arquivo só. Com três bandas, devolve ``(rgb, None)``.
    """
    caminho = Path(caminho)
    if not caminho.is_file():
        raise ErroArquivo(f"arquivo não encontrado: {caminho}")

    try:
        with Image.open(caminho) as arquivo:
            quatro_bandas = len(arquivo.getbands()) == 4
            dados = np.array(arquivo.convert("RGBA")) if quatro_bandas else None
    except UnidentifiedImageError as erro:
        raise ErroArquivo(
            f"'{caminho.name}' não é uma imagem que o Pillow reconheça. "
            f"Formatos suportados: {', '.join(EXTENSOES_SUPORTADAS)}."
        ) from erro
    except OSError as erro:
        raise ErroArquivo(f"falha ao ler '{caminho}': {erro}") from erro

    if dados is None:
        return carregar(caminho), None
    return para_float(np.ascontiguousarray(dados[..., :3])), para_float(dados[..., 3])


def carregar_par(
    caminho_antes: str | Path, caminho_depois: str | Path, *, cinza: bool = False
) -> tuple[np.ndarray, np.ndarray]:
    """Carrega as duas datas e exige que tenham o mesmo recorte.

    Formas diferentes significam que as cenas não foram recortadas sobre a mesma área.
    Comparar mesmo assim produziria um mapa de desmatamento sem sentido, então o erro
    é levantado aqui, no ponto em que ainda dá para explicar a causa ao usuário.
    """
    antes = carregar(caminho_antes, cinza=cinza)
    depois = carregar(caminho_depois, cinza=cinza)

    if antes.shape != depois.shape:
        raise ErroArquivo(
            f"as duas datas precisam ter o mesmo recorte: "
            f"'{Path(caminho_antes).name}' tem {antes.shape[:2]} e "
            f"'{Path(caminho_depois).name}' tem {depois.shape[:2]}. "
            "Recorte as duas cenas sobre a mesma área antes de comparar."
        )

    return antes, depois


def em_data_uri(imagem: np.ndarray, *, lado_maximo: int = 900, qualidade: int = 88) -> str:
    """Converte um array em URI JPEG reduzido, para embutir numa página sem servir arquivos."""
    figura = Image.fromarray(para_uint8(validar_imagem(imagem)))
    figura.thumbnail((lado_maximo, lado_maximo), Image.Resampling.LANCZOS)
    saida = io.BytesIO()
    figura.convert("RGB").save(saida, format="JPEG", quality=qualidade)
    return "data:image/jpeg;base64," + base64.b64encode(saida.getvalue()).decode("ascii")


def salvar(caminho: str | Path, imagem: np.ndarray) -> Path:
    """Grava um array em disco, convertendo para ``uint8`` na saída.

    Aceita ``[H, W]`` (cinza), ``[H, W, 3]`` (RGB) e máscara booleana, que vira preto
    e branco. Cria o diretório de destino se ele não existir.
    """
    caminho = Path(caminho)

    if imagem.dtype == np.bool_:
        imagem = imagem.astype(np.float32)

    imagem = validar_imagem(imagem)
    if imagem.ndim == 3 and imagem.shape[2] != 3:
        raise ErroArquivo(
            f"imagem com {imagem.shape[2]} bandas não pode ser salva como RGB; "
            "salve banda a banda ou componha três bandas antes"
        )

    caminho.parent.mkdir(parents=True, exist_ok=True)

    try:
        Image.fromarray(para_uint8(imagem)).save(caminho)
    except (OSError, ValueError) as erro:
        raise ErroArquivo(f"falha ao gravar '{caminho}': {erro}") from erro

    return caminho
