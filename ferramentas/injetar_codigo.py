#!/usr/bin/env python3
"""Põe o código de cada etapa DENTRO do guia (PT/EN/ES): uma linha curl para baixar o bot.py pronto
da etapa e um <details> com o arquivo inteiro. Lê sempre de etapas/NN-*/bot.py (fonte única).

uso: python3 ferramentas/injetar_codigo.py   (na raiz do repo; pode rodar de novo: refaz os blocos)
"""
import html, os, re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "https://raw.githubusercontent.com/inematds/telegram-vps-passo-a-passo/main/etapas/{}/bot.py"
BLOB = "https://github.com/inematds/telegram-vps-passo-a-passo/blob/main/etapas/{}/bot.py"
TXT = {
    "index.html": ("<strong>Primeiro, salve o código desta etapa como <code>bot.py</code></strong> na pasta do bot (ele substitui o anterior). "
                   "Jeito rápido: baixe com o <code>curl</code> abaixo. Ou escreva você mesmo: <code>nano bot.py</code>, apague o que houver, "
                   "cole o código do bloco abaixo, salve com <kbd>Ctrl+O</kbd> e <kbd>Enter</kbd>, e saia com <kbd>Ctrl+X</kbd>. Se o bot já estiver rodando, pare-o (<kbd>Ctrl+C</kbd> no terminal 2) e rode de novo para valer o arquivo novo. Nos testes, o que vem na frente do comando (<code>TELEGRAM_BOT_TOKEN=123:falso</code>, <code>DONOS=111</code>) vale mais que o <code>.env</code>.",
                   "Código desta etapa (bot.py completo)", "ver no GitHub"),
    "en/index.html": ("<strong>First, save this step's code as <code>bot.py</code></strong> in the bot folder (it replaces the previous one). "
                      "Quick way: download it with the <code>curl</code> below. Or write it yourself: <code>nano bot.py</code>, delete what's there, "
                      "paste the code from the block below, save with <kbd>Ctrl+O</kbd> and <kbd>Enter</kbd>, and exit with <kbd>Ctrl+X</kbd>. If the bot is already running, stop it (<kbd>Ctrl+C</kbd> in terminal 2) and run it again so the new file takes effect. In the tests, what comes in front of the command (<code>TELEGRAM_BOT_TOKEN=123:falso</code>, <code>DONOS=111</code>) wins over <code>.env</code>.",
                      "Code for this step (full bot.py)", "view on GitHub"),
    "es/index.html": ("<strong>Primero, guarda el código de esta etapa como <code>bot.py</code></strong> en la carpeta del bot (reemplaza el anterior). "
                      "Forma rápida: descárgalo con el <code>curl</code> de abajo. O escríbelo tú: <code>nano bot.py</code>, borra lo que haya, "
                      "pega el código del bloque de abajo, guarda con <kbd>Ctrl+O</kbd> y <kbd>Enter</kbd>, y sal con <kbd>Ctrl+X</kbd>. Si el bot ya está corriendo, detenlo (<kbd>Ctrl+C</kbd> en la terminal 2) y córrelo de nuevo para que valga el archivo nuevo. En las pruebas, lo que va delante del comando (<code>TELEGRAM_BOT_TOKEN=123:falso</code>, <code>DONOS=111</code>) vale más que el <code>.env</code>.",
                      "Código de esta etapa (bot.py completo)", "ver en GitHub"),
}
VELHO = re.compile(r'<p class="gab">[^<]*<a href="' + re.escape(BLOB.format("X")).replace("X", r"(\d\d-[^/\"]+)")
                   + r'"[^>]*>[^<]*</a></p>')
BLOCO = re.compile(r'<!-- codigo:(\d\d-[^ ]+) -->.*?<!-- /codigo -->', re.S)


def bloco(etapa, txt):
    codigo = open(os.path.join(RAIZ, "etapas", etapa, "bot.py")).read()
    return (f'<!-- codigo:{etapa} -->\n    <p class="gab">{txt[0]}</p>\n'
            f'<pre>curl -fsSLo bot.py {RAW.format(etapa)}</pre>\n'
            f'    <details class="cod"><summary>{txt[1]}</summary>'
            f'<pre>{html.escape(codigo, quote=False)}</pre>'
            f'<p class="gh"><a href="{BLOB.format(etapa)}" target="_blank" rel="noopener">{txt[2]}</a></p></details>\n'
            f'    <!-- /codigo -->')


for arq, txt in TXT.items():
    p = os.path.join(RAIZ, "guia", arq)
    s = open(p).read()
    s, n1 = VELHO.subn(lambda m: bloco(m.group(1), txt), s)
    s, n2 = BLOCO.subn(lambda m: bloco(m.group(1), txt), s)
    open(p, "w").write(s)
    print(arq, "blocos novos:", n1, "refeitos:", n2)
