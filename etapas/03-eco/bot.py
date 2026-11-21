#!/usr/bin/env python3
"""Etapa 3 — o bot fica ouvindo (long polling) e devolve o que você escreveu. Sem porta aberta na VPS."""
import json, os, sys, time, urllib.parse, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))


def carregar_env(caminho):
    if os.path.exists(caminho):
        for linha in open(caminho):
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                k, v = linha.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


carregar_env(os.path.join(AQUI, ".env"))
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
API = os.environ.get("TELEGRAM_API", "https://api.telegram.org") + f"/bot{TOKEN}/"   # TELEGRAM_API: só para teste com Telegram falso


def tg(metodo, **dados):
    req = urllib.request.Request(API + metodo, data=urllib.parse.urlencode(dados).encode())
    with urllib.request.urlopen(req, timeout=70) as r:
        return json.load(r)


def enviar(chat, texto):
    for i in range(0, len(texto), 3800):
        tg("sendMessage", chat_id=chat, text=texto[i:i + 3800])


def tratar(msg):
    chat = msg["chat"]["id"]
    texto = (msg.get("text") or "").strip()
    if texto:
        enviar(chat, f"Você disse: {texto}")


def main():
    if not TOKEN:
        sys.exit("falta TELEGRAM_BOT_TOKEN no .env")
    print("no ar (eco)", flush=True)
    desloc = 0
    while True:
        try:
            up = tg("getUpdates", offset=desloc, timeout=50)
            for u in up.get("result", []):
                desloc = u["update_id"] + 1
                if "message" in u:
                    tratar(u["message"])
        except Exception as e:
            print("rede:", str(e)[:120], flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
