#!/usr/bin/env python3
"""Monta o trabalho escrito em DOCX a partir dos capítulos em Markdown (R020–R024).

Existe por dois motivos. O primeiro é que o documento entregue tem que corresponder ao
texto revisado no repositório: copiar e colar mil linhas no editor à mão cria uma segunda
versão que diverge na primeira correção. O segundo é a formatação exigida pelo enunciado
(p.4, item III.5) — Arial 12, espaçamento 1,5, margens laterais de 2,5 cm, A4 — que fica
garantida por construção, e não por conferência visual.

**Só biblioteca padrão.** Um arquivo DOCX é um pacote ZIP de XML (Office Open XML). Não há
dependência nova: nem `python-docx`, nem `pandoc`.

## O que o documento gerado NÃO resolve sozinho

- **Integrantes (Q7):** capa e folha de rosto saem com marcadores, lidos de ``capa.json``.
- **Margens superior e inferior (Q4):** o enunciado não as especifica. O padrão adotado
  aqui é o da ABNT NBR 14724 e é uma **suposição registrada**, alterável por parâmetro.
- **Sumário:** é um campo do Word. Ao abrir, o Word pergunta se deve atualizá-lo — é
  preciso aceitar (ou pressionar F9 sobre o sumário).
- **Ficha de APS (cap. 8):** é formulário padrão da instituição; a página sai reservada.
- **Revisão tipográfica final** no Word continua necessária: este gerador aplica a
  formatação de base, não substitui a conferência do grupo contra a norma.

## Uso

```bash
python scripts/montar_documento.py                       # entrega/trabalho-escrito.docx
python scripts/montar_documento.py --sem-apendice        # sem o código-fonte (rascunho leve)
python scripts/montar_documento.py --margem-superior 3 --margem-inferior 2
```
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / "docs" / "trabalho-escrito"
SAIDA_PADRAO = RAIZ / "saidas" / "trabalho-escrito.docx"

CAPITULOS = [
    "01-introducao.md",
    "02-referencial-teorico.md",
    "03-proposta.md",
    "04-desenvolvimento.md",
    "05-conclusao.md",
]

# --------------------------------------------------------------------------------------
# Formatação. O que vem do enunciado é exigência; o que vem da ABNT é suposição até Q4.
# --------------------------------------------------------------------------------------

FONTE = "Arial"                      # enunciado, p.4, item III.5
TAMANHO_PT = 12                      # enunciado, p.4, item III.5
ESPACAMENTO = 1.5                    # enunciado, p.4, item III.5
MARGEM_ESQUERDA_CM = 2.5             # enunciado, p.4, item III.5
MARGEM_DIREITA_CM = 2.5              # enunciado, p.4, item III.5
# Superior e inferior: o enunciado não especifica (Q4). Adotado o padrão da ABNT NBR 14724,
# conferido no tutorial do Sistema de Bibliotecas da PUC-SP (2025, NBR 14724:2024): "Margens
# Superior e Esquerda - 3cm e Inferior e Direita - 2cm". Continua sendo suposição até Q4.
MARGEM_SUPERIOR_CM = 3.0
MARGEM_INFERIOR_CM = 2.0
# Mesmo tutorial: "Parágrafo 1,25 cm", "Alinhamento Justificado".
RECUO_PRIMEIRA_LINHA_CM = 1.25

A4_LARGURA_TWIPS = 11906             # 210 mm
A4_ALTURA_TWIPS = 16838              # 297 mm
TAMANHO_CODIGO_PT = 8                # código do apêndice: cabe mais por página
TAMANHO_LEGENDA_PT = 10              # legenda de figura, menor que o corpo (NBR 14724)
EMU_POR_CM = 360000                  # unidade interna do Office
LARGURA_UTIL_CM = 21.0 - MARGEM_ESQUERDA_CM - MARGEM_DIREITA_CM
ALTURA_MAXIMA_CM = 12.0              # uma figura não pode empurrar a página inteira

# Frases de controle do rascunho que não pertencem ao documento entregue.
FRASES_DE_RASCUNHO = (
    "Esta seção está completa — é parte da Fase Intermediária I.",
)

# Figuras encontradas na travessia dos capítulos, na ordem em que aparecem: a numeração
# da legenda e o identificador da relação no pacote saem daqui.
FIGURAS: list[Path] = []

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def cm_para_twips(cm: float) -> int:
    """1 polegada = 1440 twips = 2,54 cm."""
    return round(cm * 1440 / 2.54)


# --------------------------------------------------------------------------------------
# Markdown → blocos
# --------------------------------------------------------------------------------------


@dataclass
class Bloco:
    tipo: str                         # titulo, paragrafo, lista, tabela, codigo, destaque, quebra
    texto: str = ""
    nivel: int = 0
    linhas: list = field(default_factory=list)


def ler_blocos(markdown: str, *, pular_destaques: bool = False) -> list[Bloco]:
    """Converte o subconjunto de Markdown usado nos capítulos em blocos de documento.

    Cobre o que os capítulos de fato usam: títulos, parágrafos, listas, tabelas, blocos
    de código, citações em destaque e réguas horizontais (ignoradas).
    """
    blocos: list[Bloco] = []
    linhas = markdown.splitlines()
    i = 0
    paragrafo: list[str] = []

    def fechar_paragrafo():
        if paragrafo:
            texto = " ".join(s.strip() for s in paragrafo).strip()
            if texto and texto not in FRASES_DE_RASCUNHO:
                blocos.append(Bloco("paragrafo", texto))
            paragrafo.clear()

    while i < len(linhas):
        linha = linhas[i]
        despida = linha.strip()

        if despida.startswith("```"):
            fechar_paragrafo()
            codigo = []
            i += 1
            while i < len(linhas) and not linhas[i].strip().startswith("```"):
                codigo.append(linhas[i].rstrip("\n"))
                i += 1
            blocos.append(Bloco("codigo", linhas=codigo))
            i += 1
            continue

        figura = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", despida)
        if figura:
            fechar_paragrafo()
            blocos.append(Bloco("figura", figura.group(1).strip(), linhas=[figura.group(2).strip()]))
            i += 1
            continue

        titulo = re.match(r"^(#{1,6})\s+(.*)$", despida)
        if titulo:
            fechar_paragrafo()
            blocos.append(Bloco("titulo", titulo.group(2).strip(), nivel=len(titulo.group(1))))
            i += 1
            continue

        if despida in ("---", "***", "___"):
            fechar_paragrafo()
            i += 1
            continue

        if despida.startswith("|"):
            fechar_paragrafo()
            tabela = []
            while i < len(linhas) and linhas[i].strip().startswith("|"):
                celulas = [c.strip() for c in linhas[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in celulas if c):
                    tabela.append(celulas)
                i += 1
            blocos.append(Bloco("tabela", linhas=tabela))
            continue

        if despida.startswith(">"):
            fechar_paragrafo()
            destaque = []
            while i < len(linhas) and linhas[i].strip().startswith(">"):
                destaque.append(linhas[i].strip()[1:].strip())
                i += 1
            if not pular_destaques:
                texto = " ".join(d for d in destaque if d).strip()
                if texto:
                    blocos.append(Bloco("destaque", texto))
            continue

        # Só abre lista fora de parágrafo: linhas de continuação como "2018. ISBN ..." numa
        # referência bibliográfica casariam com o padrão de lista numerada.
        item = None if paragrafo else re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", linha)
        if item:
            fechar_paragrafo()
            marcador = "•" if item.group(2) in "-*" else item.group(2)
            texto = item.group(3).strip()
            i += 1
            while (i < len(linhas) and linhas[i].strip()
                   and not re.match(r"^\s*([-*]|\d+\.)\s+", linhas[i])
                   and not linhas[i].strip().startswith(("|", ">", "#", "```"))):
                texto += " " + linhas[i].strip()
                i += 1
            blocos.append(Bloco("lista", f"{marcador} {texto}", nivel=len(item.group(1)) // 2))
            continue

        if not despida:
            fechar_paragrafo()
        else:
            paragrafo.append(despida)
        i += 1

    fechar_paragrafo()
    return blocos


# --------------------------------------------------------------------------------------
# Blocos → WordprocessingML
# --------------------------------------------------------------------------------------

_INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))")


def runs(texto: str, *, negrito: bool = False) -> str:
    """Converte negrito, itálico, código e links em runs do Word."""
    partes = []
    for pedaco in _INLINE.split(texto):
        if not pedaco:
            continue
        props = ["<w:b/>"] if negrito else []
        conteudo = pedaco
        if pedaco.startswith("**") and pedaco.endswith("**"):
            conteudo, props = pedaco[2:-2], props + ["<w:b/>"]
        elif pedaco.startswith("`") and pedaco.endswith("`"):
            conteudo = pedaco[1:-1]
            props = props + [f'<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New"/>',
                             f'<w:sz w:val="{(TAMANHO_PT - 1) * 2}"/>']
        elif pedaco.startswith("[") and "](" in pedaco:
            conteudo = pedaco[1:pedaco.index("](")]
        elif pedaco.startswith("*") and pedaco.endswith("*") and len(pedaco) > 2:
            conteudo, props = pedaco[1:-1], props + ["<w:i/>"]
        rpr = f"<w:rPr>{''.join(dict.fromkeys(props))}</w:rPr>" if props else ""
        partes.append(f'<w:r>{rpr}<w:t xml:space="preserve">{escape(conteudo)}</w:t></w:r>')
    return "".join(partes)


def paragrafo(conteudo: str, estilo: str | None = None, *, alinhamento: str | None = None,
              quebra_antes: bool = False, recuo_twips: int = 0, primeira_linha_twips: int = 0,
              secao: str = "") -> str:
    ppr = []
    if estilo:
        ppr.append(f'<w:pStyle w:val="{estilo}"/>')
    if quebra_antes:
        ppr.append("<w:pageBreakBefore/>")
    if recuo_twips or primeira_linha_twips:
        ind = f' w:left="{recuo_twips}"' if recuo_twips else ""
        ind += f' w:firstLine="{primeira_linha_twips}"' if primeira_linha_twips else ""
        ppr.append(f"<w:ind{ind}/>")
    if alinhamento:
        ppr.append(f'<w:jc w:val="{alinhamento}"/>')
    return f"<w:p><w:pPr>{''.join(ppr)}{secao}</w:pPr>{conteudo}</w:p>"


def tabela(linhas: list[list[str]]) -> str:
    if not linhas:
        return ""
    colunas = max(len(l) for l in linhas)
    largura = (A4_LARGURA_TWIPS - cm_para_twips(MARGEM_ESQUERDA_CM) - cm_para_twips(MARGEM_DIREITA_CM)) // colunas
    borda = '<w:{0} w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
    bordas = "".join(borda.format(lado) for lado in ("top", "left", "bottom", "right", "insideH", "insideV"))
    xml = [f'<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders>{bordas}</w:tblBorders></w:tblPr>',
           "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{largura}"/>' for _ in range(colunas)) + "</w:tblGrid>"]
    for indice, linha in enumerate(linhas):
        xml.append("<w:tr>")
        for c in range(colunas):
            celula = linha[c] if c < len(linha) else ""
            xml.append(f'<w:tc><w:tcPr><w:tcW w:w="{largura}" w:type="dxa"/></w:tcPr>'
                       f'{paragrafo(runs(celula, negrito=indice == 0), "Tabela")}</w:tc>')
        xml.append("</w:tr>")
    xml.append("</w:tbl>")
    # Parágrafo vazio depois da tabela: o Word não permite duas tabelas coladas.
    return "".join(xml) + paragrafo("", "Tabela")


NS_WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"


def dimensoes_png(caminho: Path) -> tuple[int, int]:
    """Largura e altura em pixels, lidas do bloco IHDR — sem depender de Pillow.

    O gerador é de biblioteca padrão por decisão de projeto; um PNG começa com a
    assinatura de 8 bytes seguida do IHDR, cujos dois primeiros campos são a largura e a
    altura em big-endian.
    """
    dados = caminho.read_bytes()[:24]
    if dados[:8] != b"\x89PNG\r\n\x1a\n" or dados[12:16] != b"IHDR":
        raise SystemExit(f"{caminho} não é um PNG válido")
    return int.from_bytes(dados[16:20], "big"), int.from_bytes(dados[20:24], "big")


def figura(indice: int, caminho: Path, legenda: str) -> str:
    """Imagem centralizada, dimensionada para a largura útil, com legenda numerada.

    A ABNT põe a legenda **abaixo** da ilustração, e a fonte logo em seguida; aqui a
    legenda já traz a origem, porque toda figura deste trabalho vem do próprio programa
    ou de imagem pública identificada no capítulo.
    """
    largura_px, altura_px = dimensoes_png(caminho)
    largura_cm = LARGURA_UTIL_CM
    altura_cm = largura_cm * altura_px / largura_px
    if altura_cm > ALTURA_MAXIMA_CM:
        largura_cm *= ALTURA_MAXIMA_CM / altura_cm
        altura_cm = ALTURA_MAXIMA_CM
    cx, cy = round(largura_cm * EMU_POR_CM), round(altura_cm * EMU_POR_CM)
    id_rel = f"rIdFigura{indice}"
    nome = escape(caminho.name)

    desenho = (
        f'<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0" xmlns:wp="{NS_WP}">'
        f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{indice}" name="Figura {indice}" '
        f'descr="{escape(legenda)}"/>'
        f'<a:graphic xmlns:a="{NS_A}"><a:graphicData '
        f'uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic xmlns:pic="{NS_PIC}"><pic:nvPicPr>'
        f'<pic:cNvPr id="{indice}" name="{nome}" descr="{escape(legenda)}"/><pic:cNvPicPr/>'
        f'</pic:nvPicPr><pic:blipFill><a:blip r:embed="{id_rel}"/>'
        f'<a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        f'</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing>'
    )
    return (paragrafo(f"<w:r>{desenho}</w:r>", alinhamento="center")
            + paragrafo(runs(f"Figura {indice} — {legenda}"), "Legenda", alinhamento="center"))


def blocos_para_xml(blocos: list[Bloco], *, capitulo_em_nova_pagina: bool = True) -> str:
    xml = []
    for b in blocos:
        if b.tipo == "titulo":
            nivel = min(b.nivel, 4)
            xml.append(paragrafo(runs(b.texto), f"Titulo{nivel}",
                                 quebra_antes=capitulo_em_nova_pagina and nivel == 1))
        elif b.tipo == "paragrafo":
            xml.append(paragrafo(runs(b.texto), primeira_linha_twips=cm_para_twips(RECUO_PRIMEIRA_LINHA_CM)))
        elif b.tipo == "lista":
            xml.append(paragrafo(runs(b.texto), recuo_twips=cm_para_twips(0.75 + 0.75 * b.nivel)))
        elif b.tipo == "destaque":
            xml.append(paragrafo(runs(b.texto), "Destaque"))
        elif b.tipo == "tabela":
            xml.append(tabela(b.linhas))
        elif b.tipo == "figura":
            caminho = (PASTA / b.linhas[0]).resolve()
            FIGURAS.append(caminho)
            xml.append(figura(len(FIGURAS), caminho, b.texto))
        elif b.tipo == "codigo":
            xml.extend(paragrafo(f'<w:r><w:t xml:space="preserve">{escape(l)}</w:t></w:r>', "Codigo")
                       for l in (b.linhas or [""]))
    return "".join(xml)


# --------------------------------------------------------------------------------------
# Elementos pré-textuais e partes do pacote
# --------------------------------------------------------------------------------------


def propriedades_de_secao(margem_superior_cm: float, margem_inferior_cm: float, *,
                          cabecalho: bool, reiniciar_em: int | None = None) -> str:
    """Página A4 com as margens do documento; opcionalmente cabeçalho e reinício da contagem.

    A paginação segue o tutorial da PUC-SP para a NBR 14724: as folhas são contadas a partir
    da folha de rosto, e o número só aparece a partir da primeira página do texto.
    """
    ref = '<w:headerReference w:type="default" r:id="rIdCabecalho"/>' if cabecalho else ""
    reinicio = f'<w:pgNumType w:start="{reiniciar_em}"/>' if reiniciar_em is not None else ""
    return (f'<w:sectPr>{ref}<w:type w:val="nextPage"/>'
            f'<w:pgSz w:w="{A4_LARGURA_TWIPS}" w:h="{A4_ALTURA_TWIPS}"/>'
            f'<w:pgMar w:top="{cm_para_twips(margem_superior_cm)}" w:right="{cm_para_twips(MARGEM_DIREITA_CM)}" '
            f'w:bottom="{cm_para_twips(margem_inferior_cm)}" w:left="{cm_para_twips(MARGEM_ESQUERDA_CM)}" '
            f'w:header="{cm_para_twips(1.25)}" w:footer="{cm_para_twips(1.25)}" w:gutter="0"/>'
            f'{reinicio}</w:sectPr>')


def capa_e_rosto(dados: dict) -> str:
    def centro(texto, negrito=False):
        return paragrafo(runs(texto, negrito=negrito), alinhamento="center")

    integrantes = dados.get("integrantes") or []
    xml = [centro(dados["instituicao"], negrito=True), centro(dados["curso"])]
    xml += [centro(f"{i['nome']} — RA {i['ra']}") for i in integrantes]
    xml += [paragrafo("") for _ in range(6)]
    xml += [centro(dados["titulo"].upper(), negrito=True), paragrafo("")]
    xml += [paragrafo("") for _ in range(8)]
    xml += [centro(dados["cidade"]), centro(str(dados["ano"]))]
    xml.append("{{FIM_DA_CAPA}}")
    xml.append(paragrafo(runs(dados["instituicao"], negrito=True), alinhamento="center"))
    xml += [centro(f"{i['nome']} — RA {i['ra']}") for i in integrantes]
    xml += [paragrafo("") for _ in range(4)]
    xml += [centro(dados["titulo"].upper(), negrito=True), paragrafo("")]
    xml.append(paragrafo(runs(dados["natureza"]), "Destaque", alinhamento="both"))
    xml += [paragrafo("") for _ in range(4)]
    xml += [centro(dados["cidade"]), centro(str(dados["ano"]))]
    return "".join(xml)


def sumario() -> str:
    campo = ('<w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'
             '<w:r><w:instrText xml:space="preserve"> TOC \\o "1-3" \\h \\z \\u </w:instrText></w:r>'
             '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
             '<w:r><w:t>Atualize o sumário no Word: clique aqui e pressione F9.</w:t></w:r>'
             '<w:r><w:fldChar w:fldCharType="end"/></w:r>')
    return (paragrafo(runs("SUMÁRIO", negrito=True), alinhamento="center", quebra_antes=True)
            + "{{FIM_DOS_PRE_TEXTUAIS}}" + paragrafo(campo))


def estilos() -> str:
    tamanho = TAMANHO_PT * 2
    linha = round(240 * ESPACAMENTO)

    def titulo(nivel, italico=False):
        return (f'<w:style w:type="paragraph" w:styleId="Titulo{nivel}"><w:name w:val="heading {nivel}"/>'
                f'<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
                f'<w:pPr><w:keepNext/><w:spacing w:before="240" w:after="240"/><w:jc w:val="left"/>'
                f'<w:outlineLvl w:val="{nivel - 1}"/></w:pPr>'
                f'<w:rPr><w:b/>{"<w:i/>" if italico else ""}<w:sz w:val="{tamanho}"/></w:rPr></w:style>')

    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:styles xmlns:w="{NS_W}">'
            f'<w:docDefaults><w:rPrDefault><w:rPr>'
            f'<w:rFonts w:ascii="{FONTE}" w:hAnsi="{FONTE}" w:cs="{FONTE}" w:eastAsia="{FONTE}"/>'
            f'<w:sz w:val="{tamanho}"/><w:szCs w:val="{tamanho}"/><w:lang w:val="pt-BR"/>'
            f'</w:rPr></w:rPrDefault>'
            f'<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="{linha}" w:lineRule="auto"/>'
            f'<w:jc w:val="both"/></w:pPr></w:pPrDefault></w:docDefaults>'
            f'<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>'
            + titulo(1) + titulo(2) + titulo(3) + titulo(4, italico=True) +
            f'<w:style w:type="paragraph" w:styleId="Destaque"><w:name w:val="Destaque"/><w:basedOn w:val="Normal"/>'
            f'<w:pPr><w:ind w:left="{cm_para_twips(1.25)}"/><w:spacing w:before="120" w:after="120"/></w:pPr></w:style>'
            f'<w:style w:type="paragraph" w:styleId="Tabela"><w:name w:val="Tabela"/><w:basedOn w:val="Normal"/>'
            f'<w:pPr><w:spacing w:line="240" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr>'
            f'<w:rPr><w:sz w:val="{(TAMANHO_PT - 2) * 2}"/></w:rPr></w:style>'
            f'<w:style w:type="paragraph" w:styleId="Legenda"><w:name w:val="Legenda"/><w:basedOn w:val="Normal"/>'
            f'<w:pPr><w:spacing w:before="120" w:after="240" w:line="240" w:lineRule="auto"/>'
            f'<w:jc w:val="center"/></w:pPr><w:rPr><w:sz w:val="{TAMANHO_LEGENDA_PT * 2}"/></w:rPr></w:style>'
            f'<w:style w:type="paragraph" w:styleId="Codigo"><w:name w:val="Codigo"/><w:basedOn w:val="Normal"/>'
            f'<w:pPr><w:spacing w:line="240" w:lineRule="auto"/><w:jc w:val="left"/></w:pPr>'
            f'<w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/>'
            f'<w:sz w:val="{TAMANHO_CODIGO_PT * 2}"/></w:rPr></w:style>'
            f'</w:styles>')


def cabecalho_com_pagina() -> str:
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:hdr xmlns:w="{NS_W}"><w:p><w:pPr><w:jc w:val="right"/></w:pPr>'
            f'<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
            f'<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r>'
            f'<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:hdr>')


def documento(corpo: str, margem_superior_cm: float, margem_inferior_cm: float) -> str:
    # Uma seção termina num parágrafo que carrega o sectPr; a última fica no fim do body.
    capa = paragrafo("", secao=propriedades_de_secao(margem_superior_cm, margem_inferior_cm, cabecalho=False))
    pre = paragrafo("", secao=propriedades_de_secao(margem_superior_cm, margem_inferior_cm,
                                                    cabecalho=False, reiniciar_em=1))
    corpo = corpo.replace("{{FIM_DA_CAPA}}", capa, 1)
    # O sumário vem antes do marcador de fim dos pré-textuais: move o campo para dentro da seção.
    corpo = corpo.replace("{{FIM_DOS_PRE_TEXTUAIS}}", "", 1)
    corpo = corpo.replace("{{FIM_DO_SUMARIO}}", pre, 1)
    ultima = propriedades_de_secao(margem_superior_cm, margem_inferior_cm, cabecalho=True)
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:document xmlns:w="{NS_W}" xmlns:r="{NS_R}"><w:body>{corpo}{ultima}</w:body></w:document>')


PARTES_FIXAS = {
    "[Content_Types].xml": (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
        '<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
        '</Types>'),
    "_rels/.rels": (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>'),
    "word/_rels/document.xml.rels": (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rIdEstilos" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '<Relationship Id="rIdConfig" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>'
        '<Relationship Id="rIdCabecalho" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>'
        '</Relationships>'),
    "word/settings.xml": (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:settings xmlns:w="{NS_W}"><w:updateFields w:val="true"/><w:defaultTabStop w:val="709"/></w:settings>'),
}


def tipos_de_conteudo(com_figuras: bool) -> str:
    """``[Content_Types].xml`` — o PNG entra como extensão padrão só quando há figura."""
    png = ('<Default Extension="png" ContentType="image/png"/>' if com_figuras else "")
    return PARTES_FIXAS["[Content_Types].xml"].replace(
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>' + png, 1)


def relacoes_do_documento(figuras: list[Path]) -> str:
    """Relações fixas mais uma por figura, no mesmo índice usado pela legenda."""
    extra = "".join(
        f'<Relationship Id="rIdFigura{n}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
        f'relationships/image" Target="media/figura{n}.png"/>'
        for n, _ in enumerate(figuras, start=1))
    return PARTES_FIXAS["word/_rels/document.xml.rels"].replace("</Relationships>", extra + "</Relationships>", 1)


# --------------------------------------------------------------------------------------
# Montagem
# --------------------------------------------------------------------------------------


def referencias(texto_bibliografia: str) -> str:
    """Só a seção de referências — a tabela de verificação é registro interno do projeto."""
    m = re.search(r"^## Referências\s*$(.*?)(?=^## )", texto_bibliografia, re.S | re.M)
    if not m:
        raise SystemExit("BIBLIOGRAFIA.md sem a seção '## Referências'")
    return m.group(1)


def pendencias(dados: dict) -> list[str]:
    """O que o documento gerado ainda carrega de provisório."""
    avisos = []
    if any("Q7" in f"{i['nome']} {i['ra']}" for i in dados.get("integrantes", [])):
        avisos.append("integrantes e RAs são marcadores — Q7")
    if "[" in dados.get("cidade", ""):
        avisos.append("cidade do campus é marcador")
    return avisos


def montar(saida: Path, *, apendice: bool = True,
           margem_superior_cm: float = MARGEM_SUPERIOR_CM,
           margem_inferior_cm: float = MARGEM_INFERIOR_CM) -> list[str]:
    dados = json.loads((PASTA / "capa.json").read_text(encoding="utf-8"))
    FIGURAS.clear()
    corpo = [capa_e_rosto(dados), sumario(), "{{FIM_DO_SUMARIO}}"]

    for indice, nome in enumerate(CAPITULOS):
        xml = blocos_para_xml(ler_blocos((PASTA / nome).read_text(encoding="utf-8")))
        if indice == 0:
            xml = xml.replace("<w:pageBreakBefore/>", "", 1)
        corpo.append(xml)

    corpo.append(paragrafo(runs("6. Bibliografia"), "Titulo1", quebra_antes=True))
    corpo.append(blocos_para_xml(ler_blocos(referencias((PASTA / "BIBLIOGRAFIA.md").read_text(encoding="utf-8")))))

    if apendice:
        corpo.append(blocos_para_xml(ler_blocos((PASTA / "07-apendice.md").read_text(encoding="utf-8"),
                                                pular_destaques=True)))
    else:
        corpo.append(paragrafo(runs("7. Apêndice — código-fonte do programa"), "Titulo1", quebra_antes=True))
        corpo.append(paragrafo(runs("*Omitido nesta versão de rascunho. Gerar sem --sem-apendice.*")))

    corpo.append(paragrafo(runs("8. Ficha de Atividades Práticas Supervisionadas"), "Titulo1", quebra_antes=True))
    corpo.append(paragrafo(runs("[Inserir aqui a ficha padrão de APS preenchida em ordem cronológica "
                                "— enunciado, p.4, item III.6.]")))

    saida.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as pacote:
        reescritas = {"[Content_Types].xml", "word/_rels/document.xml.rels"}
        for nome, conteudo in PARTES_FIXAS.items():
            if nome not in reescritas:            # essas duas dependem das figuras
                pacote.writestr(nome, conteudo)
        pacote.writestr("[Content_Types].xml", tipos_de_conteudo(bool(FIGURAS)))
        pacote.writestr("word/_rels/document.xml.rels", relacoes_do_documento(FIGURAS))
        for numero, origem in enumerate(FIGURAS, start=1):
            pacote.writestr(f"word/media/figura{numero}.png", origem.read_bytes())
        pacote.writestr("word/styles.xml", estilos())
        pacote.writestr("word/header1.xml", cabecalho_com_pagina())
        pacote.writestr("word/document.xml", documento("".join(corpo), margem_superior_cm, margem_inferior_cm))

    avisos = pendencias(dados)
    if margem_superior_cm == MARGEM_SUPERIOR_CM and margem_inferior_cm == MARGEM_INFERIOR_CM:
        avisos.append(f"margens superior {MARGEM_SUPERIOR_CM} cm e inferior {MARGEM_INFERIOR_CM} cm "
                      "são suposição (ABNT NBR 14724) — Q4")
    avisos.append("sumário precisa ser atualizado ao abrir no Word (F9)")
    avisos.append("títulos seguem a numeração do enunciado (\"1. Introdução\", \"1.a.\"); a NBR 14724 "
                  "pede número sem pontuação antes do título — decidir com o professor (Q2)")
    avisos.append("ficha de APS (cap. 8) é página reservada")
    return avisos


def montar_avulso(saida: Path, origem: Path, *, paisagem: bool = False) -> Path:
    """Gera um DOCX simples a partir de um Markdown, sem capa, sumário nem apêndice.

    Serve para os documentos de apoio da entrega — hoje, as falas da apresentação. Reaproveita
    o mesmo conversor de Markdown e os mesmos estilos do trabalho escrito, para que o grupo
    entregue um conjunto com a mesma cara.
    """
    FIGURAS.clear()
    corpo = blocos_para_xml(ler_blocos(origem.read_text(encoding="utf-8")),
                            capitulo_em_nova_pagina=False)
    secao = propriedades_de_secao(2.5, 2.0, cabecalho=True)
    xml = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           f'<w:document xmlns:w="{NS_W}" xmlns:r="{NS_R}"><w:body>{corpo}{secao}</w:body></w:document>')

    saida.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as pacote:
        for nome, conteudo in PARTES_FIXAS.items():
            if nome not in {"[Content_Types].xml", "word/_rels/document.xml.rels"}:
                pacote.writestr(nome, conteudo)
        pacote.writestr("[Content_Types].xml", tipos_de_conteudo(bool(FIGURAS)))
        pacote.writestr("word/_rels/document.xml.rels", relacoes_do_documento(FIGURAS))
        pacote.writestr("word/styles.xml", estilos())
        pacote.writestr("word/header1.xml", cabecalho_com_pagina())
        pacote.writestr("word/document.xml", xml)
    return saida


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Monta o trabalho escrito em DOCX.")
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    parser.add_argument("--sem-apendice", action="store_true")
    parser.add_argument("--avulso", type=Path,
                        help="gera um DOCX simples a partir deste Markdown, sem capa nem sumário")
    parser.add_argument("--margem-superior", type=float, default=MARGEM_SUPERIOR_CM)
    parser.add_argument("--margem-inferior", type=float, default=MARGEM_INFERIOR_CM)
    args = parser.parse_args(argv)

    if args.avulso:
        caminho = montar_avulso(args.saida, args.avulso)
        print(f"Documento gerado: {caminho} ({caminho.stat().st_size // 1024} KB)")
        return 0

    avisos = montar(args.saida, apendice=not args.sem_apendice,
                    margem_superior_cm=args.margem_superior, margem_inferior_cm=args.margem_inferior)
    print(f"Documento gerado: {args.saida} ({args.saida.stat().st_size // 1024} KB)")
    print(f"Formatação: {FONTE} {TAMANHO_PT}, espaçamento {ESPACAMENTO}, A4, "
          f"margens E/D {MARGEM_ESQUERDA_CM}/{MARGEM_DIREITA_CM} cm, "
          f"S/I {args.margem_superior}/{args.margem_inferior} cm")
    print("\nAinda provisório:")
    for aviso in avisos:
        print(f"  - {aviso}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
