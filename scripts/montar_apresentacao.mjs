// Monta a apresentação do seminário (enunciado, seção III) em PPTX.
//
// Existe pelo mesmo motivo do gerador do trabalho escrito: os números da apresentação
// precisam ser os mesmos do repositório. Todo valor citado aqui sai de
// docs/resultados/*/resumo.json ou do texto já conferido em docs/trabalho-escrito/.
//
// As falas de cada integrante vão nas notas do apresentador de cada slide — é onde o
// PowerPoint as exibe no modo apresentador e de onde saem as páginas de anotações
// impressas. A versão impressa em DOCX é gerada por scripts/montar_falas.py.
//
//   node scripts/montar_apresentacao.mjs [saida.pptx]
//
// pptxgenjs não é dependência da aplicação: instale-o só para gerar o arquivo
// (`npm install pptxgenjs`) ou aponte NODE_PATH para uma instalação existente.

import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const PptxGenJS = require("pptxgenjs");

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const FIG = join(RAIZ, "docs/apresentacao/figuras");
const RES = join(RAIZ, "docs/resultados");
// O enunciado divide o projeto em duas entregas com apresentação distinta (p. 5). A
// Fase Intermediária I — Qualificação cobre o capítulo 1 e os itens de filtragem dos
// capítulos 2 e 3, antes do desenvolvimento prático. A Fase Intermediária II — Defesa
// cobre o protótipo e os resultados. Cada uma tem o seu arquivo.
const FASES = {
  qualificacao: "entrega/apresentacao-qualificacao.pptx",
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
  if (quem) {
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
  s.addText("Detecção e quantificação de desmatamento em imagens de satélite", {
    x: MARGEM, y: 1.25, w: 6.9, h: 2.25, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 36, bold: true, color: COR.branco, lineSpacingMultiple: 1.06,
  });
  s.addText("Fase Intermediária I — Qualificação do Projeto", {
    x: MARGEM, y: 3.5, w: 6.9, h: 0.5, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 19, bold: true, italic: true, color: COR.musgo,
  });

  const integrantes = [
    ["André Massarente", "G280BI1"], ["Enzo Consani", "R154149"],
    ["Isabel Da Silva", "F35FDJ4"], ["Jonathan Aparecido X Martins", "F35HCB4"],
  ];
  integrantes.forEach(([nome, ra], i) => {
    const x = MARGEM + (i % 2) * 3.55;
    const y = 4.5 + Math.floor(i / 2) * 0.72;
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
    "ANDRÉ — abertura (20 s)",
    "",
    "\"Boa noite. Nós somos o grupo do tema de sustentabilidade ambiental: detecção e",
    "quantificação de desmatamento em imagens de satélite.\"",
    "",
    "\"Eu sou o André, e comigo estão o Enzo, a Isabel e o Jonathan.\"",
    "",
    "\"Esta é a apresentação da Fase Intermediária I, a qualificação do projeto. Então o que",
    "a gente traz hoje é o capítulo 1 — o problema, o contexto e os objetivos — e os itens",
    "de filtragem dos capítulos 2 e 3: o que é filtragem e quais filtros a nossa solução usa.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 2 — O escopo desta fase
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "O que esta qualificação cobre",
    sub: "Enunciado, p. 5: “Capítulo 1 e os itens relativos a filtragem dos capítulos 2 e 3”",
    quem: "André Massarente" });

  const blocos = [
    ["1", "Capítulo 1 — o problema, o contexto e os objetivos",
      "O que é desmatamento como problema computacional, por que resolvê-lo importa e o que a aplicação se propõe a fazer.",
      "André Massarente  ·  Enzo Consani"],
    ["2", "Capítulo 2 — os conceitos de filtragem",
      "Convolução, tratamento de borda, suavização, separabilidade e realce de borda: a base teórica dos filtros.",
      "Isabel Da Silva"],
    ["3", "Capítulo 3.a — os filtros escolhidos para esta solução",
      "Quais filtros entram na nossa cadeia, em que ordem, e por que cada um está ali.",
      "Jonathan Aparecido X Martins"],
  ];
  blocos.forEach(([n, titulo, texto, quem], i) => {
    const y = 1.9 + i * 1.44;
    cartao(s, { x: MARGEM, y, w: LARGURA, h: 1.26 });
    numero(s, n, { x: MARGEM + 0.34, y: y + 0.37, d: 0.52 });
    s.addText(titulo, { x: MARGEM + 1.12, y: y + 0.14, w: 7.3, h: 0.38, isTextBox: true,
      margin: 0, fontFace: TIT, fontSize: 18, bold: true, color: COR.floresta });
    s.addText(texto, { x: MARGEM + 1.12, y: y + 0.55, w: 7.3, h: 0.6, isTextBox: true,
      margin: 0, fontFace: CORPO, fontSize: 13, color: COR.texto });
    s.addText(quem, { x: 9.15, y: y + 0.45, w: 2.75, h: 0.4, isTextBox: true, margin: 0,
      align: "right", fontFace: CORPO, fontSize: 11.5, bold: true, color: COR.suave });
  });

  cartao(s, { x: MARGEM, y: 6.22, w: LARGURA, h: 0.6, escuro: true });
  s.addText("A demonstração do protótipo e os resultados são da Fase Intermediária II — esta etapa vem antes do desenvolvimento prático.", {
    x: MARGEM + 0.35, y: 6.3, w: LARGURA - 0.7, h: 0.44, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 12.5, italic: true, color: COR.musgo });

  s.addNotes([
    "ANDRÉ — escopo (25 s)",
    "",
    "\"O manual divide o trabalho em duas entregas. A de hoje é a qualificação, e o conteúdo",
    "dela está definido no manual: capítulo 1 completo, mais os itens de filtragem dos",
    "capítulos 2 e 3.\"",
    "",
    "\"Então a ordem é: eu apresento o problema e a relevância ambiental; o Enzo continua no",
    "contexto e nos objetivos; a Isabel apresenta a teoria de filtragem do capítulo 2; e o",
    "Jonathan fecha com os filtros que a nossa proposta escolheu, no capítulo 3.\"",
    "",
    "\"A demonstração do programa e os resultados ficam para a Fase II, que é a defesa.\"",
    "",
    "SE PERGUNTAREM se já há código: dizer que sim, o protótipo já roda, e oferecer mostrar",
    "no fim se houver tempo — o slide de reserva existe para isso.",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 3 — 1.a Descrição do problema
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "1.a · O problema é bi-temporal por definição",
    quem: "André Massarente  ·  capítulo 1.a" });

  imagem(s, join(FIG, "comparativo-real.png"), { x: MARGEM, y: 1.5, w: 4.75, h: 5.15 });

  cartao(s, { x: 5.65, y: 1.55, w: 7.06, h: 1.62, escuro: true });
  s.addText("Dado um par de imagens de satélite da mesma área geográfica, captadas em datas diferentes, identificar automaticamente as regiões que perderam cobertura vegetal entre as duas datas e quantificar essa perda em área.", {
    x: 5.95, y: 1.7, w: 6.46, h: 1.35, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 15, italic: true, color: COR.branco, lineSpacingMultiple: 1.12 });

  s.addText("Por que duas datas, e não uma", {
    x: 5.65, y: 3.4, w: 7.06, h: 0.36, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 18, bold: true, color: COR.floresta });
  s.addText("Uma imagem única mostra o que existe, não o que foi perdido. Uma pastagem consolidada há trinta anos é indistinguível, numa só cena, de uma área desmatada no mês passado. A informação de desmatamento está na diferença entre duas datas.", {
    x: 5.65, y: 3.8, w: 7.06, h: 1.15, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 14.5, color: COR.texto, lineSpacingMultiple: 1.15 });

  s.addText("Por que não resolver em campo", {
    x: 5.65, y: 5.05, w: 7.06, h: 0.36, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 18, bold: true, color: COR.floresta });
  s.addText("As frentes de supressão ficam em regiões de difícil acesso, avançam continuamente e cobrem áreas grandes demais para vistoria direta. A observação orbital é o único instrumento que acompanha isso de forma sistemática.", {
    x: 5.65, y: 5.45, w: 7.06, h: 1.15, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 14.5, color: COR.texto, lineSpacingMultiple: 1.15 });

  s.addNotes([
    "ANDRÉ — descrição do problema (1 min 30 s)",
    "",
    "\"Desmatamento é a remoção da cobertura vegetal nativa de uma área. Detectar e",
    "quantificar isso em escala regional não dá para fazer em campo: as frentes ficam em",
    "lugar de difícil acesso, avançam o tempo todo e cobrem área grande demais. Satélite é o",
    "único instrumento que acompanha isso de forma sistemática.\"",
    "",
    "\"O problema, formalmente, é esse da caixa: dado um PAR de imagens da mesma área em",
    "datas diferentes, identificar as regiões que perderam cobertura vegetal e quantificar",
    "essa perda em área.\"",
    "",
    "\"E o 'par' não é detalhe, é a definição. Olhem a imagem: 2002 à esquerda, 2024 à",
    "direita, em cor natural em cima e no índice em falsa cor embaixo. Se eu mostrasse só a",
    "de 2024, eu não conseguiria dizer o que é pasto de trinta anos e o que é corte do mês",
    "passado — as duas coisas são claras na imagem. A informação está na DIFERENÇA.\"",
    "",
    "\"As imagens são reais, do satélite Terra da NASA, pelo serviço GIBS, de domínio",
    "público, e a procedência está registrada: produto, data, coordenadas, licença e URL.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 4 — 1.a Relevância ambiental
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "1.a · Relevância em termos de sustentabilidade",
    sub: "Quatro caminhos simultâneos — e o que torna o problema tratável por computação",
    quem: "André Massarente  ·  capítulo 1.a" });

  const caminhos = [
    ["Emissão de carbono", "A biomassa florestal armazena carbono; sua remoção, em geral seguida de queima, transfere esse carbono para a atmosfera."],
    ["Perda de habitat", "A conversão em pastagem elimina o habitat das espécies que dependem do dossel contínuo, e a fragmentação isola populações."],
    ["Ciclo hidrológico", "A floresta transporta umidade continental pela evapotranspiração; vegetação rasa altera esse fluxo."],
    ["Solo", "A exposição direta acelera a erosão e a perda de fertilidade."],
  ];
  const w = (LARGURA - 3 * 0.22) / 4;
  caminhos.forEach(([titulo, texto], i) => {
    const x = MARGEM + i * (w + 0.22);
    cartao(s, { x, y: 1.9, w, h: 2.32 });
    s.addText(titulo, { x: x + 0.24, y: 2.06, w: w - 0.48, h: 0.56, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 16, bold: true, color: COR.floresta });
    s.addText(texto, { x: x + 0.24, y: 2.68, w: w - 0.48, h: 1.4, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 12.5, color: COR.texto, lineSpacingMultiple: 1.12 });
  });

  s.addText("A escala é medida oficialmente", {
    x: MARGEM, y: 4.44, w: 5.6, h: 0.36, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 18, bold: true, color: COR.floresta });
  destaque(s, { x: MARGEM, y: 4.9, w: 2.7, valor: "5.731 km²", rotulo: "desmatados na Amazônia Legal\nem 2025 — 12,07% menos que 2024\n(INPE, 2026)", tamanho: 30 });
  destaque(s, { x: MARGEM + 2.9, y: 4.9, w: 2.7, valor: "42%", rotulo: "das emissões brutas do Brasil\nem 2024 vieram do uso da terra:\n906 MtCO₂e (SEEG, 2025)", tamanho: 30 });

  cartao(s, { x: 6.9, y: 4.44, w: 5.82, h: 2.24, escuro: true });
  s.addText("O que torna o problema tratável por computação", {
    x: 7.15, y: 4.58, w: 5.32, h: 0.62, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 17, bold: true, color: COR.musgo });
  s.addText("Todos esses efeitos decorrem de uma mudança opticamente observável: a assinatura espectral de um dossel florestal é diferente da de solo exposto ou pastagem, e essa diferença é mensurável a partir do espaço. É exatamente essa diferença que os filtros do capítulo 3 realçam.", {
    x: 7.15, y: 5.22, w: 5.32, h: 1.35, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 14, color: COR.branco, lineSpacingMultiple: 1.15 });

  s.addNotes([
    "ANDRÉ — relevância ambiental (1 min 10 s)",
    "",
    "\"Por que esse problema importa para sustentabilidade. A supressão de vegetação age por",
    "quatro caminhos ao mesmo tempo: carbono, habitat, ciclo da água e solo.\"",
    "",
    "\"Carbono: a floresta guarda carbono na biomassa; derrubar e queimar joga isso na",
    "atmosfera. Habitat: espécies que dependem de dossel contínuo perdem o ambiente, e a",
    "fragmentação isola o que sobra. Água: a floresta bombeia umidade pela",
    "evapotranspiração. E solo: exposto, ele erode e perde fertilidade.\"",
    "",
    "\"A escala é medida oficialmente. O INPE consolidou 5.731 quilômetros quadrados na",
    "Amazônia Legal no período de agosto de 2024 a julho de 2025 — 12% a menos que no ano",
    "anterior. E o SEEG mostra que em 2024 o uso da terra respondeu por 42% das emissões",
    "brutas de gases de efeito estufa do Brasil, 906 milhões de toneladas.\"",
    "",
    "\"Mas o ponto que liga tudo isso à nossa disciplina é o quadro da direita: todos esses",
    "efeitos vêm de uma mudança OPTICAMENTE OBSERVÁVEL. Dossel florestal reflete diferente",
    "de solo exposto. É essa diferença que os nossos filtros vão realçar.\"",
    "",
    "PASSA PARA O ENZO.",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 5 — 1.b Contexto
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "1.b · Por que resolver este problema importa",
    quem: "Enzo Consani  ·  capítulo 1.b" });

  const blocos = [
    ["Saber onde olhar", [
      "Um órgão de controle não tem efetivo para percorrer uma frente de desmatamento inteira.",
      "Ele precisa de um sistema que aponte, periodicamente, quais polígonos mudaram desde a última observação.",
      "Detecção automática transforma um problema de vigilância impossível num problema de priorização.",
    ]],
    ["Conferir compromissos", [
      "Acordos de restauração, embargos, rastreabilidade em cadeias produtivas, compromissos de desmatamento zero.",
      "Todos só têm efeito se houver como conferir se foram cumpridos.",
      "Essa conferência é, na prática, uma comparação entre duas datas — o mesmo problema do slide anterior.",
    ]],
    ["Assimetria de informação", [
      "Sem monitoramento independente, o que acontece numa frente de expansão só é sabido por quem está lá.",
      "Dado orbital aberto, processado por método reproduzível, é um contrapeso a essa assimetria.",
      "Dos 1.593 conflitos no campo registrados em 2025, 824 foram na Amazônia Legal (CPT, 2026).",
    ]],
  ];
  const w = (LARGURA - 2 * 0.24) / 3;
  blocos.forEach(([titulo, lista], i) => {
    const x = MARGEM + i * (w + 0.24);
    cartao(s, { x, y: 1.6, w, h: 3.5 });
    numero(s, i + 1, { x: x + 0.28, y: 1.82, d: 0.5 });
    s.addText(titulo, { x: x + 0.9, y: 1.76, w: w - 1.15, h: 0.62, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 17, bold: true, color: COR.floresta, valign: "middle" });
    itens(s, lista, { x: x + 0.3, y: 2.56, w: w - 0.6, h: 2.44, fontSize: 13 });
  });

  cartao(s, { x: MARGEM, y: 5.3, w: LARGURA, h: 1.4, escuro: true });
  s.addText("O custo de errar é assimétrico nas duas direções", {
    x: MARGEM + 0.4, y: 5.45, w: LARGURA - 0.8, h: 0.38, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 18, bold: true, color: COR.branco });
  s.addText("Um falso positivo — acusar desmatamento onde não houve — pode gerar sanção indevida sobre um produtor. Um falso negativo deixa passar supressão real, e a floresta não volta. Um sistema honesto precisa reconhecer quando não tem informação suficiente para decidir, em vez de sempre emitir um veredito.", {
    x: MARGEM + 0.4, y: 5.88, w: LARGURA - 0.8, h: 0.75, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 14, color: COR.musgo, lineSpacingMultiple: 1.15 });

  s.addNotes([
    "ENZO — contexto (1 min 15 s)",
    "",
    "\"Três razões pelas quais resolver isso importa.\"",
    "",
    "\"Primeira: saber onde olhar. Fiscalização ambiental não tem efetivo para percorrer a",
    "frente inteira. O que ela precisa é de um sistema que diga quais polígonos mudaram",
    "desde a última vez. Detecção automática não substitui o fiscal — ela transforma um",
    "problema de vigilância impossível num problema de priorização.\"",
    "",
    "\"Segunda: conferir compromissos. Embargo, acordo de restauração, rastreabilidade de",
    "cadeia produtiva, desmatamento zero — nada disso tem efeito se não dá para verificar. E",
    "verificar é, na prática, comparar duas datas. É o mesmo problema.\"",
    "",
    "\"Terceira: assimetria de informação. Sem monitoramento independente, quem sabe o que",
    "acontece numa frente de expansão é só quem está lá. Dado orbital aberto e método",
    "reproduzível são um contrapeso. E isso não é abstrato: a Comissão Pastoral da Terra",
    "registrou 1.593 conflitos no campo em 2025, dos quais 824 na Amazônia Legal.\"",
    "",
    "\"E embaixo, uma ideia que volta no fim da apresentação: errar custa caro dos DOIS",
    "lados. Falso positivo pune quem não desmatou; falso negativo deixa passar. Por isso a",
    "gente acha que um sistema honesto precisa saber dizer 'não tenho informação",
    "suficiente'.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 6 — 1.b Impacto ecológico
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "1.b · Impacto ecológico: a geometria importa",
    quem: "Enzo Consani  ·  capítulo 1.b" });

  imagem(s, join(RES, "imagem-real/02-depois.png"), { x: MARGEM, y: 1.6, w: 4.6, h: 4.6 });
  s.addText("São Félix do Xingu (PA), 2024 — o padrão de corte acompanha as estradas", {
    x: MARGEM, y: 6.26, w: 4.6, h: 0.44, isTextBox: true, margin: 0, align: "center",
    fontFace: CORPO, fontSize: 11.5, italic: true, color: COR.suave });

  s.addText("O impacto não é proporcional apenas à área removida, mas também à forma do corte.", {
    x: 5.55, y: 1.6, w: 7.16, h: 0.6, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 16, color: COR.texto, lineSpacingMultiple: 1.15 });

  itens(s, [
    "Cortes alongados ao longo de estradas — o padrão conhecido como espinha de peixe — produzem muito mais borda por unidade de área do que um corte compacto.",
    "Borda é onde o microclima muda: a floresta de borda fica mais seca, mais quente e mais vulnerável ao fogo do que o interior.",
    "A fragmentação isola populações de espécies que não atravessam área aberta.",
  ], { x: 5.55, y: 2.35, w: 7.16, h: 2.1, fontSize: 14.5 });

  cartao(s, { x: 5.55, y: 4.6, w: 7.16, h: 2.06, escuro: true });
  s.addText("A consequência sobre o que o sistema precisa produzir", {
    x: 5.85, y: 4.76, w: 6.56, h: 0.38, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 17, bold: true, color: COR.musgo });
  s.addText("Não basta um número de área total. Um sistema útil precisa entregar as regiões individualmente, com a forma e a localização de cada uma, porque a análise ecológica depende disso. É por essa razão que a solução proposta rotula componentes conexos e descreve cada região separadamente, em vez de apenas somar pixels.", {
    x: 5.85, y: 5.2, w: 6.56, h: 1.3, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 14, color: COR.branco, lineSpacingMultiple: 1.15 });

  s.addNotes([
    "ENZO — impacto ecológico (50 s)",
    "",
    "\"Uma coisa que a gente aprendeu escrevendo o capítulo 1 e que mudou o desenho do",
    "projeto: o impacto do desmatamento não depende só de QUANTO foi removido, mas da FORMA.\"",
    "",
    "\"Olhem a imagem: o corte acompanha as estradas. É o padrão que chamam de espinha de",
    "peixe. Um corte alongado desse tipo produz muito mais borda por unidade de área do que",
    "um corte compacto do mesmo tamanho.\"",
    "",
    "\"E borda importa porque é onde o microclima muda: a floresta de borda é mais seca, mais",
    "quente e mais vulnerável ao fogo. Além disso a fragmentação isola espécies que não",
    "atravessam área aberta.\"",
    "",
    "\"A consequência para o nosso sistema está no quadro escuro: NÃO BASTA um número de área",
    "total. O sistema precisa entregar as regiões uma a uma, com forma e localização. É por",
    "isso que a nossa solução rotula componentes conexos e descreve cada região, em vez de",
    "só somar pixels. O requisito ecológico virou requisito de software.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 7 — 1.c Objetivos
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "1.c · Objetivos", quem: "Enzo Consani  ·  capítulo 1.c" });

  cartao(s, { x: MARGEM, y: 1.5, w: LARGURA, h: 1.32, escuro: true });
  s.addText("Objetivo geral", { x: MARGEM + 0.4, y: 1.62, w: 3.0, h: 0.32, isTextBox: true,
    margin: 0, fontFace: TIT, fontSize: 15, bold: true, color: COR.musgo });
  s.addText("Desenvolver uma aplicação em Python que, a partir de um par de imagens reais de satélite da mesma área em datas distintas, aplique técnicas de processamento digital de imagens para detectar e quantificar áreas que perderam cobertura vegetal, produzindo dados preparados para alimentar um modelo de visão computacional.", {
    x: MARGEM + 0.4, y: 1.96, w: LARGURA - 0.8, h: 0.8, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 14, color: COR.branco, lineSpacingMultiple: 1.12 });

  s.addText("Objetivos específicos", { x: MARGEM, y: 2.95, w: 8.2, h: 0.36, isTextBox: true,
    margin: 0, fontFace: TIT, fontSize: 18, bold: true, color: COR.floresta });
  const especificos = [
    "Adquirir imagens reais de satélite com procedência registrada e de forma reproduzível",
    "Implementar os filtros pelo próprio grupo, sem implementações prontas de biblioteca",
    "Realçar a diferença entre vegetação e solo exposto por índices espectrais",
    "Segmentar as áreas de perda de cobertura, separando-as do restante da cena",
    "Quantificar a perda em pixels e, com resolução conhecida, em hectares, região a região",
    "Preparar recortes rotulados no formato que um modelo de visão computacional consome",
    "Treinar e avaliar um classificador com métrica que não superestime o desempenho",
    "Reconhecer os próprios limites: recusar um número quando a imagem não o sustenta",
  ];
  especificos.forEach((texto, i) => {
    const x = MARGEM + (i % 2) * 4.2;
    const y = 3.4 + Math.floor(i / 2) * 0.82;
    numero(s, i + 1, { x, y: y + 0.02, d: 0.38, cor: COR.musgo });
    s.addText(texto, { x: x + 0.52, y, w: 3.55, h: 0.76, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 12.5, color: COR.texto, lineSpacingMultiple: 1.1 });
  });

  cartao(s, { x: 9.15, y: 3.4, w: 3.57, h: 3.22 });
  s.addText("O que está fora do escopo", { x: 9.4, y: 3.54, w: 3.07, h: 0.34, isTextBox: true,
    margin: 0, fontFace: TIT, fontSize: 16, bold: true, color: COR.alerta });
  itens(s, [
    "Processar cenas completas em escala operacional",
    "Substituir sistemas oficiais de monitoramento",
    "Classificar o uso que sucedeu a floresta",
    "Operar em tempo real ou com alerta automático",
    "Produzir índices comparáveis à literatura científica",
  ], { x: 9.4, y: 3.96, w: 3.07, h: 2.5, fontSize: 12 });

  s.addNotes([
    "ENZO — objetivos (55 s)",
    "",
    "\"O objetivo geral é a frase da caixa escura, e ela foi escrita colada no enunciado: uma",
    "aplicação em Python que aplica processamento de imagens sobre um par de datas para",
    "detectar e quantificar perda de cobertura, PRODUZINDO DADOS PREPARADOS para alimentar um",
    "modelo de visão computacional. O processamento de imagens aqui é preparação de dados,",
    "não é o produto final.\"",
    "",
    "\"Os oito objetivos específicos: adquirir imagem real com procedência; implementar os",
    "filtros por conta própria; realçar a diferença com índices; segmentar; quantificar;",
    "preparar recortes rotulados; treinar e avaliar sem superestimar; e o oitavo, reconhecer",
    "os próprios limites.\"",
    "",
    "\"Esse oitavo não estava na versão inicial. A gente acrescentou depois — e explica por",
    "quê na defesa.\"",
    "",
    "\"E a coluna da direita é tão importante quanto: o que a gente NÃO se propõe a fazer.",
    "Não substituímos o INPE, não processamos cena inteira em escala operacional, não",
    "classificamos o uso que veio depois da floresta e não produzimos índice comparável com",
    "a literatura. Delimitar isso é o que torna os objetivos verificáveis.\"",
    "",
    "PASSA PARA A ISABEL.",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 8 — 2.e.iii Convolução e tratamento de borda
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "2.e.iii · Filtragem: uma operação, muitos filtros",
    quem: "Isabel Da Silva  ·  capítulo 2.e.iii" });

  s.addText("Todos os filtros espaciais deste trabalho são casos particulares da mesma operação.", {
    x: MARGEM, y: 1.46, w: 6.2, h: 0.5, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 15, color: COR.texto });

  cartao(s, { x: MARGEM, y: 2.0, w: 6.2, h: 1.62, escuro: true });
  s.addText("Convolução", { x: MARGEM + 0.3, y: 2.12, w: 5.6, h: 0.3, isTextBox: true,
    margin: 0, fontFace: TIT, fontSize: 14, bold: true, color: COR.musgo });
  s.addText("(I * K)(x, y) = Σ Σ  K(i, j) · I(x − i, y − j)", {
    x: MARGEM + 0.3, y: 2.44, w: 5.6, h: 0.34, isTextBox: true, margin: 0,
    fontFace: "Courier New", fontSize: 14, color: COR.branco });
  s.addText("Correlação cruzada", { x: MARGEM + 0.3, y: 2.86, w: 5.6, h: 0.3, isTextBox: true,
    margin: 0, fontFace: TIT, fontSize: 14, bold: true, color: COR.musgo });
  s.addText("(I ⊗ K)(x, y) = Σ Σ  K(i, j) · I(x + i, y + j)", {
    x: MARGEM + 0.3, y: 3.18, w: 5.6, h: 0.34, isTextBox: true, margin: 0,
    fontFace: "Courier New", fontSize: 14, color: COR.branco });

  s.addText("A diferença é o sinal dos índices — e ela importa", {
    x: MARGEM, y: 3.82, w: 6.2, h: 0.34, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 17, bold: true, color: COR.floresta });
  itens(s, [
    "Para núcleos simétricos — média, gaussiano, laplaciano — as duas operações dão o mesmo resultado.",
    "Para núcleos antissimétricos, como Sobel e Prewitt, elas diferem no sinal: uma borda clara-para-escura troca de sinal com uma escura-para-clara.",
    "Como aqui interessa a magnitude do gradiente, o sinal não muda a conclusão — mas a implementação precisa saber qual das duas executa. As duas estão implementadas separadamente.",
  ], { x: MARGEM, y: 4.24, w: 6.2, h: 2.3, fontSize: 13 });

  s.addText("Tratamento de borda", { x: 7.2, y: 1.5, w: 5.52, h: 0.36, isTextBox: true,
    margin: 0, fontFace: TIT, fontSize: 18, bold: true, color: COR.floresta });
  s.addText("Num pixel da margem, parte da vizinhança exigida pelo núcleo cai fora da imagem. Há três saídas: encolher a imagem, inventar valores, ou estendê-la por uma regra explícita. Este trabalho estende, e oferece quatro regras.", {
    x: 7.2, y: 1.9, w: 5.52, h: 0.95, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 13.5, color: COR.texto, lineSpacingMultiple: 1.12 });

  const modos = [
    ["reflete", "espelha os pixels em torno da margem — padrão, não cria descontinuidade artificial"],
    ["replica", "repete o pixel da margem — usado em morfologia, onde o valor extremo importa"],
    ["zero", "preenche com zero — cria borda escura artificial"],
    ["circular", "trata a imagem como toroidal — raramente apropriado aqui"],
  ];
  modos.forEach(([nome, texto], i) => {
    const y = 2.98 + i * 0.66;
    s.addText(nome, { x: 7.2, y, w: 1.15, h: 0.34, isTextBox: true, margin: 0,
      fontFace: "Courier New", fontSize: 12.5, bold: true, color: COR.floresta });
    s.addText(texto, { x: 8.4, y, w: 4.32, h: 0.6, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 12, color: COR.texto, lineSpacingMultiple: 1.08 });
  });

  cartao(s, { x: 7.2, y: 5.6, w: 5.52, h: 1.06 });
  s.addText("A escolha não é cosmética: preencher com zero numa cena de floresta cria uma faixa escura na margem que o índice de vegetação lê como solo exposto — e que a segmentação marcaria como desmatamento na borda da imagem.", {
    x: 7.42, y: 5.72, w: 5.08, h: 0.86, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 12, italic: true, color: COR.alerta, lineSpacingMultiple: 1.1 });

  s.addNotes([
    "ISABEL — convolução e borda (1 min 15 s)",
    "",
    "\"O capítulo 2 é a base teórica. E o ponto de partida é que todos os filtros espaciais",
    "que a gente usa são casos particulares de UMA operação: a convolução.\"",
    "",
    "\"A fórmula está aí: para cada pixel, você percorre a vizinhança, multiplica pelo peso",
    "correspondente do núcleo e soma. Mudar o filtro é mudar o núcleo.\"",
    "",
    "\"Logo abaixo está a correlação cruzada, que é a mesma soma sem a inversão dos índices.",
    "Essa distinção é muito ignorada, e a gente faz questão dela: para núcleo simétrico —",
    "média, gaussiano, laplaciano — dá exatamente o mesmo resultado. Para núcleo",
    "antissimétrico, como o Sobel, muda o SINAL: uma borda de claro para escuro inverte em",
    "relação a uma de escuro para claro.\"",
    "",
    "\"No nosso caso interessa a magnitude, então o sinal não muda a conclusão — mas a",
    "implementação precisa saber qual das duas está rodando. Por isso as duas estão",
    "implementadas separadamente no código.\"",
    "",
    "\"À direita, o tratamento de borda. No pixel da margem, parte da vizinhança cai fora da",
    "imagem. Dá para encolher a imagem, inventar valor, ou estender por uma regra. A gente",
    "estende, com quatro regras.\"",
    "",
    "\"E isso não é detalhe cosmético — está no quadro de baixo: se você preenche com ZERO",
    "numa cena de floresta, cria uma faixa escura na margem. O índice de vegetação lê faixa",
    "escura como solo exposto, e a segmentação marcaria desmatamento na borda da imagem. Por",
    "isso o padrão é reflexão.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 9 — 2.e.iii Suavização
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "2.e.iii · Filtros de suavização",
    sub: "Reduzir ruído sem apagar a borda que a segmentação precisa encontrar",
    quem: "Isabel Da Silva  ·  capítulo 2.e.iii" });

  const filtros = [
    ["Média aritmética", "Núcleo com todos os pesos iguais a 1/k².",
      "Reduz ruído, mas borra bordas com o mesmo peso com que borra o ruído, porque trata todos os vizinhos igualmente.", "linear"],
    ["Gaussiano", "K(i, j) = (1/2πσ²) · exp(−(i²+j²)/2σ²)",
      "Os pesos decaem com a distância ao centro. Normalizado para somar 1, o que preserva o brilho médio da imagem. É o filtro usado antes da limiarização neste trabalho.", "linear"],
    ["Mediana", "Não é uma convolução: substitui o pixel pela mediana da vizinhança.",
      "Por ser estatística de ordem, remove ruído impulsivo sem borrar a borda — um valor extremo isolado não altera a mediana. Custa mais que a convolução.", "não linear"],
  ];
  const w = (LARGURA - 2 * 0.24) / 3;
  filtros.forEach(([titulo, formula, texto, tipo], i) => {
    const x = MARGEM + i * (w + 0.24);
    cartao(s, { x, y: 1.9, w, h: 3.2 });
    s.addText(titulo, { x: x + 0.28, y: 2.05, w: w - 0.56, h: 0.36, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 18, bold: true, color: COR.floresta });
    s.addText(tipo, { x: x + 0.28, y: 2.44, w: w - 0.56, h: 0.26, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 11, italic: true, color: COR.suave });
    s.addText(formula, { x: x + 0.28, y: 2.76, w: w - 0.56, h: 0.72, isTextBox: true, margin: 0,
      fontFace: "Courier New", fontSize: 11, color: COR.texto, lineSpacingMultiple: 1.1 });
    s.addText(texto, { x: x + 0.28, y: 3.56, w: w - 0.56, h: 1.44, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 13, color: COR.texto, lineSpacingMultiple: 1.14 });
  });

  cartao(s, { x: MARGEM, y: 5.3, w: LARGURA, h: 1.4, escuro: true });
  s.addText("Por que suavizar é obrigatório antes de limiarizar", {
    x: MARGEM + 0.4, y: 5.44, w: LARGURA - 0.8, h: 0.38, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 18, bold: true, color: COR.branco });
  s.addText("Sem suavização, o ruído do sensor faz pixels individuais atravessarem o limiar nas duas direções e a máscara sai esburacada. Uma máscara esburacada multiplica a contagem de componentes conexos e inviabiliza a análise por região — o sistema reportaria centenas de “áreas desmatadas” de poucos pixels onde há uma só. E a análise por região é justamente o que o capítulo 1 exigiu.", {
    x: MARGEM + 0.4, y: 5.86, w: LARGURA - 0.8, h: 0.78, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 13.5, color: COR.musgo, lineSpacingMultiple: 1.14 });

  s.addNotes([
    "ISABEL — suavização (1 min)",
    "",
    "\"Três filtros de suavização, e eles não são intercambiáveis.\"",
    "",
    "\"A média é o mais simples: todos os vizinhos com o mesmo peso. Reduz ruído, mas borra a",
    "borda com a mesma força com que borra o ruído — justamente porque trata todo mundo",
    "igual.\"",
    "",
    "\"O gaussiano resolve isso fazendo o peso decair com a distância ao centro. E ele é",
    "normalizado para somar 1, o que preserva o brilho médio da imagem. É esse que a gente",
    "usa antes da limiarização.\"",
    "",
    "\"A mediana é diferente dos dois: ela nem é uma convolução. Ela troca o pixel pela",
    "mediana da vizinhança. Como mediana é estatística de ordem, um pixel isolado com valor",
    "absurdo não muda o resultado — então ela remove ruído impulsivo SEM borrar a borda. O",
    "preço é ser mais cara.\"",
    "",
    "\"E o quadro de baixo é a justificativa de tudo isso. Se a gente não suaviza, o ruído do",
    "sensor faz pixel individual atravessar o limiar, e a máscara sai cheia de buraco. Aí a",
    "contagem de componentes conexos explode: o sistema ia reportar centenas de 'áreas",
    "desmatadas' de três pixels onde existe uma só. E a análise por região é exatamente o que",
    "o capítulo 1 disse que era necessário.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 10 — 2.e.iii Separabilidade
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "2.e.iii · Separabilidade: álgebra com efeito medido",
    quem: "Isabel Da Silva  ·  capítulo 2.e.iii" });

  s.addText("A convolução 2D direta custa k² multiplicações por pixel. Para o núcleo gaussiano esse custo cai para 2k — e a redução não é uma aproximação.", {
    x: MARGEM, y: 1.5, w: 6.3, h: 0.72, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 15, color: COR.texto, lineSpacingMultiple: 1.15 });

  cartao(s, { x: MARGEM, y: 2.32, w: 6.3, h: 1.3, escuro: true });
  s.addText("G(x, y) = exp(−(x² + y²)/2σ²)\n        = exp(−x²/2σ²) · exp(−y²/2σ²)\n        = g(x) · g(y)", {
    x: MARGEM + 0.3, y: 2.46, w: 5.7, h: 1.0, isTextBox: true, margin: 0,
    fontFace: "Courier New", fontSize: 13, color: COR.branco, lineSpacingMultiple: 1.2 });

  itens(s, [
    "O expoente da gaussiana é uma soma, e o expoente de uma soma é o produto de exponenciais: o núcleo 2D é exatamente o produto externo de dois núcleos 1D idênticos.",
    "Convoluir pelo núcleo 2D equivale a convoluir por g na horizontal e depois por g na vertical.",
    "A normalização acompanha: se cada núcleo 1D soma 1, o produto externo soma 1.",
    "A média também é separável, e é implementada assim. A mediana não é — estatísticas de ordem não se decompõem dessa forma.",
  ], { x: MARGEM, y: 3.76, w: 6.3, h: 2.5, fontSize: 13 });

  s.addChart(pres.ChartType.bar, [{
    name: "Ganho",
    labels: ["3 × 3", "5 × 5", "9 × 9", "15 × 15", "21 × 21"],
    values: [1.4, 2.2, 3.9, 5.2, 9.4],
  }], {
    x: 7.2, y: 1.6, w: 5.52, h: 4.15,
    barDir: "col", chartColors: [COR.floresta],
    showTitle: true, title: "Ganho do gaussiano separável, por lado da janela",
    titleFontFace: TIT, titleFontSize: 14, titleColor: COR.floresta,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '0.0"×"',
    dataLabelFontFace: CORPO, dataLabelFontSize: 11, dataLabelColor: COR.texto,
    catAxisLabelColor: COR.suave, catAxisLabelFontFace: CORPO, catAxisLabelFontSize: 11,
    valAxisLabelColor: COR.suave, valAxisLabelFontFace: CORPO, valAxisLabelFontSize: 10,
    valAxisMaxVal: 11, valGridLine: { color: "DDE4D8", size: 1 },
    catGridLine: { style: "none" }, showLegend: false,
  });

  s.addText("Medido sobre uma imagem de 440 × 440 pixels. A maior diferença entre os dois caminhos foi de 1,0 × 10⁻⁶ — arredondamento de ponto flutuante, não diferença de método. A equivalência é verificada por teste, inclusive nas bordas e nos quatro modos de margem.", {
    x: 7.2, y: 5.82, w: 5.52, h: 0.85, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 11.5, italic: true, color: COR.suave, lineSpacingMultiple: 1.1 });

  s.addNotes([
    "ISABEL — separabilidade (1 min)",
    "",
    "\"Essa é a parte mais bonita do capítulo 2, na nossa opinião, porque é álgebra pura com",
    "efeito medido.\"",
    "",
    "\"Convolução 2D direta custa k ao quadrado multiplicações por pixel. Para o gaussiano dá",
    "para baixar isso para 2k. E não é aproximação — é identidade.\"",
    "",
    "\"A conta está aí: o expoente da gaussiana é uma SOMA, x² mais y². E exponencial de soma",
    "é produto de exponenciais. Então o núcleo 2D é exatamente o produto externo de dois",
    "núcleos 1D iguais. Convoluir pelo 2D é a mesma coisa que passar o 1D na horizontal e",
    "depois na vertical.\"",
    "",
    "\"O gráfico é a medição no nosso código, numa imagem de 440 por 440. Numa janela 3 por 3",
    "o ganho é pequeno, 1,4 vezes. Numa 21 por 21 chega a 9,4 vezes. Faz sentido: o ganho",
    "cresce com k.\"",
    "",
    "\"E a diferença entre os dois caminhos foi de 10 elevado a menos 6 — isso é",
    "arredondamento de float, não diferença de método. A gente tem teste que confere essa",
    "equivalência inclusive nas bordas e nos quatro modos de margem, porque é lá que ela",
    "poderia falhar.\"",
    "",
    "\"A média também é separável. A mediana NÃO é: a mediana de uma janela 2D não é a",
    "mediana das medianas das linhas, porque estatística de ordem não se decompõe assim.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 11 — 2.e.iii Realce de borda e textura
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "2.e.iii · Realce de borda e textura",
    sub: "Bordas são descontinuidades; detectá-las é estimar derivadas espaciais",
    quem: "Isabel Da Silva  ·  capítulo 2.e.iii" });

  cartao(s, { x: MARGEM, y: 1.9, w: 6.2, h: 2.62 });
  s.addText("Sobel — primeira derivada", { x: MARGEM + 0.3, y: 2.04, w: 5.6, h: 0.34,
    isTextBox: true, margin: 0, fontFace: TIT, fontSize: 17, bold: true, color: COR.floresta });
  s.addText("     ⎡ −1  0  +1 ⎤          ⎡ −1  −2  −1 ⎤\nKx = ⎢ −2  0  +2 ⎥    Ky = ⎢  0   0   0 ⎥\n     ⎣ −1  0  +1 ⎦          ⎣ +1  +2  +1 ⎦", {
    x: MARGEM + 0.3, y: 2.42, w: 5.6, h: 0.95, isTextBox: true, margin: 0,
    fontFace: "Courier New", fontSize: 11.5, color: COR.texto, lineSpacingMultiple: 1.15 });
  s.addText("O peso 2 na linha central é suavização perpendicular — é o que torna o Sobel menos sensível a ruído que uma diferença simples. O Prewitt tem a mesma estrutura sem essa ponderação, e está implementado para permitir a comparação.", {
    x: MARGEM + 0.3, y: 3.45, w: 5.6, h: 0.95, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 12.5, color: COR.texto, lineSpacingMultiple: 1.12 });

  cartao(s, { x: MARGEM, y: 4.66, w: 6.2, h: 1.32, escuro: true });
  s.addText("|∇I| = √(Gx² + Gy²)          θ = arctan(Gy / Gx)", {
    x: MARGEM + 0.3, y: 4.8, w: 5.6, h: 0.34, isTextBox: true, margin: 0,
    fontFace: "Courier New", fontSize: 13, color: COR.branco });
  s.addText("A magnitude é invariante à orientação da borda: é ela que realça o contorno entre floresta e área desmatada, independentemente da direção do corte.", {
    x: MARGEM + 0.3, y: 5.2, w: 5.6, h: 0.68, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 12.5, color: COR.musgo, lineSpacingMultiple: 1.12 });

  cartao(s, { x: 7.2, y: 1.9, w: 5.52, h: 2.62 });
  s.addText("Laplaciano — segunda derivada", { x: 7.5, y: 2.04, w: 4.92, h: 0.34,
    isTextBox: true, margin: 0, fontFace: TIT, fontSize: 17, bold: true, color: COR.floresta });
  s.addText("    ⎡  0   1   0 ⎤\nK = ⎢  1  −4   1 ⎥        I' = I − c · ∇²I\n    ⎣  0   1   0 ⎦", {
    x: 7.5, y: 2.42, w: 4.92, h: 0.8, isTextBox: true, margin: 0,
    fontFace: "Courier New", fontSize: 11.5, color: COR.texto, lineSpacingMultiple: 1.15 });
  s.addText("Isotrópico e sensível a detalhe fino e a ruído. A soma dos pesos é zero: leva a zero uma região constante e também uma rampa linear — propriedade usada como caso de teste analítico. Subtrair uma fração dele da imagem original é o realce de nitidez.", {
    x: 7.5, y: 3.3, w: 4.92, h: 1.1, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 12.5, color: COR.texto, lineSpacingMultiple: 1.12 });

  cartao(s, { x: 7.2, y: 4.66, w: 5.52, h: 1.32 });
  s.addText("Textura por desvio-padrão local", { x: 7.5, y: 4.78, w: 4.92, h: 0.32,
    isTextBox: true, margin: 0, fontFace: TIT, fontSize: 16, bold: true, color: COR.floresta });
  s.addText("Dossel florestal fechado é irregular em altura e sombreamento e produz desvio local alto; pastagem e solo exposto são homogêneos e produzem desvio baixo. É hipótese da literatura, ainda não validada neste trabalho.", {
    x: 7.5, y: 5.14, w: 4.92, h: 0.76, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 12, color: COR.texto, lineSpacingMultiple: 1.1 });

  s.addText("Definições consolidadas em Gonzalez e Woods (2018): correlação e convolução (p. 178), núcleos separáveis (p. 185), suavização (p. 189–190), mediana (p. 198), laplaciano (p. 202) e gradiente (p. 208 e 779).", {
    x: MARGEM, y: 6.14, w: LARGURA, h: 0.4, isTextBox: true, margin: 0, align: "center",
    fontFace: CORPO, fontSize: 11, italic: true, color: COR.suave });

  s.addNotes([
    "ISABEL — realce de borda e textura (1 min 10 s)",
    "",
    "\"Bordas são descontinuidades. Detectar borda é estimar derivada espacial.\"",
    "",
    "\"O Sobel é a primeira derivada. São dois núcleos: um para a direção x e outro para y. E",
    "tem um detalhe que vale explicar: o peso 2 na linha do meio não é enfeite — é suavização",
    "na direção perpendicular. É isso que faz o Sobel ser menos sensível a ruído do que uma",
    "diferença simples. O Prewitt é a mesma estrutura sem esse peso, e a gente implementou",
    "para poder comparar.\"",
    "",
    "\"Dos dois sai a magnitude do gradiente, que é a raiz da soma dos quadrados. A magnitude",
    "é invariante à orientação — e isso importa muito aqui, porque o corte pode estar em",
    "qualquer direção. A magnitude acende o contorno de qualquer jeito.\"",
    "",
    "\"O laplaciano é segunda derivada, isotrópico. Como ele responde a MUDANÇA DE TAXA, é",
    "muito sensível a detalhe fino e a ruído. Repara que a soma dos pesos é zero: isso",
    "significa que região constante vai a zero, e rampa linear também. A gente usa exatamente",
    "isso como caso de teste analítico.\"",
    "",
    "\"E o último quadro é a textura: desvio-padrão de uma janela deslizante. A ideia é que",
    "dossel fechado é irregular, com sombra, então tem desvio alto; pasto é homogêneo, desvio",
    "baixo. Eu preciso ser honesta: isso é hipótese da literatura e AINDA NÃO foi validada",
    "por nós. Está declarado assim no trabalho.\"",
    "",
    "PASSA PARA O JONATHAN.",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 12 — 3.a Os filtros escolhidos
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "3.a · Os filtros escolhidos, e a função de cada um",
    sub: "Cada filtro entra porque resolve um problema concreto da cadeia, e sai um passo antes de onde atrapalharia",
    quem: "Jonathan Aparecido X Martins  ·  capítulo 3.a" });

  const escolhidos = [
    ["Realce espectral", "Índice de vegetação\nNDVI; NBR quando há SWIR 2", "Reduz as bandas a um mapa escalar onde vegetação e solo exposto ficam em extremos opostos"],
    ["Suavização", "Gaussiano 5 × 5", "Impede que o ruído do sensor atravesse o limiar pixel a pixel"],
    ["Limiarização", "Otsu sobre o histograma conjunto", "Separa vegetação de não-vegetação com a mesma régua nas duas datas"],
    ["Limpeza", "Abertura seguida de fechamento", "Remove respingos isolados e fecha buracos internos"],
    ["Contorno", "Gradiente morfológico", "Extrai a borda das regiões para exibição"],
    ["Realce de borda", "Sobel — magnitude do gradiente", "Torna visível a fronteira floresta/corte"],
    ["Textura", "Desvio-padrão local 5 × 5", "Descritor para a etapa de modelo"],
  ];
  const alturaLinha = 0.62;
  s.addText("Etapa", { x: MARGEM + 0.15, y: 1.95, w: 2.2, h: 0.3, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 11, bold: true, color: COR.suave, charSpacing: 0.8 });
  s.addText("Filtro", { x: MARGEM + 2.5, y: 1.95, w: 3.3, h: 0.3, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 11, bold: true, color: COR.suave, charSpacing: 0.8 });
  s.addText("Por que está aqui", { x: MARGEM + 6.0, y: 1.95, w: 5.9, h: 0.3, isTextBox: true,
    margin: 0, fontFace: CORPO, fontSize: 11, bold: true, color: COR.suave, charSpacing: 0.8 });

  escolhidos.forEach(([etapa, filtro, porque], i) => {
    const y = 2.3 + i * alturaLinha;
    if (i % 2 === 0) cartao(s, { x: MARGEM, y, w: LARGURA, h: alturaLinha - 0.06 });
    s.addText(etapa, { x: MARGEM + 0.15, y: y + 0.06, w: 2.2, h: 0.44, isTextBox: true,
      margin: 0, fontFace: TIT, fontSize: 13, bold: true, color: COR.floresta, valign: "middle" });
    s.addText(filtro, { x: MARGEM + 2.5, y: y + 0.03, w: 3.3, h: 0.5, isTextBox: true,
      margin: 0, fontFace: CORPO, fontSize: 12, bold: true, color: COR.texto,
      valign: "middle", lineSpacingMultiple: 1.0 });
    s.addText(porque, { x: MARGEM + 6.0, y: y + 0.03, w: 5.9, h: 0.5, isTextBox: true,
      margin: 0, fontFace: CORPO, fontSize: 12, color: COR.texto, valign: "middle" });
  });

  s.addNotes([
    "JONATHAN — os filtros escolhidos (1 min 15 s)",
    "",
    "\"Agora o capítulo 3, que é a nossa proposta. A Isabel mostrou o que existe; eu mostro o",
    "que a gente escolheu e por quê.\"",
    "",
    "\"E o 'por quê' importa: a escolha não foi por catálogo. Cada filtro entrou porque",
    "resolve um problema concreto que aparece na cadeia.\"",
    "",
    "\"Primeiro o índice de vegetação, que reduz várias bandas a um mapa escalar onde",
    "vegetação e solo exposto ficam em extremos opostos. Depois o gaussiano 5 por 5, pelo",
    "motivo que a Isabel explicou: sem ele o ruído atravessa o limiar.\"",
    "",
    "\"Aí vem o Otsu sobre o histograma CONJUNTO das duas datas — e o 'conjunto' é uma decisão",
    "nossa, que eu explico no próximo slide. Depois a limpeza morfológica: abertura tira",
    "respingo isolado, fechamento tapa buraco interno.\"",
    "",
    "\"O gradiente morfológico extrai o contorno das regiões para exibir. O Sobel torna",
    "visível a fronteira entre floresta e corte. E o desvio-padrão local é o descritor de",
    "textura que vai para a etapa de modelo.\"",
    "",
    "\"A frase de baixo resume a lógica: cada filtro sai um passo antes de onde ele",
    "atrapalharia. A ORDEM faz parte da proposta, não é acidente.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 13 — 3.a Efeito na cena real
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "3.a · O efeito de cada filtro, na cena real",
    sub: "Enunciado, p. 3, item 3.a: o resultado dos filtros deve ser apresentado e analisado",
    quem: "Jonathan Aparecido X Martins  ·  capítulo 3.a" });

  imagem(s, join(FIG, "efeito-dos-filtros.png"), { x: MARGEM, y: 1.88, w: 8.6, h: 4.9 });

  const notas = [
    ["NBR bruto", "O índice já separa: amarelo é solo exposto, verde é vegetação. Mas o granulado é ruído do sensor, e é ele que estragaria o limiar."],
    ["Gaussiano e mediana", "O ruído sai e a estrutura fica. A borda do corte continua no lugar — é isso que a suavização precisa preservar."],
    ["Sobel e textura", "O gradiente acende no contorno do corte e no rio. O desvio-padrão local responde ao mesmo contorno por outro caminho."],
  ];
  notas.forEach(([titulo, texto], i) => {
    const y = 1.9 + i * 1.42;
    s.addText(titulo, { x: 9.42, y, w: 3.3, h: 0.34, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 16, bold: true, color: COR.floresta });
    s.addText(texto, { x: 9.42, y: y + 0.38, w: 3.3, h: 1.0, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 12.5, color: COR.texto, lineSpacingMultiple: 1.12 });
  });

  cartao(s, { x: 9.42, y: 6.02, w: 3.3, h: 0.78 });
  s.addText("São Félix do Xingu (PA), 2024 · MODIS/Terra via NASA GIBS · recorte de 200 × 200 px", {
    x: 9.6, y: 6.12, w: 2.96, h: 0.6, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 11, italic: true, color: COR.suave });

  s.addNotes([
    "JONATHAN — efeito dos filtros (1 min)",
    "",
    "\"E aqui estão os filtros rodando de verdade, sobre um recorte da cena real de 2024.",
    "Isso não é ilustração de livro: é a saída do nosso código.\"",
    "",
    "\"Em cima, à esquerda, a cor natural. Ao lado, o índice NBR bruto: o amarelo é solo",
    "exposto, o verde é vegetação. O índice já separa bem — mas olhem o granulado. Aquilo é",
    "ruído do sensor, e é exatamente o que estragaria a limiarização.\"",
    "",
    "\"O terceiro painel é o gaussiano 5 por 5. Comparem com o do lado: o granulado sumiu e a",
    "estrutura continua lá. Embaixo à esquerda, a mediana, que faz um trabalho parecido por",
    "outro caminho.\"",
    "",
    "\"E os dois últimos são o realce de borda e a textura. O Sobel acende no contorno do",
    "corte e no rio. O desvio-padrão local responde ao mesmo contorno, mas por variação local",
    "em vez de derivada.\"",
    "",
    "\"O enunciado pede que o resultado dos filtros seja apresentado E ANALISADO. É isso que",
    "este slide faz: cada painel tem uma razão de estar na cadeia, e dá para ver o efeito.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 14 — 3.a Suavizar antes de limiarizar
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "3.a · A ordem não é indiferente",
    quem: "Jonathan Aparecido X Martins  ·  capítulo 3.a" });

  cartao(s, { x: MARGEM, y: 1.55, w: 6.2, h: 2.5 });
  s.addText("Suavizar antes de limiarizar", { x: MARGEM + 0.32, y: 1.7, w: 5.56, h: 0.4,
    isTextBox: true, margin: 0, fontFace: TIT, fontSize: 20, bold: true, color: COR.floresta });
  s.addText("Suavizar depois da limiarização operaria sobre uma máscara binária — seria morfologia, não filtragem — e não recuperaria a informação já destruída pelo limiar. O ruído precisa ser atenuado enquanto o dado ainda é contínuo.", {
    x: MARGEM + 0.32, y: 2.2, w: 5.56, h: 1.7, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 15, color: COR.texto, lineSpacingMultiple: 1.2 });

  cartao(s, { x: 7.2, y: 1.55, w: 5.52, h: 2.5, escuro: true });
  s.addText("O efeito de omitir esse passo é mensurável", { x: 7.5, y: 1.68, w: 4.92, h: 0.62,
    isTextBox: true, margin: 0, fontFace: TIT, fontSize: 18, bold: true, color: COR.branco });
  s.addText("Sem suavização a máscara sai esburacada e a contagem de componentes conexos explode. O sistema reportaria centenas de regiões de poucos pixels onde existe uma só, inviabilizando a análise por região que o capítulo 1 justificou como necessária.", {
    x: 7.5, y: 2.36, w: 4.92, h: 1.56, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 14, color: COR.musgo, lineSpacingMultiple: 1.2 });

  s.addText("Por que os filtros foram implementados pelo grupo", {
    x: MARGEM, y: 4.28, w: LARGURA, h: 0.4, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 20, bold: true, color: COR.floresta });

  const razoes = [
    ["É exigência do enunciado", "Página 3, item 3.a: “Os filtros devem ser desenvolvidos pelo grupo.”"],
    ["É o que permite defender o trabalho", "Uma chamada a cv2.GaussianBlur não permite responder o que acontece na borda, por que o núcleo é normalizado, ou por que convolução difere de correlação."],
    ["A restrição é verificável", "Dentro de sentinela/pdi a única dependência permitida é o NumPy, e a ausência de cv2, skimage, scipy e PIL é conferida por inspeção do código."],
  ];
  const w = (LARGURA - 2 * 0.24) / 3;
  razoes.forEach(([titulo, texto], i) => {
    const x = MARGEM + i * (w + 0.24);
    cartao(s, { x, y: 4.78, w, h: 1.85 });
    numero(s, i + 1, { x: x + 0.26, y: 4.98, d: 0.46 });
    s.addText(titulo, { x: x + 0.86, y: 4.96, w: w - 1.1, h: 0.5, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 15, bold: true, color: COR.floresta, valign: "middle" });
    s.addText(texto, { x: x + 0.28, y: 5.56, w: w - 0.56, h: 1.0, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 12.5, color: COR.texto, lineSpacingMultiple: 1.12 });
  });

  s.addNotes([
    "JONATHAN — a ordem e a autoria (1 min)",
    "",
    "\"Duas coisas para fechar a proposta.\"",
    "",
    "\"A primeira é a ordem. Pode parecer indiferente suavizar antes ou depois do limiar, e",
    "não é. Suavizar DEPOIS estaria operando sobre uma máscara binária — aquilo já seria",
    "morfologia, não filtragem — e não recupera a informação que o limiar destruiu. O ruído",
    "tem que ser atenuado enquanto o dado ainda é contínuo.\"",
    "",
    "\"E o efeito de pular esse passo é mensurável: a máscara sai esburacada e a contagem de",
    "componentes conexos explode. Voltamos ao capítulo 1: a análise por região era um",
    "requisito ecológico, e ela morre se a máscara estiver cheia de buraco.\"",
    "",
    "\"A segunda é por que a gente implementou os filtros. Primeiro porque o enunciado exige,",
    "na página 3. Mas tem uma razão prática que a gente sentiu: uma chamada a",
    "cv2.GaussianBlur não permite responder o que acontece na borda, por que o núcleo é",
    "normalizado, ou por que convolução difere de correlação. Com o código no repositório,",
    "cada uma dessas perguntas tem resposta em uma linha.\"",
    "",
    "\"E a restrição é verificável, não é promessa: dentro da pasta pdi a única dependência",
    "permitida é o NumPy, e a ausência de cv2, skimage, scipy e PIL é conferida por inspeção.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 15 — O que vem na Fase II
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "O que vem na Fase Intermediária II", escuro: true,
    sub: "Esta qualificação fecha o que precisa estar decidido antes do desenvolvimento prático",
    quem: "Jonathan Aparecido X Martins  ·  encerramento" });

  const etapas = [
    ["Segmentação", "Otsu conjunto, morfologia e rotulagem de componentes conexos: transformar o índice filtrado em regiões com forma e área."],
    ["Quantificação", "Converter pixels em hectares a partir da resolução espacial, e descrever cada região individualmente."],
    ["Preparação dos dados", "Recortar a cena, rotular os recortes pela máscara de segmentação e extrair os descritores."],
    ["Modelo e avaliação", "Treinar o classificador sobre os recortes rotulados e medir o desempenho sem superestimá-lo."],
  ];
  const w = (LARGURA - 3 * 0.22) / 4;
  etapas.forEach(([titulo, texto], i) => {
    const x = MARGEM + i * (w + 0.22);
    cartao(s, { x, y: 2.05, w, h: 2.7, escuro: true });
    numero(s, i + 1, { x: x + w / 2 - 0.27, y: 2.28, d: 0.54, cor: COR.musgo });
    s.addText(titulo, { x: x + 0.12, y: 2.98, w: w - 0.24, h: 0.4, isTextBox: true, margin: 0,
      align: "center", fontFace: TIT, fontSize: 16, bold: true, color: COR.branco });
    s.addText(texto, { x: x + 0.2, y: 3.44, w: w - 0.4, h: 1.2, isTextBox: true, margin: 0,
      align: "center", fontFace: CORPO, fontSize: 12.5, color: COR.musgo, lineSpacingMultiple: 1.12 });
  });

  s.addText("O capítulo 1 já definiu o que o sistema precisa produzir. O capítulo 2 fixou os conceitos. O capítulo 3.a escolheu os filtros e a ordem. O que falta é executar.", {
    x: 1.8, y: 5.1, w: L - 3.6, h: 0.75, isTextBox: true, margin: 0, align: "center",
    fontFace: CORPO, fontSize: 15, italic: true, color: COR.musgo, lineSpacingMultiple: 1.15 });

  s.addText("Obrigado. Perguntas?", {
    x: MARGEM, y: 5.95, w: LARGURA, h: 0.6, isTextBox: true, margin: 0, align: "center",
    fontFace: TIT, fontSize: 28, bold: true, color: COR.branco });

  s.addNotes([
    "JONATHAN — encerramento (35 s)",
    "",
    "\"Fechando: esta qualificação entrega o que precisa estar decidido ANTES do",
    "desenvolvimento prático.\"",
    "",
    "\"O capítulo 1 definiu o problema como bi-temporal, mostrou por que ele importa e — o",
    "que talvez seja o mais útil — mostrou que a análise precisa ser por REGIÃO, não só por",
    "área total. O capítulo 2 fixou os conceitos de filtragem. E o 3.a escolheu quais filtros",
    "entram, em que ordem, e por quê.\"",
    "",
    "\"O que vem na Fase II é a execução: segmentação, quantificação em hectares, preparação",
    "dos recortes rotulados, e o modelo com a avaliação.\"",
    "",
    "\"Obrigado. Estamos à disposição para perguntas — e qualquer um de nós responde sobre",
    "qualquer parte.\"",
    "",
    "SE SOBRAR TEMPO ou se pedirem para ver rodando: o próximo slide é reserva, e a Isabel",
    "abre o programa na aba de filtragem.",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 16 — Reserva: os filtros rodando no programa
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Reserva · os filtros rodando no programa",
    sub: "Só se houver tempo ou se for pedido — a demonstração completa é da Fase II",
    quem: "Isabel Da Silva  ·  slide de reserva" });

  imagem(s, join(FIG, "telas/tela-filtragem.png"), { x: MARGEM, y: 1.88, w: 5.25, h: 4.9 });

  s.addText("O protótipo já aplica os filtros deste capítulo sobre o par de datas e exibe o efeito de cada etapa separadamente.", {
    x: 6.3, y: 1.95, w: 6.42, h: 0.7, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 15, color: COR.texto, lineSpacingMultiple: 1.15 });

  itens(s, [
    "À esquerda, o índice bruto; no centro, o gaussiano 5 × 5; à direita, a magnitude do gradiente de Sobel.",
    "Os painéis de baixo já são segmentação — conteúdo da Fase II, mostrado aqui só para situar onde a filtragem entra na cadeia.",
    "A aplicação roda em localhost e não depende de internet.",
  ], { x: 6.3, y: 2.8, w: 6.42, h: 2.2, fontSize: 14 });

  cartao(s, { x: 6.3, y: 5.05, w: 6.42, h: 1.62 });
  s.addText("Como abrir, se for pedido", { x: 6.55, y: 5.18, w: 5.92, h: 0.34, isTextBox: true,
    margin: 0, fontFace: TIT, fontSize: 16, bold: true, color: COR.floresta });
  s.addText("sentinela app        →  aba “Etapas do processamento”", {
    x: 6.55, y: 5.56, w: 5.92, h: 0.34, isTextBox: true, margin: 0,
    fontFace: "Courier New", fontSize: 12.5, color: COR.texto });
  s.addText("Deixar o navegador já aberto antes de começar. Se a interface não subir, o plano B é a linha de comando: sentinela demo --tamanho 200 --area 80", {
    x: 6.55, y: 5.98, w: 5.92, h: 0.6, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 12, italic: true, color: COR.suave, lineSpacingMultiple: 1.1 });

  s.addNotes([
    "ISABEL — slide de reserva (só se pedirem, 1 min)",
    "",
    "NÃO apresentar por padrão. Este slide existe para o caso de sobrar tempo ou de alguém",
    "pedir para ver o programa. A demonstração completa é da Fase II.",
    "",
    "\"O protótipo já existe e já aplica esses filtros. Aqui está a aba de etapas do",
    "processamento.\"",
    "",
    "\"À esquerda o índice bruto, no meio o gaussiano 5 por 5, à direita o Sobel. É a mesma",
    "sequência que a gente acabou de descrever, rodando.\"",
    "",
    "\"Os painéis de baixo já são segmentação, que é conteúdo da próxima fase — estou",
    "mostrando só para situar onde a filtragem entra na cadeia.\"",
    "",
    "ANTES: deixar o navegador já aberto em localhost:8501. Não subir o servidor ao vivo.",
  ].join("\n"));
}

}

