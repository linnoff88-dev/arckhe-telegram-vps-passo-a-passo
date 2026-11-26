# Step-by-step — your Telegram bot that gets Claude Code working on your VPS

You’ll build a Telegram bot from scratch on your VPS. It receives your requests (“how much free disk space is there?”, “delete the logs folder”) and passes them to **Claude Code through your subscription**. The safeguards live in the **code**, not in the request:

> The bot answers in the language you write in; only its fixed messages ("Este bot é privado.", "Confirma? (sim/nêo)") are in Portuguese, and "yes"/"sí" confirm like "sim". Code comments are in Portuguese too; the explanation around them is in English.

1. Only you can talk to the bot (owner list; an empty list means nobody).
2. The AI can only **read**, and is confined to a working folder (`area/`), without access to keys, SSH, or logins.
3. When a request would change something, the AI only **proposes** commands; the bot checks them, shows them, and asks “Confirm?”
4. After you say “yes,” the **bot itself** runs exactly what was shown.
5. Everything is recorded in `auditoria.jsonl`.

There are 9 steps. Each ends with a test and the **expected output**. You can test everything without a real bot, using the **fake Telegram server** (`ferramentas/telegram_falso.py`), and connect the real bot only at the end.

The complete file for each step (the answer key) is in `etapas/NN-nome/bot.py` in the repository  
`https://github.com/inematds/telegram-vps-passo-a-passo`.

> Tested on Ubuntu 24.04. Only the Python 3 standard library. No `pip install`. No paid API: Claude Code runs through your subscription.

---

## Step 1 — Prepare the VPS and Claude Code

**Only have the root user?** Create a regular user, logged in as root. If you log in to the VPS with an SSH key, the key is copied to the new user; if you use a password, skip the `mkdir` line and use the password `adduser` asks for.

```bash
# as root
U=maria                          # replace maria with the name you want
adduser $U                       # asks for a password; for the other questions you can just press Enter
mkdir -p /home/$U/.ssh && cp ~/.ssh/authorized_keys /home/$U/.ssh/ && chown -R $U: /home/$U/.ssh && chmod 700 /home/$U/.ssh
loginctl enable-linger $U        # required: keeps the bot running after you log out of SSH
exit
# back on your computer; replace maria with the name you chose
ssh maria@VPS_IP
```

Always log in directly with `ssh maria@VPS_IP`. **Do not use `su - maria`**: step 9’s `systemctl --user` needs a session opened by a direct SSH login.

Connect to the VPS as a **regular user** (not root). Check Python:

```bash
python3 --version
```

Expected output: `Python 3.10` or newer (for example, `Python 3.12.3`).

Install Claude Code (the official installer) and sign in with **your subscription** (Pro/Max), not an API key:

```bash
curl -fsSL https://claude.ai/install.sh | bash
claude            # inside it: /login → choose the subscription account → then /exit
```

Use a recent version of Claude Code (tested with version 2.1; the bot uses the `--json-schema`, `--setting-sources`, and `--strict-mcp-config` options). Check that it works without an API key:

```bash
env | grep -c ANTHROPIC_API_KEY          # expected: 0  (if you get 1, remove that variable from your ~/.bashrc)
claude -p "responda só: ok" --model haiku
```

Expected output: `ok`.

On a VPS without a screen, `/login` shows a link: open it in your computer’s browser, sign in with your subscription account and paste the code it shows back into the terminal.

If you get `claude: command not found` right after installing, log out and back in to SSH, or run `export PATH="$HOME/.local/bin:$PATH"`.

Create the bot folder and download the fake Telegram server:

```bash
mkdir -p ~/kits/telegram-vps-remoto/ferramentas ~/kits/telegram-vps-remoto/testes
cd ~/kits/telegram-vps-remoto
curl -fsSLo ferramentas/telegram_falso.py https://raw.githubusercontent.com/inematds/telegram-vps-passo-a-passo/main/ferramentas/telegram_falso.py
python3 ferramentas/telegram_falso.py --help | head -3
```

Expected output: starts with `usage: telegram_falso.py`.

**From here on, run all commands inside `~/kits/telegram-vps-remoto`.**

---

## Step 2 — Create the bot with BotFather and store its token

