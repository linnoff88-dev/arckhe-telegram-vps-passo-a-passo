#!/usr/bin/env python3
"""Refaz as etapas 5–9 a partir do kit (fonte da verdade): ~/projetos/telegram-vps-remoto.

- 08 e 09: bot.py = kit (diff vazio); 09 também leva testes/testar_travas.py e systemd/*.service do kit.
- 07: kit sem a auditoria.  06: 07 sem o "sim" (eh_sim, conferir_tar, executar).  05: só as listas NEGADO/LEITURA.
Depois rode ferramentas/injetar_codigo.py para atualizar o código dentro do guia.

uso: python3 ferramentas/sincronizar_etapas.py [caminho-do-kit]
"""
import os, re, shutil, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/projetos/telegram-vps-remoto")
E = lambda *p: os.path.join(RAIZ, "etapas", *p)

k = open(os.path.join(KIT, "bot.py")).read()
for d in ("08-auditoria", "09-systemd-e-testes"):
    open(E(d, "bot.py"), "w").write(k)
shutil.copy(os.path.join(KIT, "testes", "testar_travas.py"), E("09-systemd-e-testes", "testes", "testar_travas.py"))
for f in os.listdir(os.path.join(KIT, "systemd")):
    shutil.copy(os.path.join(KIT, "systemd", f), E("09-systemd-e-testes", "systemd", f))

# 07: sem auditoria
t = k.replace("  5. Tudo vai para auditoria.jsonl (sem o token).\n", "  (A auditoria entra na etapa 8.)\n")
t = re.sub(r'AUDITORIA = os\.environ\.get\(.*\n', "", t)
t, n = re.subn(r"def auditar\(\*\*ev\):\n(    .*\n)+\n\n", "", t)
assert n == 1, "auditar"
t = "\n".join(l for l in t.split("\n") if "auditar(" not in l)
t = t.replace('"""Telegram VPS remoto — você pede', '"""Etapa 7 — Telegram VPS remoto — você pede', 1)
assert "auditar" not in t and "AUDITORIA" not in t
open(E("07-sim-e-execucao", "bot.py"), "w").write(t)

# 06: sem o "sim"
t = t.replace('"""Etapa 7 — Telegram VPS remoto', '"""Etapa 6 — Telegram VPS remoto', 1)
a = ('     todo caminho dentro da área, sem shell), guarda e pergunta "Confirma?". Depois do "sim",\n'
     '     quem roda é o próprio bot, exatamente o que foi mostrado. A IA nunca tem ferramenta de escrita.')
assert a in t, "docstring"
t = t.replace(a, '     todo caminho dentro da área, sem shell), guarda e pergunta "Confirma?". Nesta etapa o bot\n'
                 '     ainda NÃO executa nada: o "sim" entra na etapa 7. A IA nunca tem ferramenta de escrita.')
for pad in (r'PRAZO_OK = .*\n', r'SIM_FORTE = .*\n', r'SIM_SOZINHO = .*\n'):
    t, n = re.subn(pad, "", t)
    assert n == 1, pad
for fn in ("eh_sim", "conferir_tar", "executar"):
    t, n = re.subn(r"def %s\(.*?\n\n\n" % fn, "", t, flags=re.S)
    assert n == 1, fn
velho = t[t.index("    p = pendente.get(chat)"):t.index('    tg("sendChatAction"')]
t = t.replace(velho, '    if pendente.pop(chat, None):\n'
                     '        enviar(chat, "Ainda não executo nada: o \\"sim\\" entra na etapa 7. Pedido descartado.")\n'
                     '        return\n')
open(E("06-proposta-e-validador", "bot.py"), "w").write(t)

# 05: listas iguais ao kit
f5 = E("05-leitura", "bot.py")
u = open(f5).read()
novo = k[k.index('H = os.path.expanduser("~")\nNEGADO = ['):k.index('# Depois do "sim"')].rstrip("\n") + "\n"
velho = u[u.index('H = os.path.expanduser("~")\nNEGADO = ['):u.index("\n\ndef tg(")] + "\n"
u = u.replace(velho, novo)
um = [l for l in k.split("\n") if l.startswith("os.umask(")]
if um and um[0] not in u:
    ancora = 'AQUI = os.path.dirname(os.path.abspath(__file__))\n'
    u = u.replace(ancora, ancora + um[0] + "\n", 1)
open(f5, "w").write(u)

import ast
for d in ("05-leitura", "06-proposta-e-validador", "07-sim-e-execucao", "08-auditoria", "09-systemd-e-testes"):
    ast.parse(open(E(d, "bot.py")).read())
print("etapas 5–9 sincronizadas com", KIT)
