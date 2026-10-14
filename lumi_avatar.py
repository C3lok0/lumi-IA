"""
Mini assistente visual da LUMI (canto da tela) com animações em pixel art.

Uso no app.py:
    from lumi_avatar import LumiAvatar
    lumi = LumiAvatar()          # cria o "espaço" fixo da Lumi na tela
    lumi.set("pensando")         # troca o estado/animação na hora
    lumi.set("feliz")            # volta sozinha para "standby" depois de alguns segundos
"""
import base64
import time
from functools import lru_cache
from pathlib import Path

import streamlit as st

PASTA = Path(__file__).parent / "imagens"

# estado -> (arquivo, segundos até voltar ao standby (None = fica até a próxima ação), texto de acessibilidade, balão)
ESTADOS = {
    "standby":  ("lumi_standby.png",  None, "Lumi está aguardando você",         ""),
    "pensando": ("lumi_pensando.png", None, "Lumi está pensando na resposta",    "pensando"),
    "feliz":    ("lumi_feliz.png",    5,    "Lumi respondeu com sucesso",        ""),
    "erro":     ("lumi_erro.png",     8,    "Lumi encontrou um erro",            ""),
    "cansada":  ("lumi_cansada.png",  None, "Lumi está cansada: limite da API atingido", "zzz"),
}

CSS = """
<style>
/* ---------- posição: fixa no canto, sem empurrar nada do layout ---------- */
.lumi-wrap{
  position:fixed; right:18px; bottom:96px;      /* 96px = acima da barra de digitação */
  width:110px; z-index:999;                      /* abaixo de modais/menus do Streamlit */
  pointer-events:none; user-select:none;
}
.lumi-box{ position:relative; width:100%; aspect-ratio:141/291; }
.lumi-box img{
  position:absolute; inset:0; width:100%; height:100%;
  image-rendering:pixelated;                     /* visual pixel art nítido */
  filter:drop-shadow(0 3px 6px rgba(0,0,0,.28));
  transform-origin:50% 100%;
}
.lumi-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}

/* ---------- animações (steps() = movimento "quadro a quadro" de pixel art) ---------- */
@keyframes lumi-respira { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-3px)} }
@keyframes lumi-pensa   { 0%,100%{transform:rotate(-2deg)} 50%{transform:rotate(2deg)} }
@keyframes lumi-pula    { 0%,100%{transform:translateY(0)} 25%{transform:translateY(-14px)} 50%{transform:translateY(0)} 75%{transform:translateY(-7px)} }
@keyframes lumi-treme   { 0%,100%{transform:translateX(0)} 20%{transform:translateX(-4px)} 40%{transform:translateX(4px)} 60%{transform:translateX(-3px)} 80%{transform:translateX(3px)} }
@keyframes lumi-sono    { 0%,100%{transform:rotate(-1.5deg) translateY(0)} 50%{transform:rotate(1.5deg) translateY(2px)} }
@keyframes lumi-some    { to{opacity:0} }
@keyframes lumi-aparece { from{opacity:0} to{opacity:1} }

.lumi-standby  .lumi-main{animation:lumi-respira 2s steps(2,jump-none) infinite}
.lumi-pensando .lumi-main{animation:lumi-pensa .9s steps(4) infinite}
.lumi-feliz    .lumi-main{animation:lumi-pula .9s steps(6) 3, lumi-some .3s linear var(--hold) forwards}
.lumi-erro     .lumi-main{animation:lumi-treme .5s steps(5) 3, lumi-some .3s linear var(--hold) forwards}
.lumi-cansada  .lumi-main{animation:lumi-sono 3s steps(6) infinite}
/* ao fim do tempo, o standby (camada de baixo) assume sozinho, sem precisar de rerun */
.lumi-idle{animation:lumi-respira 2s steps(2,jump-none) infinite}

/* ---------- balões em pixel art (pontinhos / zzz) ---------- */
.lumi-bubble{
  position:absolute; top:-6px; right:-8px; display:flex; gap:4px; align-items:center;
  background:#fff; border:3px solid #5b3b3b; padding:5px 7px; border-radius:2px;
  box-shadow:3px 3px 0 rgba(0,0,0,.25); font:700 13px/1 monospace; color:#5b3b3b;
}
.lumi-bubble i{width:6px;height:6px;background:#5b3b3b;display:block;animation:lumi-pisca 1.2s steps(1) infinite}
.lumi-bubble i:nth-child(2){animation-delay:.3s} .lumi-bubble i:nth-child(3){animation-delay:.6s}
@keyframes lumi-pisca{0%,100%{opacity:.2} 33%{opacity:1}}
.lumi-zzz span{display:inline-block;animation:lumi-sobe 2.4s steps(4) infinite}
.lumi-zzz span:nth-child(2){animation-delay:.6s} .lumi-zzz span:nth-child(3){animation-delay:1.2s}
@keyframes lumi-sobe{0%{transform:translateY(4px);opacity:0} 40%{opacity:1} 100%{transform:translateY(-6px);opacity:0}}

/* ---------- telas pequenas e acessibilidade ---------- */
@media (max-width:640px){ .lumi-wrap{width:78px; right:8px; bottom:84px} .lumi-bubble{display:none} }
@media (prefers-reduced-motion:reduce){ .lumi-box img, .lumi-bubble i, .lumi-zzz span{animation:none!important} }
</style>
"""