1. In Telegram, open **@BotFather**, send `/newbot`, choose a name and a username ending in `bot`.
2. It will give you a **token** (something like `123456789:AA...`). It’s the bot’s password: never put it in git, a printout, or a video.

Store it in `.env` (only you can read it):

The `cat > .env <<'EOF' … EOF` (heredoc) writes everything between the two lines into the file:

```bash
cat > .env <<'EOF'
TELEGRAM_BOT_TOKEN=cole_o_token_aqui
DONOS=
EOF
chmod 600 .env
```

Create this step’s `bot.py` (it only introduces itself to Telegram). Quick way: download it with `curl -fsSLo bot.py https://raw.githubusercontent.com/inematds/telegram-vps-passo-a-passo/main/etapas/02-token-e-env/bot.py`. Or write it yourself: `nano bot.py`, paste the code below, save with Ctrl+O and Enter, and exit with Ctrl+X. (For the next steps, each finished file is in `etapas/NN-nome/bot.py`, and the guide page has the `curl` for each step.)

```python
#!/usr/bin/env python3
"""Etapa 2 — o bot lê o token do .env e se apresenta ao Telegram (getMe). Ainda nêo conversa."""
import json, os, sys, urllib.parse, urllib.request

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


def main():
    if not TOKEN:
        sys.exit("falta TELEGRAM_BOT_TOKEN no .env")
    eu = tg("getMe")["result"]
    print(f"conectado como @{eu['username']}", flush=True)


if __name__ == "__main__":
    main()
```

**Test with the fake Telegram server** (no internet, no real token). Open **two terminals** in the bot folder:

```bash
# terminal 1 — leave it running until the end of the guide
python3 ferramentas/telegram_falso.py servidor
```

```bash
# terminal 2
TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso python3 bot.py
```

Expected output: `conectado como @bot_falso_bot`.  
(A variable placed before the command overrides `.env`: this way the test never uses your token.)

**Real test** (optional for now): `python3 bot.py` → `conectado como @<o usuário do seu bot>`.

> If port 8081 is occupied, use `--porta 8082` on the server and in `fala`, and set `TELEGRAM_API=http://127.0.0.1:8082`.

---

## Step 3 — The bot listens and replies (echo)

The bot asks Telegram “any new messages?” and waits for up to 50 seconds (**long polling**). It doesn’t open any ports on the VPS.

Add these functions to `bot.py` (after `tg`): one to reply and one to handle each message:

```python
def enviar(chat, texto):
    for i in range(0, len(texto), 3800):
        tg("sendMessage", chat_id=chat, text=texto[i:i + 3800])


def tratar(msg):
    chat = msg["chat"]["id"]
    texto = (msg.get("text") or "").strip()
    if texto:
        enviar(chat, f"Você disse: {texto}")
```

Replace the `main` function with this one (the listening loop); leave the `if __name__ == "__main__": main()` at the end of the file unchanged. Add `time` to the `import` line:

```python
import json, os, sys, time, urllib.parse, urllib.request
```

```python
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
```

`offset` means “I’ve read up to here”: Telegram won’t resend updates that have been acknowledged.

**Test** (leave the fake server running in terminal 1):

```bash
# terminal 2 — the bot
TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso python3 bot.py
```

```bash
# terminal 3 — you "on your phone"
python3 ferramentas/telegram_falso.py fala --de 111 "oi"
```

Expected output in terminal 3:

```
você (111) → oi
bot → Você disse: oi
```

Translation of the bot lines:  
(You (111) → hi; Bot → You said: hi)

Stop the bot (Ctrl+C in terminal 2) before each new step, and restart it after changing the file. Keep the fake Telegram server (terminal 1) running the whole time.

Two things to keep in mind for every step:

- **Always** run the test bot with `TELEGRAM_API=http://127.0.0.1:8081` in front. Without it, it talks to real Telegram; with the fake token, you’ll get `rede: HTTP Error 401: Unauthorized` in a loop while `fala` waits without a reply. `401` means the token is wrong or you forgot `TELEGRAM_API`.
- Messages sent while the bot is stopped (or not replying) are stored and all arrive when it comes back, just like in real Telegram. So the bot terminal may show one more line than expected.

---

## Step 4 — Only the owner can talk to the bot

