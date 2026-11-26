#!/usr/bin/env python3
"""Etapa 7 — Telegram VPS remoto — você pede pelo Telegram, o Claude Code trabalha na sua VPS.

Travas no CÓDIGO (nêo só no prompt):
  1. Só quem está em DONOS fala com o bot. Lista vazia = ninguém (o bot só anota o ID de quem tentou).
  2. Toda mensagem passa primeiro por uma chamada SÓ DE LEITURA (Read/Glob/Grep e poucos comandos
     de consulta), presa na pasta de trabalho.
  3. Se a IA quiser mudar algo, ela só PROPÕE comandos. O bot confere (lista curta de comandos,
     todo caminho dentro da área, sem shell), guarda e pergunta "Confirma?". Depois do "sim",
     quem roda é o próprio bot, exatamente o que foi mostrado. A IA nunca tem ferramenta de escrita.
  4. Pasta de chaves, SSH e logins do Claude/Codex ficam negados nas duas fases.
  (A auditoria entra na etapa 8.)

Só biblioteca padrêo do Python. Long polling (sem webhook, sem porta aberta).
"""
import json, os, re, shlex, subprocess, sys, time, urllib.parse, urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
os.umask(0o077)   # auditoria.jsonl e área: só o dono do bot lê (os pedidos ficam lá)


def carregar_env(caminho):
    if os.path.exists(caminho):
        for linha in open(caminho):
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                k, v = linha.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


carregar_env(os.path.join(AQUI, ".env"))
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
DONOS = {int(x) for x in os.environ.get("DONOS", "").replace(" ", "").split(",") if x}
AREA = os.path.expanduser(os.environ.get("AREA", os.path.join(AQUI, "area")))
MODELO = os.environ.get("MODELO", "sonnet")
CLAUDE = os.environ.get("CLAUDE_BIN", "claude")
PRAZO_OK = int(os.environ.get("PRAZO_OK_S", "600"))   # pedido pendente vale 10 min
TEMPO_IA = int(os.environ.get("TEMPO_IA_S", "300"))
API = os.environ.get("TELEGRAM_API", "https://api.telegram.org") + f"/bot{TOKEN}/"   # TELEGRAM_API: só para teste com Telegram falso

H = os.path.expanduser("~")
NEGADO = [  # vale nas duas fases. Sintaxe do Claude Code: "~/" = home, "//" = caminho absoluto
    "Read(~/.config/**)", "Read(~/.ssh/**)", "Read(~/.claude/**)", "Read(~/.codex/**)",
    "Read(~/.npm-global/**)", "Read(~/.aws/**)", "Read(~/.docker/**)", "Read(~/.kube/**)", "Read(~/.gnupg/**)",
    "Read(~/.git-credentials)", "Read(~/.netrc)", "Read(~/.bash_history)", f"Read(/{AQUI}/.env)", "Read(**/.env)", "Read(//etc/shadow)", "Read(//root/**)",
    "Edit", "Write", "NotebookEdit",
    "Bash(sudo:*)", "Bash(su:*)", "Bash(reboot:*)", "Bash(shutdown:*)", "Bash(poweroff:*)",
    "Bash(systemctl:*)", "Bash(curl:*)", "Bash(wget:*)", "Bash(ssh:*)", "Bash(scp:*)",
    "Bash(env:*)", "Bash(printenv:*)", "Bash(cat:*)", "Bash(head:*)", "Bash(tail:*)", "Bash(less:*)",
    "Bash(more:*)", "Bash(sed:*)", "Bash(awk:*)", "Bash(grep:*)", "Bash(find:*)", "Bash(du:*)", "WebFetch", "WebSearch",
]
# Leitura de CONTEÚDO só dentro da área ("./**" = relativo à pasta onde o claude roda). Fora dela a IA só
# vê espaço em disco e nomes de pastas (df/ls), nunca o que tem dentro dos arquivos.
# Sem "du": "du --files0-from=<arquivo>" devolve o conteúdo do arquivo na mensagem de erro.
LEITURA = ["Read(./**)", "Glob(./**)", "Grep(./**)", "Bash(df:*)", "Bash(ls:*)",
           "Bash(free:*)", "Bash(uptime:*)"]
# Depois do "sim" quem roda é o BOT, nêo a IA: só estes comandos, só dentro da área, sem shell.
COMANDOS_OK = {"rm", "rmdir", "mv", "cp", "mkdir", "touch", "gzip", "gunzip", "tar"}
OPCOES_OK = {  # só opções sem valor; qualquer outra (inclusive -C, -t, --directory=) é recusada
    "rm": {"-r", "-f", "-rf", "-fr", "-v"}, "mv": {"-n", "-v"}, "cp": {"-r", "-a", "-n", "-v", "-p"},
    "mkdir": {"-p", "-v"}, "rmdir": {"-v"}, "touch": set(), "gzip": {"-k", "-v", "-9"}, "gunzip": {"-k", "-v"},
    "tar": {"-czf", "-cf", "-cjf", "-xzf", "-xf", "-xjf", "-tf", "-tzf", "-v"},
}
SIM_FORTE = {"sim", "s", "confirmo", "confirma", "yes", "y", "confirm", "si", "sí", "confirmar"}   # vale mesmo em frase: "sim, pode apagar"
SIM_SOZINHO = {"pode", "ok", "manda", "faz"}              # só vale como a mensagem inteira

