"""Comparador de duas datas: uma linha que se arrasta para revelar uma imagem sobre a outra.

Só apresentação. As imagens chegam prontas do pipeline e são embutidas como JPEG reduzido.
"""

from __future__ import annotations

ALTURA = 660


def html(antes: str, depois: str, proporcao: float) -> str:
    """Página do comparador. ``proporcao`` é largura dividida por altura da imagem."""
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; background: transparent; }}
.cena {{ position: relative; height: {ALTURA - 8}px; max-width: 100%; aspect-ratio: {proporcao:.4f};
  margin: 0 auto; overflow: hidden; border-radius: 3px; }}
.cena img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: fill; user-select: none; }}
#antes {{ clip-path: inset(0 calc(100% - var(--x)) 0 0); }}
.linha {{ position: absolute; top: 0; bottom: 0; left: var(--x); width: 2px; margin-left: -1px;
  background: #fff; box-shadow: 0 0 6px #0008; pointer-events: none; }}
.alca {{ position: absolute; top: 50%; left: var(--x); width: 14px; height: 52px; margin: -26px 0 0 -7px;
  background: #fff; border-radius: 3px; box-shadow: 0 1px 6px #0008; pointer-events: none; }}
.data {{ position: absolute; top: 10px; padding: 3px 9px; background: #000a; color: #fff;
  font: 600 15px "Segoe UI", system-ui, sans-serif; border-radius: 2px; pointer-events: none; }}
#rot-antes {{ left: 10px; }} #rot-depois {{ right: 10px; }}
input {{ position: absolute; inset: 0; width: 100%; height: 100%; margin: 0; opacity: 0; cursor: ew-resize; }}
.cena:has(input:focus-visible) {{ outline: 3px solid #fff; outline-offset: -3px; }}
</style></head><body>
<div class="cena" id="cena" style="--x: 50%">
  <img src="{depois}" alt="Imagem depois">
  <img id="antes" src="{antes}" alt="Imagem antes">
  <div class="linha"></div><div class="alca" aria-hidden="true"></div>
  <div class="data" id="rot-antes">Antes</div><div class="data" id="rot-depois">Depois</div>
  <input type="range" min="0" max="100" value="50" aria-label="Comparar antes e depois">
</div>
<script>
const cena = document.getElementById("cena");
document.querySelector("input").addEventListener("input", (e) => cena.style.setProperty("--x", e.target.value + "%"));
</script></body></html>"""