// ======================================================================================
// Fase Intermediária II — Defesa: protótipo e resultados
// ======================================================================================

function deckDefesa() {

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
    "ANDRÉ — abertura (20 s)",
    "",
    "\"Boa noite. Nós somos o grupo do tema de sustentabilidade ambiental: detecção e",
    "quantificação de desmatamento em imagens de satélite.\"",
    "",
    "\"Eu sou o André, e comigo estão o Enzo, a Isabel e o Jonathan. Cada um de nós",
    "apresenta uma parte, e todos respondem perguntas sobre qualquer parte.\"",
    "",
    "\"São treze minutos: o problema, como o sistema funciona, o programa rodando ao vivo",
    "e os resultados — inclusive um resultado que foi uma recusa, e vamos explicar por quê.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 2 — Roteiro
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "O que vamos mostrar",
    sub: "As três partes que o enunciado exige da apresentação (seção III, item 2)",
    quem: "André Massarente" });

  const blocos = [
    ["1", "Explicação do problema e contexto",
      "Por que desmatamento não se detecta numa imagem só, e o que o programa se propõe a fazer.",
      "André Massarente  ·  Enzo Consani"],
    ["2", "Demonstração da aplicação",
      "O programa rodando: as cinco etapas, a quantificação e a recusa, ao vivo.",
      "Isabel Da Silva"],
    ["3", "Discussão dos resultados",
      "O que funcionou, o que o sistema recusou medir e por que a recusa está certa.",
      "Jonathan Aparecido X Martins"],
  ];

  blocos.forEach(([n, titulo, texto, quem], i) => {
    const y = 1.85 + i * 1.62;
    cartao(s, { x: MARGEM, y, w: LARGURA, h: 1.4 });
    numero(s, n, { x: MARGEM + 0.34, y: y + 0.44, d: 0.52 });
    s.addText(titulo, { x: MARGEM + 1.12, y: y + 0.2, w: 7.2, h: 0.38, isTextBox: true,
      margin: 0, fontFace: TIT, fontSize: 19, bold: true, color: COR.floresta });
    s.addText(texto, { x: MARGEM + 1.12, y: y + 0.62, w: 7.3, h: 0.6, isTextBox: true,
      margin: 0, fontFace: CORPO, fontSize: 13.5, color: COR.texto });
    s.addText(quem, { x: 9.25, y: y + 0.52, w: 2.65, h: 0.4, isTextBox: true, margin: 0,
      align: "right", fontFace: CORPO, fontSize: 12, bold: true, color: COR.suave });
  });

  s.addNotes([
    "ANDRÉ — roteiro (25 s)",
    "",
    "\"A apresentação segue exatamente as três partes pedidas no manual da APS.\"",
    "",
    "\"Primeiro o problema e o contexto — eu começo e o Enzo continua explicando como o",
    "sistema funciona por dentro. Depois a Isabel mostra o programa rodando. No fim o",
    "Jonathan discute os resultados.\"",
    "",
    "\"Guardem uma frase: o resultado mais importante deste trabalho foi o programa se",
    "recusar a dar um número. No final a gente explica por que isso é um acerto.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 3 — O problema
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Desmatamento se vê entre duas datas, não numa imagem",
    quem: "André Massarente  ·  problema e contexto" });
  imagem(s, join(FIG, "comparativo-real.png"), { x: MARGEM, y: 1.5, w: 4.75, h: 5.15 });

  s.addText("Uma cena só não distingue pasto de trinta anos de corte do mês passado. A informação está na diferença entre duas datas.", {
    x: 5.65, y: 1.62, w: 7.06, h: 0.95, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 16, color: COR.texto, lineSpacingMultiple: 1.15,
  });

  cartao(s, { x: 5.65, y: 2.78, w: 7.06, h: 1.62 });
  s.addText("São Félix do Xingu (PA)", { x: 5.95, y: 2.95, w: 6.5, h: 0.34, isTextBox: true,
    margin: 0, fontFace: TIT, fontSize: 17, bold: true, color: COR.floresta });
  itens(s, [
    "MODIS/Terra, composição de refletância corrigida, via NASA GIBS — domínio público",
    "Duas datas: 2002-07-01 e 2024-07-05, mesmo recorte, mesma estação do ano",
    "Grade de ≈253 metros por pixel · recorte de 440 × 440 pixels",
  ], { x: 5.95, y: 3.3, w: 6.5, h: 1.0, fontSize: 12.5 });

  s.addText("O custo de errar é assimétrico nas duas direções", {
    x: 5.65, y: 4.62, w: 7.06, h: 0.34, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 17, bold: true, color: COR.floresta });
  s.addText([
    { text: "Falso positivo", options: { bold: true, breakLine: false } },
    { text: "  aciona fiscalização sobre quem não desmatou.", options: { breakLine: true } },
    { text: "Falso negativo", options: { bold: true, breakLine: false } },
    { text: "  deixa o corte passar e a floresta não volta.", options: {} },
  ], { x: 5.65, y: 4.98, w: 7.06, h: 0.9, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 14, color: COR.texto, lineSpacingMultiple: 1.2 });

  s.addText("Por isso o sistema prefere não responder a responder errado — é a decisão que aparece no slide 10.", {
    x: 5.65, y: 5.95, w: 7.06, h: 0.7, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 13, italic: true, color: COR.alerta });

  s.addNotes([
    "ANDRÉ — o problema (2 min)",
    "",
    "\"Esta é a mesma região da Amazônia em duas datas: 2002 em cima à esquerda, 2024 à",
    "direita. Embaixo, o mesmo recorte no índice NBR, em falsa cor — o verde escuro é",
    "vegetação densa, o amarelo é solo exposto.\"",
    "",
    "\"Olhando só a imagem de 2024, eu não sei o que é pasto antigo e o que é corte",
    "recente. As duas coisas são claras na imagem. A informação de desmatamento não está",
    "numa imagem: está na DIFERENÇA entre duas datas. É daí que sai todo o desenho do",
    "sistema.\"",
    "",
    "\"As imagens são reais, do satélite Terra da NASA, obtidas pelo serviço GIBS. São de",
    "domínio público e a procedência está registrada no trabalho escrito: produto, data,",
    "coordenadas, licença e URL.\"",
    "",
    "\"Por que isso importa: fiscalizar a Amazônia inteira a olho é impossível. Detecção",
    "automática não substitui o fiscal — ela diz onde olhar primeiro.\"",
    "",
    "\"E errar custa caro dos dois lados. Se o sistema aponta desmatamento onde não houve,",
    "alguém é punido injustamente. Se deixa passar, a floresta não volta. Guardem essa",
    "frase, porque ela volta no final da apresentação.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 4 — Objetivo
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "O objetivo: preparar dados, não classificar imagem",
    quem: "André Massarente  ·  problema e contexto" });

  cartao(s, { x: MARGEM, y: 1.55, w: LARGURA, h: 1.55, escuro: true });
  s.addText("“…propor uma solução baseada em processamento de imagens para preparação dos dados, de modo que a posteriori, estes possam alimentar modelos de visão computacional.”", {
    x: MARGEM + 0.45, y: 1.72, w: LARGURA - 0.9, h: 0.95, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 18, italic: true, color: COR.branco, lineSpacingMultiple: 1.1,
  });
  s.addText("Manual da APS 2026/2 — Objetivo, p. 2", {
    x: MARGEM + 0.45, y: 2.66, w: LARGURA - 0.9, h: 0.3, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 11.5, color: COR.musgo });

  const colunas = [
    ["O que o PDI entrega aqui", [
      "A máscara de perda de vegetação, calculada entre duas datas",
      "Os recortes de imagem já rotulados por essa máscara",
      "Quinze descritores por recorte, todos calculados pelo nosso código",
    ]],
    ["O que o modelo faz com isso", [
      "Aprende a separar desmatado de intacto a partir dos recortes",
      "Passa a classificar recortes novos sem precisar do par de datas",
      "Só existe porque a etapa de PDI produziu o rótulo",
    ]],
  ];
  colunas.forEach(([titulo, lista], i) => {
    const x = MARGEM + i * (LARGURA / 2 + 0.16);
    const w = LARGURA / 2 - 0.16;
    s.addText(titulo, { x, y: 3.45, w, h: 0.4, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 19, bold: true, color: COR.floresta });
    itens(s, lista, { x, y: 3.95, w, h: 1.9, fontSize: 14.5 });
  });

  cartao(s, { x: MARGEM, y: 5.9, w: LARGURA, h: 0.82 });
  s.addText([
    { text: "Restrição central do enunciado:  ", options: { bold: true } },
    { text: "“Os filtros devem ser desenvolvidos pelo grupo” (p. 3, item 3.a). Dentro do núcleo de PDI a única dependência é o NumPy — nenhum OpenCV, nenhum scikit-image, nenhum scipy.ndimage." },
  ], { x: MARGEM + 0.35, y: 6.0, w: LARGURA - 0.7, h: 0.62, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 13, color: COR.texto, lineSpacingMultiple: 1.1 });

  s.addNotes([
    "ANDRÉ — objetivo e abordagem (1 min)",
    "",
    "\"Essa frase é do enunciado, e ela decide o projeto inteiro: o processamento de",
    "imagens aqui é PREPARAÇÃO DE DADOS. Ele não é o produto final.\"",
    "",
    "\"Na prática: o PDI compara as duas datas e produz uma máscara de perda de vegetação.",
    "Essa máscara vira o RÓTULO dos recortes de imagem. Os recortes rotulados treinam um",
    "classificador, que depois consegue olhar um recorte novo sem precisar do par de",
    "datas. O modelo só existe porque a etapa de PDI gerou o rótulo.\"",
    "",
    "\"E uma restrição que vale a pena registrar agora: o enunciado exige que os filtros",
    "sejam desenvolvidos pelo grupo. Então dentro do nosso núcleo de processamento a única",
    "biblioteca é o NumPy. Não tem OpenCV, não tem scikit-image, não tem scipy. O Enzo vai",
    "mostrar os filtros funcionando no próximo slide.\"",
    "",
    "PASSA PARA O ENZO.",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 5 — As cinco etapas
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "As cinco etapas, e onde cada uma mora no código",
    sub: "A arquitetura do programa espelha a sequência nomeada pelo enunciado (p. 3, item 2.e)",
    quem: "Enzo Consani  ·  como o sistema funciona" });

  const etapas = [
    ["Aquisição", "Baixa o par de datas do NASA GIBS e mede a qualidade da cena.", "dataio/"],
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

  s.addText("Cada etapa guarda o resultado intermediário: a interface mostra o efeito de um filtro por vez, e o trabalho escrito reproduz a mesma sequência.", {
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
    "Isabel vai mostrar etapa por etapa na tela.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 6 — Os filtros são nossos
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Os filtros foram implementados pelo grupo",
    sub: "Cada painel abaixo sai de sentinela/pdi, escrito com NumPy — sobre a cena real de 2024",
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
  s.addText("340 testes automatizados, contra casos analíticos — não contra a saída de outra biblioteca.", {
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
    "\"E os testes: 340 no total. Eles não comparam com OpenCV — comparam com casos",
    "analíticos. Convolução com núcleo identidade devolve a imagem original; Sobel numa",
    "rampa linear devolve gradiente constante; Otsu numa imagem bimodal cai entre os dois",
    "modos.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 7 — Decisão 1 e 2
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Duas decisões que mudam o resultado",
    quem: "Enzo Consani  ·  como o sistema funciona" });

  const decisoes = [
    ["1", "Suavizar antes de limiarizar",
      "O limiar é aplicado pixel a pixel. Sem o gaussiano, o ruído do dossel atravessa o corte em pontos isolados e a máscara sai esburacada — o programa relata centenas de “regiões” onde existe uma só.",
      "Suavizar depois não resolve: a informação já foi destruída na binarização."],
    ["2", "Um limiar único para as duas datas",
      "Rodar Otsu em cada data produz duas réguas diferentes. A comparação passaria a medir a diferença entre os limiares, não a diferença no terreno.",
      "Solução: Otsu sobre o histograma conjunto das duas datas. Uma régua só, aplicada aos dois lados."],
  ];
  decisoes.forEach(([n, titulo, texto, fecho], i) => {
    const x = MARGEM + i * (LARGURA / 2 + 0.16);
    const w = LARGURA / 2 - 0.16;
    cartao(s, { x, y: 1.55, w, h: 4.95 });
    numero(s, n, { x: x + 0.34, y: 1.85, d: 0.55 });
    s.addText(titulo, { x: x + 1.02, y: 1.82, w: w - 1.32, h: 0.72, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 19, bold: true, color: COR.floresta, valign: "middle" });
    s.addText(texto, { x: x + 0.36, y: 2.66, w: w - 0.72, h: 2.0, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 14.5, color: COR.texto, lineSpacingMultiple: 1.18 });
    s.addText(fecho, { x: x + 0.36, y: 4.9, w: w - 0.72, h: 1.3, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 13.5, italic: true, color: COR.floresta, lineSpacingMultiple: 1.15 });
  });

  s.addText("pdi/filtros.py · pdi/limiar.py — otsu_conjunto", {
    x: MARGEM, y: 6.62, w: LARGURA, h: 0.3, isTextBox: true, margin: 0, align: "center",
    fontFace: "Courier New", fontSize: 11, color: COR.suave });

  s.addNotes([
    "ENZO — decisões 1 e 2 (1 min)",
    "",
    "\"Duas decisões de projeto que mudam o resultado, e que a gente consegue defender.\"",
    "",
    "\"Primeira: suavizar ANTES de limiarizar. O limiar é uma comparação pixel a pixel. Se",
    "a imagem chega com ruído, cada pixel de ruído que passa do corte vira um ponto isolado",
    "na máscara. O programa então rotula centenas de regiõezinhas onde na verdade existe uma",
    "área só. E não adianta suavizar depois — depois de binarizar a informação já se perdeu.\"",
    "",
    "\"Segunda: um limiar único para as duas datas. Isso parece detalhe e não é. Se a gente",
    "roda Otsu separado em 2002 e em 2024, cada data ganha uma régua própria. Aí a",
    "comparação entre as duas máscaras passa a medir a diferença entre as REGRAS, não a",
    "diferença no terreno. A solução foi juntar os dois histogramas e calcular um limiar só,",
    "que é aplicado dos dois lados.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 8 — Decisão 3: recusa
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Decisão 3: o sistema sabe quando não sabe",
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
// 9 — Do PDI ao modelo
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Da máscara ao modelo de visão computacional",
    sub: "É aqui que o processamento de imagens vira dado de treino — o objetivo literal do enunciado",
    quem: "Enzo Consani  ·  como o sistema funciona" });

  const passos = [
    ["Recortar", "A cena é dividida em recortes de 16 × 16 pixels, com sobreposição."],
    ["Rotular", "Cada recorte recebe a classe pela cobertura da máscara: acima de 60% é desmatado, abaixo de 5% é intacto. O meio é descartado."],
    ["Descrever", "Quinze descritores por recorte — média e desvio de cada canal, índices, brilho e textura — todos calculados por pdi/."],
    ["Treinar", "Floresta aleatória do scikit-learn, que o enunciado permite: ela entra só como algoritmo de aprendizado."],
  ];
  const w = (LARGURA - 3 * 0.22) / 4;
  passos.forEach(([titulo, texto], i) => {
    const x = MARGEM + i * (w + 0.22);
    cartao(s, { x, y: 2.05, w, h: 2.55 });
    numero(s, i + 1, { x: x + 0.26, y: 2.28, d: 0.5 });
    s.addText(titulo, { x: x + 0.9, y: 2.3, w: w - 1.1, h: 0.46, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 17, bold: true, color: COR.floresta, valign: "middle" });
    s.addText(texto, { x: x + 0.28, y: 2.94, w: w - 0.56, h: 1.5, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 12.5, color: COR.texto, lineSpacingMultiple: 1.12 });
  });

  cartao(s, { x: MARGEM, y: 4.88, w: LARGURA, h: 1.55, escuro: true });
  s.addText("Treino e teste são separados por blocos da imagem, não por sorteio de recorte", {
    x: MARGEM + 0.42, y: 5.05, w: LARGURA - 0.84, h: 0.4, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 18, bold: true, color: COR.branco });
  s.addText("Os recortes se sobrepõem. Sortear um a um colocaria o mesmo pedaço de terreno nos dois lados da divisão, e a acurácia medida seria vazamento de dados, não desempenho. Recortes que cruzam a fronteira de bloco são descartados.", {
    x: MARGEM + 0.42, y: 5.5, w: LARGURA - 0.84, h: 0.85, isTextBox: true, margin: 0,
    fontFace: CORPO, fontSize: 14, color: COR.musgo, lineSpacingMultiple: 1.15 });

  s.addNotes([
    "ENZO — do PDI ao modelo (50 s)",
    "",
    "\"Essa é a ponte entre as duas metades do trabalho. A máscara que o PDI produziu vira",
    "o rótulo do conjunto de treino.\"",
    "",
    "\"A cena é recortada em pedaços de 16 por 16. Cada recorte olha quanto da sua área está",
    "marcada na máscara: mais de 60 por cento, é desmatado; menos de 5 por cento, é intacto.",
    "O que cai no meio a gente joga fora de propósito — rótulo duvidoso ensina coisa errada.\"",
    "",
    "\"De cada recorte saem quinze descritores, e todos são calculados pelo nosso código de",
    "PDI. Se o professor perguntar de onde vem a textura, a resposta é desvio-padrão local,",
    "e o algoritmo está no repositório. O scikit-learn entra só no algoritmo de aprendizado,",
    "que é o que o enunciado permite.\"",
    "",
    "\"E o detalhe embaixo, que é o erro mais comum nesse tipo de trabalho: a divisão entre",
    "treino e teste é POR BLOCO da imagem, não por sorteio. Como os recortes se sobrepõem,",
    "sortear um a um colocaria o mesmo pedaço de terreno nos dois lados. A acurácia ficaria",
    "linda e seria vazamento.\"",
    "",
    "PASSA PARA A ISABEL.",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 10 — Demonstração
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Demonstração da aplicação", escuro: true,
    sub: "O programa roda em localhost e não depende de internet",
    quem: "Isabel Da Silva  ·  demonstração" });

  const passos = [
    ["Cena sintética", "Área desmatada de tamanho conhecido — rotulada como sintética na tela."],
    ["As cinco etapas", "Índice bruto, gaussiano, Sobel e o mapa de mudança, um painel por etapa."],
    ["A quantificação", "400 pixels construídos, 400 pixels detectados — e o valor em hectares."],
    ["A recusa", "Zerar a área desmatada: duas datas iguais, e o programa se recusa a responder."],
    ["O modelo", "Os recortes rotulados treinam o classificador — com o aviso que vem junto."],
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

  s.addText("Se a interface não abrir, o plano B é a linha de comando: sentinela demo --tamanho 200 --area 80 --modelo", {
    x: MARGEM, y: 5.95, w: LARGURA, h: 0.4, isTextBox: true, margin: 0, align: "center",
    fontFace: CORPO, fontSize: 13, italic: true, color: COR.musgo });

  s.addNotes([
    "ISABEL — abertura da demonstração (25 s)",
    "",
    "ANTES DE COMEÇAR: o navegador já tem que estar aberto em localhost:8501, com a cena",
    "sintética carregada, tamanho da cena em 80 e lado da área desmatada em 20. NÃO subir o",
    "servidor ao vivo.",
    "",
    "\"Agora o programa rodando. Ele é uma aplicação local, roda no navegador e não precisa",
    "de internet — o que a gente mostra aqui funciona offline.\"",
    "",
    "\"O roteiro é esse: começo pela cena sintética, mostro as cinco etapas por dentro,",
    "mostro a quantificação batendo com a verdade de terreno, depois mostro o programa se",
    "recusando a responder, e termino no modelo.\"",
    "",
    "\"Por que cena sintética e não a imagem de satélite: porque na cena sintética eu SEI",
    "qual é a resposta certa. É assim que a gente confere se a quantificação funciona. A",
    "imagem real vem no bloco do Jonathan.\"",
    "",
    "[TROCAR PARA O NAVEGADOR]",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 11 — Tela: filtragem e segmentação
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Etapa por etapa, na tela",
    sub: "Aba “Etapas do processamento” — a mesma tela que aparece na demonstração ao vivo",
    quem: "Isabel Da Silva  ·  demonstração" });

  imagem(s, join(FIG, "telas/tela-filtragem.png"), { x: MARGEM, y: 1.88, w: 5.25, h: 4.92 });

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
    "ISABEL — etapas na tela (1 min 30 s, ao vivo)",
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
    quem: "Isabel Da Silva  ·  demonstração" });

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
    "ISABEL — quantificação e recusa (2 min, ao vivo)",
    "",
    "\"Agora a quantificação. A cena foi construída com um corte de 20 por 20 pixels, o que",
    "dá 400 pixels. O programa detectou 400. Erro de zero por cento. E o próprio programa",
    "mostra a verdade de terreno ali embaixo, para dar para conferir.\"",
    "",
    "\"Ao lado, os 400 pixels convertidos em hectares. Isso depende da resolução: a 10",
    "metros por pixel, que é o Sentinel-2, dá 4 hectares. A escala é escolhida ali na barra",
    "lateral, e é assim que se sai de pixel para área de verdade.\"",
    "",
    "\"Mas eu preciso ser honesta sobre o que esse número prova: ele prova que a CADEIA",
    "funciona de ponta a ponta. Ele não prova desempenho no mundo real, porque quem",
    "construiu a separação entre floresta e corte foi o gerador da cena. Por isso a tela",
    "avisa em azul que a imagem é sintética.\"",
    "",
    "AGORA, AO VIVO: arrastar 'Lado da área desmatada' para 0.",
    "",
    "\"Agora eu zerei a área desmatada: são duas datas de floresta intacta, sem corte",
    "nenhum. Olhem o que acontece.\"",
    "",
    "[Apontar a caixa vermelha]",
    "",
    "\"O programa SE RECUSA a dar um número, e explica: a distinguibilidade ficou em 2,66,",
    "abaixo do mínimo de 4,0. Sem duas classes reais, o limiar cortaria o ruído ao meio e",
    "inventaria desmatamento onde não houve. Recusar é a resposta certa.\"",
    "",
    "DEPOIS: voltar a área para 60 e o tamanho da cena para 200; abrir a aba Modelo.",
    "",
    "\"E no modelo: os recortes rotulados pela máscara treinam a floresta aleatória. O F1 dá",
    "1,000 — e o programa avisa, em amarelo, que esse número NÃO vale como validação,",
    "porque em cena sintética a separação foi construída. O Jonathan explica agora o que",
    "aconteceu quando a gente rodou isso em imagem de satélite de verdade.\"",
    "",
    "PASSA PARA O JONATHAN.",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 13 — Resultado sintético + modelo
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Resultado 1 — a cadeia funciona de ponta a ponta",
    sub: "Cena sintética, com verdade de terreno conhecida",
    quem: "Jonathan Aparecido X Martins  ·  discussão dos resultados" });

  destaque(s, { x: MARGEM, y: 1.95, w: 2.78, valor: "0,0%", rotulo: "erro na área detectada,\nnos dois tamanhos de corte" });
  destaque(s, { x: MARGEM + 3.0, y: 1.95, w: 2.78, valor: `${br(sintetica.area_hectares, 1)} ha`, rotulo: "6.400 px a 10 m/pixel,\nconvertidos pelo programa" });
  destaque(s, { x: MARGEM + 6.0, y: 1.95, w: 2.78, valor: "1,000", rotulo: "precisão, revocação e F1\ndo classificador", cor: COR.alerta });
  destaque(s, { x: MARGEM + 9.0, y: 1.95, w: 2.78, valor: "≈730 ms", rotulo: "cadeia completa sobre\numa cena de 440 × 440" });

  imagem(s, join(FIG, "telas/tela-modelo.png"), { x: MARGEM, y: 3.62, w: 6.35, h: 3.12 });

  cartao(s, { x: 7.35, y: 3.62, w: 5.37, h: 3.12 });
  s.addText("O 1,000 não valida o modelo", {
    x: 7.6, y: 3.75, w: 4.9, h: 0.4, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 18, bold: true, color: COR.alerta });
  itens(s, [
    "Em cena sintética a separação entre as classes foi construída — acertar era o esperado.",
    "O próprio programa emite o aviso junto da métrica, sem depender de quem lê o relatório.",
    "O que o número mostra é que a preparação de dados funciona de ponta a ponta.",
    "Os descritores de textura não se separam nesta cena: as duas classes receberam o mesmo ruído.",
  ], { x: 7.6, y: 4.22, w: 4.9, h: 2.4, fontSize: 12.5 });

  s.addNotes([
    "JONATHAN — resultado sintético (45 s)",
    "",
    "\"Resumindo o que a Isabel mostrou, em números. A quantificação errou zero por cento",
    "nos dois tamanhos de corte que a gente testou: 400 pixels e 6.400 pixels. A 10 metros",
    "por pixel, os 6.400 viram 64 hectares. E a cadeia inteira roda em cerca de 730",
    "milissegundos numa cena de 440 por 440.\"",
    "",
    "\"O classificador deu 1,000 em precisão, revocação e F1. E eu quero ser muito claro",
    "sobre isso, porque é o tipo de número que engana: ele NÃO valida o modelo.\"",
    "",
    "\"Numa cena sintética quem construiu a separação entre as classes foi o nosso gerador.",
    "Acertar tudo era o resultado esperado, não uma conquista. Tanto que o próprio programa",
    "emite esse aviso em amarelo, junto da métrica — ele não depende de alguém lembrar de",
    "ler a ressalva no relatório.\"",
    "",
    "\"O que esse número mostra de verdade é que a preparação de dados funciona de ponta a",
    "ponta: a máscara vira rótulo, o rótulo vira conjunto de treino, e o treino acontece.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 14 — Resultado real: a recusa
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Resultado 2 — em imagem real, o sistema recusou",
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

  s.addText("Três hipóteses testadas antes de concluir que a causa é a resolução", {
    x: MARGEM, y: 5.6, w: 8.3, h: 0.32, isTextBox: true, margin: 0,
    fontFace: TIT, fontSize: 15, bold: true, color: COR.floresta });
  const hipoteses = [
    ["Era o índice errado?", `NBR ${br(real.distinguibilidade)} contra NDVI ${br(2.994)} — melhora, e segue abaixo de ${br(4.0)}`],
    ["Era a abordagem errada?", `Limiarizar a imagem de diferença é pior: ${br(2.788)}`],
    ["Era a resolução?", "Confirmado — é a única hipótese que sobrou de pé"],
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
    "\"A causa é a resolução. A 253 metros por pixel, cada pixel mistura floresta, pasto,",
    "regeneração e estrada num valor só. Tudo vira um cinza intermediário.\"",
    "",
    "\"E a gente não chutou isso. Testou três hipóteses: primeiro, será que era o índice",
    "errado? Trocamos NDVI por NBR: melhorou de 2,99 para 3,51 e continuou abaixo de 4.",
    "Segundo, será que era a abordagem? Limiarizar a imagem de diferença deu 2,79, ainda",
    "pior. Terceiro, a resolução — é a única que sobrou, e é a que explica tudo.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 15 — A decisão metodológica
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "Bastava baixar o critério para 3,0", escuro: true,
    quem: "Jonathan Aparecido X Martins  ·  discussão dos resultados" });

  s.addText("“Escolher a régua depois de ver a medida não é medir.”", {
    x: MARGEM, y: 2.2, w: LARGURA, h: 1.35, isTextBox: true, margin: 0, align: "center",
    fontFace: TIT, fontSize: 33, bold: true, italic: true, color: COR.branco,
    lineSpacingMultiple: 1.1, valign: "middle" });

  s.addText("O critério de 4,0 foi fixado em cena sintética, antes de existir imagem real no projeto. Quando a cena real deu 3,51, mudar o número teria produzido uma área em hectares para colocar no trabalho — e essa área não significaria nada.", {
    x: 2.1, y: 3.6, w: L - 4.2, h: 1.1, isTextBox: true, margin: 0, align: "center",
    fontFace: CORPO, fontSize: 15.5, color: COR.musgo, lineSpacingMultiple: 1.2 });

  const colunas = [
    ["O que o sistema entregou", "Um mapa de mudança, as distribuições, a medida de separação e a recusa explicada."],
    ["O que ele não entregou", "Um número de hectares desmatados — porque a imagem disponível não sustenta esse número."],
    ["O que falta para entregar", "Imagem de 10 a 30 metros por pixel: Sentinel-2 ou Landsat. Não falta código."],
  ];
  const w = (LARGURA - 2 * 0.24) / 3;
  colunas.forEach(([titulo, texto], i) => {
    const x = MARGEM + i * (w + 0.24);
    cartao(s, { x, y: 4.95, w, h: 1.55, escuro: true });
    s.addText(titulo, { x: x + 0.28, y: 5.1, w: w - 0.56, h: 0.34, isTextBox: true, margin: 0,
      fontFace: TIT, fontSize: 15.5, bold: true, color: COR.musgo });
    s.addText(texto, { x: x + 0.28, y: 5.48, w: w - 0.56, h: 0.92, isTextBox: true, margin: 0,
      fontFace: CORPO, fontSize: 13, color: COR.branco, lineSpacingMultiple: 1.12 });
  });

  s.addNotes([
    "JONATHAN — a decisão metodológica (45 s)",
    "",
    "ESTE É O SLIDE MAIS IMPORTANTE DA APRESENTAÇÃO. Falar devagar.",
    "",
    "\"A cena real deu 3,51. O nosso critério é 4,0. Bastava baixar o critério para 3,0 e a",
    "gente teria um número de hectares para colocar no trabalho.\"",
    "",
    "[pausa]",
    "",
    "\"A gente não fez isso. Escolher a régua depois de ver a medida não é medir.\"",
    "",
    "\"O critério de 4,0 foi calibrado em cena sintética, antes de existir imagem real no",
    "projeto. Mudar ele depois, só para a cena passar, produziria um número bonito e sem",
    "significado nenhum.\"",
    "",
    "\"Então o que o sistema entregou foi: o mapa de mudança, as distribuições, a medida de",
    "separação e a recusa — com o motivo explicado na tela. O que ele não entregou foi o",
    "número de hectares.\"",
    "",
    "\"E o que falta para entregar esse número não é código. É imagem de 10 a 30 metros por",
    "pixel — Sentinel-2 ou Landsat. Com MODIS, a 253 metros, não dá.\"",
  ].join("\n"));
}

