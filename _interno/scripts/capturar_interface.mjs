#!/usr/bin/env node
// Captura a interface atual para os slides e para a evidência em _interno/docs/resultados/telas/.
//
// Envia as imagens de exemplos/, processa, abre as etapas e grava:
//   - páginas inteiras em _interno/docs/resultados/telas/;
//   - recortes dos slides em _interno/docs/apresentacao/figuras/telas/, pela posição real
//     dos elementos na página (nada de coordenada fixa, que quebra a cada mudança de layout).
//
// Dirige um Chromium headless pelo protocolo DevTools, com o WebSocket nativo do Node >= 22.
// O app precisa estar rodando só nesta máquina, por exemplo:
//   .venv/bin/sentinela app --porta 8599
//   CHROME=/caminho/do/chrome URL_APP=http://127.0.0.1:8599 node _interno/scripts/capturar_interface.mjs

import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const CHROME = process.env.CHROME;
const URL_APP = process.env.URL_APP ?? "http://127.0.0.1:8501";
const TELAS = join(RAIZ, "_interno/docs/resultados/telas");
const FIGURAS = join(RAIZ, "_interno/docs/apresentacao/figuras/telas");
const ANTES = join(RAIZ, "exemplos/2018-07-03_cor-e-infravermelho.png");
const DEPOIS = join(RAIZ, "exemplos/2024-07-16_cor-e-infravermelho.png");
const LARGURA = 1440;

if (!CHROME) { console.error("Defina CHROME com o caminho de um Chromium/Chrome."); process.exit(2); }
mkdirSync(TELAS, { recursive: true }); mkdirSync(FIGURAS, { recursive: true });

const esperar = (ms) => new Promise((r) => setTimeout(r, ms));
const navegador = spawn(CHROME, ["--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
  "--remote-debugging-port=9346", `--window-size=${LARGURA},1000`, "about:blank"], { stdio: "ignore" });

let alvo;
for (let i = 0; i < 100 && !alvo; i++) {
  try { alvo = (await (await fetch("http://127.0.0.1:9346/json/list")).json()).find((t) => t.type === "page"); } catch {}
  if (!alvo) await esperar(200);
}
const ws = new WebSocket(alvo.webSocketDebuggerUrl);
await new Promise((ok) => ws.addEventListener("open", ok, { once: true }));
let proximo = 0; const pendentes = new Map();
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pendentes.has(m.id)) { pendentes.get(m.id)(m); pendentes.delete(m.id); } });
const cdp = (method, params = {}) => new Promise((ok) => { const id = ++proximo; pendentes.set(id, ok); ws.send(JSON.stringify({ id, method, params })); });
const avaliar = async (x) => (await cdp("Runtime.evaluate", { expression: x, returnByValue: true })).result?.result?.value;
async function ate(x, rotulo, limite = 120000) {
  const t = Date.now();
  while (Date.now() - t < limite) { if (await avaliar(x)) return; await esperar(400); }
  throw new Error("tempo esgotado: " + rotulo);
}
const OCIOSO = `!document.querySelector('[data-testid="stStatusWidget"]')`;

async function abrirPaginaInteira() {
  await ate(OCIOSO, "fim da execução"); await esperar(1500);
  const altura = await avaliar(`Math.ceil(document.querySelector('[data-testid="stMainBlockContainer"]').getBoundingClientRect().bottom + 40)`);
  await cdp("Emulation.setDeviceMetricsOverride", { width: LARGURA, height: altura, deviceScaleFactor: 1, mobile: false });
  await esperar(900);
}
async function gravar(caminho, clip) {
  const { result } = await cdp("Page.captureScreenshot", { format: "png", ...(clip ? { clip: { ...clip, scale: 1 } } : {}) });
  writeFileSync(caminho, Buffer.from(result.data, "base64"));
  console.log("  " + caminho.replace(RAIZ + "/", ""));
}
// Retângulo que vai do topo do primeiro elemento ao fundo do último, com margem.
async function retangulo(expressaoInicio, expressaoFim, margem = 16) {
  return avaliar(`(() => {
    const a = (${expressaoInicio}).getBoundingClientRect(), b = (${expressaoFim}).getBoundingClientRect();
    const x = Math.min(a.left, b.left) - ${margem}, y = a.top - ${margem};
    return { x, y, width: Math.max(a.right, b.right) - x + ${margem}, height: b.bottom - y + ${margem} };
  })()`);
}
async function clicarAba(numero) {
  await avaliar(`document.querySelectorAll('[data-testid="stTab"]')[${numero - 1}].click()`);
  await esperar(1500);
}

async function entradasDoComponente() {
  const doc = await cdp("DOM.getDocument", { depth: -1, pierce: true });
  let raiz = null;
  const visitar = (no) => {
    if (raiz) return;
    if (no.nodeName === "IFRAME" && no.contentDocument) { raiz = no.contentDocument.nodeId; return; }
    for (const filho of no.children || []) visitar(filho);
  };
  visitar(doc.result.root);
  return (await cdp("DOM.querySelectorAll", { nodeId: raiz, selector: "input[type=file]" })).result.nodeIds;
}

