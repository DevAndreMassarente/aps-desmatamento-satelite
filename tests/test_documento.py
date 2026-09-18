"""Testes do gerador do trabalho escrito em DOCX.

O que importa verificar: o pacote é um DOCX estruturalmente válido, a formatação exigida
pelo enunciado (p.4, item III.5) está nos estilos por construção, e nada de rascunho —
marcador de fonte pendente, frase de controle, tabela interna de verificação — vaza para o
documento entregue.

Não há Word nesta máquina: o teste garante XML bem formado e as partes obrigatórias do
pacote, não a renderização.
"""

import importlib.util
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

_caminho = Path(__file__).resolve().parents[1] / "scripts" / "montar_documento.py"
_spec = importlib.util.spec_from_file_location("montar_documento", _caminho)
gerador = importlib.util.module_from_spec(_spec)
# O gerador usa @dataclass, que procura o próprio módulo em sys.modules durante a definição
# da classe. Carregado por caminho, o módulo precisa ser registrado antes de executar.
sys.modules[_spec.name] = gerador
_spec.loader.exec_module(gerador)

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


@pytest.fixture(scope="module")
def pacote(tmp_path_factory):
    destino = tmp_path_factory.mktemp("doc") / "trabalho.docx"
    avisos = gerador.montar(destino, apendice=False)
    with zipfile.ZipFile(destino) as z:
        # As imagens entram no pacote como bytes; só as partes de texto são decodificadas.
        partes = {nome: (z.read(nome) if nome.startswith("word/media/") else
                         z.read(nome).decode("utf-8")) for nome in z.namelist()}
    return partes, avisos


class TestPacote:
    def test_tem_as_partes_obrigatorias(self, pacote):
        partes, _ = pacote
        for nome in ("[Content_Types].xml", "_rels/.rels", "word/document.xml",
                     "word/styles.xml", "word/_rels/document.xml.rels"):
            assert nome in partes, nome

    def test_todo_xml_e_bem_formado(self, pacote):
        partes, _ = pacote
        for nome, conteudo in partes.items():
            if isinstance(conteudo, str):
                ET.fromstring(conteudo.encode("utf-8"))  # levanta se estiver malformado

    def test_relacoes_apontam_para_partes_existentes(self, pacote):
        partes, _ = pacote
        alvos = re.findall(r'Target="([^"]+)"', partes["word/_rels/document.xml.rels"])
        for alvo in alvos:
            assert f"word/{alvo}" in partes, alvo


class TestFormatacaoDoEnunciado:
    """Enunciado, p.4, item III.5 — garantido por construção."""

    def test_fonte_arial_12(self, pacote):
        estilos = ET.fromstring(pacote[0]["word/styles.xml"])
        padrao = estilos.find(f"{W}docDefaults/{W}rPrDefault/{W}rPr")
        assert padrao.find(f"{W}rFonts").get(f"{W}ascii") == "Arial"
        assert padrao.find(f"{W}sz").get(f"{W}val") == "24"  # meios-pontos

    def test_espacamento_um_e_meio(self, pacote):
        estilos = ET.fromstring(pacote[0]["word/styles.xml"])
        espacamento = estilos.find(f"{W}docDefaults/{W}pPrDefault/{W}pPr/{W}spacing")
        assert espacamento.get(f"{W}line") == "360"  # 240 = simples
        assert espacamento.get(f"{W}lineRule") == "auto"

    def test_papel_a4(self, pacote):
        corpo = ET.fromstring(pacote[0]["word/document.xml"])
        tamanho = corpo.find(f"{W}body/{W}sectPr/{W}pgSz")
        assert (tamanho.get(f"{W}w"), tamanho.get(f"{W}h")) == ("11906", "16838")

    def test_margens_laterais_de_dois_e_meio_centimetros(self, pacote):
        corpo = ET.fromstring(pacote[0]["word/document.xml"])
        margens = corpo.find(f"{W}body/{W}sectPr/{W}pgMar")
        assert margens.get(f"{W}left") == margens.get(f"{W}right") == "1417"

    def test_margens_superior_e_inferior_sao_parametro(self, tmp_path):
        destino = tmp_path / "m.docx"
        gerador.montar(destino, apendice=False, margem_superior_cm=2.5, margem_inferior_cm=2.5)
        with zipfile.ZipFile(destino) as z:
            margens = ET.fromstring(z.read("word/document.xml")).find(f"{W}body/{W}sectPr/{W}pgMar")
        assert margens.get(f"{W}top") == margens.get(f"{W}bottom") == "1417"

    def test_conversao_de_centimetros(self):
        assert gerador.cm_para_twips(2.54) == 1440