// --------------------------------------------------------------------------------------
// 16 — Conclusão
// --------------------------------------------------------------------------------------

{
  const s = slide({ titulo: "O que fica deste trabalho",
    quem: "Jonathan Aparecido X Martins  ·  encerramento" });

  const colunas = [
    ["O que funciona", [
      "Cinco etapas de PDI implementadas pelo grupo, só com NumPy",
      "Quantificação exata em cena de verdade de terreno conhecida",
      "Preparação de dados que alimenta um classificador de fato",
      "340 testes automatizados contra casos analíticos",
    ]],
    ["O que aprendemos", [
      "A primeira cena real estava tomada por fumaça de queimada e passou no controle de nuvem: o infravermelho de ondas curtas atravessa fumaça",
      "Foi o sistema recusando a detecção que levou a equipe até a causa",
      "O controle de qualidade passou a medir bruma no canal azul",
    ]],
    ["O que falta", [
      "Imagem de 10 a 30 m/pixel para o número em hectares",
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
    "dados alimentando um classificador de verdade; e 340 testes automatizados.\"",
    "",
    "\"O que a gente aprendeu foi na marra. A primeira cena real que baixamos estava tomada",
    "de fumaça de queimada, e passou no nosso controle de nuvem — porque o infravermelho de",
    "ondas curtas atravessa fumaça. Quem apontou o problema foi o próprio sistema, recusando",
    "a detecção. A gente foi investigar a recusa e achou a fumaça. Hoje o controle de",
    "qualidade mede bruma no canal azul.\"",
    "",
    "\"E o que falta: imagem de resolução melhor, validar os descritores de textura, e",
    "tratar registro geométrico quando as duas datas vierem de origens diferentes.\"",
    "",
    "\"Obrigado. Estamos à disposição para as perguntas — e qualquer um de nós responde",
    "sobre qualquer parte.\"",
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