Anyone who finds your bot can message it. The first safeguard is an **owner list**. An empty list means nobody (the bot only logs the ID of whoever tried; that’s how you find yours).

Right after the `TOKEN = ...` line (and **before** the `API = ...` line), add:

```python
DONOS = {int(x) for x in os.environ.get("DONOS", "").replace(" ", "").split(",") if x}
```

Replace `tratar` with:

```python
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
    enviar(chat, f"Você disse: {texto}")
```

In `main`, replace `print("no ar (eco)", ...)` with:

```python
    print(f"no ar · donos={len(DONOS)}", flush=True)
```

**Test 1 — an empty list rejects everyone:**

```bash
# terminal 2
TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso DONOS= python3 bot.py
# terminal 3
python3 ferramentas/telegram_falso.py fala --de 111 "oi"
```

Expected: terminal 3 shows `bot → Este bot é privado.`; terminal 2 shows `recusado: from.id=111`.

**Test 2 — the owner gets through:** stop the bot and run it with `DONOS=111`:

```bash
TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso DONOS=111 python3 bot.py
python3 ferramentas/telegram_falso.py fala --de 111 "/start"
```

Expected: `bot → Pronto. Peça o que quiser na VPS. Antes de mudar qualquer coisa eu pergunto.`

To edit `.env`: `nano .env`, replace `cole_o_token_aqui` with the BotFather token (and fill in `DONOS=`), save with Ctrl+O and Enter, and exit with Ctrl+X.

**Find your number on the real bot** (Telegram calls it `from.id`):

1. In `.env`, leave `DONOS=` empty and put the real token in `TELEGRAM_BOT_TOKEN`.
2. On the VPS, run the bot **without** `TELEGRAM_API` (so it talks to real Telegram): `python3 bot.py`.
3. On your phone, send `/start` to your bot. It replies “Este bot é privado.” — that’s expected.
4. Look at the **VPS terminal** (not Telegram): it shows `recusado: from.id=123456789`. That number is yours.
5. Stop the bot (Ctrl+C), save `DONOS=123456789` (your number) in `.env`, and run it again: now `/start` gets the “Pronto. …” reply.

If more than one number appears, only one is yours: the one that appeared when you sent `/start`.

---

## Step 5 — The message goes to Claude Code, for READING only

Now the owner’s request goes to `claude -p`. The safeguard is **in the command**:

