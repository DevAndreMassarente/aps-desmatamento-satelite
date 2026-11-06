// Monta a apresentação do seminário (enunciado, seção III) em PPTX.
//
// Existe pelo mesmo motivo do gerador do trabalho escrito: os números da apresentação
// precisam ser os mesmos do repositório. Todo valor citado aqui sai de
// _interno/docs/resultados/*/resumo.json ou do texto já conferido em _interno/docs/trabalho-escrito/.
//
// As falas de cada integrante vão nas notas do apresentador de cada slide — é onde o
// PowerPoint as exibe no modo apresentador e de onde saem as páginas de anotações
// impressas. A versão impressa em DOCX é gerada por _interno/scripts/montar_falas.py.
//
//   node _interno/scripts/montar_apresentacao.mjs [saida.pptx]
//
// pptxgenjs não é dependência da aplicação: instale-o só para gerar o arquivo
// (`npm install pptxgenjs`) ou aponte NODE_PATH para uma instalação existente.

import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const PptxGenJS = require("pptxgenjs");

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const FIG = join(RAIZ, "_interno/docs/apresentacao/figuras");
const RES = join(RAIZ, "_interno/docs/resultados");
// O enunciado divide o projeto em duas entregas com apresentação distinta (p. 5). A
// Fase Intermediária I — Qualificação cobre o capítulo 1 e os itens de filtragem dos
// capítulos 2 e 3, antes do desenvolvimento prático. A Fase Intermediária II — Defesa
// cobre o protótipo e os resultados. Cada uma tem o seu arquivo.
const FASES = {
  qualificacao: "entrega/fase-1/apresentacao-qualificacao.pptx",
  defesa: "entrega/apresentacao-defesa.pptx",
};
const pedida = process.argv[2] ?? "ambas";
if (!["ambas", ...Object.keys(FASES)].includes(pedida)) {
  console.error(`Fase desconhecida: ${pedida}. Use qualificacao, defesa ou ambas.`);
  process.exit(1);
}

// Números lidos do próprio repositório: se a evidência mudar, o slide muda junto.
const real = JSON.parse(readFileSync(join(RES, "imagem-real/resumo.json"), "utf-8"));
const sintetica = JSON.parse(readFileSync(join(RES, "cena-sintetica/resumo.json"), "utf-8"));
const sentinel = JSON.parse(readFileSync(join(RES, "sentinel-2/teste.json"), "utf-8"));
const calibracao = JSON.parse(readFileSync(join(RES, "sentinel-2/calibracao.json"), "utf-8"));

const distinguibilidadeNbr = (filtro) => calibracao.filter(filtro)
  .map((janela) => janela.nbr.distinguibilidade).sort((a, b) => a - b);
const janelasIntactas = distinguibilidadeNbr((j) => j.nova < 0.005 && j.antiga < 0.05);
const janelasComPerda = distinguibilidadeNbr((j) => j.nova >= 0.03);
const mediana = (v) => v.length % 2
  ? v[(v.length - 1) / 2]
  : (v[v.length / 2 - 1] + v[v.length / 2]) / 2;

const br = (n, casas = 2) => n.toLocaleString("pt-BR", {
  minimumFractionDigits: casas, maximumFractionDigits: casas,
});

// --------------------------------------------------------------------------------------
// Identidade visual. Verde de floresta porque o assunto é cobertura vegetal; o terracota
// é reservado ao que o sistema recusa — nunca usado como enfeite.
// --------------------------------------------------------------------------------------

const COR = {
  escuro: "16301B",      // fundo das capas e dos slides de virada
  floresta: "2C5F2D",    // primária
  musgo: "97BC62",       // secundária
  claro: "F4F7F1",       // fundo dos slides de conteúdo
  branco: "FFFFFF",
  cartao: "E7EEE0",      // tinte suave dos blocos
  texto: "3A3F38",
  suave: "6E756A",
  alerta: "B24B2E",      // só para recusa e limitação
};

const TIT = "Cambria";
const CORPO = "Calibri";
const L = 13.333;
const ALT = 7.5;
const MARGEM = 0.62;
const LARGURA = L - 2 * MARGEM;

const sombra = () => ({ type: "outer", color: "1B2A1C", blur: 10, offset: 2, angle: 90, opacity: 0.18 });

/** Dimensões de um PNG lidas do bloco IHDR — evita esticar imagem por engano. */
function dimensoesPng(caminho) {
  const b = readFileSync(caminho).subarray(0, 24);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

/**
 * Coloca a imagem dentro da caixa (x, y, w, h) preservando a proporção e centralizando
 * no eixo que sobrar. Uma imagem esticada é o defeito mais visível num slide, e a conta
 * feita à mão erra sempre que a figura é regerada com outro tamanho.
 */
function imagem(s, caminho, { x, y, w, h, alinhar = "centro" }) {
  const nat = dimensoesPng(caminho);
  const escala = Math.min(w / nat.w, h / nat.h);
  const lw = nat.w * escala;
  const lh = nat.h * escala;
  const dx = alinhar === "esquerda" ? 0 : (w - lw) / 2;
  s.addImage({ path: caminho, x: x + dx, y: y + (h - lh) / 2, w: lw, h: lh, shadow: sombra() });
  return { x: x + dx, y: y + (h - lh) / 2, w: lw, h: lh };
}

// As peças de montagem escrevem na apresentação corrente. Cada fase abre a sua.
let pres;
// Na defesa o nome de quem fala fica só nas notas, não no slide.
let semRodape = false;

function abrirApresentacao() {
  pres = new PptxGenJS();
  pres.layout = "LAYOUT_WIDE";
  pres.author = "André Massarente, Enzo Consani, Isabel Da Silva, Jonathan Aparecido X Martins";
  pres.company = "Universidade Paulista — UNIP";
  pres.title = "Detecção e quantificação de desmatamento em imagens de satélite";
}

// --------------------------------------------------------------------------------------
// Peças reutilizadas
// --------------------------------------------------------------------------------------

/** Slide de conteúdo: fundo claro, título, e o nome de quem fala no rodapé. */
function slide({ titulo, sub, quem, escuro = false }) {
  const s = pres.addSlide();
  s.background = { color: escuro ? COR.escuro : COR.claro };
  if (titulo) {
    s.addText(titulo, {
      x: MARGEM, y: 0.44, w: LARGURA, h: 0.94, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 32, bold: true, color: escuro ? COR.branco : COR.floresta,
      valign: "middle", fit: "shrink",
    });
  }
  if (sub) {
    s.addText(sub, {
      x: MARGEM, y: 1.38, w: LARGURA, h: 0.4, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 15, italic: true,
      color: escuro ? COR.musgo : COR.suave, valign: "middle",
    });
  }
  if (quem && !semRodape) {
    s.addText(quem, {
      x: MARGEM, y: ALT - 0.62, w: LARGURA, h: 0.3, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 10.5, color: escuro ? COR.musgo : COR.suave,
    });
  }
  return s;
}

/** Bloco de texto sobre tinte suave — o cartão é o motivo visual repetido no deck. */
function cartao(s, { x, y, w, h, escuro = false }) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.12,
    fill: { color: escuro ? "1F3D24" : COR.cartao },
    line: { color: escuro ? "1F3D24" : COR.cartao, width: 0 },
  });
}

/** Número dentro de um círculo de musgo: numera etapas e decisões sem virar lista. */
function numero(s, n, { x, y, d = 0.52, cor = COR.floresta }) {
  s.addShape(pres.ShapeType.ellipse, { x, y, w: d, h: d, fill: { color: cor } });
  s.addText(String(n), {
    x, y, w: d, h: d, isTextBox: true, margin: 0, align: "center", valign: "middle",
    fontFace: TIT, fontSize: 18, bold: true, color: COR.branco,
  });
}

/** Número grande com rótulo embaixo. */
function destaque(s, { x, y, w, valor, rotulo, cor = COR.floresta, tamanho = 40 }) {
  s.addText(valor, {
    x, y, w, h: 0.72, isTextBox: true, margin: 0, align: "center",
    fontFace: TIT, fontSize: tamanho, bold: true, color: cor,
  });
  s.addText(rotulo, {
    x, y: y + 0.74, w, h: 0.62, isTextBox: true, margin: 0, align: "center",
    fontFace: CORPO, fontSize: 12, color: COR.suave,
  });
}

function itens(s, lista, opcoes) {
  s.addText(lista.map((t, i) => ({
    text: t, options: { bullet: true, breakLine: i < lista.length - 1 },
  })), {
    isTextBox: true, fontFace: CORPO, fontSize: 15, color: COR.texto,
    paraSpaceAfter: 9, ...opcoes,
  });
}

// ======================================================================================
// Fase Intermediária I — Qualificação: capítulo 1 e os itens de filtragem dos caps. 2 e 3
// ======================================================================================

