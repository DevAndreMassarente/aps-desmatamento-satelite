#!/usr/bin/env node
// Captura screenshots da interface em execução, para _interno/docs/resultados/telas/.
//
// Por que existe: o AGENTS.md exige que os screenshots venham da versão ENTREGUE. Um
// print tirado à mão numa versão anterior é evidência falsa por omissão. Este script
// regera as telas por comando, e deve rodar de novo antes de fechar a entrega.
//
// Dirige um Chromium headless pelo protocolo DevTools usando o WebSocket nativo do
// Node >= 22 — sem dependência nova. A espera é por CONTEÚDO (métricas renderizadas),
// não por tempo: o Streamlit carrega por websocket, e um print por tempo pega o
// esqueleto de carregamento.
//
// Uso (com a interface já rodando em localhost:8501):
//   CHROME=/caminho/do/chrome node _interno/scripts/capturar_telas.mjs [destino]

import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";

const CHROME = process.env.CHROME;
const URL_APP = process.env.URL_APP ?? "http://localhost:8501";
const DESTINO = process.argv[2] ?? "_interno/docs/resultados/telas";
const PORTA = 9333;
const LARGURA = 1400;

if (!CHROME) {
  console.error("Defina CHROME com o caminho de um Chromium/Chrome.");
  process.exit(2);
}

const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

const navegador = spawn(
  CHROME,
  ["--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
   `--remote-debugging-port=${PORTA}`, `--window-size=${LARGURA},1000`, "about:blank"],
  { stdio: "ignore" },
);

let alvo;
for (let i = 0; i < 100 && !alvo; i++) {
  try {
    const lista = await (await fetch(`http://127.0.0.1:${PORTA}/json/list`)).json();
    alvo = lista.find((t) => t.type === "page");
  } catch { /* navegador ainda subindo */ }
  if (!alvo) await esperar(200);
}
if (!alvo) {
  navegador.kill();
  console.error("Chromium não respondeu no protocolo DevTools.");
  process.exit(1);
}

const ws = new WebSocket(alvo.webSocketDebuggerUrl);
await new Promise((ok, erro) => {
  ws.addEventListener("open", ok, { once: true });
  ws.addEventListener("error", erro, { once: true });
});

let proximoId = 0;
const pendentes = new Map();
ws.addEventListener("message", (evento) => {
  const msg = JSON.parse(evento.data);
  if (msg.id && pendentes.has(msg.id)) {
    pendentes.get(msg.id)(msg);
    pendentes.delete(msg.id);
  }
});
const cdp = (method, params = {}) =>
  new Promise((ok) => {
    const id = ++proximoId;
    pendentes.set(id, ok);
    ws.send(JSON.stringify({ id, method, params }));
  });

const avaliar = async (expressao) =>
  (await cdp("Runtime.evaluate", { expression: expressao, returnByValue: true }))
    .result?.result?.value;

async function ate(expressao, descricao, limite = 90_000) {
  const inicio = Date.now();
  while (Date.now() - inicio < limite) {
    if (await avaliar(expressao)) return;
    await esperar(400);
  }
  throw new Error(`tempo esgotado esperando: ${descricao}`);
}

// Espera a execução do script do Streamlit terminar: sem indicador "running".
const OCIOSO = `!document.querySelector('[data-testid="stStatusWidget"]')`;
const IMAGENS_PRONTAS =
  `[...document.querySelectorAll('img')].every(i => i.complete && i.naturalWidth > 0)`;

async function capturar(nome) {
  await ate(`${OCIOSO} && ${IMAGENS_PRONTAS}`, "fim da renderização");
  await esperar(800);
  const altura = await avaliar(`Math.ceil(Math.max(
      ...[...document.querySelectorAll('[data-testid="stMainBlockContainer"], [data-testid="stSidebarContent"]')]
        .map(e => e.getBoundingClientRect().bottom), 900))`);
  await cdp("Emulation.setDeviceMetricsOverride",
            { width: LARGURA, height: altura + 40, deviceScaleFactor: 1, mobile: false });
  await esperar(600);
  const { result } = await cdp("Page.captureScreenshot", { format: "png" });
  const caminho = `${DESTINO}/${nome}`;
  writeFileSync(caminho, Buffer.from(result.data, "base64"));
  console.log(`  ${caminho}  (${LARGURA}×${altura + 40})`);
  await cdp("Emulation.setDeviceMetricsOverride",
            { width: LARGURA, height: 1000, deviceScaleFactor: 1, mobile: false });
}

async function clicarAba(rotulo) {
  const ok = await avaliar(`(() => {
    const aba = [...document.querySelectorAll('[data-testid="stTab"]')]
      .find(b => b.innerText.trim() === ${JSON.stringify(rotulo)});
    if (aba) aba.click();
    return !!aba;
  })()`);
  if (!ok) throw new Error(`aba não encontrada: ${rotulo}`);
  await esperar(800);
}

async function slidar(trechoDoRotulo, tecla) {
  const ok = await avaliar(`(() => {
    const bloco = [...document.querySelectorAll('[data-testid="stSlider"]')]
      .find(s => s.innerText.includes(${JSON.stringify(trechoDoRotulo)}));
    // Streamlit 1.63 usa react-aria: a alça é um <input type="range"> visualmente oculto.
    const alca = bloco?.querySelector('input[type="range"]');
    if (alca) alca.focus();
    return !!alca;
  })()`);
  if (!ok) throw new Error(`slider não encontrado: ${trechoDoRotulo}`);
  const codigos = { Home: 36, End: 35 };
  for (const type of ["keyDown", "keyUp"]) {
    await cdp("Input.dispatchKeyEvent",
              { type, key: tecla, code: tecla, windowsVirtualKeyCode: codigos[tecla] });
  }
  await esperar(1500);
  await ate(OCIOSO, `rerun após mover ${trechoDoRotulo}`);
}

try {
  mkdirSync(DESTINO, { recursive: true });
  await cdp("Page.enable");
  await cdp("Runtime.enable");
  await cdp("Emulation.setDeviceMetricsOverride",
            { width: LARGURA, height: 1000, deviceScaleFactor: 1, mobile: false });
  await cdp("Page.navigate", { url: URL_APP });

  await ate(`document.querySelectorAll('[data-testid="stMetric"]').length >= 4`,
            "métricas da cena sintética");

  console.log("Capturando:");
  await capturar("01-etapas.png");
  await clicarAba("Detecção");
  await capturar("02-deteccao.png");

  // Modelo no cenário do roteiro (bloco 4, passo 7): cena 200, área desmatada 60. Na cena
  // padrão 80×80 o teste fica com uma classe só e a tela mostraria um caso degenerado.
  await slidar("Tamanho da cena", "End");
  await slidar("Lado da área desmatada", "End");
  await clicarAba("Modelo");
  await ate(`document.body.innerText.includes("F1")`, "métricas do classificador");
  await capturar("03-modelo.png");

  await slidar("Lado da área desmatada", "Home");
  await ate(`document.body.innerText.includes("não confiável")`, "caixa de recusa");
  await cdp("Runtime.evaluate", { expression: "window.scrollTo(0, 0)" });
  await capturar("04-recusa.png");
} catch (erro) {
  console.error(`Falha: ${erro.message}`);
  process.exitCode = 1;
} finally {
  ws.close();
  navegador.kill();
}