ESQUEMA = json.dumps({
    "type": "object",
    "properties": {
        "resposta": {"type": "string", "description": "o que você descobriu, em linguagem simples, curto, na língua do dono"},
        "acao": {"type": ["object", "null"], "properties": {
            "descricao": {"type": "string", "description": "o que vai mudar, em uma frase"},
            "passos": {"type": "string", "description": "comandos exatos que serêo rodados"}},
            "required": ["descricao", "passos"]},
    },
    "required": ["resposta", "acao"],
})
REGRAS_LEITURA = (
    "Você é o assistente da VPS do dono, falando pelo Telegram. Nesta etapa você SÓ LÊ: investigue o que "
    f"for preciso dentro de {AREA} e responda. Se o pedido exigir mudar, apagar, mover ou criar algo, NêO "
    "tente fazer: preencha 'acao' com o que mudaria e os comandos exatos (só dentro da pasta de trabalho). "
    "Os passos sêo comandos simples (rm, rmdir, mv, cp, mkdir, touch, gzip, gunzip, tar), separados por ' && ', "
    "com caminhos relativos à pasta de trabalho; nada de |, ;, $, crase, ~ ou '..'. "
    "Sem curingas (* ? [): cite cada arquivo pelo nome, porque o bot executa os comandos sem shell. "
    "Se nêo precisar mudar nada, 'acao' = null. Nunca mostre chaves, senhas, tokens ou arquivos .env. "
    "Resposta curta, para celular, na mesma língua em que o dono escreveu."
)


def tg(metodo, **dados):
    req = urllib.request.Request(API + metodo, data=urllib.parse.urlencode(dados).encode())
    with urllib.request.urlopen(req, timeout=70) as r:
        return json.load(r)


def enviar(chat, texto):
    for i in range(0, len(texto), 3800):
        tg("sendMessage", chat_id=chat, text=texto[i:i + 3800])


def env_limpo():
    """O Claude Code roda pela assinatura: nenhuma chave de API vai para o processo."""
    e = {k: v for k, v in os.environ.items()
         if not k.startswith(("ANTHROPIC_", "OPENAI_", "OPENROUTER_", "TELEGRAM_"))}
    e["HOME"] = H
    return e


def claude(prompt, permitido, esquema=None):
    cmd = [CLAUDE, "-p", prompt, "--model", MODELO, "--output-format", "json",
           "--no-session-persistence", "--permission-mode", "dontAsk",
           # Ignora settings.json/CLAUDE.md/hooks/MCP do usuário: regras "allow" de lá (ex.: Bash(rm:*))
           # se somariam ao --allowedTools e furariam a trava. Só vale o que está aqui.
           "--setting-sources", "", "--strict-mcp-config",
           "--allowedTools", *permitido, "--disallowedTools", *NEGADO]
    if esquema:
        cmd += ["--json-schema", esquema, "--append-system-prompt", REGRAS_LEITURA]
    p = subprocess.run(cmd, cwd=AREA, env=env_limpo(), capture_output=True, text=True,
                       timeout=TEMPO_IA, stdin=subprocess.DEVNULL)
    try:
        saida = json.loads(p.stdout)
    except json.JSONDecodeError:
        raise RuntimeError((p.stderr or p.stdout)[-400:])
    if esquema:
        return saida.get("structured_output") or {"resposta": saida.get("result", ""), "acao": None}
    return saida.get("result", "")


def validar(passos):
    """Devolve a lista de comandos (listas de argumentos) ou levanta ValueError dizendo o porquê."""
    if any(c in passos for c in "|;`$<>\n~") or ".." in passos:
        raise ValueError("passos com caractere proibido")
    if any(c in passos for c in "*?["):
        raise ValueError("curinga nêo funciona aqui (o bot roda sem shell): cite cada arquivo pelo nome")
    cmds = []
    for parte in passos.split("&&"):
        args = shlex.split(parte.strip())
        if not args:
            continue
        if args[0] == "cd" and len(args) == 2 and os.path.realpath(args[1]) == os.path.realpath(AREA):
            continue  # "cd <área>" no começo é inofensivo
        if args[0] not in COMANDOS_OK:
            raise ValueError(f"comando fora da lista: {args[0]}")
        for a in args[1:]:
            if a.startswith("-"):
                # Opçêo só da lista curta: nada de -C/-t/--directory=... que levam para fora da área.
                if a not in OPCOES_OK.get(args[0], set()):
                    raise ValueError(f"opçêo nêo permitida: {a}")
                continue
            real = os.path.realpath(os.path.join(AREA, a))
            if real != os.path.realpath(AREA) and not real.startswith(os.path.realpath(AREA) + os.sep):
                raise ValueError(f"caminho fora da área: {a}")
            if real == os.path.realpath(AREA) and args[0] in ("rm", "mv"):
                raise ValueError("nêo posso apagar ou mover a própria área")
        cmds.append(args)
    if not cmds:
        raise ValueError("nenhum comando")
    return cmds