@lru_cache(maxsize=None)
def _b64(arquivo: str) -> str:
    dados = (PASTA / arquivo).read_bytes()
    return "data:image/png;base64," + base64.b64encode(dados).decode()


def _html(estado: str, decorrido: float) -> str:
    arquivo, hold, aria, balao = ESTADOS[estado]

    # estados temporários que já expiraram viram standby (ex.: rerun por clique na sidebar)
    if hold is not None and decorrido >= hold:
        estado = "standby"
        arquivo, hold, aria, balao = ESTADOS[estado]

    if balao == "pensando":
        bubble = '<div class="lumi-bubble"><i></i><i></i><i></i></div>'
    elif balao == "zzz":
        bubble = '<div class="lumi-bubble lumi-zzz"><span>z</span><span>z</span><span>Z</span></div>'
    else:
        bubble = ""

    idle = ""
    style = ""
    if hold is not None:  # camada standby por baixo, para onde a Lumi "volta" sozinha
        idle = f'<img class="lumi-idle" src="{_b64(ESTADOS["standby"][0])}" alt="">'
        # --hold = tempo que ainda falta; o fade-out só começa depois disso (continua certo mesmo após um rerun)
        style = f' style="--hold:{max(hold - decorrido, 0):.2f}s"'

    return (
        f'<div class="lumi-wrap lumi-{estado}" role="status" aria-live="polite"{style}>'
        f'<div class="lumi-box">{idle}'
        f'<img class="lumi-main" src="{_b64(arquivo)}" alt="Lumi, assistente virtual">'
        f'{bubble}</div>'
        f'<span class="lumi-sr">{aria}</span></div>'
    )


class LumiAvatar:
    """Cria um placeholder fixo e permite trocar a animação a qualquer momento do script."""

    def __init__(self):
        st.markdown(CSS, unsafe_allow_html=True)
        self._slot = st.empty()
        ss = st.session_state
        ss.setdefault("lumi_estado", "standby")
        ss.setdefault("lumi_desde", time.time())
        self._desenhar()

    def _desenhar(self):
        ss = st.session_state
        self._slot.markdown(_html(ss.lumi_estado, time.time() - ss.lumi_desde), unsafe_allow_html=True)

    def set(self, estado: str):
        st.session_state.lumi_estado = estado
        st.session_state.lumi_desde = time.time()
        self._desenhar()
