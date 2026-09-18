# Telas da interface

> **Todas as telas usam a cena SINTÉTICA de demonstração**, e ela está rotulada como tal
> no topo de cada uma. Servem como evidência de que a **interface funciona** — não como
> evidência sobre o mundo real. A evidência em imagem real está em `../results/`.

## Regerar antes da entrega

O `AGENTS.md` exige que os screenshots venham da **versão entregue**. Com a interface
rodando (`sentinela app`):

```bash
CHROME=/caminho/do/chrome node scripts/capturar_telas.mjs
```

O script dirige um Chromium headless pelo protocolo DevTools e espera o **conteúdo**
renderizar — não um tempo fixo, que captura o esqueleto de carregamento do Streamlit.

> **Reinicie a interface antes de capturar.** O servidor do Streamlit reexecuta o
> `app/principal.py` a cada acesso, mas mantém os módulos do pacote (`modelo/`, `pdi/`,
> `pipeline/`) **importados da primeira vez**. Um screenshot tirado de um servidor antigo
> mostra o texto do código antigo — com os testes todos passando, porque eles sobem a
> interface do zero.
>
> Aconteceu neste projeto: a correção da vírgula no aviso de equilíbrio estava no disco e
> testada, e a tela capturada ainda mostrava "equilíbrio 0.15". Só o reinício resolveu.

## As telas

| Arquivo | Aba | Estado | O que mostra |
|---------|-----|--------|--------------|
| `01-etapas.png` | Etapas do processamento | cena 80×80, área 20×20 | as quatro etapas de PDI; área detectada de 400 px contra 400 px construídos |
| `02-deteccao.png` | Detecção | idem | sobreposição da perda e tabela de regiões |
| `03-modelo.png` | Modelo | cena 200×200, área 60×60 | classificador com divisão espacial, métricas, avisos e importância dos descritores |
| `04-recusa.png` | — | área desmatada 0 | **a recusa**: duas datas de floresta intacta, nenhuma área reportada |

A tela de Modelo usa a cena maior porque, na 80×80, o conjunto de teste fica com uma
classe só e as métricas são degeneradas — é o cenário do passo 7 do roteiro da
apresentação.

## Defeitos encontrados por estas telas

Os screenshots não são só evidência — eles acharam problemas que a suíte de testes não
pegava:

1. **Ícones em emoji viravam quadrados vazios** em máquina sem fonte de emoji. Trocados por
   ícones Material, que o Streamlit traz embutidos; há teste impedindo emoji como ícone.
2. **Máscara toda branca sumia no fundo branco** e parecia imagem faltando. Ganhou moldura
   cinza, sem alterar o dado.
3. **Números com ponto decimal** numa interface em português. Trocados por vírgula.
4. **O aviso de "desempenho perfeito" disparava com o teste de uma classe só**, ao lado de
   precisão, revocação e F1 iguais a zero. Corrigido no classificador, com teste de
   regressão.
