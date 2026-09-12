"""Interface de demonstração em Streamlit.

Executar com ``sentinela app`` ou ``streamlit run src/sentinela/app/principal.py``.
O módulo ``principal`` só é importável com o Streamlit instalado (extra ``app``).
"""

CAMINHO_APP = __file__.replace("__init__.py", "principal.py")

__all__ = ["CAMINHO_APP"]
