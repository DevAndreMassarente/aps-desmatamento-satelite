"""Identidade visual da interface. Só aparência: nenhuma decisão de detecção mora aqui.

Fundo claro de carta topográfica, painéis brancos com contorno fino, verde da floresta nos
controles e vermelho só para perda e recusa. A fonte fica embutida no CSS porque a
demonstração não pode depender da internet da sala de aula.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

FONTES = Path(__file__).resolve().parent / "fontes"

FLORESTA = "#2B6B4F"
PERDA = "#D2453A"

# Os dois temas nativos do Streamlit. Quem assiste troca entre eles no menu ⋮ → Settings;
# sliders, tabelas e avisos mudam junto, o que um CSS próprio não conseguiria.
TEMA = {
    "theme.light.backgroundColor": "#F3F5F4",
    "theme.light.secondaryBackgroundColor": "#E3E8E5",
    "theme.light.textColor": "#17211C",
    "theme.light.primaryColor": FLORESTA,
    "theme.dark.backgroundColor": "#111715",
    "theme.dark.secondaryBackgroundColor": "#1C2521",
    "theme.dark.textColor": "#E4EAE6",
    "theme.dark.primaryColor": "#2F7D5A",
}

# Marca: uma grade de pixels de floresta com um bloco perdido, que é o que o programa mede.
MARCA_SVG = (
    '<svg width="34" height="34" viewBox="0 0 4 4" aria-hidden="true" shape-rendering="crispEdges">'
    f'<rect width="4" height="4" fill="{FLORESTA}"/>'
    f'<rect x="2" y="1" width="2" height="2" fill="{PERDA}"/>'
    '<path d="M1 0V4M2 0V4M3 0V4M0 1H4M0 2H4M0 3H4" stroke="#fff" stroke-width="0.08"/>'
    "</svg>"
)

# Sistema visual. As cores de base vêm do tema ativo (claro ou noturno); superfícies, linhas
# e texto secundário são derivados da cor do texto com color-mix, e por isso acompanham a
# troca de tema sem uma segunda folha de estilo. Vermelho só para perda e recusa.
_CSS = f"""
.stApp {{
  --linha: color-mix(in srgb, currentColor 14%, transparent);
  --linha-forte: color-mix(in srgb, currentColor 26%, transparent);
  --superficie: color-mix(in srgb, currentColor 4%, transparent);
  --superficie-2: color-mix(in srgb, currentColor 7%, transparent);
  --apagado: color-mix(in srgb, currentColor 64%, transparent);
  --perda: {PERDA};
  --r-1: 4px; --r-2: 8px; --r-3: 12px;
  --t-1: 0.82rem; --t-2: 0.92rem; --t-3: 1rem; --t-4: 1.2rem; --t-5: 1.55rem; --t-6: 2.2rem;
}}
html, body, .stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp h1, .stApp h2,
.stApp h3, .stApp button, .stApp summary, .stApp textarea {{
  font-family: "Barlow", "Segoe UI", system-ui, sans-serif;
}}
.stApp h1, .stApp h2, .stApp h3 {{ font-weight: 600; letter-spacing: 0; padding: 0; }}
.block-container {{ max-width: 1360px; padding: 0 2rem 4rem; }}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stAppDeployButton"],
footer, [data-testid="stStatusWidget"], [data-testid="stHeaderActionElements"] {{ display: none; }}
header[data-testid="stHeader"] {{ background: transparent; height: 3.4rem; }}

/* Barra superior */
.topo {{
  display: flex; align-items: center; gap: 0.7rem; height: 3.4rem;
  margin: 0 calc(50% - 50vw) 1.6rem; padding: 0 calc(50vw - 50% + 0.1rem);
  border-bottom: 1px solid var(--linha);
}}
.topo svg {{ width: 22px; height: 22px; }}
.topo b {{ font-size: var(--t-4); font-weight: 600; }}
.topo span {{ font-size: var(--t-2); color: var(--apagado); padding-left: 0.7rem; border-left: 1px solid var(--linha); }}

/* Painel de entrada */
.st-key-entrada {{
  background: var(--superficie); border: 1px solid var(--linha); border-radius: var(--r-3);
  padding: 1.1rem 1.1rem 1.2rem; gap: 0.85rem;
}}
.subtitulo {{ font-size: var(--t-2); font-weight: 600; margin: 0.4rem 0 0.1rem; }}
.st-key-entrada .subtitulo:first-child {{ margin-top: 0; }}
[data-testid="stFileUploader"] label p {{ font-size: var(--t-2); font-weight: 600; }}
[data-testid="stFileUploaderDropzone"] {{
  background: transparent; border: 1px dashed var(--linha-forte); border-radius: var(--r-2); padding: 0.7rem;
}}
[data-testid="stFileUploaderDropzone"] small, [data-testid="stFileUploaderDropzoneInstructions"] span {{ font-size: var(--t-1); }}
[data-testid="stBaseButton-primary"] {{ border-radius: var(--r-2); min-height: 2.8rem; font-weight: 600; }}
[data-testid="stPopover"] button, [data-testid="stBaseButton-secondary"] {{ border-radius: var(--r-2); }}
[data-testid="stButtonGroup"] button {{ font-size: var(--t-2); }}