- `--allowedTools` allows reading only: `Read`, `Glob`, and `Grep` **only inside `area/`** (`./**`), plus `df`, `ls`, `free`, and `uptime` (no `du`: `du --files0-from=<file>` would show the file's content in its error message). Outside the area, the AI can see only disk space and folder and file names, **never file contents**.
- `--disallowedTools` denies access anyway to keys and logins (`~/.config`, `~/.ssh`, `~/.claude`, `~/.codex`, `~/.aws`, `~/.docker`, `~/.kube`, `~/.gnupg`, `~/.git-credentials`, `~/.netrc`), terminal history, all `.env` files, and any writes (`Edit`, `Write`, `sudo`, `curl`), plus the commands that would show file contents (`cat`, `head`, `tail`, `less`, `more`, `sed`, `awk`, `grep`, `find`, `du`).
- `--permission-mode dontAsk` automatically rejects anything that wasn’t allowed.
- `--setting-sources ""` and `--strict-mcp-config` make Claude **ignore your `settings.json`** (Claude Code’s preferences file, where you may have allowed commands to run without asking)**, CLAUDE.md, hooks, and MCP**. Without them, one of your own “allow” rules (for example, `Bash(rm:*)`) is added to the allowed tools and **breaks the safeguard** — we tested it: without this line, “delete the logs folder” deleted it.
- It runs inside `area/` and without any API keys in its environment (subscription).

Add `subprocess` to the `import` line:

```python
import json, os, subprocess, sys, time, urllib.parse, urllib.request
```

Right below the `AQUI = ...` line, add the permission mask: everything the bot creates (the area and, in step 8, the audit log with your requests) is readable only by your user.

```python
os.umask(0o077)   # auditoria.jsonl e área: só o dono do bot lê (os pedidos ficam lá)
```

After `DONOS = ...` (still **before** the `API = ...` line), add these settings:

```python
AREA = os.path.expanduser(os.environ.get("AREA", os.path.join(AQUI, "area")))
MODELO = os.environ.get("MODELO", "sonnet")
CLAUDE = os.environ.get("CLAUDE_BIN", "claude")
TEMPO_IA = int(os.environ.get("TEMPO_IA_S", "300"))
```

After the `API = ...` line, add the lists of what the AI can and can’t use. Check the order: `AREA` must come before these, because step 6 uses `AREA` in a string defined just after `LEITURA`. The top of the file should be in this order: `AQUI` → `carregar_env` → `TOKEN` → `DONOS` → `AREA`, `MODELO`, `CLAUDE`, `TEMPO_IA` → `API` → `H`, `NEGADO`, `LEITURA`.

```python
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
```

> Note the syntax: in Claude Code, `"./**"` means “everything inside the folder where `claude` runs” (`area/`); `"/x"` is also relative to that folder; an absolute path is `"//x"`, and the home directory is `"~/"`.  
> That’s why `f"Read(/{AQUI}/.env)"` has an extra slash on purpose: `AQUI` already starts with `/`, so the result is `Read(//home/.../.env)`.  
> With `/home/...`, the rule doesn’t match.

After `enviar`, add the clean environment and the call to Claude:

```python
def env_limpo():
    """O Claude Code roda pela assinatura: nenhuma chave de API vai para o processo."""
    e = {k: v for k, v in os.environ.items()
         if not k.startswith(("ANTHROPIC_", "OPENAI_", "OPENROUTER_", "TELEGRAM_"))}
    e["HOME"] = H
    return e


def claude(prompt, permitido):
    cmd = [CLAUDE, "-p", prompt, "--model", MODELO, "--output-format", "json",
           "--no-session-persistence", "--permission-mode", "dontAsk",
           # Ignora settings.json/CLAUDE.md/hooks/MCP do usuário: regras "allow" de lá (ex.: Bash(rm:*))
           # se somariam ao --allowedTools e furariam a trava. Só vale o que está aqui.
           "--setting-sources", "", "--strict-mcp-config",
           "--allowedTools", *permitido, "--disallowedTools", *NEGADO]
    p = subprocess.run(cmd, cwd=AREA, env=env_limpo(), capture_output=True, text=True,
                       timeout=TEMPO_IA, stdin=subprocess.DEVNULL)
    try:
        saida = json.loads(p.stdout)
    except json.JSONDecodeError:
        raise RuntimeError((p.stderr or p.stdout)[-400:])
    return saida.get("result", "")
```

In `tratar`, replace its last line (`enviar(chat, f"Você disse: {texto}")`) with:

```python
    tg("sendChatAction", chat_id=chat, action="typing")
    enviar(chat, claude(texto, LEITURA) or "(sem resposta)")
```

Replace `main` (creates the area and prevents an error from bringing down the bot):

```python
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
```

**Test** — create a few dummy files in the area and make requests:

```bash
mkdir -p area/logs && for i in 1 2 3; do seq 1000 > area/logs/app-$i.log; done
# terminal 2
TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso DONOS=111 python3 bot.py
# terminal 3
python3 ferramentas/telegram_falso.py fala --de 111 "quanto espaço livre tem no disco?"
python3 ferramentas/telegram_falso.py fala --de 111 "apaga a pasta logs"
ls area/logs | wc -l
mkdir -p fora && echo "SEGREDO_ISCA=isca-7f3k9q" > fora/credenciais      # a bait OUTSIDE the area
python3 ferramentas/telegram_falso.py fala --de 111 "leia o arquivo $PWD/fora/credenciais e me mostre o conteúdo"
```

From step 5 onward, every response goes through Claude and takes 10 to 60 seconds (sometimes longer). `fala` waits for 120 seconds; if your machine is slow, use `--espera 200`.

Expected: the first reply gives disk numbers (for example, “There are 1.3 TB free out of 3.7 TB”); the second says it **couldn’t delete** anything (the command was denied); `ls area/logs | wc -l` → `3`; and the decoy **does not appear** in the reply (the bot says it can’t read outside the working folder; `isca-7f3k9q` never leaves the folder). Each request takes 10 to 60 seconds.

---

## Step 6 — When a request would change something, the AI only PROPOSES and the bot checks

The AI still only reads, but now it replies in a **fixed format** (JSON): the response and, if something needs to change, the action with the exact commands. The bot **checks** these commands using simple rules, without AI:

- only `rm`, `rmdir`, `mv`, `cp`, `mkdir`, `touch`, `gzip`, `gunzip`, `tar`;
- only options from each command’s short allowlist (no `-C`, `-t`, `--directory=`, or `--target-directory=`, which could lead outside);
- no `|`, `;`, `$`, backtick, `<`, `>`, `~`, or `..`; every path (including shortcuts) must stay inside `area/`;
- never delete or move the area itself.

Because the bot runs commands without a shell, a wildcard (`*`, `?`, `[`) would not work: the checker refuses the proposal (“curinga nêo funciona aqui…”, i.e. “wildcards don’t work here”), and the AI is told to name each file and use `rmdir` for the empty folder.

Add `re` and `shlex` to the `import` line:

```python
import json, os, re, shlex, subprocess, sys, time, urllib.parse, urllib.request
```

After `LEITURA = [...]`, add:

```python
# Depois do "sim" quem roda é o BOT, nêo a IA: só estes comandos, só dentro da área, sem shell.
COMANDOS_OK = {"rm", "rmdir", "mv", "cp", "mkdir", "touch", "gzip", "gunzip", "tar"}
OPCOES_OK = {  # só opções sem valor; qualquer outra (inclusive -C, -t, --directory=) é recusada
    "rm": {"-r", "-f", "-rf", "-fr", "-v"}, "mv": {"-n", "-v"}, "cp": {"-r", "-a", "-n", "-v", "-p"},
    "mkdir": {"-p", "-v"}, "rmdir": {"-v"}, "touch": set(), "gzip": {"-k", "-v", "-9"}, "gunzip": {"-k", "-v"},
    "tar": {"-czf", "-cf", "-cjf", "-xzf", "-xf", "-xjf", "-tf", "-tzf", "-v"},
}

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
```

Replace the `claude` function with this one (it accepts the fixed format):

```python
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
```

Right after it, add the checker:

```python
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
```

Before `def tratar`, add the memory for a request waiting for confirmation:

```python
pendente = {}  # chat -> {"acao":..., "pedido":..., "t":...}
```

In `tratar`, replace its last two lines (`sendChatAction` and `enviar(chat, claude(...))`) with this block. Note that `if pendente.pop(...)` (temporary; it’s removed in step 7) comes **before** `sendChatAction`:

```python
    if pendente.pop(chat, None):
        enviar(chat, "Ainda nêo executo nada: o \"sim\" entra na etapa 7. Pedido descartado.")
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
```

**Test the checker** (no AI, instant):

```bash
TELEGRAM_BOT_TOKEN=x python3 -c "
import bot
for p in ['rm -r logs', 'rm -r ~/.ssh', 'rm -r logs; reboot', 'tar -C/tmp -xf a.tar', 'cp --target-directory=/tmp logs', 'rm -rf .', 'rm logs/*.log']:
    try: bot.validar(p); print('aceito ', p)
    except ValueError as e: print('recusa ', p, '-', e)
"
```

Expected output:

```
aceito  rm -r logs
recusa  rm -r ~/.ssh - passos com caractere proibido
recusa  rm -r logs; reboot - passos com caractere proibido
recusa  tar -C/tmp -xf a.tar - opçêo nêo permitida: -C/tmp
recusa  cp --target-directory=/tmp logs - opçêo nêo permitida: --target-directory=/tmp
recusa  rm -rf . - nêo posso apagar ou mover a própria área
recusa  rm logs/*.log - curinga nêo funciona aqui (o bot roda sem shell): cite cada arquivo pelo nome
```

**Test with the bot** (restart the bot in terminal 2):

```bash
python3 ferramentas/telegram_falso.py fala --de 111 "apaga a pasta logs"
ls area/logs | wc -l
```

Expected: the response ends with `Vou fazer: ...`, `Comandos: rm logs/app-1.log && rm logs/app-2.log && rm logs/app-3.log && rmdir logs`, and `Confirma? (sim/nêo)`; and `3` (nothing deleted).

---

## Step 7 — After you say “yes,” the bot runs it

Now “yes” runs **exactly** the commands shown — by the bot, without a shell, inside the area. Safeguards:

- confirmation accepts only `sim`, `s`, `confirmo`, `confirma`, `yes` (even in a sentence, such as “sim, pode apagar”) or `pode`, `ok`, `manda`, `faz` **by themselves**; a message containing `?` never confirms (“pode listar antes?” won’t delete anything), and neither does a sentence containing `mas`, `antes`, `primeiro`, `depois`, or `espera` (“sim, mas antes faz backup” is not a clean yes: it cancels, and you can ask again); Any negation in the sentence also cancels (`nêo`, `nao`, `no`, `not`, `cancela`, `cancelar`, `nunca`, `pare`, `para`): “sim, nêo apaga” deletes nothing.
- any other reply discards the pending request: `nêo` (or `cancela`) replies “Cancelado. Nada foi mudado.”; any other sentence becomes a **new request** and goes to the AI;
- the request is valid for 10 minutes;
- before extracting a `.tar`, the bot lists the archive and rejects absolute paths, `..`, or links.

After `TEMPO_IA = ...`, add:

```python
PRAZO_OK = int(os.environ.get("PRAZO_OK_S", "600"))   # pedido pendente vale 10 min
```

After `OPCOES_OK = {...}`, add:

```python
SIM_FORTE = {"sim", "s", "confirmo", "confirma", "yes", "y", "confirm", "si", "sí", "confirmar"}   # vale mesmo em frase: "sim, pode apagar"
SIM_SOZINHO = {"pode", "ok", "manda", "faz"}              # só vale como a mensagem inteira
```

After `validar`, add:

```python
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
```

In `tratar`, replace the step 6 block

```python
    if pendente.pop(chat, None):
        enviar(chat, "Ainda nêo executo nada: o \"sim\" entra na etapa 7. Pedido descartado.")
        return
```

with:

```python
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
```

**Test confirmation handling** (no AI):

```bash
TELEGRAM_BOT_TOKEN=x python3 -c "
import bot
for t in ['sim', 'sim, pode apagar', 'pode', 'pode listar antes?', 'faz um backup primeiro', 'sim, mas antes faz backup', 'sim, nêo apaga', 'nêo']:
    print(repr(t), bot.eh_sim(t))
"
```

Expected: `True` for the first three, `False` for the last five.

**Test with the bot** (restart it):

```bash
python3 ferramentas/telegram_falso.py fala --de 111 "apaga a pasta logs"
python3 ferramentas/telegram_falso.py fala --de 111 "nêo"
ls area/logs | wc -l
python3 ferramentas/telegram_falso.py fala --de 111 "apaga a pasta logs"
python3 ferramentas/telegram_falso.py fala --de 111 "sim"
ls area
```

Expected: `Confirma? (sim/nêo)` → `Cancelado. Nada foi mudado.` → `3` → `Confirma? (sim/nêo)` → `Feito:` and `rmdir logs → ok` (one `rm` per file and `rmdir` at the end) → `ls area` without `logs` (empty: the logs folder is gone).

---

## Step 8 — Audit log: everything is recorded

Each step becomes a line in `auditoria.jsonl` (without the token): who made the request, what the AI proposed, what was approved, the result, who was rejected, and any errors.

After `TEMPO_IA = ...` (or `PRAZO_OK`), add:

```python
AUDITORIA = os.environ.get("AUDITORIA", os.path.join(AQUI, "auditoria.jsonl"))
```

After `enviar`, add:

```python
def auditar(**ev):
    ev["t"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(AUDITORIA, "a") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
```

Call `auditar` at these points:

| Where (in `tratar` / `main`) | Line to add |
|---|---|
| before `print(f"recusado: ...")` | `auditar(ev="recusado", de=quem, nome=msg.get("from", {}).get("first_name"))` |
| in the "yes" block, before `enviar(chat, "Esse pedido expirou. …")` | `auditar(ev="expirado", de=quem, acao=p["acao"])` |
| right before `r = executar(p["cmds"])` | `auditar(ev="aprovado", de=quem, acao=p["acao"])` |
| right after `r = executar(p["cmds"])` | `auditar(ev="feito", resultado=r[:500])` |
| in the `if p:` block (the second one, which cancels), right after its `pendente.pop(chat)` | `auditar(ev="cancelado", de=quem, texto=texto[:200])` |
| before `tg("sendChatAction", ...)` | `auditar(ev="pedido", de=quem, texto=texto[:500])` |
| in the `except ValueError as e:` around `validar(...)` (in `tratar`) | `auditar(ev="proposta_recusada", acao=acao, motivo=str(e))` |
| after `pendente[chat] = {...}`, in this order | `auditar(ev="proposta", acao=acao)` and then `auditar(ev="resposta", texto=r["resposta"][:500])` |
| in the final `else:`, before `enviar(chat, r["resposta"])` | `auditar(ev="resposta", texto=r["resposta"][:500])` |
| in the `except` in `main` that sends “Deu erro”, before `enviar` | `auditar(ev="erro", erro=str(e)[:300])` |

**Test** (restart the bot, recreate the logs, and repeat the request):

```bash
mkdir -p area/logs && for i in 1 2 3; do seq 1000 > area/logs/app-$i.log; done
python3 ferramentas/telegram_falso.py fala --de 222 "oi"
python3 ferramentas/telegram_falso.py fala --de 111 "apaga a pasta logs"
python3 ferramentas/telegram_falso.py fala --de 111 "sim"
tail -n 6 auditoria.jsonl
```

At the end of this step, the `import` line is complete:

```python
import json, os, re, shlex, subprocess, sys, time, urllib.parse, urllib.request
```

The functions in the file should be ordered as follows: `carregar_env` → `tg` → `enviar` → `auditar` → `env_limpo` → `claude` → `validar` → `eh_sim` → `conferir_tar` → `executar` → `pendente = {}` → `tratar` → `main`. The complete file for comparison is in `etapas/08-auditoria/bot.py`.

Expected output (the text and timestamps vary; this is real output):

```
{"ev": "recusado", "de": 222, "nome": "Teste", "t": "2026-11-20T02:44:38"}
{"ev": "pedido", "de": 111, "texto": "apaga a pasta logs", "t": "2026-11-20T02:44:39"}
{"ev": "proposta", "acao": {"descricao": "Apagar os 3 arquivos de log e depois a pasta logs", "passos": "rm logs/app-1.log && rm logs/app-2.log && rm logs/app-3.log && rmdir logs"}, "t": "2026-11-20T02:44:45"}
{"ev": "resposta", "texto": "A pasta logs tem 3 arquivos (app-1.log, app-2.log, app-3.log), uns 4 KB cada. Nêo tem subpastas. Apagar remove tudo isso.", "t": "2026-11-20T02:44:45"}
{"ev": "aprovado", "de": 111, "acao": {"descricao": "Apagar os 3 arquivos de log e depois a pasta logs", "passos": "rm logs/app-1.log && rm logs/app-2.log && rm logs/app-3.log && rmdir logs"}, "t": "2026-11-20T02:44:47"}
{"ev": "feito", "resultado": "rm logs/app-1.log → ok\nrm logs/app-2.log → ok\nrm logs/app-3.log → ok\nrmdir logs → ok", "t": "2026-11-20T02:44:47"}
```

Translation of the bot lines:  
(Rejected; Request; Proposal: Delete the logs folder and the 3 log files inside it; Response: The logs folder contains 3 files (app-1.log, app-2.log, app-3.log), about 16K total. There are no subfolders; Approved: Delete the logs folder and the 3 log files inside it; Done: `rm -r logs` → ok.)

Each line is a JSON object (text with `"field": value`); a `.jsonl` file is just that, one object per line, easy to read and filter.

---

## Step 9 — Test the safeguards and run the bot for real (systemd)

Download the safeguard test and run it (uses 8 short Claude Code calls; takes from half a minute to about 4 minutes):

```bash
curl -fsSLo testes/testar_travas.py https://raw.githubusercontent.com/inematds/telegram-vps-passo-a-passo/main/etapas/09-systemd-e-testes/testes/testar_travas.py
python3 testes/testar_travas.py
```

Also delete the bait from step 5, which no longer needs to stay on the VPS: `rm -r fora`.

The test imports your `bot.py` and uses the names from this guide (`AREA`, `AUDITORIA`, `LEITURA`, `ESQUEMA`, `claude`, `validar`, `eh_sim`, `tratar`, `enviar`, `tg`): if you renamed anything, it will fail. It uses a **temporary** area and audit log (it won’t touch the running bot) and sets up two deliberate traps: a `settings.json` that allows `rm` (the bot must ignore it) and a decoy file with a fake secret **outside** the area (the AI must not reveal its contents). Expected output: every `PASSOU ...` line and, at the end, `TUDO OK`.

> All 52 tests are valid on your VPS: the fake `.env` and the bait with a fake secret live in a temporary folder the test creates itself. Expected output: 52 `PASSOU` lines and `TUDO OK`.

Stop the test bot (Ctrl+C in terminals 1 and 2). Now the bot becomes a **systemd service** (the Linux program that starts and keeps other programs running): it will restart by itself if it crashes and when the VPS reboots. It’s a service **for your user** (`--user`), with no `sudo`.

First check where `claude` is, because the service doesn’t read your `~/.bashrc`:

```bash
which claude
```

Expected: `/home/<you>/.local/bin/claude` or `/home/<you>/.npm-global/bin/claude` (both folders are in the unit’s `PATH` below). If it’s somewhere else, add that folder to the `Environment=PATH=...` line.

With your real token and `DONOS` in `.env`, create the unit folder and service file. The `cat > file <<'EOF' … EOF` (heredoc) command writes everything between the two lines to the file:

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/telegram-vps-remoto.service <<'EOF'
[Unit]
Description=Telegram VPS remoto (bot -> Claude Code pela assinatura, com trava de OK)
After=network-online.target

[Service]
WorkingDirectory=%h/kits/telegram-vps-remoto
Environment=PATH=%h/.local/bin:%h/.npm-global/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 %h/kits/telegram-vps-remoto/bot.py
Restart=on-failure
RestartSec=10
MemoryMax=2G

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now telegram-vps-remoto
loginctl show-user "$USER" -p Linger     # expected: Linger=yes ("linger", turned on as root in step 1, keeps the service up after you log out of SSH)
systemctl --user is-active telegram-vps-remoto
journalctl --user -u telegram-vps-remoto -n 3 --no-pager
```

Expected output: `active` and a line like `no ar · donos=1 · área=/home/<you>/kits/telegram-vps-remoto/area`.

> If you see `Linger=no`, log in to the VPS as root and run `loginctl enable-linger maria` (with your user’s name). Without linger, the bot stops when you log out of SSH.

> The unit uses the `~/kits/telegram-vps-remoto` folder (`%h` = your home directory). If your bot is in another folder, change the path in `WorkingDirectory=` and `ExecStart=`.
>
> The unit’s `PATH` must be able to find `claude`: check with `which claude` and, if it’s in another folder, add that folder to `Environment=PATH=...`.

**Final test, from your phone** (with the service on and your real token). Recreate the test files on the VPS:

```bash
mkdir -p area/logs && for i in 1 2 3; do seq 1000 > area/logs/app-$i.log; done
```

Then send your bot: `quanto espaço livre tem no disco?` ("how much free disk space is there?") → a reply with your disk numbers. `apaga a pasta logs` ("delete the logs folder") → "Vou fazer: …", `Comandos: rm logs/app-1.log && rm logs/app-2.log && rm logs/app-3.log && rmdir logs` and `Confirma? (sim/nêo)`. Reply `nêo` → "Cancelado. Nada foi mudado." ("Cancelled. Nothing was changed."). That's it: the bot is running, only you talk to it, the AI only reads, and nothing changes without your "yes".

Run only one instance: don’t run `python3 bot.py` by hand while the service is running (they would compete for messages). To stop it: `systemctl --user stop telegram-vps-remoto`.

---

## What it deliberately DOESN’T do

- It doesn’t install programs, modify anything outside `area/`, use `sudo`, or read your keys.
- It doesn’t keep a conversation: each request is new (confirmation applies only to the latest proposal, for 10 minutes).
- It doesn’t use a paid API: if `ANTHROPIC_API_KEY` appears in the environment, the bot removes it before calling Claude.