function deckQualificacao() {
semRodape = false;

// --------------------------------------------------------------------------------------
// 1 — Capa
// --------------------------------------------------------------------------------------

{
  const s = pres.addSlide();
  s.background = { color: COR.escuro };
  imagem(s, join(FIG, "efeito-dos-filtros.png"), { x: 7.9, y: 1.55, w: 5.0, h: 4.4 });
  s.addText("APS · Processamento de Imagens e Visão Computacional · 2026/2", {
    x: MARGEM, y: 0.72, w: 6.9, h: 0.3, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 12.5, color: COR.musgo, charSpacing: 1.2,
  });
  s.addText("Detecção de desmatamento em imagens de satélite", {
    x: MARGEM, y: 1.3, w: 6.9, h: 1.9, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 38, bold: true, color: COR.branco, lineSpacingMultiple: 1.06,
  });
  s.addText("Fase Intermediária I — Qualificação do Projeto", {
    x: MARGEM, y: 3.35, w: 6.9, h: 0.5, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 19, bold: true, italic: true, color: COR.musgo,
  });

  [["André Massarente", "G280BI1"], ["Enzo Consani", "R154149"],
   ["Isabel Da Silva", "F35FDJ4"], ["Jonathan Aparecido X Martins", "F35HCB4"]
  ].forEach(([nome, ra], i) => {
    const x = MARGEM + (i % 2) * 3.55;
    const y = 4.45 + Math.floor(i / 2) * 0.72;
    s.addText(nome, { x, y, w: 3.4, h: 0.3, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 13, bold: true, color: COR.branco });
    s.addText(`RA ${ra}`, { x, y: y + 0.28, w: 3.4, h: 0.28, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 11.5, color: COR.musgo });
  });
  s.addText("Universidade Paulista — UNIP  ·  Ciência da Computação  ·  São Paulo, 2026", {
    x: MARGEM, y: 6.42, w: 6.9, h: 0.3, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 11.5, color: COR.suave,
  });

  s.addNotes([
    "ANDRÉ — 30 s",
    "",
    "\"Boa noite. Nosso tema é detecção de desmatamento em imagens de satélite.\"",
    "",
    "\"Eu sou o André, e comigo estão o Enzo, a Isabel e o Jonathan.\"",
    "",
    "\"Hoje é a qualificação do projeto. Então a gente apresenta o capítulo 1 — qual é o",
    "problema e o que queremos fazer — e a parte de filtragem dos capítulos 2 e 3.\"",
    "",
    "\"A demonstração do programa e os resultados ficam para a próxima entrega.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 2 — Capítulo 1.a: o problema
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "O problema: comparar duas datas",
    quem: "André Massarente  ·  capítulo 1" });

  imagem(s, join(FIG, "comparativo-real.png"), { x: MARGEM, y: 1.5, w: 4.75, h: 5.15 });

  cartao(s, { x: 5.65, y: 1.55, w: 7.06, h: 1.5, escuro: true });
  s.addText("Dadas duas imagens de satélite da mesma área, em datas diferentes: encontrar as regiões que perderam vegetação e medir quanto isso dá em área.", {
    x: 5.95, y: 1.72, w: 6.46, h: 1.2, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 17, italic: true, color: COR.branco, lineSpacingMultiple: 1.15 });

  s.addText("Por que duas datas, e não uma", {
    x: 5.65, y: 3.28, w: 7.06, h: 0.4, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 20, bold: true, color: COR.floresta });
  s.addText("Uma imagem mostra o que existe hoje. Ela não diz o que foi perdido: um pasto de trinta anos e uma área cortada mês passado são iguais na foto. O que revela desmatamento é a diferença entre duas datas.", {
    x: 5.65, y: 3.74, w: 7.06, h: 1.25, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 16, color: COR.texto, lineSpacingMultiple: 1.18 });

  s.addText("E por que satélite", {
    x: 5.65, y: 5.1, w: 7.06, h: 0.4, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 20, bold: true, color: COR.floresta });
  s.addText("A área é grande demais e de difícil acesso para vistoria em campo. Satélite é o único jeito de acompanhar isso de forma regular.", {
    x: 5.65, y: 5.56, w: 7.06, h: 1.0, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 16, color: COR.texto, lineSpacingMultiple: 1.18 });

  s.addNotes([
    "ANDRÉ — 1 min 30 s",
    "",
    "\"Essa é a mesma região da Amazônia em duas datas. Em cima, 2002 e 2024 na cor normal.",
    "Embaixo, as mesmas imagens com cores realçadas: verde escuro é mata fechada, amarelo é",
    "terra exposta.\"",
    "",
    "\"O ponto principal do nosso trabalho é esse: se eu olhar só a imagem de 2024, eu não",
    "consigo dizer o que é pasto antigo e o que é corte recente. Os dois aparecem claros. O",
    "que mostra desmatamento é a DIFERENÇA entre as duas datas.\"",
    "",
    "\"Por isso o problema que a gente resolve é esse da caixa: duas imagens da mesma área em",
    "datas diferentes, achar o que perdeu vegetação e medir quanto isso dá.\"",
    "",
    "\"E por que satélite: a região é enorme e de difícil acesso. Não dá para mandar gente",
    "olhar tudo.\"",
    "",
    "\"As imagens são reais, do satélite Terra da NASA. São públicas e a gente registrou a",
    "origem de cada uma no trabalho: data, coordenada, licença e endereço.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 3 — Capítulo 1.b: por que importa
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Por que isso importa",
    quem: "Enzo Consani  ·  capítulo 1" });

  const blocos = [
    ["O que se perde quando a floresta cai", [
      "Carbono: a mata guarda carbono, e derrubar joga ele no ar",
      "Bichos: espécies que dependem da mata fechada perdem o lugar",
      "Água: a floresta ajuda a mover umidade pelo continente",
      "Solo: exposto, ele erode e perde fertilidade",
    ]],
    ["Por que precisa ser automático", [
      "Ninguém tem gente para percorrer a floresta inteira",
      "O que a fiscalização precisa é saber ONDE olhar primeiro",
      "Embargos e acordos ambientais só valem se der para conferir — e conferir é comparar duas datas",
    ]],
    ["Por que errar é caro dos dois lados", [
      "Apontar desmatamento onde não houve pune um produtor inocente",
      "Deixar passar um corte real significa que a floresta não volta",
      "Por isso o sistema precisa saber dizer “não tenho certeza”",
    ]],
  ];
  const w = (LARGURA - 2 * 0.24) / 3;
  blocos.forEach(([titulo, lista], i) => {
    const x = MARGEM + i * (w + 0.24);
    cartao(s, { x, y: 1.55, w, h: 3.5 });
    s.addText(titulo, { x: x + 0.3, y: 1.72, w: w - 0.6, h: 0.72, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 17, bold: true, color: COR.floresta });
    itens(s, lista, { x: x + 0.3, y: 2.52, w: w - 0.6, h: 2.4, fontSize: 13.5 });
  });

  destaque(s, { x: MARGEM, y: 5.3, w: 3.1, valor: "5.731 km²", rotulo: "de floresta derrubada na\nAmazônia Legal em 2025 (INPE)", tamanho: 30 });
  destaque(s, { x: MARGEM + 3.3, y: 5.3, w: 3.1, valor: "42%", rotulo: "das emissões do Brasil em 2024\nvieram do uso da terra (SEEG)", tamanho: 30 });

  cartao(s, { x: 7.3, y: 5.22, w: 5.42, h: 1.52, escuro: true });
  s.addText("O formato do corte também importa", { x: 7.55, y: 5.34, w: 4.92, h: 0.34,
    isTextBox: true, margin: 0, fontFace: TIT, fontSize: 16, bold: true, color: COR.musgo });
  s.addText("Um corte comprido junto de uma estrada faz muito mais estrago que um corte quadrado do mesmo tamanho. Por isso o sistema precisa mostrar cada área separada, e não só somar tudo.", {
    x: 7.55, y: 5.7, w: 4.92, h: 0.96, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 13, color: COR.branco, lineSpacingMultiple: 1.12 });

  s.addNotes([
    "ENZO — 1 min 15 s",
    "",
    "\"Três motivos para resolver isso.\"",
    "",
    "\"O primeiro é o que se perde. A mata guarda carbono, e derrubar joga esse carbono no",
    "ar. Os bichos que dependem de mata fechada perdem o lugar. A floresta ajuda a mover",
    "umidade pelo continente. E o solo, exposto, erode.\"",
    "",
    "\"E a escala é grande: o INPE mediu 5.731 quilômetros quadrados derrubados na Amazônia",
    "no último ano. O uso da terra sozinho responde por 42% das emissões do Brasil.\"",
    "",
    "\"O segundo motivo é por que precisa ser automático: ninguém tem gente para percorrer a",
    "floresta inteira. A fiscalização precisa saber onde olhar PRIMEIRO. E embargo, acordo",
    "ambiental, essas coisas só valem se der para conferir depois — e conferir é comparar",
    "duas datas.\"",
    "",
    "\"O terceiro é que errar custa caro dos dois lados. Se o sistema aponta desmatamento",
    "onde não houve, alguém é punido injustamente. Se deixa passar, a floresta não volta.",
    "Por isso a gente acha que o sistema precisa conseguir dizer 'não tenho certeza'.\"",
    "",
    "\"E o quadro da direita mudou o nosso projeto: um corte comprido do lado de uma estrada",
    "faz muito mais estrago que um corte quadrado do mesmo tamanho, porque tem muito mais",
    "borda. Então não basta dar um número total — o sistema tem que mostrar cada área",
    "separada.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 4 — O que o programa faz
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "O que o programa faz",
    sub: "Entram duas imagens da mesma área; saem as áreas que perderam vegetação, medidas e prontas para o modelo",
    quem: "Enzo Consani  ·  capítulo 1" });

  imagem(s, join(FIG, "telas/tela-parametros.png"), { x: MARGEM, y: 1.86, w: 2.5, h: 4.5 });
  s.addText("Quem usa escolhe o índice, o tamanho da suavização e a área mínima — nada fica escondido", {
    x: MARGEM, y: 6.02, w: 2.5, h: 0.8, isTextBox: true, margin: 0, align: "center",
    fontFace: CORPO, fontSize: 11, italic: true, color: COR.suave, lineSpacingMultiple: 1.1 });

  const passos = [
    ["Recebe duas datas", "Duas imagens da mesma área, tiradas com anos de diferença.", true],
    ["Calcula o índice", "Junta as bandas do satélite num valor só, em que mata e terra exposta ficam em extremos opostos.", true],
    ["Filtra", "Tira o ruído do sensor e realça o contorno, sem apagar a borda entre mata e corte.", true],
    ["Separa e mede", "Marca o que perdeu vegetação, identifica cada área isolada e converte pixels em hectares.", false],
    ["Prepara os dados", "Recorta pedaços da imagem já rotulados, no formato que um modelo de visão computacional consome.", false],
  ];
  passos.forEach(([titulo, texto, hoje], i) => {
    const y = 1.86 + i * 0.92;
    cartao(s, { x: 3.35, y, w: 9.37, h: 0.84, escuro: hoje });
    numero(s, i + 1, { x: 3.58, y: y + 0.19, d: 0.5, cor: hoje ? COR.musgo : COR.floresta });
    s.addText(titulo, { x: 4.22, y: y + 0.17, w: 2.2, h: 0.54, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 17, bold: true, valign: "middle",
      color: hoje ? COR.branco : COR.floresta });
    s.addText(texto, { x: 6.5, y: y + 0.14, w: 6.0, h: 0.6, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 13.5, valign: "middle",
      color: hoje ? COR.musgo : COR.texto, lineSpacingMultiple: 1.1 });
  });

  s.addText("Os três primeiros passos, em verde escuro, são o conteúdo de hoje. Os dois últimos ficam para a próxima entrega.", {
    x: 3.35, y: 6.5, w: 9.37, h: 0.32, isTextBox: true, margin: 0, align: "center",
    fontFace: CORPO, fontSize: 12.5, italic: true, color: COR.suave });

  s.addNotes([
    "ENZO — 1 min 15 s",
    "",
    "\"Antes de entrar na parte técnica, o que o programa faz, em cinco passos.\"",
    "",
    "\"Um: ele recebe duas imagens da mesma área, tiradas com anos de diferença.\"",
    "",
    "\"Dois: calcula o índice de vegetação. Isso junta as várias bandas do satélite num",
    "valor só, escolhido de um jeito que mata e terra exposta ficam bem separadas.\"",
    "",
    "\"Três: filtra. Tira o ruído do sensor e realça o contorno — sem apagar a borda entre a",
    "mata e o corte, que é justamente o que a gente quer achar.\"",
    "",
    "\"Quatro: separa e mede. Marca o que perdeu vegetação, identifica cada área isolada e",
    "converte de pixel para hectare.\"",
    "",
    "\"Cinco: prepara os dados. Recorta pedaços da imagem já marcados como desmatado ou",
    "intacto, no formato que um modelo de visão computacional consegue usar para aprender.\"",
    "",
    "\"E é por isso que o enunciado fala em PREPARAÇÃO DE DADOS: o processamento de imagens",
    "não é o produto final aqui. Ele é a fábrica dos exemplos que treinam o modelo.\"",
    "",
    "\"Os três primeiros passos, em verde escuro, são o que a gente detalha hoje. Os dois",
    "últimos são o conteúdo da próxima entrega.\"",
    "",
    "\"À esquerda é a tela do programa: quem usa escolhe o índice, o tamanho da suavização e",
    "a área mínima de uma região. A gente deixou tudo à mostra de propósito.\"",
    "",
    "PASSA PARA A ISABEL.",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 5 — Capítulo 2: o que é filtragem
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "O que é filtrar uma imagem",
    quem: "Isabel Da Silva  ·  capítulo 2" });

  cartao(s, { x: MARGEM, y: 1.5, w: LARGURA, h: 1.32, escuro: true });
  s.addText("Uma imagem é uma tabela de números. Filtrar é trocar cada número por uma conta feita com ele e os vizinhos. Muda a conta, muda o filtro.", {
    x: MARGEM + 0.45, y: 1.68, w: LARGURA - 0.9, h: 1.0, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 20, italic: true, color: COR.branco, lineSpacingMultiple: 1.15 });

  s.addText("A conta se chama convolução", { x: MARGEM, y: 3.0, w: 6.2, h: 0.4,
    isTextBox: true, margin: 0, fontFace: TIT, fontSize: 20, bold: true, color: COR.floresta });
  s.addText("(I * K)(x, y) = Σ Σ  K(i, j) · I(x − i, y − j)", {
    x: MARGEM, y: 3.5, w: 6.2, h: 0.4, isTextBox: true, margin: 0,
    fontFace: "Courier New", fontSize: 14, color: COR.texto });
  itens(s, [
    "K é uma matriz pequena de pesos, geralmente 3×3 ou 5×5. É ela que define o filtro.",
    "Todos os filtros deste trabalho são a mesma conta com pesos diferentes.",
    "A correlação é a mesma soma sem inverter os índices: dá igual para pesos simétricos e troca o sinal no detector de borda.",
  ], { x: MARGEM, y: 4.0, w: 6.2, h: 2.4, fontSize: 14 });

  s.addText("E o que acontece na beirada da imagem", { x: 7.2, y: 3.0, w: 5.52, h: 0.4,
    isTextBox: true, margin: 0, fontFace: TIT, fontSize: 20, bold: true, color: COR.floresta });
  s.addText("No pixel da margem, metade dos vizinhos que a conta pede não existe. A nossa solução é espelhar a imagem para fora da borda.", {
    x: 7.2, y: 3.5, w: 5.52, h: 0.85, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 15, color: COR.texto, lineSpacingMultiple: 1.15 });

  cartao(s, { x: 7.2, y: 4.5, w: 5.52, h: 1.9 });
  s.addText("Por que isso não é detalhe", { x: 7.45, y: 4.64, w: 5.02, h: 0.34,
    isTextBox: true, margin: 0, fontFace: TIT, fontSize: 16, bold: true, color: COR.alerta });
  s.addText("Se a gente preenchesse a margem com preto, criaria uma faixa escura em volta da imagem. O programa leria essa faixa como terra exposta — e marcaria desmatamento na borda de toda cena.", {
    x: 7.45, y: 5.04, w: 5.02, h: 1.2, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 14, color: COR.texto, lineSpacingMultiple: 1.15 });

  s.addNotes([
    "ISABEL — 1 min 15 s",
    "",
    "\"Agora a parte de filtragem, que é o conteúdo da nossa disciplina.\"",
    "",
    "\"Começando pelo básico: uma imagem, para o computador, é uma tabela de números. Cada",
    "pixel é um número. Filtrar é trocar cada número por uma conta feita com ele e com os",
    "vizinhos em volta.\"",
    "",
    "\"E o que muda de um filtro para outro é só a conta. A conta se chama convolução, e é",
    "essa fórmula. Parece complicada, mas o que ela diz é simples: pega uma matriz pequena de",
    "pesos, o K, encosta ela em cima do pixel, multiplica cada vizinho pelo peso",
    "correspondente e soma tudo.\"",
    "",
    "\"Trocar o K é trocar o filtro. Todos os filtros que eu vou mostrar agora são a MESMA",
    "conta, só com pesos diferentes. Por isso a gente escreveu essa conta uma vez só.\"",
    "",
    "SE PERGUNTAREM a diferença entre convolução e correlação: é o sinal dos índices. Dá o",
    "mesmo resultado quando os pesos são simétricos; muda o sinal no detector de borda, onde",
    "os pesos são invertidos de um lado para o outro. As duas estão implementadas.",
    "",
    "\"Do lado direito tem um detalhe que parece bobo e não é: o pixel da beirada. Nele,",
    "metade dos vizinhos que a conta pede não existe. A gente resolve espelhando a imagem",
    "para fora.\"",
    "",
    "\"Se em vez disso a gente preenchesse com preto, ia criar uma moldura escura na imagem.",
    "E o programa leria essa moldura como terra exposta — ou seja, ia marcar desmatamento na",
    "borda de toda cena.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 6 — Capítulo 2: suavização
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Filtros que tiram o ruído",
    sub: "Sem isso, o passo seguinte do programa não funciona",
    quem: "Isabel Da Silva  ·  capítulo 2" });

  const filtros = [
    ["Média", "Todos os vizinhos com o mesmo peso.", "Tira ruído, mas borra a borda com a mesma força. Simples demais."],
    ["Gaussiano", "Vizinho perto pesa mais que vizinho longe.", "É o que a gente usa. Tira o ruído e preserva melhor a borda."],
    ["Mediana", "Troca o pixel pelo valor do meio da vizinhança.", "Ótimo contra pixel isolado esquisito, e não borra a borda. Só é mais lento."],
  ];
  const w = (LARGURA - 2 * 0.24) / 3;
  filtros.forEach(([titulo, como, quando], i) => {
    const x = MARGEM + i * (w + 0.24);
    cartao(s, { x, y: 1.9, w, h: 2.25 });
    s.addText(titulo, { x: x + 0.28, y: 2.04, w: w - 0.56, h: 0.4, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 19, bold: true, color: COR.floresta });
    s.addText(como, { x: x + 0.28, y: 2.48, w: w - 0.56, h: 0.6, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 13.5, bold: true, color: COR.texto, lineSpacingMultiple: 1.1 });
    s.addText(quando, { x: x + 0.28, y: 3.1, w: w - 0.56, h: 0.95, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 13, color: COR.suave, lineSpacingMultiple: 1.12 });
  });

  cartao(s, { x: MARGEM, y: 4.32, w: 6.2, h: 2.34, escuro: true });
  s.addText("Por que tirar o ruído é obrigatório", { x: MARGEM + 0.3, y: 4.48, w: 5.6, h: 0.4,
    isTextBox: true, margin: 0, fontFace: TIT, fontSize: 18, bold: true, color: COR.branco });
  s.addText("Depois da filtragem o programa corta a imagem em duas classes: com mata e sem mata. Se o ruído ficar, pixels soltos passam para o lado errado e o resultado sai furado como uma peneira. Aí o programa conta centenas de áreas minúsculas onde existe uma só — e a gente acabou de dizer que precisa mostrar cada área separada.", {
    x: MARGEM + 0.3, y: 4.94, w: 5.6, h: 1.6, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 14, color: COR.musgo, lineSpacingMultiple: 1.18 });

  s.addChart(pres.ChartType.bar, [{
    name: "Ganho",
    labels: ["3 × 3", "5 × 5", "9 × 9", "15 × 15", "21 × 21"],
    values: [1.4, 2.2, 3.9, 5.2, 9.4],
  }], {
    x: 7.1, y: 4.32, w: 5.62, h: 2.34,
    barDir: "col", chartColors: [COR.floresta],
    showTitle: true, title: "Quantas vezes o gaussiano ficou mais rápido",
    titleFontFace: TIT, titleFontSize: 13, titleColor: COR.floresta,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '0.0"×"',
    dataLabelFontFace: CORPO, dataLabelFontSize: 10, dataLabelColor: COR.texto,
    catAxisLabelColor: COR.suave, catAxisLabelFontFace: CORPO, catAxisLabelFontSize: 10,
    valAxisHidden: true, valAxisMaxVal: 11,
    valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false,
  });

  s.addNotes([
    "ISABEL — 1 min 15 s",
    "",
    "\"Três filtros que tiram ruído, e eles não são iguais.\"",
    "",
    "\"A MÉDIA é a mais simples: soma os vizinhos e divide. Só que ela trata todo mundo",
    "igual, então borra a borda com a mesma força com que tira o ruído.\"",
    "",
    "\"O GAUSSIANO resolve isso: vizinho perto pesa mais que vizinho longe. É esse que a",
    "gente usa.\"",
    "",
    "\"A MEDIANA é diferente: em vez de somar, ela pega o valor do meio da vizinhança. Um",
    "pixel isolado com valor absurdo não muda o valor do meio, então ela limpa esse tipo de",
    "ruído sem borrar nada. O preço é ser mais lenta.\"",
    "",
    "\"Por que isso é obrigatório: depois da filtragem o programa corta a imagem em duas —",
    "com mata e sem mata. Se o ruído ficar, pixel solto passa para o lado errado e o",
    "resultado sai furado como peneira. Aí o programa conta centenas de áreas minúsculas onde",
    "existe uma só. E a gente acabou de dizer que precisa mostrar cada área separada.\"",
    "",
    "\"O gráfico é uma otimização nossa. O gaussiano dá para fazer em duas passadas simples",
    "em vez de uma passada pesada — e o resultado é exatamente o mesmo. Numa janela grande",
    "ficou 9 vezes mais rápido.\"",
    "",
    "SE PERGUNTAREM por que dá o mesmo resultado: porque o peso do gaussiano em duas dimensões",
    "é o produto do peso em x pelo peso em y. É identidade matemática, não aproximação. A",
    "diferença medida entre os dois caminhos foi da ordem de 0,000001.",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 7 — Capítulo 2: bordas e textura
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Filtros que acham a borda",
    sub: "Onde a mata acaba e o corte começa, a imagem muda de valor de repente",
    quem: "Isabel Da Silva  ·  capítulo 2" });

  cartao(s, { x: MARGEM, y: 1.9, w: 6.2, h: 2.75 });
  s.addText("Sobel — acha a fronteira", { x: MARGEM + 0.3, y: 2.04, w: 5.6, h: 0.4,
    isTextBox: true, margin: 0, fontFace: TIT, fontSize: 19, bold: true, color: COR.floresta });
  s.addText("     ⎡ −1  0  +1 ⎤          ⎡ −1  −2  −1 ⎤\nKx = ⎢ −2  0  +2 ⎥    Ky = ⎢  0   0   0 ⎥\n     ⎣ −1  0  +1 ⎦          ⎣ +1  +2  +1 ⎦", {
    x: MARGEM + 0.3, y: 2.5, w: 5.6, h: 0.95, isTextBox: true, margin: 0,
    fontFace: "Courier New", fontSize: 11.5, color: COR.texto, lineSpacingMultiple: 1.15 });
  s.addText("Um K procura mudança na horizontal, o outro na vertical. Juntando os dois, o filtro acende onde o valor muda de repente — que é exatamente o contorno da área cortada, em qualquer direção.", {
    x: MARGEM + 0.3, y: 3.52, w: 5.6, h: 1.0, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 14, color: COR.texto, lineSpacingMultiple: 1.15 });

  cartao(s, { x: 7.2, y: 1.9, w: 5.52, h: 2.75 });
  s.addText("Textura — mede o quanto varia", { x: 7.45, y: 2.04, w: 5.02, h: 0.4,
    isTextBox: true, margin: 0, fontFace: TIT, fontSize: 19, bold: true, color: COR.floresta });
  s.addText("Em vez de olhar a borda, este mede o quanto os valores oscilam dentro de um quadradinho.", {
    x: 7.45, y: 2.5, w: 5.02, h: 0.62, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 14, color: COR.texto, lineSpacingMultiple: 1.15 });
  s.addText("A ideia é que mata fechada é cheia de sombra e copa irregular, então varia muito; pasto é liso e varia pouco.", {
    x: 7.45, y: 3.18, w: 5.02, h: 0.7, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 14, color: COR.texto, lineSpacingMultiple: 1.15 });
  s.addText("Isso é hipótese da literatura — nós ainda não confirmamos.", {
    x: 7.45, y: 3.94, w: 5.02, h: 0.56, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 13.5, bold: true, italic: true, color: COR.alerta,
    lineSpacingMultiple: 1.1 });

  cartao(s, { x: MARGEM, y: 4.85, w: LARGURA, h: 1.55, escuro: true });
  s.addText("Laplaciano — o irmão mais sensível do Sobel", { x: MARGEM + 0.4, y: 4.98,
    w: LARGURA - 0.8, h: 0.38, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 17, bold: true, color: COR.branco });
  s.addText("Enquanto o Sobel responde à mudança, o laplaciano responde à mudança da mudança. Isso o torna ótimo para realçar detalhe fino — e também muito sensível a ruído. Ele tem uma propriedade útil: numa área de valor constante, ou numa rampa suave, o resultado dá zero. A gente usa exatamente isso para testar se a nossa implementação está certa.", {
    x: MARGEM + 0.4, y: 5.4, w: LARGURA - 0.8, h: 0.9, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 14, color: COR.musgo, lineSpacingMultiple: 1.18 });

  s.addNotes([
    "ISABEL — 1 min",
    "",
    "\"Agora os filtros que acham a borda. A ideia: onde a mata acaba e o corte começa, o",
    "valor da imagem muda de repente. Achar borda é achar essa mudança brusca.\"",
    "",
    "\"O SOBEL faz isso com dois conjuntos de pesos: um procura mudança na horizontal, o",
    "outro na vertical. Juntando os dois, o filtro acende no contorno da área cortada — e",
    "funciona em qualquer direção, o corte pode estar torto que tanto faz.\"",
    "",
    "\"A TEXTURA é outra ideia. Em vez de olhar a borda, ela mede o quanto os valores oscilam",
    "dentro de um quadradinho. Mata fechada é cheia de sombra e copa irregular, então varia",
    "muito. Pasto é liso, varia pouco.\"",
    "",
    "\"E eu preciso ser honesta: isso é uma hipótese que a gente leu na literatura. Nós ainda",
    "NÃO confirmamos que funciona no nosso caso. Está escrito assim no trabalho.\"",
    "",
    "\"Por último o LAPLACIANO. O Sobel responde à mudança; o laplaciano responde à mudança",
    "da mudança. Isso deixa ele ótimo para detalhe fino e muito sensível a ruído.\"",
    "",
    "\"Ele tem uma propriedade que a gente aproveitou: numa área lisa, ou numa rampa suave, o",
    "resultado tem que dar zero. Então a gente escreveu um teste que passa uma rampa e",
    "confere se dá zero. É assim que a gente sabe que a nossa implementação está certa — sem",
    "comparar com biblioteca nenhuma.\"",
    "",
    "PASSA PARA O JONATHAN.",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 8 — Capítulo 3.a: os filtros escolhidos
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Os filtros que escolhemos, e para quê",
    sub: "Cada um está na cadeia porque resolve um problema — e a ordem faz parte da escolha",
    quem: "Jonathan Aparecido X Martins  ·  capítulo 3" });

  const escolhidos = [
    ["1", "Índice de vegetação", "Junta as cores num valor só, onde mata e terra exposta ficam bem separadas"],
    ["2", "Gaussiano 5 × 5", "Tira o ruído antes de o programa cortar a imagem em duas classes"],
    ["3", "Limiar de Otsu", "Decide sozinho o valor de corte entre mata e não-mata, igual para as duas datas"],
    ["4", "Abertura e fechamento", "Limpa respingos soltos e tapa buracos dentro das áreas"],
    ["5", "Sobel", "Realça o contorno da área cortada"],
    ["6", "Variação local 5 × 5", "Mede textura, para alimentar o modelo depois"],
  ];
  const alturaLinha = 0.68;
  escolhidos.forEach(([n, filtro, porque], i) => {
    const y = 2.1 + i * alturaLinha;
    if (i % 2 === 0) cartao(s, { x: MARGEM, y, w: LARGURA, h: alturaLinha - 0.06 });
    numero(s, n, { x: MARGEM + 0.22, y: y + 0.12, d: 0.42, cor: COR.musgo });
    s.addText(filtro, { x: MARGEM + 0.86, y: y + 0.08, w: 3.3, h: 0.5, isTextBox: true,
      margin: 0, fontFace: TIT, fontSize: 16, bold: true, color: COR.floresta, valign: "middle" });
    s.addText(porque, { x: MARGEM + 4.3, y: y + 0.08, w: 7.6, h: 0.5, isTextBox: true,
      margin: 0, fontFace: CORPO, fontSize: 14, color: COR.texto, valign: "middle" });
  });

  s.addText("Suavizar tem que vir antes do corte. Depois do corte a imagem já virou preto e branco — o estrago não volta.", {
    x: MARGEM, y: 6.26, w: LARGURA, h: 0.34, isTextBox: true, margin: 0, align: "center",
    fontFace: CORPO, fontSize: 13.5, italic: true, color: COR.alerta });

  s.addNotes([
    "JONATHAN — 1 min 15 s",
    "",
    "\"A Isabel mostrou os filtros que existem. Eu mostro quais a gente escolheu e por quê —",
    "porque a escolha não foi por catálogo, cada um resolve um problema.\"",
    "",
    "\"Primeiro o ÍNDICE DE VEGETAÇÃO. Ele junta as cores da imagem num valor só, escolhido",
    "de um jeito que mata e terra exposta ficam em extremos opostos. É o que deixa o resto",
    "do trabalho possível.\"",
    "",
    "\"Segundo o GAUSSIANO, pelo motivo que a Isabel explicou: tirar o ruído antes do corte.\"",
    "",
    "\"Terceiro o LIMIAR DE OTSU. Ele olha a imagem e decide sozinho qual valor separa mata de",
    "não-mata. E a gente usa o MESMO valor de corte nas duas datas — se usasse um para cada,",
    "a comparação ia medir a diferença entre as regras, não a diferença no terreno.\"",
    "",
    "\"Quarto, abertura e fechamento: limpa respingo solto e tapa buraco dentro das áreas.",
    "Quinto, o Sobel, para realçar o contorno. Sexto, a variação local, que é a textura para",
    "o modelo.\"",
    "",
    "\"E a frase de baixo é a regra de ouro: suavizar tem que vir ANTES do corte. Depois do",
    "corte a imagem já virou preto e branco, e o que se perdeu não volta.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 9 — Capítulo 3.a: o efeito na cena real
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Os filtros rodando na imagem real",
    quem: "Jonathan Aparecido X Martins  ·  capítulo 3" });

  imagem(s, join(FIG, "efeito-dos-filtros.png"), { x: MARGEM, y: 1.6, w: 8.7, h: 5.15 });

  const notas = [
    ["O que entra", "A imagem do satélite e o índice de vegetação. O amarelo é terra exposta, o verde é mata."],
    ["O que o gaussiano faz", "Compare o segundo painel com o terceiro: o granulado sumiu e o desenho do terreno continuou."],
    ["O que o Sobel acha", "Nos dois painéis de baixo à direita, o contorno do corte e o rio acendem sozinhos."],
  ];
  notas.forEach(([titulo, texto], i) => {
    const y = 1.72 + i * 1.5;
    s.addText(titulo, { x: 9.55, y, w: 3.17, h: 0.36, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 16, bold: true, color: COR.floresta });
    s.addText(texto, { x: 9.55, y: y + 0.4, w: 3.17, h: 1.02, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 13, color: COR.texto, lineSpacingMultiple: 1.14 });
  });

  cartao(s, { x: 9.55, y: 6.06, w: 3.17, h: 0.72 });
  s.addText("São Félix do Xingu (PA), 2024 · imagem da NASA, de domínio público", {
    x: 9.72, y: 6.16, w: 2.83, h: 0.56, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 11, italic: true, color: COR.suave, lineSpacingMultiple: 1.1 });

  s.addNotes([
    "JONATHAN — 1 min",
    "",
    "\"E aqui estão esses filtros rodando de verdade, num pedaço da imagem de 2024. Isso não",
    "é figura de livro: é a saída do nosso programa.\"",
    "",
    "\"O primeiro painel é a imagem como ela é. O segundo já é o índice de vegetação: o",
    "amarelo é terra exposta, o verde é mata. Só que olhem o granulado — aquilo é ruído.\"",
    "",
    "\"O terceiro painel é o mesmo depois do gaussiano. Comparem os dois: o granulado sumiu e",
    "o desenho do terreno continuou lá. É exatamente isso que a gente precisava.\"",
    "",
    "\"Embaixo, à esquerda, a mediana fazendo um trabalho parecido. E os dois últimos são o",
    "Sobel e a textura: repara que o contorno do corte e o rio acendem sozinhos.\"",
    "",
    "\"O enunciado pede que o resultado dos filtros seja mostrado E analisado. É isso que este",
    "slide faz: cada painel tem um motivo de estar ali, e dá para ver o efeito.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 10 — O programa aplicando os filtros
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "O programa aplicando os filtros",
    sub: "A mesma sequência dos slides anteriores, rodando sobre as duas datas",
    quem: "Isabel Da Silva  ·  encerramento" });

  imagem(s, join(FIG, "telas/tela-aquisicao.png"), { x: MARGEM, y: 1.85, w: 4.25, h: 4.5 });
  s.addText("Passos 1 e 2: as duas datas e o índice de vegetação", {
    x: MARGEM, y: 6.42, w: 4.25, h: 0.34, isTextBox: true, margin: 0, align: "center",
    fontFace: CORPO, fontSize: 11.5, italic: true, color: COR.suave });

  imagem(s, join(FIG, "telas/tela-filtragem.png"), { x: 5.1, y: 1.85, w: 7.62, h: 3.62 });

  cartao(s, { x: 5.1, y: 5.62, w: 7.62, h: 1.18, escuro: true });
  s.addText("Os filtros são nossos", { x: 5.35, y: 5.74, w: 4.7, h: 0.34, isTextBox: true,
    margin: 0, fontFace: TIT, fontSize: 17, bold: true, color: COR.branco });
  s.addText("O enunciado exige que o grupo escreva os filtros. Dentro do núcleo do programa a única biblioteca que entra é a de contas com números.", {
    x: 5.35, y: 6.1, w: 4.7, h: 0.6, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 12.5, color: COR.musgo, lineSpacingMultiple: 1.12 });
  s.addText("Obrigado.\nPerguntas?", { x: 10.2, y: 5.78, w: 2.3, h: 0.9, isTextBox: true,
    margin: 0, align: "right", fontFace: TIT, fontSize: 21, bold: true, color: COR.musgo,
    lineSpacingMultiple: 1.05 });

  s.addNotes([
    "ISABEL — 1 min",
    "",
    "\"Para fechar, o programa fazendo isso tudo.\"",
    "",
    "\"À esquerda, os passos 1 e 2: em cima as duas datas lado a lado, embaixo o índice de",
    "vegetação das duas. O verde é mata e o amarelo é terra exposta — já dá para ver a",
    "diferença entre as datas.\"",
    "",
    "\"À direita, o passo 3, que é o conteúdo de hoje. São os três painéis da filtragem: o",
    "índice sem tratamento, com aquele granulado que é o ruído; o mesmo depois do gaussiano,",
    "com o granulado limpo e o quadrado ainda no lugar; e o Sobel, que acende só no contorno",
    "do quadrado.\"",
    "",
    "\"Repara na legenda que o próprio programa escreve ali: filtros implementados pelo",
    "grupo, com NumPy puro. É exigência do enunciado e a gente cumpriu — dentro do núcleo do",
    "programa não entra OpenCV nem nada pronto.\"",
    "",
    "\"E por que isso foi bom para nós, além da exigência: chamando uma função pronta a gente",
    "não saberia responder o que acontece na borda da imagem, nem por que o resultado é",
    "aquele. Com o código sendo nosso, cada pergunta dessas tem resposta.\"",
    "",
    "\"Obrigado. Qualquer um de nós responde perguntas sobre qualquer parte.\"",
    "",
    "OBS: esta cena é sintética, construída por nós para demonstrar o programa — o próprio",
    "programa avisa isso na tela. As imagens de satélite reais estão no slide 9.",
  ].join("\n"));
}

}