class TestConteudo:
    def test_estrutura_exigida_pelo_enunciado(self, pacote):
        texto = pacote[0]["word/document.xml"]
        for titulo in ("1. Introdução", "2. Referencial teórico", "3. Proposta",
                       "4. Desenvolvimento", "5. Conclusão", "6. Bibliografia",
                       "7. Apêndice", "8. Ficha de Atividades Práticas Supervisionadas"):
            assert titulo in texto, titulo

    def test_nada_de_rascunho_vaza(self, pacote):
        texto = pacote[0]["word/document.xml"]
        assert "NEEDS_SOURCE" not in texto
        assert "Esta seção está completa" not in texto
        assert "Descartadas" not in texto, "a tabela interna de verificação não é do documento"

    def test_referencias_estao_presentes(self, pacote):
        texto = pacote[0]["word/document.xml"]
        assert "A threshold selection method from gray-level histograms" in texto
        assert "Random forests" in texto

    def test_tabelas_viram_tabelas_do_word(self, pacote):
        assert pacote[0]["word/document.xml"].count("<w:tbl>") >= 10

    def test_sumario_e_campo_atualizavel(self, pacote):
        partes, _ = pacote
        assert 'TOC \\o "1-3"' in partes["word/document.xml"]
        assert '<w:updateFields w:val="true"/>' in partes["word/settings.xml"]

    def test_titulos_entram_no_sumario(self, pacote):
        estilos = pacote[0]["word/styles.xml"]
        assert re.search(r'styleId="Titulo1".*?<w:outlineLvl w:val="0"/>', estilos)

    def test_negrito_do_markdown_vira_negrito(self):
        xml = gerador.runs("um **forte** fim")
        assert "<w:b/>" in xml and "forte" in xml and "**" not in xml

    def test_caracteres_especiais_sao_escapados(self):
        xml = gerador.runs("a < b & c > d")
        ET.fromstring(f'<w:p xmlns:w="{W[1:-1]}">{xml}</w:p>')

    def test_capa_traz_os_integrantes_e_nenhum_marcador(self, pacote):
        """Q7 foi respondida: capa e folha de rosto saem com nomes e RAs reais."""
        texto = pacote[0]["word/document.xml"]
        assert "André Massarente" in texto and "G280BI1" in texto
        assert "[NOME DO INTEGRANTE" not in texto and "Q7" not in texto
        assert not any("Q7" in a for a in pacote[1])

    def test_margens_sem_fonte_no_enunciado_continuam_avisadas(self, pacote):
        assert any("Q4" in a for a in pacote[1])


class TestNormaABNT:
    """NBR 14724, conferida no tutorial do Sistema de Bibliotecas da PUC-SP."""

    def test_paragrafo_de_corpo_tem_recuo_de_primeira_linha(self, pacote):
        assert 'w:firstLine="709"' in pacote[0]["word/document.xml"]  # 1,25 cm

    def test_titulos_e_tabelas_nao_recebem_recuo(self):
        blocos = gerador.ler_blocos("# 1. Título\n\n| a | b |\n|---|---|\n| 1 | 2 |\n")
        xml = gerador.blocos_para_xml(blocos)
        assert "firstLine" not in xml

    def test_tres_secoes_capa_pretextuais_e_texto(self, pacote):
        corpo = ET.fromstring(pacote[0]["word/document.xml"])
        secoes = corpo.findall(f".//{W}sectPr")
        assert len(secoes) == 3

    def test_numero_de_pagina_so_na_secao_do_texto(self, pacote):
        corpo = ET.fromstring(pacote[0]["word/document.xml"])
        secoes = corpo.findall(f".//{W}sectPr")
        com_cabecalho = [s.find(f"{W}headerReference") is not None for s in secoes]
        assert com_cabecalho == [False, False, True]

    def test_contagem_comeca_na_folha_de_rosto(self, pacote):
        corpo = ET.fromstring(pacote[0]["word/document.xml"])
        pre_textuais = corpo.findall(f".//{W}sectPr")[1]
        assert pre_textuais.find(f"{W}pgNumType").get(f"{W}start") == "1"

    def test_capa_e_folha_de_rosto_trazem_o_ano(self, pacote):
        """Regressão: a inserção da quebra de seção tinha apagado o ano da capa."""
        corpo = ET.fromstring(pacote[0]["word/document.xml"])
        paragrafos = ["".join(t.text or "" for t in p.iter(f"{W}t")) for p in corpo.iter(f"{W}p")]
        fim_capa = next(i for i, p in enumerate(corpo.iter(f"{W}p")) if p.find(f"{W}pPr/{W}sectPr") is not None)
        assert "2026" in paragrafos[:fim_capa], "ano ausente da capa"
        assert paragrafos[fim_capa + 1:].count("2026") >= 1, "ano ausente da folha de rosto"

    def test_numeracao_dos_titulos_e_avisada(self, pacote):
        assert any("Q2" in a for a in pacote[1])


