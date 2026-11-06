"""Linha de comando do Sentinela.

Três usos:

```bash
sentinela app                                     # abre a interface no navegador
sentinela detectar --antes t1.png --depois t2.png # processa um par e grava as saídas
sentinela demo --saida _interno/docs/resultados/imagem-real      # roda a cena sintética de demonstração
```

Existe porque a demonstração ao vivo depende do Streamlit, mas a geração de evidência
para o trabalho escrito precisa ser **reproduzível por comando**: um resultado que só
existe depois de alguém clicar numa tela não é reproduzível.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from .dataio import (
    ErroArquivo,
    carregar,
    carregar_par,
    indice_em_falsa_cor,
    mapa_de_mudanca,
    metros_por_pixel as ler_metros_por_pixel,
    par_bitemporal,
    salvar,
    sobrepor_mascara,
)
from .pdi.nucleo import ErroImagem
from .pipeline import detectar_desmatamento, equilibrar, extrair_amostras


def _gravar_saidas(destino: Path, imagens: dict, resultado) -> list[Path]:
    """Grava os intermediários que entram na evidência do trabalho escrito."""
    destino.mkdir(parents=True, exist_ok=True)

    saidas = {
        "01-antes.png": imagens["rgb_antes"],
        "02-depois.png": imagens["rgb_depois"],
        "03-indice-antes.png": indice_em_falsa_cor(resultado.indice_antes),
        "04-indice-depois.png": indice_em_falsa_cor(resultado.indice_depois),
        "05-vegetacao-antes.png": resultado.vegetacao_antes,
        "06-vegetacao-depois.png": resultado.vegetacao_depois,
        "07-mapa-mudanca.png": mapa_de_mudanca(resultado.mudanca),
        "08-perda-detectada.png": resultado.perda,
        "09-sobreposicao.png": sobrepor_mascara(imagens["rgb_depois"], resultado.perda),
    }

    gravados = [salvar(destino / nome, dados) for nome, dados in saidas.items()]

    relatorio = destino / "resumo.json"
    relatorio.write_text(
        json.dumps(resultado.resumo(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    gravados.append(relatorio)

    return gravados


def _relatar(resultado, gravados: list[Path] | None = None) -> None:
    """Imprime o resumo no terminal, com a recusa explícita quando for o caso."""
    resumo = resultado.resumo()

    print(f"\nÍndice de vegetação : {resumo['metodo_indice'].upper()}")
    print(f"Limiar de Otsu      : {resumo['limiar']:.4f} (único para as duas datas)")
    print(f"Distinguibilidade   : {resumo['distinguibilidade']:.3f}")

    if not resultado.confiavel:
        print(
            "\n  DETECÇÃO NÃO CONFIÁVEL — nenhuma área reportada.\n"
            "  A cena não apresenta duas classes separáveis. Sem elas o limiar\n"
            "  automático corta o ruído do dossel ao meio e produziria desmatamento\n"
            "  onde não houve."
        )
    else:
        print(f"\nÁrea desmatada      : {resumo['area_pixels']} pixels")
        if resumo["area_hectares"] is not None:
            print(f"                      {resumo['area_hectares']:.3f} hectares")
        else:
            print("                      (sem resolução espacial: só em pixels)")
        print(f"Regiões detectadas  : {resumo['regioes_detectadas']}")
        print(f"Fração da cena      : {resumo['proporcao_da_cena'] * 100:.2f}%")

    if resultado.alerta_de_registro:
        print(
            "\n  AVISO: ganho de vegetação alto demais. As duas datas podem não estar\n"
            "  alinhadas, ou a diferença pode ser sazonal."
        )

    if gravados:
        print(f"\n{len(gravados)} arquivos gravados em {gravados[0].parent}")


def _treinar_e_relatar(conjunto, *, proporcao_teste: float, semente: int) -> int:
    """Treina o classificador sobre as amostras e imprime a avaliação.

    Separado dos comandos porque `detectar` e `demo` relatam da mesma forma.
    """
    from .modelo import ErroModelo, treinar_e_avaliar

    print(f"\nAmostras             : {conjunto.resumo()}")

    try:
        classificador, avaliacao = treinar_e_avaliar(
            conjunto, proporcao_teste=proporcao_teste, semente=semente
        )
    except ErroModelo as erro:
        print(f"\nModelo não treinado: {erro}", file=sys.stderr)
        return 1

    resumo = avaliacao.resumo()
    matriz = resumo["matriz_confusao"]

    print("\n--- Classificador (floresta aleatória) ---")
    print(f"Amostras de teste    : {resumo['amostras_de_teste']}")
    print(f"Acurácia             : {resumo['acuracia']:.4f}")
    print(f"Precisão             : {resumo['precisao']:.4f}")
    print(f"Revocação            : {resumo['revocacao']:.4f}")
    print(f"F1                   : {resumo['f1']:.4f}")
    print("\nMatriz de confusão:")
    print(f"  intacto correto      {matriz['intacto_correto']:>5}")
    print(f"  desmatamento correto {matriz['desmatamento_correto']:>5}")
    print(f"  falso alarme         {matriz['falso_alarme']:>5}")
    print(f"  desmatamento perdido {matriz['desmatamento_perdido']:>5}")

    print("\nFeatures mais influentes:")
    for nome, peso in classificador.importancia_das_features()[:5]:
        print(f"  {nome:<20} {peso:.4f}")

    for aviso in avaliacao.avisos:
        print(f"\n  AVISO: {aviso}")

    return 0


def comando_app(args: argparse.Namespace) -> int:
    """Sobe a interface Streamlit no navegador."""
    from .app import CAMINHO_APP, estilo

    try:
        import streamlit  # noqa: F401
    except ImportError:
        print(
            "Streamlit não está instalado. Instale o extra da interface:\n"
            '  pip install -e ".[app]"',
            file=sys.stderr,
        )
        return 1

    # Só nesta máquina: sem isso o Streamlit escuta em todas as interfaces, e na rede
    # da sala de aula qualquer um conseguiria abrir o app.
    comando = [sys.executable, "-m", "streamlit", "run", CAMINHO_APP,
               "--server.port", str(args.porta), "--server.address", "127.0.0.1"]
    for opcao, valor in estilo.TEMA.items():
        comando += [f"--{opcao}", valor]
    return subprocess.call(comando)


def comando_detectar(args: argparse.Namespace) -> int:
    """Processa um par bi-temporal vindo do disco."""
    try:
        rgb_antes, rgb_depois = carregar_par(args.antes, args.depois)
        nir_antes = carregar(args.nir_antes, cinza=True) if args.nir_antes else None
        nir_depois = carregar(args.nir_depois, cinza=True) if args.nir_depois else None
        swir_antes = carregar(args.swir_antes, cinza=True) if args.swir_antes else None
        swir_depois = carregar(args.swir_depois, cinza=True) if args.swir_depois else None
    except ErroArquivo as erro:
        print(f"Erro de leitura: {erro}", file=sys.stderr)
        return 1

    metros = args.metros_por_pixel or ler_metros_por_pixel(args.depois)

    try:
        resultado = detectar_desmatamento(
            rgb_antes, rgb_depois, nir_antes, nir_depois,
            swir_antes=swir_antes, swir_depois=swir_depois,
            metodo=args.metodo,
            suavizacao=args.suavizacao,
            area_minima=args.area_minima,
            metros_por_pixel=metros,
        )
    except ErroImagem as erro:
        print(f"Erro de processamento: {erro}", file=sys.stderr)
        return 1

    gravados = None
    if args.saida:
        imagens = {"rgb_antes": rgb_antes, "rgb_depois": rgb_depois}
        gravados = _gravar_saidas(Path(args.saida), imagens, resultado)

    _relatar(resultado, gravados)

    if args.modelo:
        conjunto = extrair_amostras(rgb_depois, resultado.perda, lado=args.lado)
        return _treinar_e_relatar(
            conjunto, proporcao_teste=args.proporcao_teste, semente=args.semente
        )

    return 0


def comando_demo(args: argparse.Namespace) -> int:
    """Roda a cadeia completa sobre a cena **sintética** de demonstração."""
    print(
        "CENA SINTÉTICA — demonstração do programa.\n"
        "Não é imagem de satélite e não pode ser apresentada como evidência real\n"
        "(AGENTS.md §11). A validação sobre imagem real é o requisito R032.\n"
    )

    lado = args.tamanho
    corte_lado = args.area
    corte = None
    if corte_lado > 0:
        inicio = (lado - corte_lado) // 2
        corte = (slice(inicio, inicio + corte_lado), slice(inicio, inicio + corte_lado))

    par = par_bitemporal(corte=corte, tamanho=(lado, lado))

    resultado = detectar_desmatamento(
        par["rgb_antes"], par["rgb_depois"], par["nir_antes"], par["nir_depois"],
        metros_por_pixel=args.metros_por_pixel,
    )

    gravados = _gravar_saidas(Path(args.saida), par, resultado) if args.saida else None
    _relatar(resultado, gravados)

    esperada = par["area_esperada"]
    if esperada and resultado.confiavel:
        erro = abs(resultado.area_pixels - esperada) / esperada * 100
        print(f"\nVerdade de terreno  : {esperada} pixels")
        print(f"Erro da detecção    : {erro:.1f}%")

    conjunto = extrair_amostras(par["rgb_depois"], resultado.perda)

    if not args.modelo:
        print(f"\nAmostras para o modelo: {conjunto.resumo()}")
        print(f"Após equilibrar       : {equilibrar(conjunto).resumo()}")
        print("\nUse --modelo para treinar e avaliar o classificador.")
        return 0

    return _treinar_e_relatar(
        conjunto, proporcao_teste=args.proporcao_teste, semente=args.semente
    )


def comando_apendice(args: argparse.Namespace) -> int:
    """Gera o apêndice de código-fonte exigido pelo Capítulo 7 do enunciado (R018).

    Automatizado de propósito: um apêndice copiado à mão diverge do código entregue na
    primeira correção feita depois de copiar, e a divergência é exatamente o tipo de
    coisa que uma banca encontra.
    """
    raiz = Path(__file__).resolve().parents[2]
    origem = raiz / "src" / "sentinela"

    if not origem.is_dir():
        print(f"Código-fonte não encontrado em {origem}", file=sys.stderr)
        return 1

    # Ordem de leitura, não alfabética: o apêndice é lido por quem quer entender o
    # sistema, e o núcleo vem antes de quem o consome.
    ordem = [
        "pdi/nucleo.py", "pdi/cor.py", "pdi/filtros.py", "pdi/limiar.py",
        "pdi/morfologia.py", "pdi/segmentacao.py",
        "dataio/imagem.py", "dataio/geo.py", "dataio/visual.py", "dataio/sintetico.py",
        "pipeline/deteccao.py", "pipeline/amostras.py",
        "modelo/caracteristicas.py", "modelo/classificador.py",
        "app/principal.py", "app/estilo.py", "app/comparador.py", "cli.py",
    ]

    encontrados = [caminho for caminho in ordem if (origem / caminho).is_file()]
    restantes = sorted(
        str(caminho.relative_to(origem))
        for caminho in origem.rglob("*.py")
        if caminho.is_file()
        and str(caminho.relative_to(origem)) not in encontrados
        and "__pycache__" not in str(caminho)
        and caminho.name != "__init__.py"
    )
    arquivos = encontrados + restantes

    cabecalho = [
        "# 7. Apêndice — código-fonte do programa",
        "",
        "> **Gerado automaticamente** por `sentinela apendice`. Não editar à mão: a edição",
        "> se perde na próxima geração, e um apêndice editado deixa de corresponder ao",
        "> código entregue.",
        "",
        "Os filtros de processamento de imagens em `pdi/` foram implementados pelo grupo,",
        "com NumPy apenas, conforme exige o enunciado (p.3, item 3.a).",
        "",
        "## Índice",
        "",
    ]

    indice = []
    corpo = []
    total_linhas = 0

    for relativo in arquivos:
        texto = (origem / relativo).read_text(encoding="utf-8").rstrip()
        linhas = len(texto.splitlines())
        total_linhas += linhas

        indice.append(f"- `sentinela/{relativo}` — {linhas} linhas")
        corpo.extend(
            ["", "---", "", f"## `sentinela/{relativo}`", "", "```python", texto, "```"]
        )

    rodape = ["", f"**Total: {len(arquivos)} arquivos, {total_linhas} linhas.**"]

    destino = Path(args.saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(cabecalho + indice + rodape + corpo) + "\n", encoding="utf-8")

    print(f"Apêndice gerado: {destino}")
    print(f"{len(arquivos)} arquivos, {total_linhas} linhas.")
    print(
        "\nAo montar o documento final, conferir se o volume do apêndice é compatível "
        "com o limite de páginas do trabalho."
    )
    return 0


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sentinela",
        description="Detecção e quantificação de desmatamento em imagens de satélite.",
    )
    subcomandos = parser.add_subparsers(dest="comando", required=True)

    app = subcomandos.add_parser("app", help="abre a interface no navegador")
    app.add_argument("--porta", type=int, default=8501)
    app.set_defaults(funcao=comando_app)

    detectar = subcomandos.add_parser("detectar", help="processa um par de imagens")
    detectar.add_argument("--antes", required=True, help="imagem RGB da primeira data")
    detectar.add_argument("--depois", required=True, help="imagem RGB da segunda data")
    detectar.add_argument("--nir-antes", dest="nir_antes")
    detectar.add_argument("--nir-depois", dest="nir_depois")
    detectar.add_argument("--swir-antes", dest="swir_antes",
                          help="banda SWIR da primeira data — necessária para --metodo ndmi (SWIR 1) ou nbr (SWIR 2)")
    detectar.add_argument("--swir-depois", dest="swir_depois")
    detectar.add_argument("--saida", help="diretório para gravar as imagens e o resumo")
    detectar.add_argument("--metodo", default="auto",
                          choices=("auto", "ndvi", "ndmi", "nbr", "vari", "exg"))
    detectar.add_argument("--suavizacao", type=int, default=5)
    detectar.add_argument("--area-minima", dest="area_minima", type=int, default=25)
    detectar.add_argument("--metros-por-pixel", dest="metros_por_pixel", type=float,
                          help="sobrepõe o metadado geográfico do arquivo")
    detectar.add_argument("--modelo", action="store_true",
                          help="treina e avalia o classificador sobre as amostras")
    detectar.add_argument("--lado", type=int, default=16,
                          help="lado do recorte das amostras, em pixels")
    detectar.add_argument("--proporcao-teste", dest="proporcao_teste", type=float,
                          default=0.3)
    detectar.add_argument("--semente", type=int, default=0)
    detectar.set_defaults(funcao=comando_detectar)

    demo = subcomandos.add_parser("demo", help="roda a cena sintética de demonstração")
    demo.add_argument("--saida", help="diretório para gravar as imagens e o resumo")
    demo.add_argument("--tamanho", type=int, default=80, help="lado da cena, em pixels")
    demo.add_argument("--area", type=int, default=20,
                      help="lado da área desmatada; 0 gera floresta intacta")
    demo.add_argument("--metros-por-pixel", dest="metros_por_pixel", type=float,
                      default=10.0)
    demo.add_argument("--modelo", action="store_true",
                      help="treina e avalia o classificador sobre as amostras")
    demo.add_argument("--proporcao-teste", dest="proporcao_teste", type=float, default=0.3)
    demo.add_argument("--semente", type=int, default=0)
    demo.set_defaults(funcao=comando_demo)

    apendice = subcomandos.add_parser(
        "apendice", help="gera o apêndice de código-fonte do trabalho escrito"
    )
    apendice.add_argument("--saida", default="_interno/docs/trabalho-escrito/07-apendice.md")
    apendice.set_defaults(funcao=comando_apendice)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)

    try:
        return args.funcao(args)
    except KeyboardInterrupt:
        print("\nInterrompido.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