// ======================================================================================
// Fase Intermediária II — Defesa: protótipo e resultados
// ======================================================================================

function deckDefesa() {
semRodape = true;

// --------------------------------------------------------------------------------------
// 1 — Capa
// --------------------------------------------------------------------------------------

{
  const s = pres.addSlide();
  s.background = { color: COR.escuro };
  s.addImage({ path: join(RES, "imagem-real/02-depois.png"), x: 8.15, y: 0, w: 5.183, h: ALT,
    sizing: { type: "cover", w: 5.183, h: ALT } });
  s.addShape(pres.ShapeType.rect, { x: 7.85, y: 0, w: 0.5, h: ALT,
    fill: { color: COR.escuro }, line: { width: 0 } });

  s.addText("APS · Processamento de Imagens e Visão Computacional · 2026/2", {
    x: MARGEM, y: 0.72, w: 6.9, h: 0.3, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 12.5, color: COR.musgo, charSpacing: 1.2,
  });
  s.addText("Detecção e quantificação de desmatamento em imagens de satélite", {
    x: MARGEM, y: 1.25, w: 6.9, h: 2.25, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 38, bold: true, color: COR.branco, lineSpacingMultiple: 1.06,
  });
  s.addText("Processamento digital de imagens para preparar dados de visão computacional", {
    x: MARGEM, y: 3.52, w: 6.9, h: 0.6, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 15, italic: true, color: COR.musgo,
  });

  const integrantes = [
    ["André Massarente", "G280BI1"],
    ["Enzo Consani", "R154149"],
    ["Isabel Da Silva", "F35FDJ4"],
    ["Jonathan Aparecido X Martins", "F35HCB4"],
  ];
  integrantes.forEach(([nome, ra], i) => {
    const x = MARGEM + (i % 2) * 3.55;
    const y = 4.55 + Math.floor(i / 2) * 0.72;
    s.addText(nome, { x, y, w: 3.4, h: 0.3, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 13, bold: true, color: COR.branco });
    s.addText(`RA ${ra}`, { x, y: y + 0.28, w: 3.4, h: 0.28, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 11.5, color: COR.musgo });
  });

  s.addText("Universidade Paulista — UNIP  ·  Ciência da Computação  ·  São Paulo, 2026", {
    x: MARGEM, y: 6.42, w: 6.9, h: 0.3, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 11.5, color: COR.suave,
  });

  s.addNotes([
    "ISABEL — abertura (20 s)",
    "",
    "\"Boa noite. Nós somos o grupo do tema de sustentabilidade ambiental: detecção e",
    "quantificação de desmatamento em imagens de satélite.\"",
    "",
    "\"Eu sou a Isabel, e comigo estão o André, o Enzo e o Jonathan. Cada um de nós",
    "apresenta uma parte, e todos respondem perguntas sobre qualquer parte.\"",
    "",
    "\"São dez minutos: o problema, como o sistema funciona, o programa rodando ao vivo",
    "e os resultados — inclusive um resultado que foi uma recusa, e vamos explicar por quê.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 3 — Recapitulação da Fase I
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Relembrando a Fase I",
    sub: "O que foi apresentado na qualificação, em quatro pontos",
    quem: "Isabel Da Silva  ·  problema e contexto" });
  imagem(s, join(FIG, "comparativo-real.png"), { x: MARGEM, y: 1.95, w: 4.4, h: 4.75 });

  const pontos = [
    ["O problema", "Desmatamento não se vê numa imagem só. Ele aparece na diferença entre duas datas da mesma área."],
    ["O objetivo", "Usar o processamento de imagens para preparar dados que alimentem um modelo de visão computacional (Manual da APS, p. 2)."],
    ["Os filtros", "Escritos pelo grupo, só com NumPy: índice de vegetação, gaussiano, limiar de Otsu, abertura e fechamento, Sobel e variação local."],
    ["O que mudou desde então", "O protótipo roda as cinco etapas, treina o modelo e foi testado em imagem Sentinel-2 de 10 m, comparada ao PRODES."],
  ];
  pontos.forEach(([titulo, texto], i) => {
    const y = 1.95 + i * 1.2;
    s.addText(titulo, { x: 5.45, y, w: 7.25, h: 0.36, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 18, bold: true, color: COR.floresta });
    s.addText(texto, { x: 5.45, y: y + 0.4, w: 7.25, h: 0.72, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 14, color: COR.texto, lineSpacingMultiple: 1.12 });
  });

  s.addNotes([
    "ISABEL — recapitulação da Fase I (1 min)",
    "",
    "\"Antes de mostrar o que é novo, uma revisão rápida do que apresentamos na qualificação.\"",
    "",
    "\"O problema: olhando uma imagem só, não dá para saber o que é pasto antigo e o que é",
    "corte recente. O desmatamento aparece quando comparamos a mesma área em duas datas,",
    "como nestas imagens de 2002 e 2024.\"",
    "",
    "\"O objetivo, pelo enunciado: o processamento de imagens prepara os dados que depois",
    "alimentam um modelo de visão computacional. Ele não é o produto final.\"",
    "",
    "\"Os filtros foram escritos por nós, só com NumPy, como o enunciado exige.\"",
    "",
    "\"E o que mudou desde então: o protótipo ficou pronto, o modelo é treinado, e testamos",
    "o programa numa imagem de satélite de 10 metros, comparando com o mapeamento oficial do",
    "INPE. O Enzo mostra agora como o sistema funciona por dentro.\"",
    "",
    "PASSA PARA O ENZO.",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 5 — As cinco etapas
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "As cinco etapas do programa",
    sub: "A sequência nomeada pelo enunciado (p. 3, item 2.e), e onde cada etapa está no código",
    quem: "Enzo Consani  ·  como o sistema funciona" });

  const etapas = [
    ["Aquisição", "Baixa o par de datas e mede a qualidade da cena.", "dataio/"],
    ["Manipulação", "Converte espaços de cor e calcula os índices NDVI, NBR e ExG.", "pdi/cor.py"],
    ["Filtragem", "Gaussiano, média, mediana, Sobel, laplaciano, desvio-padrão local.", "pdi/filtros.py"],
    ["Segmentação", "Otsu conjunto, morfologia e rotulagem de componentes conexos.", "pdi/limiar.py\npdi/segmentacao.py"],
    ["Modelo", "Recorta, rotula, extrai descritores e treina a floresta aleatória.", "modelo/"],
  ];
  const w = (LARGURA - 4 * 0.2) / 5;
  etapas.forEach(([nome, texto, arquivo], i) => {
    const x = MARGEM + i * (w + 0.2);
    cartao(s, { x, y: 2.1, w, h: 3.85 });
    numero(s, i + 1, { x: x + w / 2 - 0.29, y: 2.32, d: 0.58 });
    s.addText(nome, { x: x + 0.12, y: 3.02, w: w - 0.24, h: 0.4, isTextBox: true, margin: 0,
      align: "center", fontFace: TIT, fontSize: 17, bold: true, color: COR.floresta });
    s.addText(texto, { x: x + 0.16, y: 3.48, w: w - 0.32, h: 1.55, isTextBox: true, margin: 0,
      align: "center", fontFace: CORPO, fontSize: 12.5, color: COR.texto, lineSpacingMultiple: 1.1 });
    s.addText(arquivo, { x: x + 0.12, y: 5.1, w: w - 0.24, h: 0.62, isTextBox: true, margin: 0,
      align: "center", fontFace: "Courier New", fontSize: 10.5, color: COR.suave });
  });

  s.addText("Cada etapa guarda o resultado intermediário, e a interface mostra uma etapa por vez.", {
    x: MARGEM, y: 6.15, w: LARGURA, h: 0.5, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 13.5, italic: true, color: COR.suave, align: "center" });

  s.addNotes([
    "ENZO — arquitetura (40 s)",
    "",
    "\"O programa tem cinco etapas, e elas não são invenção nossa: é a sequência que o",
    "próprio enunciado nomeia. A gente espelhou isso na organização das pastas do código,",
    "então cada etapa tem um lugar e dá para apontar onde ela está.\"",
    "",
    "\"Aquisição baixa o par de datas. Manipulação calcula os índices de vegetação.",
    "Filtragem aplica os filtros espaciais. Segmentação decide o que é perda e o que não é.",
    "E o modelo pega o resultado e treina o classificador.\"",
    "",
    "\"Um detalhe de implementação que importa para a demonstração: o programa guarda TODOS",
    "os resultados intermediários. Não é uma caixa que entra imagem e sai número — a",
    "André vai mostrar etapa por etapa na tela.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 6 — Os filtros são nossos
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Os filtros foram implementados pelo grupo",
    sub: "Filtros escritos com NumPy, aplicados à cena real de 2024",
    quem: "Enzo Consani  ·  como o sistema funciona" });

  imagem(s, join(FIG, "efeito-dos-filtros.png"), { x: MARGEM, y: 1.88, w: 8.6, h: 4.95 });

  const notas = [
    ["Convolução", "Uma função genérica com tratamento de borda; todo filtro linear é um núcleo passado para ela."],
    ["Separabilidade", `O gaussiano roda como dois passes 1D: numa janela 21 × 21 fica ${br(9.4, 1)}× mais rápido, com diferença de 10⁻⁶.`],
    ["Sobel e textura", "Gradiente para realçar a borda do corte; desvio-padrão local para medir textura do dossel."],
  ];
  notas.forEach(([titulo, texto], i) => {
    const y = 1.85 + i * 1.36;
    s.addText(titulo, { x: 9.42, y, w: 3.3, h: 0.34, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 16, bold: true, color: COR.floresta });
    s.addText(texto, { x: 9.42, y: y + 0.38, w: 3.3, h: 0.96, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 12.5, color: COR.texto, lineSpacingMultiple: 1.12 });
  });

  cartao(s, { x: 9.42, y: 5.98, w: 3.3, h: 0.82 });
  s.addText("363 testes automatizados conferem os filtros contra resultados conhecidos.", {
    x: 9.58, y: 6.08, w: 3.0, h: 0.64, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 11.5, color: COR.texto });

  s.addNotes([
    "ENZO — os filtros (50 s)",
    "",
    "\"Aqui estão os filtros rodando sobre a cena real de 2024. Em cima: a cor natural, o",
    "índice NBR bruto e o mesmo índice depois do gaussiano 5 por 5 — repara que o ruído",
    "sumiu e a estrutura ficou. Embaixo: a mediana, o Sobel realçando as bordas, e o",
    "desvio-padrão local, que é a nossa medida de textura.\"",
    "",
    "\"Tudo isso é código nosso. A base é uma função de convolução genérica com tratamento",
    "de borda; todo filtro linear é só um núcleo diferente passado para ela.\"",
    "",
    "\"Uma otimização que vale citar: o gaussiano é separável. Em vez de uma janela 2D, a",
    "gente roda dois passes 1D — porque e elevado a menos x ao quadrado menos y ao quadrado",
    "é igual ao produto dos dois. Numa janela 21 por 21 isso deu 9,4 vezes mais rápido, e a",
    "diferença entre os dois caminhos é da ordem de 10 elevado a menos 6, que é",
    "arredondamento de ponto flutuante.\"",
    "",
    "\"E os testes: 363 no total. Eles não comparam com OpenCV — comparam com casos",
    "analíticos. Convolução com núcleo identidade devolve a imagem original; Sobel numa",
    "rampa linear devolve gradiente constante; Otsu numa imagem bimodal cai entre os dois",
    "modos.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 8 — Decisão 3: recusa
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "O sistema sabe quando não sabe",
    quem: "Enzo Consani  ·  como o sistema funciona" });

  s.addText("O método de Otsu sempre devolve um número — mesmo numa imagem que não tem duas classes. Aplicado a uma cena homogênea, ele corta o ruído do dossel ao meio e produz “desmatamento” onde não houve nenhum.", {
    x: MARGEM, y: 1.5, w: 7.4, h: 1.1, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 15.5, color: COR.texto, lineSpacingMultiple: 1.15 });

  s.addText("Antes de usar o limiar, o programa mede o tamanho de efeito entre as duas classes que ele acabou de separar. Abaixo do critério, ele recusa a quantificação e diz por quê.", {
    x: MARGEM, y: 2.72, w: 7.4, h: 0.95, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 15.5, bold: true, color: COR.floresta, lineSpacingMultiple: 1.15 });

  destaque(s, { x: MARGEM, y: 3.85, w: 2.3, valor: br(2.65, 2), rotulo: "piso: o valor que uma\nimagem sem classes produz", cor: COR.suave, tamanho: 34 });
  destaque(s, { x: MARGEM + 2.55, y: 3.85, w: 2.3, valor: br(4.0, 2), rotulo: "mínimo exigido para\nreportar área", cor: COR.floresta, tamanho: 34 });
  destaque(s, { x: MARGEM + 5.1, y: 3.85, w: 2.3, valor: br(real.distinguibilidade, 2), rotulo: "medido na cena real:\nrecusado", cor: COR.alerta, tamanho: 34 });

  s.addText("Os dois limites foram fixados antes de rodar a cena real — e não foram alterados depois.", {
    x: MARGEM, y: 5.65, w: 7.4, h: 0.4, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 13, italic: true, color: COR.texto });

  imagem(s, join(FIG, "telas/tela-recusa.png"), { x: 8.25, y: 2.55, w: 4.45, h: 1.5 });
  s.addText("A mensagem que o programa mostra na tela", {
    x: 8.25, y: 4.12, w: 4.45, h: 0.3, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 11.5, italic: true, color: COR.suave, align: "center" });

  s.addNotes([
    "ENZO — a recusa (1 min 10 s)",
    "",
    "\"Essa é a decisão da qual a gente mais se orgulha, e é a que mais rende pergunta.\"",
    "",
    "\"O método de Otsu SEMPRE devolve um número. Você pode dar a ele uma foto de uma parede",
    "branca e ele devolve um limiar. Se a cena é homogênea — floresta intacta nas duas datas",
    "— ele vai cortar o ruído do dossel no meio e metade da cena vira 'desmatamento'.\"",
    "",
    "\"Então antes de usar o limiar, o programa mede o tamanho de efeito entre as duas",
    "classes que ele acabou de separar: a distância entre as médias dividida pelo desvio",
    "combinado. É uma medida padrão de separação entre distribuições.\"",
    "",
    "\"Os três números: 2,65 é o piso — é mais ou menos o que uma imagem SEM classes",
    "produz, porque Otsu sempre acha alguma coisa. 4,0 é o mínimo que a gente exige para",
    "reportar área. E 3,51 foi o que a cena real de satélite deu: abaixo do mínimo, então",
    "recusado.\"",
    "",
    "\"O ponto importante: esses dois limites foram fixados ANTES de rodar a imagem real, e",
    "não foram mexidos depois. O Jonathan volta nisso no final.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 10 — Demonstração
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Demonstração da aplicação", escuro: true,
    quem: "André Massarente  ·  demonstração" });

  const passos = [
    ["Envio das imagens", "A imagem de 2018 e a de 2024 da mesma área, enviadas na hora."],
    ["As cinco etapas", "Índice, filtragem e mapa de mudança calculados na hora."],
    ["A recusa", "Na imagem real, as classes não se separam o bastante, e o programa não dá número."],
    ["A conferência", "Na cena sintética, 400 pixels construídos e 400 detectados."],
    ["O passo a passo", "Índice, filtragem e mapa de mudança das duas imagens enviadas."],
  ];
  const w = (LARGURA - 4 * 0.2) / 5;
  passos.forEach(([titulo, texto], i) => {
    const x = MARGEM + i * (w + 0.2);
    cartao(s, { x, y: 2.3, w, h: 3.3, escuro: true });
    numero(s, i + 1, { x: x + w / 2 - 0.27, y: 2.55, d: 0.54, cor: COR.musgo });
    s.addText(titulo, { x: x + 0.1, y: 3.25, w: w - 0.2, h: 0.4, isTextBox: true, margin: 0,
      align: "center", fontFace: TIT, fontSize: 16, bold: true, color: COR.branco });
    s.addText(texto, { x: x + 0.16, y: 3.72, w: w - 0.32, h: 1.6, isTextBox: true, margin: 0,
      align: "center", fontFace: CORPO, fontSize: 12.5, color: COR.musgo, lineSpacingMultiple: 1.12 });
  });


  s.addNotes([
    "ANDRÉ — demonstração ao vivo (3 min)",
    "",
    "[Alt+Tab para o navegador. O app já abre em Enviar imagens]",
    "",
    "[No painel da esquerda: 2018 em Imagem antes, 2024 em Imagem depois]",
    "\"Estas são imagens reais do satélite Sentinel-2, da mesma área do Pará em julho de 2018",
    "e julho de 2024. Cada arquivo traz a cor e o infravermelho, que separa floresta de solo.\"",
    "",
    "[Clicar em Processar imagens. Leva cerca de 15 s]",
    "\"O programa roda agora as cinco etapas sobre 2,25 milhões de pixels.\"",
    "",
    "[Arrastar a linha da comparação de um lado para o outro]",
    "\"Dá para ver a floresta virar pasto. E o programa se recusou a dar um número:",
    "floresta e área aberta não se separam o bastante nesta imagem. O Jonathan explica.\"",
    "",
    "[Etapas do processamento: abas 3 Filtragem e 4 Segmentação]",
    "\"Aqui está cada etapa. Na filtragem, o gaussiano tirando o ruído e o Sobel marcando",
    "a borda. Na segmentação, o mesmo limiar nas duas datas e o mapa de mudança.\"",
    "",
    "[Se sobrar tempo: Cena sintética no painel da esquerda]",
    "\"Para conferir a conta, uma cena em que nós desenhamos o corte: 400 pixels construídos",
    "e 400 detectados.\"",
    "",
    "[Alt+Tab para o PowerPoint e avançar o slide]",
    "PASSA PARA O JONATHAN.",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 14 — Resultado real: a recusa
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Em imagem real, o sistema recusou",
    sub: `São Félix do Xingu (PA) · MODIS/Terra · 2002-07-01 × 2024-07-05 · ≈253 m/pixel`,
    quem: "Jonathan Aparecido X Martins  ·  discussão dos resultados" });

  imagem(s, join(FIG, "histogramas-ndvi-nbr.png"), { x: MARGEM, y: 1.9, w: 8.3, h: 3.6 });

  const pontos = [
    ["A perda é visível", "Na cor natural e no índice, a mudança entre 2002 e 2024 se enxerga a olho nu."],
    ["A mediana caiu", "NDVI de +0,944 para +0,794; NBR de +0,799 para +0,504 — na escala nativa do índice."],
    ["Mas o vale é raso", "Existe vale entre os montes; ele só não é fundo o bastante para nenhum corte atingir o tamanho de efeito exigido."],
  ];
  pontos.forEach(([titulo, texto], i) => {
    const y = 1.95 + i * 1.18;
    s.addText(titulo, { x: 9.12, y, w: 3.6, h: 0.32, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 15, bold: true, color: COR.floresta });
    s.addText(texto, { x: 9.12, y: y + 0.34, w: 3.6, h: 0.8, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 12, color: COR.texto, lineSpacingMultiple: 1.1 });
  });

  cartao(s, { x: 9.12, y: 5.55, w: 3.6, h: 1.25 });
  s.addText("A 253 metros, cada pixel mistura floresta, pasto, regeneração e estrada num valor só.", {
    x: 9.32, y: 5.68, w: 3.2, h: 1.0, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 12.5, italic: true, color: COR.texto, lineSpacingMultiple: 1.12 });

  s.addText("Três hipóteses testadas para explicar a recusa", {
    x: MARGEM, y: 5.6, w: 8.3, h: 0.32, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 15, bold: true, color: COR.floresta });
  const hipoteses = [
    ["Era o índice errado?", `NBR ${br(real.distinguibilidade)} contra NDVI ${br(2.994)} — melhora, e segue abaixo de ${br(4.0)}`],
    ["Era a abordagem errada?", `Limiarizar a imagem de diferença é pior: ${br(2.788)}`],
    ["Era a resolução?", "Hipótese principal aqui, testada a 10 m no próximo slide"],
  ];
  hipoteses.forEach(([pergunta, resposta], i) => {
    const y = 5.98 + i * 0.29;
    s.addText([
      { text: pergunta + "   ", options: { bold: true } },
      { text: resposta, options: { color: i === 2 ? COR.alerta : COR.suave } },
    ], { x: MARGEM, y, w: 8.3, h: 0.28, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 12, color: COR.texto });
  });

  s.addNotes([
    "JONATHAN — o resultado real (1 min 15 s)",
    "",
    "\"Agora o resultado principal, que é o que aconteceu com a imagem de satélite de",
    "verdade: o sistema se recusou a quantificar.\"",
    "",
    "\"Este gráfico é a distribuição do índice nas duas datas. À esquerda o NDVI, à direita",
    "o NBR. Azul é 2002, laranja é 2024, e a linha vertical é o limiar de Otsu.\"",
    "",
    "\"Tem perda de vegetação: a mediana do NDVI caiu de 0,944 para 0,794, e a do NBR de",
    "0,799 para 0,504 — isso na escala nativa do índice, que vai de menos 1 a mais 1.\"",
    "",
    "\"E tem vale entre os montes — no NDVI de 2024 dá para ver dois montes. Só que o vale",
    "é RASO. Nenhum corte ali separa as classes com o tamanho de efeito que a gente exige.\"",
    "",
    "SE PERGUNTAREM 'não tem vale?': a figura mostra que tem. O problema não é ausência de",
    "vale, é profundidade do vale.",
    "",
    "\"Nossa hipótese principal aqui foi a resolução. A 253 metros por pixel, cada pixel",
    "mistura floresta, pasto, regeneração e estrada num valor só.\"",
    "",
    "\"Testamos outras explicações: trocamos NDVI por NBR, que melhorou de 2,99 para 3,51 e",
    "continuou abaixo de 4. Limiarizar a imagem de diferença deu 2,79, ainda pior. Faltava",
    "testar a resolução de verdade, e a gente fez isso: já vou mostrar.\"",
    "",
    "\"E uma decisão: bastava baixar o critério de 4 para 3 e teríamos um número. Não",
    "fizemos isso. Escolher a régua depois de ver a medida não é medir.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 16 — Sentinel-2 contra o PRODES
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "A 10 metros, com o PRODES como referência",
    sub: "Sentinel-2 L2A · 2018-07-03 × 2024-07-16 · recorte de 15 × 15 km · índice NBR",
    quem: "Jonathan Aparecido X Martins  ·  discussão dos resultados" });

  const paineis = [
    ["sentinel-antes.png", "2018"],
    ["sentinel-depois.png", "2024"],
    ["sentinel-mascara.png", "Máscara do programa (diagnóstico)"],
    ["sentinel-prodes.png", "PRODES 2019–2024"],
  ];
  const lado = 2.82;
  const vao = (LARGURA - 4 * lado) / 3;
  paineis.forEach(([arquivo, legenda], i) => {
    const x = MARGEM + i * (lado + vao);
    imagem(s, join(FIG, arquivo), { x, y: 1.85, w: lado, h: lado });
    s.addText(legenda, { x, y: 4.7, w: lado, h: 0.28, isTextBox: true, margin: 0, align: "center",
      fontFace: CORPO, fontSize: 12, bold: true, color: COR.texto });
  });

  const colunas = [
    ["O programa recusou", `Distinguibilidade ${br(sentinel.distinguibilidade)}, abaixo de ${br(sentinel.limite_vigente, 1)}. Nenhuma área foi reportada, e o critério não foi alterado.`],
    ["A máscara exagera", `${br(sentinel.area_mascara_ha, 0)} ha contra ${br(sentinel.area_prodes_ha, 0)} ha do PRODES. Precisão ${br(sentinel.precisao)}, revocação ${br(sentinel.revocacao)}. Pasto e rebrota podem pesar, sem separação medida.`],
    ["A recusa pode melhorar", `Em ${janelasIntactas.length} janelas intactas, o maior valor foi ${br(janelasIntactas.at(-1))}. Em ${janelasComPerda.length} com perda, a mediana foi ${br(mediana(janelasComPerda))}. Amostra pequena: é hipótese.`],
  ];
  const w = (LARGURA - 2 * 0.24) / 3;
  colunas.forEach(([titulo, texto], i) => {
    const x = MARGEM + i * (w + 0.24);
    cartao(s, { x, y: 5.08, w, h: 1.62 });
    s.addText(titulo, { x: x + 0.2, y: 5.16, w: w - 0.4, h: 0.32, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 15, bold: true, color: i === 0 ? COR.alerta : COR.floresta });
    s.addText(texto, { x: x + 0.2, y: 5.5, w: w - 0.4, h: 1.14, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 12.5, color: COR.texto, lineSpacingMultiple: 1.08 });
  });

  s.addNotes([
    "JONATHAN — o teste a 10 metros (1 min)",
    "",
    "\"Baixamos imagem Sentinel-2, de 10 metros por pixel. Agora os talhões aparecem",
    "claramente. Mesmo assim, o sistema recusou: deu 3,97, e o critério é 4,0. E a gente manteve",
    "o critério.\"",
    "",
    "\"Então a resolução explicava só parte do problema. Para medir o resto, usamos o PRODES,",
    "o mapeamento de desmatamento do INPE, como referência independente.\"",
    "",
    "\"Olhando a máscara só como diagnóstico, ela marca cerca de 7.975 hectares, e o PRODES",
    "cerca de 4.125. Ela acerta boa parte do que o PRODES marca, mas marca muito além disso.",
    "Pasto e rebrota podem pesar, mas a gente não mediu quanto.\"",
    "",
    "\"Isso não é a área desmatada do recorte. É a medida de quanto o método ainda erra.\"",
    "",
    "\"Com o NBR, as janelas intactas ficaram bem abaixo das janelas com desmatamento. Isso",
    "sugere que dá para melhorar a recusa, mas com poucos controles e um único tile. Fica como",
    "hipótese, não como resultado.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 17 — Conclusão
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "O que fica deste trabalho",
    quem: "Jonathan Aparecido X Martins  ·  encerramento" });

  const colunas = [
    ["O que funciona", [
      "Cinco etapas de PDI implementadas pelo grupo, só com NumPy",
      "Quantificação exata em cena de verdade de terreno conhecida",
      "Preparação de dados que alimenta um classificador de fato",
      "363 testes automatizados, incluindo casos analíticos dos filtros",
    ]],
    ["O que aprendemos", [
      "A primeira cena real estava tomada por fumaça de queimada e passou no controle de nuvem: o infravermelho de ondas curtas atravessa fumaça",
      "Foi o sistema recusando a detecção que levou a equipe até a causa",
      "O controle de qualidade passou a medir bruma no canal azul",
    ]],
    ["O que falta", [
      "Separar floresta de pasto e rebrota, para reduzir a área marcada a mais",
      "Recalibrar o critério com mais controles e outros tiles",
      "Validar os descritores de textura, que a cena sintética não separa",
      "Registro geométrico entre as duas datas, em cenas de origens diferentes",
    ]],
  ];
  const w = (LARGURA - 2 * 0.24) / 3;
  colunas.forEach(([titulo, lista], i) => {
    const x = MARGEM + i * (w + 0.24);
    cartao(s, { x, y: 1.6, w, h: 4.15 });
    s.addText(titulo, { x: x + 0.3, y: 1.78, w: w - 0.6, h: 0.42, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 19, bold: true, color: COR.floresta });
    itens(s, lista, { x: x + 0.3, y: 2.3, w: w - 0.6, h: 3.3, fontSize: 13 });
  });

  s.addText("Obrigado. Perguntas?", {
    x: MARGEM, y: 6.0, w: LARGURA, h: 0.62, isTextBox: true, margin: 0, align: "center",
    fontFace: TIT, fontSize: 28, bold: true, color: COR.floresta });

  s.addNotes([
    "JONATHAN — encerramento (30 s)",
    "",
    "\"Fechando: o que funciona são as cinco etapas de processamento, todas escritas por",
    "nós com NumPy; a quantificação exata quando existe verdade de terreno; a preparação de",
    "dados alimentando um classificador de verdade; e 363 testes automatizados.\"",
    "",
    "\"O que a gente aprendeu foi na marra. A primeira cena real que baixamos estava tomada",
    "de fumaça de queimada, e passou no nosso controle de nuvem — porque o infravermelho de",
    "ondas curtas atravessa fumaça. Quem apontou o problema foi o próprio sistema, recusando",
    "a detecção. A gente foi investigar a recusa e achou a fumaça. Hoje o controle de",
    "qualidade mede bruma no canal azul.\"",
    "",
    "\"E o que falta: separar floresta de pasto e rebrota, recalibrar o critério com mais",
    "controles, validar os descritores de textura, e tratar registro geométrico quando as",
    "duas datas vierem de origens diferentes.\"",
    "",
    "\"Obrigado. Estamos à disposição para as perguntas — e qualquer um de nós responde",
    "sobre qualquer parte.\"",
  ].join("\n"));
}


// --------------------------------------------------------------------------------------
// Reserva — mostrar só se a demonstração ao vivo falhar
// --------------------------------------------------------------------------------------

// --------------------------------------------------------------------------------------
// 11 — Tela: filtragem e segmentação
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Etapa por etapa, na tela",
    quem: "André Massarente  ·  demonstração" });

  imagem(s, join(FIG, "telas/tela-etapas-3-4.png"), { x: MARGEM, y: 1.88, w: 5.25, h: 4.92 });

  const notas = [
    ["3 · Filtragem", "O índice bruto, o mesmo índice depois do gaussiano 5 × 5 e a magnitude do gradiente de Sobel, que realça a borda do corte."],
    ["4 · Segmentação", "O limiar de Otsu conjunto separa vegetação de solo exposto nas duas datas; o mapa de mudança compara as duas máscaras."],
    ["A legenda de cores", "Vermelho é perda de vegetação, verde é ganho, verde-escuro é vegetação estável e cinza é solo exposto nas duas datas."],
  ];
  notas.forEach(([titulo, texto], i) => {
    const y = 1.8 + i * 1.44;
    s.addText(titulo, { x: 6.3, y, w: 6.4, h: 0.36, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 18, bold: true, color: COR.floresta });
    s.addText(texto, { x: 6.3, y: y + 0.42, w: 6.4, h: 0.98, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 14, color: COR.texto, lineSpacingMultiple: 1.15 });
  });

  cartao(s, { x: 6.3, y: 6.08, w: 6.4, h: 0.72 });
  s.addText("O mapa de mudança não é a diferença entre duas imagens: é a comparação entre duas máscaras obtidas com o mesmo limiar.", {
    x: 6.48, y: 6.18, w: 6.04, h: 0.54, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 12.5, italic: true, color: COR.texto });

  s.addNotes([
    "ANDRÉ — etapas na tela (1 min 30 s, ao vivo)",
    "",
    "NA TELA, aba \"Etapas do processamento\":",
    "",
    "\"Etapa 1, aquisição: as duas datas lado a lado. Etapa 2, o índice de vegetação — o",
    "verde é vegetação densa e o amarelo é solo exposto. Já dá para ver o corte na segunda",
    "data.\"",
    "",
    "\"Etapa 3 é a filtragem, e aqui é onde aparece o trabalho da disciplina. À esquerda o",
    "índice bruto, com o ruído. No meio, depois do gaussiano 5 por 5 — o ruído sumiu e a",
    "borda do corte continuou lá. À direita o Sobel, que é a magnitude do gradiente: ele",
    "acende exatamente no contorno da área cortada.\"",
    "",
    "\"Etapa 4, segmentação. O limiar separa vegetação de solo exposto, e o mapa de mudança",
    "compara as duas máscaras. Atenção na legenda: vermelho é PERDA, verde é ganho,",
    "verde-escuro é vegetação que ficou de pé e cinza é solo exposto nas duas datas.\"",
    "",
    "\"E uma coisa que costuma confundir: esse mapa não é a subtração de uma imagem pela",
    "outra. É a comparação entre duas máscaras calculadas com o MESMO limiar, que é a",
    "decisão que o Enzo explicou.\"",
  ].join("\n"));
}


