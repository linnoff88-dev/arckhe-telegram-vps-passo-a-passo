#!/usr/bin/env python3
"""Telegram FALSO, para testar o bot sem bot real, sem internet e sem token.

Imita só o que o bot usa da Bot API: getMe, getUpdates (long polling), sendMessage e sendChatAction.
Você "fala" como se fosse alguém no celular e vê o que o bot respondeu.

Terminal 1:  python3 ferramentas/telegram_falso.py servidor
Terminal 2:  TELEGRAM_API=http://127.0.0.1:8081 python3 bot.py
Terminal 3:  python3 ferramentas/telegram_falso.py fala --de 111 "oi"

Só biblioteca padrêo do Python. Escuta apenas em 127.0.0.1.
"""
import argparse, json, sys, threading, time, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

trava = threading.Condition()
updates = []     # o que "as pessoas" mandaram para o bot
respostas = []   # o que o bot mandou de volta
proximo = [1]    # próximo update_id


class Tratador(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silencioso
        pass

    def _dados(self):
        url = urllib.parse.urlparse(self.path)
        dados = {k: v[0] for k, v in urllib.parse.parse_qs(url.query).items()}
        n = int(self.headers.get("Content-Length") or 0)
        if n:
            corpo = self.rfile.read(n).decode()
            if "json" in (self.headers.get("Content-Type") or ""):
                dados.update(json.loads(corpo or "{}"))
            else:
                dados.update({k: v[0] for k, v in urllib.parse.parse_qs(corpo).items()})
        return url.path, dados

    def _json(self, obj, codigo=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    do_GET = do_POST = lambda self: self._rota()

    def _rota(self):
        caminho, d = self._dados()
        if caminho == "/_fala":                      # alguém manda mensagem para o bot
            with trava:
                uid = proximo[0]
                proximo[0] += 1
                de = int(d.get("de", 111))
                updates.append({"update_id": uid, "message": {
                    "message_id": uid, "date": int(time.time()), "text": d.get("texto", ""),
                    "chat": {"id": de, "type": "private"},
                    "from": {"id": de, "is_bot": False, "first_name": d.get("nome", "Teste")}}})
                trava.notify_all()
            return self._json({"ok": True, "update_id": uid, "respostas_ate_agora": len(respostas)})
        if caminho == "/_respostas":                 # o que o bot respondeu (a partir de ?desde=N)
            desde = int(d.get("desde", 0))
            with trava:
                return self._json({"ok": True, "total": len(respostas), "result": respostas[desde:]})
        partes = caminho.strip("/").split("/")
        if len(partes) != 2 or not partes[0].startswith("bot") or len(partes[0]) < 4:
            return self._json({"ok": False, "error_code": 404, "description": "Not Found"}, 404)
        metodo = partes[1]
        if metodo == "getMe":
            return self._json({"ok": True, "result": {"id": 1, "is_bot": True, "first_name": "Bot falso",
                                                      "username": "bot_falso_bot"}})
        if metodo == "getUpdates":
            desloc = int(d.get("offset", 0) or 0)
            espera = min(float(d.get("timeout", 0) or 0), 50)
            fim = time.time() + espera
            with trava:
                # Como no Telegram de verdade: pedir offset=N confirma (apaga) tudo antes de N.
                updates[:] = [u for u in updates if u["update_id"] >= desloc]
                while True:
                    novos = [u for u in updates if u["update_id"] >= desloc]
                    resto = fim - time.time()
                    if novos or resto <= 0:
                        return self._json({"ok": True, "result": novos})
                    trava.wait(resto)
        if metodo == "sendMessage":
            with trava:
                respostas.append({"chat_id": int(d.get("chat_id", 0)), "text": d.get("text", "")})
                trava.notify_all()
            return self._json({"ok": True, "result": {"message_id": 1000 + len(respostas)}})
        if metodo == "sendChatAction":
            return self._json({"ok": True, "result": True})
        return self._json({"ok": False, "error_code": 400, "description": f"método nêo imitado: {metodo}"}, 400)


def servidor(porta):
    try:
        s = ThreadingHTTPServer(("127.0.0.1", porta), Tratador)
    except OSError:
        sys.exit(f"a porta {porta} já está em uso: rode com --porta 8082 (e use a mesma porta no TELEGRAM_API e no fala)")
    print(f"Telegram falso no ar em http://127.0.0.1:{porta}  (Ctrl+C para parar)", flush=True)
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        pass


def pedir(base, caminho, **dados):
    req = urllib.request.Request(base + caminho, data=urllib.parse.urlencode(dados).encode())
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def fala(base, de, texto, espera, silencio):
    """Manda o texto como a pessoa `de` e mostra as respostas do bot (espera até `espera` s)."""
    r = pedir(base, "/_fala", de=de, texto=texto)
    desde, fim, ultima, viu = r["respostas_ate_agora"], time.time() + espera, None, 0
    print(f"você ({de}) → {texto}")
    while time.time() < fim:
        novas = pedir(base, "/_respostas", desde=desde)["result"]
        for m in novas:
            if m["chat_id"] == de:
                print("bot → " + m["text"].replace("\n", "\n      "))
                viu += 1
        if novas:
            desde += len(novas)
            ultima = time.time()
        if ultima and time.time() - ultima >= silencio:
            break
        time.sleep(0.3)
    if not viu:
        print(f"(o bot nêo respondeu em {espera:.0f} s — ele está rodando com TELEGRAM_API apontando para cá?)")
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("servidor", help="sobe o Telegram falso")
    a.add_argument("--porta", type=int, default=8081)
    b = sub.add_parser("fala", help="manda uma mensagem para o bot e mostra a resposta")
    b.add_argument("texto")
    b.add_argument("--de", type=int, default=111, help="ID de quem fala (o seu ID ou um estranho)")
    b.add_argument("--porta", type=int, default=8081)
    b.add_argument("--espera", type=float, default=120, help="segundos esperando a 1ª resposta")
    b.add_argument("--silencio", type=float, default=3, help="depois da resposta, espera mais isto")
    x = ap.parse_args()
    if x.cmd == "servidor":
        servidor(x.porta)
    else:
        sys.exit(fala(f"http://127.0.0.1:{x.porta}", x.de, x.texto, x.espera, x.silencio))


if __name__ == "__main__":
    main()