def eh_sim(texto):
    """'sim', 'sim, pode apagar' e 'pode' confirmam; 'pode listar antes?' e 'faz um backup primeiro' nêo."""
    if "?" in texto:
        return False
    palavras = re.sub(r"[^\wáéíóúêõç ]", "", texto.lower()).split()
    if not palavras:
        return False
    if any(w in ("no", "not") for w in (palavras[0], palavras[1:2] and palavras[1], palavras[-1])):
        return False   # "no" só cancela no começo: em português "no" também é "em + o" ("sim, apaga o que está no log")
    if any(w in palavras for w in ("mas", "pero", "but", "antes", "primeiro", "depois", "espera",
                                   "nêo", "nao", "cancela", "cancelar", "nunca", "pare", "para")):
        return False   # "sim, mas antes faz backup" nêo é um sim limpo: cancela e pede de novo
    return palavras[0] in SIM_FORTE or (len(palavras) == 1 and palavras[0] in SIM_SOZINHO)


def conferir_tar(args):
    """Antes de extrair, lista o pacote: membro com caminho absoluto, '..' ou link é recusado."""
    if not any(a.startswith("-x") for a in args):
        return
    arq = args[-1]
    p = subprocess.run(["tar", "-tvf", arq], cwd=AREA, capture_output=True, text=True, timeout=60)
    if p.returncode:
        raise ValueError("nêo consegui listar o pacote")
    for linha in p.stdout.splitlines():
        nome = linha.split(None, 5)[-1] if len(linha.split(None, 5)) == 6 else linha
        if linha[:1] in ("l", "h") or nome.startswith("/") or ".." in nome.split("/"):
            raise ValueError(f"pacote com caminho perigoso: {nome[:80]}")


def executar(cmds):
    saidas = []
    for args in cmds:
        if args[0] == "tar":
            try:
                conferir_tar(args)
            except ValueError as e:
                saidas.append(f"{' '.join(args)} → recusado: {e}")
                break
        p = subprocess.run(args, cwd=AREA, capture_output=True, text=True, timeout=120, env=env_limpo())
        saidas.append(f"{' '.join(args)} → {'ok' if p.returncode == 0 else 'erro: ' + p.stderr.strip()[:200]}")
        if p.returncode:
            break
    return "\n".join(saidas)


pendente = {}  # chat -> {"acao":..., "pedido":..., "t":...}


def tratar(msg):
    chat, quem = msg["chat"]["id"], msg.get("from", {}).get("id")
    texto = (msg.get("text") or "").strip()
    if quem not in DONOS:
        print(f"recusado: from.id={quem}", flush=True)
        enviar(chat, "Este bot é privado.")
        return
    if not texto:
        return
    if texto == "/start":
        enviar(chat, "Pronto. Peça o que quiser na VPS. Antes de mudar qualquer coisa eu pergunto.")
        return
    p = pendente.get(chat)
    if p and eh_sim(texto):
        pendente.pop(chat)
        if time.time() - p["t"] > PRAZO_OK:
            enviar(chat, "Esse pedido expirou. Peça de novo.")
            return
        r = executar(p["cmds"])
        enviar(chat, "Feito:\n" + r)
        return
    if p:
        pendente.pop(chat)
        palavras = re.sub(r"[^\wáéíóúêõç ]", "", texto.lower()).split()
        if palavras and palavras[0] in ("nêo", "nao", "n", "cancela", "cancelar", "no"):
            enviar(chat, "Cancelado. Nada foi mudado.")
            return
    tg("sendChatAction", chat_id=chat, action="typing")
    r = claude(texto, LEITURA, ESQUEMA)
    acao = r.get("acao")
    if acao:
        try:
            cmds = validar(acao.get("passos", ""))
        except ValueError as e:
            enviar(chat, f"{r['resposta']}\n\nIsso eu nêo faço por aqui ({e}). Faça direto no terminal, se for o caso.")
            return
        pendente[chat] = {"acao": acao, "cmds": cmds, "t": time.time()}
        enviar(chat, f"{r['resposta']}\n\nVou fazer: {acao['descricao']}\nComandos: {acao['passos']}\n\nConfirma? (sim/nêo)")
    else:
        enviar(chat, r["resposta"])


def main():
    if not TOKEN:
        sys.exit("falta TELEGRAM_BOT_TOKEN no .env")
    os.makedirs(AREA, exist_ok=True)
    print(f"no ar · donos={len(DONOS)} · área={AREA}", flush=True)
    desloc = 0
    while True:
        try:
            up = tg("getUpdates", offset=desloc, timeout=50)
            for u in up.get("result", []):
                desloc = u["update_id"] + 1
                if "message" in u:
                    try:
                        tratar(u["message"])
                    except Exception as e:  # um erro nêo derruba o bot
                        enviar(u["message"]["chat"]["id"], f"Deu erro: {str(e)[:200]}")
        except Exception as e:
            print("rede:", str(e)[:120], flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