await cdp("Page.enable"); await cdp("Runtime.enable"); await cdp("DOM.enable");
await cdp("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: "light" }] });
await cdp("Page.navigate", { url: URL_APP });
await ate(`!!document.querySelector('iframe[title*="quadros"]')`, "quadros de envio");
await esperar(2500);

// Se o app guardou imagens de uma sessão anterior, a página já abre com o resultado.
if (!(await avaliar(`!!document.querySelector('[data-testid="stTab"]')`))) {
  let ids = await entradasDoComponente();
  await cdp("DOM.setFileInputFiles", { nodeId: ids[0], files: [ANTES] });
  await esperar(6000); await ate(OCIOSO, "envio da imagem antes");
  ids = await entradasDoComponente();
  await cdp("DOM.setFileInputFiles", { nodeId: ids[1], files: [DEPOIS] });
  await esperar(6000); await ate(OCIOSO, "envio da imagem depois");
  await ate(`[...document.querySelectorAll('button')].some(b => b.innerText.includes('Processar') && !b.disabled)`, "botão Processar");
  await avaliar(`[...document.querySelectorAll('button')].find(b => b.innerText.includes('Processar')).click()`);
  await ate(`!!document.querySelector('[data-testid="stTab"]')`, "resultado", 180000);
}

console.log("Capturando:");
await abrirPaginaInteira();
await gravar(join(TELAS, "01-etapas.png"));
// Visão geral para o slide da demonstração: do topo da página ao fim da comparação.
await gravar(join(FIGURAS, "tela-demo.png"), await avaliar(`(() => {
  const fim = [...document.querySelectorAll('iframe')].find((f) => !f.title.includes('quadros') && f.getBoundingClientRect().height > 0);
  const legenda = fim.closest('[data-testid="stVerticalBlock"]');
  return { x: 0, y: 0, width: ${LARGURA}, height: Math.ceil(fim.getBoundingClientRect().bottom + 6) };
})()`));

await clicarAba(3);
await abrirPaginaInteira();
await gravar(join(FIGURAS, "tela-filtragem-app.png"), await avaliar(`(() => {
  const visivel = (e) => e.getBoundingClientRect().height > 0;
  const etapa = [...document.querySelectorAll('.etapa')].find((e) => visivel(e) && e.innerText.includes('Filtragem'));
  const painel = etapa.closest('[role="tabpanel"]');
  const partes = [etapa, ...painel.querySelectorAll('[data-testid="stImage"]'),
    ...painel.querySelectorAll('[data-testid="stCaptionContainer"]')].filter(visivel);
  const r = partes.map((e) => e.getBoundingClientRect());
  const x = Math.min(...r.map((q) => q.left)) - 16, y = Math.min(...r.map((q) => q.top)) - 16;
  return { x, y, width: Math.max(...r.map((q) => q.right)) - x + 16, height: Math.max(...r.map((q) => q.bottom)) - y + 16 };
})()`));

await clicarAba(4);
await abrirPaginaInteira();
await gravar(join(TELAS, "04-recusa.png"));
// Só elementos visíveis: as abas fechadas continuam no DOM, com tamanho zero.
await gravar(join(FIGURAS, "tela-etapas-3-4.png"), await avaliar(`(() => {
  const visivel = (e) => e.getBoundingClientRect().height > 0;
  const etapa = [...document.querySelectorAll('.etapa')].find((e) => visivel(e) && e.innerText.includes('Segmentação'));
  const painel = etapa.closest('[role="tabpanel"]');
  const partes = [etapa, ...painel.querySelectorAll('[data-testid="stImage"]'),
    [...painel.querySelectorAll('small')].find((s) => s.innerText.includes('perda de vegetação'))].filter(visivel);
  const r = partes.map((e) => e.getBoundingClientRect());
  const x = Math.min(...r.map((q) => q.left)) - 16, y = Math.min(...r.map((q) => q.top)) - 16;
  return { x, y, width: Math.max(...r.map((q) => q.right)) - x + 16, height: Math.max(...r.map((q) => q.bottom)) - y + 16 };
})()`));
await gravar(join(FIGURAS, "tela-recusa.png"), await retangulo(
  `[...document.querySelectorAll('.subtitulo')].find(p => p.innerText.includes('Decisão do limiar'))`,
  `[...document.querySelectorAll('[data-testid="stDataFrame"]')].at(-1)`));

await avaliar(`[...document.querySelectorAll('button')].find(b => b.innerText.trim() === 'Cena sintética').click()`);
await ate(`[...document.querySelectorAll('[data-testid="stMetricLabel"]')].some(m => m.innerText.includes('Área desmatada'))`, "cena sintética");
await abrirPaginaInteira();
await gravar(join(TELAS, "02-deteccao.png"));
await gravar(join(FIGURAS, "tela-deteccao.png"), await retangulo(
  `document.querySelector('[data-testid="stMetric"]')`,
  `document.querySelector('iframe[title*="components.v1.html"], iframe:not([title*="quadros"])')`));

await clicarAba(5);
await abrirPaginaInteira();
await gravar(join(TELAS, "03-modelo.png"));

navegador.kill();
process.exit(0);