class TestParserDeReferencias:
    def test_linha_de_continuacao_com_ano_nao_vira_lista(self):
        """Regressão: '2018. ISBN ...' casava com lista numerada e partia a referência."""
        texto = ("GONZALEZ, R. C.; WOODS, R. E. **Digital image processing**. 4. ed. [S. l.]: Pearson,\n"
                 "2018. ISBN 978-0-13-335672-4.\n")
        blocos = gerador.ler_blocos(texto)
        assert [b.tipo for b in blocos] == ["paragrafo"]
        assert "2018. ISBN" in blocos[0].texto

    def test_lista_numerada_depois_de_linha_em_branco_continua_lista(self):
        blocos = gerador.ler_blocos("Intro:\n\n1. primeiro\n2. segundo\n")
        assert [b.tipo for b in blocos] == ["paragrafo", "lista", "lista"]

    def test_apendice_entra_como_codigo(self, tmp_path):
        destino = tmp_path / "completo.docx"
        gerador.montar(destino, apendice=True)
        with zipfile.ZipFile(destino) as z:
            texto = z.read("word/document.xml").decode("utf-8")
        assert texto.count('w:val="Codigo"') > 1000
        assert "def kernel_gaussiano_1d(" in texto
        # A frase existe legitimamente no código-fonte do cli.py reproduzido no apêndice; o que
        # não pode existir é o aviso interno renderizado como parágrafo de destaque.
        corpo = ET.fromstring(texto)
        destaques = [
            "".join(t.text or "" for t in p.iter(f"{W}t"))
            for p in corpo.iter(f"{W}p")
            if (s := p.find(f"{W}pPr/{W}pStyle")) is not None and s.get(f"{W}val") == "Destaque"
        ]
        assert not any("Gerado automaticamente" in d for d in destaques)


class TestFiguras:
    """O enunciado pede que o resultado dos filtros seja apresentado (p.3, item 3.a):
    sem imagem no documento, o texto descreve um efeito que o leitor não vê."""

    def test_o_documento_traz_imagens(self, pacote):
        partes, _ = pacote
        midia = [n for n in partes if n.startswith("word/media/")]
        assert len(midia) >= 5, midia

    def test_cada_imagem_tem_relacao_e_legenda(self, pacote):
        partes, _ = pacote
        corpo = ET.fromstring(partes["word/document.xml"])
        A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
        R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
        alvos = {r.get("Id") for r in ET.fromstring(partes["word/_rels/document.xml.rels"])}
        embutidas = [b.get(f"{R}embed") for b in corpo.iter(f"{A}blip")]
        assert embutidas and set(embutidas) <= alvos
        legendas = [
            "".join(t.text or "" for t in p.iter(f"{W}t"))
            for p in corpo.iter(f"{W}p")
            if (e := p.find(f"{W}pPr/{W}pStyle")) is not None and e.get(f"{W}val") == "Legenda"
        ]
        assert len(legendas) == len(embutidas)
        assert all(l.startswith(f"Figura {n} — ") for n, l in enumerate(legendas, start=1))

    def test_png_declarado_no_content_types(self, pacote):
        assert 'Extension="png"' in pacote[0]["[Content_Types].xml"]

    def test_figura_cabe_na_largura_util(self):
        largura = gerador.LARGURA_UTIL_CM * gerador.EMU_POR_CM
        caminho = (gerador.PASTA / ".." / "apresentacao" / "figuras" / "efeito-dos-filtros.png").resolve()
        xml = gerador.figura(1, caminho, "teste")
        cx = int(re.search(r'<wp:extent cx="(\d+)"', xml).group(1))
        assert cx <= largura + 1

    def test_markdown_de_imagem_vira_bloco_de_figura(self):
        blocos = gerador.ler_blocos("![uma legenda](../x/y.png)\n")
        assert [b.tipo for b in blocos] == ["figura"]
        assert blocos[0].texto == "uma legenda" and blocos[0].linhas == ["../x/y.png"]

    def test_png_invalido_e_recusado(self, tmp_path):
        falso = tmp_path / "falso.png"
        falso.write_bytes(b"nao sou um png")
        with pytest.raises(SystemExit):
            gerador.dimensoes_png(falso)


class TestDocumentoAvulso:
    """As falas da apresentação saem do mesmo conversor, sem capa nem sumário."""

    @staticmethod
    @pytest.fixture(scope="class")
    def falas(tmp_path_factory):
        destino = tmp_path_factory.mktemp("avulso") / "falas.docx"
        origem = Path(__file__).resolve().parents[1] / "docs" / "apresentacao" / "ROTEIRO.md"
        gerador.montar_avulso(destino, origem)
        with zipfile.ZipFile(destino) as z:
            return {n: z.read(n).decode("utf-8") for n in z.namelist()}

    def test_xml_bem_formado_e_partes_obrigatorias(self, falas):
        for nome in ("[Content_Types].xml", "word/document.xml", "word/styles.xml"):
            assert nome in falas
            ET.fromstring(falas[nome].encode("utf-8"))

    def test_nao_tem_capa_nem_sumario(self, falas):
        assert "TOC" not in falas["word/document.xml"]
        assert "UNIVERSIDADE PAULISTA" not in falas["word/document.xml"]

    def test_cada_integrante_tem_bloco_de_falas(self, falas):
        texto = falas["word/document.xml"]
        for nome in ("André Massarente", "Enzo Consani", "Isabel Da Silva",
                     "Jonathan Aparecido X Martins"):
            assert nome in texto, nome

    def test_traz_o_que_nao_dizer(self, falas):
        """Regressão de integridade: a lista do que não afirmar na banca é parte da entrega."""
        assert "ele se recusou" in falas["word/document.xml"]