// --------------------------------------------------------------------------------------
// 12 — Tela: quantificação
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "A quantificação bate com a verdade de terreno",
    quem: "André Massarente  ·  demonstração" });

  imagem(s, join(FIG, "telas/tela-deteccao.png"), { x: MARGEM, y: 1.55, w: 7.15, h: 5.2,
    alinhar: "esquerda" });

  const linhas = [
    ["400 px", "construídos pelo gerador da cena (corte de 20 × 20)"],
    ["400 px", "detectados pelo programa"],
    ["0,0%", "de erro"],
  ];
  linhas.forEach(([valor, rotulo], i) => {
    const y = 1.72 + i * 1.12;
    s.addText(valor, { x: 8.05, y, w: 1.75, h: 0.58, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 30, bold: true, color: i === 2 ? COR.floresta : COR.texto });
    s.addText(rotulo, { x: 9.9, y: y + 0.06, w: 2.85, h: 0.85, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 13, color: COR.suave, valign: "top" });
  });

  cartao(s, { x: 8.05, y: 5.05, w: 4.68, h: 1.72 });
  s.addText("Isto verifica o encadeamento, não o desempenho no mundo real", {
    x: 8.25, y: 5.16, w: 4.28, h: 0.62, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 15, bold: true, color: COR.alerta });
  s.addText("A separação entre floresta e corte foi construída pelo gerador da cena, que a rotula como sintética no código e na interface. Ela demonstra o programa, não o resultado científico.", {
    x: 8.25, y: 5.82, w: 4.28, h: 0.85, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 12, color: COR.texto, lineSpacingMultiple: 1.1 });

  s.addNotes([
    "ANDRÉ — quantificação e recusa (2 min, ao vivo)",
    "",
    "\"Agora a quantificação. A cena foi construída com um corte de 20 por 20 pixels, o que",
    "dá 400 pixels. O programa detectou 400. Erro de zero por cento. E o próprio programa",
    "mostra a verdade de terreno ali embaixo, para dar para conferir.\"",
    "",
    "\"Ao lado, os 400 pixels convertidos em hectares. Isso depende da resolução: a 10",
    "metros por pixel, que é o Sentinel-2, dá 4 hectares. A escala é escolhida ali na barra",
    "lateral, e é assim que se sai de pixel para área de verdade.\"",
    "",
    "\"Mas eu preciso ser honesto sobre o que esse número prova: ele prova que a CADEIA",
    "funciona de ponta a ponta. Ele não prova desempenho no mundo real, porque quem",
    "construiu a separação entre floresta e corte foi o gerador da cena. Por isso a tela",
    "avisa que a imagem é sintética.\"",
    "",
    "AGORA, AO VIVO: arrastar 'Lado da área desmatada' para 0.",
    "",
    "\"Agora eu zerei a área desmatada: são duas datas de floresta intacta, sem corte",
    "nenhum. Olhem o que acontece.\"",
    "",
    "[Apontar o aviso de recusa]",
    "",
    "\"O programa SE RECUSA a dar um número, e explica: a distinguibilidade ficou em 2,66,",
    "abaixo do mínimo de 4,0. Sem duas classes reais, o limiar cortaria o ruído ao meio e",
    "inventaria desmatamento onde não houve. Recusar é a resposta certa.\"",
    "",
    "DEPOIS: voltar a área para 60 e o tamanho da cena para 200; abrir a aba Modelo.",
    "",
    "\"E no modelo: os recortes rotulados pela máscara treinam a floresta aleatória. O F1 dá",
    "1,000 — e o programa avisa que esse número NÃO vale como validação,",
    "porque em cena sintética a separação foi construída. O Jonathan explica agora o que",
    "aconteceu quando a gente rodou isso em imagem de satélite de verdade.\"",
    "",
    "PASSA PARA O JONATHAN.",
  ].join("\n"));
}

}

// ======================================================================================
// Montagem
// ======================================================================================

for (const [fase, destino] of Object.entries(FASES)) {
  if (pedida !== "ambas" && pedida !== fase) continue;
  abrirApresentacao();
  (fase === "qualificacao" ? deckQualificacao : deckDefesa)();
  const caminho = join(RAIZ, destino);
  await pres.writeFile({ fileName: caminho });
  console.log(`${destino} — ${pres.slides?.length ?? "?"} slides`);
}