/* Estado vazio */
.vazio {{
  min-height: 30rem; border: 1px dashed var(--linha-forte); border-radius: var(--r-3);
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1.4rem;
  padding: 2rem; text-align: center;
}}
.vazio .quadros {{ display: flex; gap: 0.9rem; }}
.vazio .quadros span {{
  width: 9.5rem; height: 9.5rem; border-radius: var(--r-2); background: var(--superficie-2);
  display: flex; align-items: flex-end; padding: 0.6rem; font-size: var(--t-2); color: var(--apagado);
}}
.vazio p {{ max-width: 30rem; font-size: var(--t-3); line-height: 1.5; color: var(--apagado); margin: 0; }}

/* Veredito */
[data-testid="stMetric"] {{ padding: 0.2rem 0 0.2rem 1rem; border-left: 1px solid var(--linha); }}
[data-testid="stMetricValue"] {{ font-weight: 600; font-size: var(--t-6); font-variant-numeric: tabular-nums; }}
[data-testid="stMetricLabel"] p {{ font-size: var(--t-2); color: var(--apagado); }}
[data-testid="stAlert"] > div {{ border-radius: var(--r-2); }}
[data-testid="stAlert"] p {{ font-size: var(--t-3); line-height: 1.5; }}
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) > div {{
  background: color-mix(in srgb, var(--perda) 9%, transparent); border: 1px solid color-mix(in srgb, var(--perda) 45%, transparent);
}}
[data-testid="stAlertContentError"], [data-testid="stAlertContentError"] p {{ color: inherit; }}
[data-testid="stAlertContentError"] p strong {{ color: var(--perda); font-size: var(--t-4); }}

/* Cartão de resultado */
.veredito {{ margin: 0 0 0.9rem; }}
.veredito h2 {{ font-size: var(--t-5) !important; line-height: 1.25; margin: 0.35rem 0 0.4rem !important; }}
.veredito p {{ font-size: var(--t-3); line-height: 1.5; margin: 0; max-width: 52rem; }}
.selo {{ display: inline-block; font-size: var(--t-2) !important; font-weight: 600; padding: 0.15rem 0.6rem;
  border-radius: 999px; border: 1px solid currentColor; }}
.selo.recusado {{ color: var(--perda); }}
.selo.aceito {{ color: inherit; opacity: 0.8; }}
[data-testid="stElementToolbar"], [data-testid="stImage"] button {{ display: none !important; }}

/* Trilho das etapas */
.trilho {{ font-size: var(--t-5) !important; margin: 2.6rem 0 0.6rem !important; }}
.stTabs [data-baseweb="tab-list"] {{
  gap: 0.25rem; padding: 0.25rem; background: var(--superficie-2); border-radius: var(--r-2); border: 0;
}}
.stTabs [data-baseweb="tab"] {{ height: 2.5rem; padding: 0 1.1rem; border-radius: var(--r-1); }}
.stTabs [data-baseweb="tab"] p {{ font-size: var(--t-3); color: var(--apagado); white-space: pre; }}
.stTabs [aria-selected="true"] {{ background: var(--background-color, transparent); box-shadow: 0 0 0 1px var(--linha); }}
.stTabs [aria-selected="true"] p {{ color: inherit; font-weight: 600; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none; }}
.etapa {{ margin: 1.4rem 0 1rem; max-width: 46rem; }}
.etapa h3 {{ font-size: var(--t-5) !important; margin: 0 0 0.3rem !important; }}
.etapa p {{ font-size: var(--t-3); line-height: 1.5; color: var(--apagado); margin: 0; }}

/* Imagens, legendas e tabelas */
[data-testid="stImage"] img {{ border-radius: var(--r-1); max-height: 380px; object-fit: contain; }}
[data-testid="stImageCaption"], [data-testid="stCaptionContainer"] p {{ font-size: var(--t-2); color: var(--apagado); }}
[data-testid="stDataFrame"] {{ border-radius: var(--r-2); }}
[data-testid="stExpander"] details {{ border-radius: var(--r-2); border-color: var(--linha); }}
code {{ font-size: 0.9em; }}
:focus-visible {{ outline: 2px solid currentColor !important; outline-offset: 2px; }}
@media (max-width: 760px) {{ .block-container {{ padding: 0 1rem 3rem; }} .topo span {{ display: none; }} }}
"""


def _fonte(arquivo: str, peso: int) -> str:
    dados = base64.b64encode((FONTES / arquivo).read_bytes()).decode("ascii")
    return (
        f'@font-face {{ font-family: "Barlow"; font-weight: {peso}; font-display: swap; '
        f'src: url(data:font/woff2;base64,{dados}) format("woff2"); }}'
    )


@lru_cache(maxsize=1)
def fontes_css() -> str:
    """Declarações ``@font-face`` embutidas. Sem os arquivos, usa as fontes do sistema."""
    try:
        return "\n".join(_fonte(f"barlow-latin-{peso}-normal.woff2", peso) for peso in (400, 600))
    except OSError:
        return ""


def folha_de_estilo() -> str:
    """CSS completo da página, pronto para ``st.html``."""
    return f"<style>{fontes_css()}\n{_CSS}</style>"
