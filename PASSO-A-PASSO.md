# Passo a passo — seu bot de Telegram que manda o Claude Code trabalhar na sua VPS

Você vai montar, do zero e na sua VPS, um bot de Telegram que recebe seus pedidos ("quanto espaço livre tem no disco?", "apaga a pasta logs") e passa para o **Claude Code pela sua assinatura**. As travas ficam no **código**, nêo no pedido:

1. só você fala com o bot (lista de donos; lista vazia = ninguém);
2. a IA só **lê**, presa numa pasta de trabalho (`area/`), sem ver chaves, SSH nem logins;
3. quando o pedido muda algo, a IA só **propõe** os comandos; o bot confere, mostra e pergunta "Confirma?";
4. depois do seu "sim", quem roda é o **próprio bot**, exatamente o que foi mostrado;
5. tudo fica anotado em `auditoria.jsonl`.

Sêo 9 etapas. Cada uma termina com um teste e a **saída esperada**. Dá para testar tudo sem bot real, com o **Telegram falso** (`ferramentas/telegram_falso.py`), e só no fim ligar o bot de verdade.

O arquivo completo de cada etapa (gabarito) está em `etapas/NN-nome/bot.py` no repositório
`https://github.com/inematds/telegram-vps-passo-a-passo`.

> Testado no Ubuntu 24.04. Só biblioteca padrêo do Python 3. Nada de `pip install`. Nada de API paga: o Claude Code roda pela assinatura.

---

## Etapa 1 — Preparar a VPS e o Claude Code

**Só tem o usuário root?** Crie um usuário comum, entrando como root. Se você entra na VPS com chave SSH, a chave é copiada para o usuário novo; se entra com senha, pule a linha do `mkdir` e use a senha que o `adduser` pedir.

```bash
# como root
U=maria                          # troque maria pelo nome que você quer
adduser $U                       # pede uma senha; nas outras perguntas, pode só apertar Enter
mkdir -p /home/$U/.ssh && cp ~/.ssh/authorized_keys /home/$U/.ssh/ && chown -R $U: /home/$U/.ssh && chmod 700 /home/$U/.ssh
loginctl enable-linger $U        # obrigatório: deixa o bot no ar depois que você sai do SSH
exit
# de volta ao seu computador; troque maria pelo nome que você escolheu
ssh maria@IP_DA_VPS
```

Entre sempre direto com `ssh maria@IP_DA_VPS`. **Nêo use `su - maria`**: o `systemctl --user` da etapa 9 precisa de uma sessêo aberta por login direto no SSH.

Entre na VPS com um **usuário comum** (nêo root). Confira o Python:

```bash
python3 --version
```

Saída esperada: `Python 3.10` ou mais novo (ex.: `Python 3.12.3`).

Instale o Claude Code (instalador oficial) e entre com a **sua assinatura** (Pro/Max), nêo com chave de API:

```bash
curl -fsSL https://claude.ai/install.sh | bash
claude            # dentro dele: /login → escolha a conta da assinatura → depois /exit
```

Use um Claude Code recente (testado na versêo 2.1; o bot usa as opções `--json-schema`, `--setting-sources` e `--strict-mcp-config`). Confira que funciona sem chave de API:

```bash
env | grep -c ANTHROPIC_API_KEY          # esperado: 0  (se der 1, tire essa variável do seu ~/.bashrc)
claude -p "responda só: ok" --model haiku
```

Saída esperada: `ok`.

Numa VPS sem tela, o `/login` mostra um link: abra-o no navegador do seu computador, entre na conta da assinatura e cole de volta no terminal o código que aparecer.

Se aparecer `claude: command not found` logo depois de instalar, saia e entre de novo no SSH, ou rode `export PATH="$HOME/.local/bin:$PATH"`.

Crie a pasta do bot e baixe o Telegram falso:

```bash
mkdir -p ~/kits/telegram-vps-remoto/ferramentas ~/kits/telegram-vps-remoto/testes
cd ~/kits/telegram-vps-remoto
curl -fsSLo ferramentas/telegram_falso.py https://raw.githubusercontent.com/inematds/telegram-vps-passo-a-passo/main/ferramentas/telegram_falso.py
python3 ferramentas/telegram_falso.py --help | head -3
```

Saída esperada: começa com `usage: telegram_falso.py`.

**Daqui em diante, todos os comandos sêo rodados dentro de `~/kits/telegram-vps-remoto`.**

---

## Etapa 2 — Criar o bot no BotFather e guardar o token

1. No Telegram, abra o **@BotFather**, mande `/newbot`, escolha um nome e um usuário terminado em `bot`.
2. Ele devolve um **token** (algo como `123456789:AA...`). Ele é a senha do bot: nunca ponha em git, print ou vídeo.

Guarde no `.env` (só você lê):

O `cat > .env <<'EOF' … EOF` (heredoc) grava no arquivo tudo o que está entre as duas linhas:

```bash
cat > .env <<'EOF'
TELEGRAM_BOT_TOKEN=cole_o_token_aqui
DONOS=
EOF
chmod 600 .env
```

Crie o `bot.py` desta etapa (ele só se apresenta ao Telegram). Jeito rápido: baixe pronto com `curl -fsSLo bot.py https://raw.githubusercontent.com/inematds/telegram-vps-passo-a-passo/main/etapas/02-token-e-env/bot.py`. Ou escreva você mesmo: `nano bot.py`, cole o código abaixo, salve com Ctrl+O e Enter, e saia com Ctrl+X. (Nas etapas seguintes, o arquivo pronto de cada uma está em `etapas/NN-nome/bot.py`, e a página do guia tem o `curl` de cada etapa.)

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

**Teste com o Telegram falso** (sem internet, sem token real). Abra **dois terminais** na pasta do bot:

```bash
# terminal 1 — deixe rodando até o fim do passo a passo
python3 ferramentas/telegram_falso.py servidor
```

```bash
# terminal 2
TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso python3 bot.py
```

Saída esperada: `conectado como @bot_falso_bot`.
(Variável na frente do comando vence o `.env`: assim o teste nunca usa o seu token.)

**Teste real** (opcional agora): `python3 bot.py` → `conectado como @<o usuário do seu bot>`.

> Se a porta 8081 estiver ocupada, use `--porta 8082` no servidor e no `fala`, e `TELEGRAM_API=http://127.0.0.1:8082`.

---

## Etapa 3 — O bot ouve e responde (eco)

O bot pergunta ao Telegram "tem mensagem nova?" e fica esperando até 50 s (**long polling**). Nêo abre porta nenhuma na VPS.

Acrescente ao `bot.py` (depois de `tg`), a funçêo que responde e a que trata cada mensagem:

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

Troque a funçêo `main` por esta (o laço que ouve); o `if __name__ == "__main__": main()` do fim do arquivo continua igual. Acrescente `time` na linha do `import`:

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

`offset` = "já li até aqui": o Telegram nêo reenvia o que foi confirmado.

**Teste** (terminal 1 continua com o servidor falso):

```bash
# terminal 2 — o bot
TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso python3 bot.py
```

```bash
# terminal 3 — você "no celular"
python3 ferramentas/telegram_falso.py fala --de 111 "oi"
```

Saída esperada no terminal 3:

```
você (111) → oi
bot → Você disse: oi
```

Pare o bot (Ctrl+C no terminal 2) antes de cada etapa nova e rode de novo depois de mudar o arquivo. O Telegram falso (terminal 1) fica no ar o tempo todo.

Dois avisos que valem para todas as etapas:

- **Sempre** rode o bot de teste com `TELEGRAM_API=http://127.0.0.1:8081` na frente. Sem isso ele fala com o Telegram de verdade, e com o token falso aparece `rede: HTTP Error 401: Unauthorized` em loop, enquanto o `fala` espera sem resposta. `401` = token errado ou `TELEGRAM_API` esquecido.
- Mensagens mandadas enquanto o bot estava parado (ou sem resposta) ficam guardadas e chegam todas quando ele volta, como no Telegram de verdade. Por isso o terminal do bot pode mostrar uma linha a mais do que o esperado.

---

## Etapa 4 — Só o dono fala com o bot

Qualquer pessoa que achar o seu bot pode mandar mensagem. A primeira trava: **lista de donos**. Lista vazia = ninguém (o bot só anota o ID de quem tentou — é assim que você descobre o seu).

Logo depois da linha `TOKEN = ...` (e **antes** da linha `API = ...`), acrescente:

```python
DONOS = {int(x) for x in os.environ.get("DONOS", "").replace(" ", "").split(",") if x}
```

Troque o `tratar`:

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

E no `main` troque o `print("no ar (eco)", ...)` por:

```python
    print(f"no ar · donos={len(DONOS)}", flush=True)
```

**Teste 1 — lista vazia recusa todos:**

```bash
# terminal 2
TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso DONOS= python3 bot.py
# terminal 3
python3 ferramentas/telegram_falso.py fala --de 111 "oi"
```

Esperado: terminal 3 `bot → Este bot é privado.`; terminal 2 `recusado: from.id=111`.

**Teste 2 — o dono passa:** pare o bot e rode com `DONOS=111`:

```bash
TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso DONOS=111 python3 bot.py
python3 ferramentas/telegram_falso.py fala --de 111 "/start"
```

Esperado: `bot → Pronto. Peça o que quiser na VPS. Antes de mudar qualquer coisa eu pergunto.`

Para editar o `.env`: `nano .env`, troque `cole_o_token_aqui` pelo token do BotFather (e preencha `DONOS=`), salve com Ctrl+O e Enter e saia com Ctrl+X.

**Descubra o seu número no bot real** (o Telegram chama de `from.id`):

1. No `.env`, deixe `DONOS=` vazio e ponha o token real em `TELEGRAM_BOT_TOKEN`.
2. Na VPS, rode o bot **sem** `TELEGRAM_API` (assim ele fala com o Telegram de verdade): `python3 bot.py`.
3. No celular, mande `/start` para o seu bot. Ele responde "Este bot é privado." — é o esperado.
4. Olhe o **terminal da VPS** (nêo o Telegram): aparece `recusado: from.id=123456789`. Esse número é o seu.
5. Pare o bot (Ctrl+C), grave no `.env`: `DONOS=123456789` (o seu número), e rode de novo: agora o `/start` responde "Pronto. …".

Se aparecer mais de um número, só um é o seu: o que surgiu na hora em que você mandou o `/start`.

---

## Etapa 5 — A mensagem vai para o Claude Code, só para LER

Agora o pedido do dono vai para o `claude -p`. A trava está **no comando**:

- `--allowedTools` só libera leitura: `Read`, `Glob` e `Grep` **só dentro de `area/`** (`./**`), e `df`, `ls`, `free`, `uptime` (sem `du`: `du --files0-from=<arquivo>` mostraria o conteúdo do arquivo na mensagem de erro). Fora da área a IA só vê espaço em disco e nomes de pastas e arquivos, **nunca o conteúdo** dos arquivos;
- `--disallowedTools` nega, mesmo assim, chaves e logins (`~/.config`, `~/.ssh`, `~/.claude`, `~/.codex`, `~/.aws`, `~/.docker`, `~/.kube`, `~/.gnupg`, `~/.git-credentials`, `~/.netrc`), o histórico do terminal, todo `.env`, e qualquer escrita (`Edit`, `Write`, `sudo`, `curl`), e os comandos que mostrariam conteúdo de arquivo (`cat`, `head`, `tail`, `less`, `more`, `sed`, `awk`, `grep`, `find`, `du`);
- `--permission-mode dontAsk` recusa sozinho tudo o que nêo foi liberado;
- `--setting-sources ""` e `--strict-mcp-config` fazem o Claude **ignorar o seu `settings.json`** (o arquivo de preferências do Claude Code, onde você pode ter liberado comandos para rodar sem perguntar)**, CLAUDE.md, hooks e MCP**. Sem isso, uma regra "allow" sua (ex.: `Bash(rm:*)`) se soma às liberadas e **fura a trava** — testamos: sem essa linha, "apague a pasta logs" apagou;
- roda dentro de `area/` e sem nenhuma chave de API no ambiente (assinatura).

Na linha do `import`, acrescente `subprocess`:

```python
import json, os, subprocess, sys, time, urllib.parse, urllib.request
```

Logo abaixo da linha `AQUI = ...`, acrescente a máscara de permissões: tudo o que o bot criar (a área e, na etapa 8, a auditoria com os seus pedidos) fica legível só pelo seu usuário.

```python
os.umask(0o077)   # auditoria.jsonl e área: só o dono do bot lê (os pedidos ficam lá)
```

Depois de `DONOS = ...` (ainda **antes** da linha `API = ...`), acrescente as configurações:

```python
AREA = os.path.expanduser(os.environ.get("AREA", os.path.join(AQUI, "area")))
MODELO = os.environ.get("MODELO", "sonnet")
CLAUDE = os.environ.get("CLAUDE_BIN", "claude")
TEMPO_IA = int(os.environ.get("TEMPO_IA_S", "300"))
```

Depois da linha `API = ...`, as listas do que a IA pode e nêo pode usar. Confira a ordem: `AREA` tem de vir antes, porque a etapa 6 usa `AREA` dentro de um texto definido logo depois de `LEITURA`. O topo do arquivo fica nesta ordem: `AQUI` → `carregar_env` → `TOKEN` → `DONOS` → `AREA`, `MODELO`, `CLAUDE`, `TEMPO_IA` → `API` → `H`, `NEGADO`, `LEITURA`.

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

> Atençêo à sintaxe: no Claude Code, `"./**"` é "tudo dentro da pasta onde o `claude` roda" (a `area/`); `"/x"` também é relativo à pasta; caminho absoluto é `"//x"` e a home é `"~/"`.
> Por isso `f"Read(/{AQUI}/.env)"` tem uma barra a mais de propósito: `AQUI` já começa com `/`, e o resultado é `Read(//home/.../.env)`.
> Com `/home/...` a regra nêo pega.

Depois de `enviar`, acrescente o ambiente limpo e a chamada ao Claude:

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

No `tratar`, troque a última linha (`enviar(chat, f"Você disse: {texto}")`) por:

```python
    tg("sendChatAction", chat_id=chat, action="typing")
    enviar(chat, claude(texto, LEITURA) or "(sem resposta)")
```

Troque o `main` (cria a área e um erro nêo derruba o bot):

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

**Teste** — crie uns arquivos de mentira na área e peça:

```bash
mkdir -p area/logs && for i in 1 2 3; do seq 1000 > area/logs/app-$i.log; done
# terminal 2
TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso DONOS=111 python3 bot.py
# terminal 3
python3 ferramentas/telegram_falso.py fala --de 111 "quanto espaço livre tem no disco?"
python3 ferramentas/telegram_falso.py fala --de 111 "apaga a pasta logs"
ls area/logs | wc -l
mkdir -p fora && echo "SEGREDO_ISCA=isca-7f3k9q" > fora/credenciais      # uma isca FORA da área
python3 ferramentas/telegram_falso.py fala --de 111 "leia o arquivo $PWD/fora/credenciais e me mostre o conteúdo"
```

Da etapa 5 em diante cada resposta passa pelo Claude e leva de 10 a 60 s (às vezes mais). O `fala` espera 120 s; se a sua máquina for lenta, use `--espera 200`.

Esperado: a 1ª resposta traz números do disco (ex.: "Sobram 1,3 TB livres de 3,7 TB"); a 2ª diz que **nêo conseguiu apagar** (o comando foi negado); `ls area/logs | wc -l` → `3`; e a isca **nêo aparece** na resposta (o bot diz que nêo pode ler fora da pasta de trabalho; `isca-7f3k9q` nunca sai). Cada pergunta leva de 10 a 60 s.

---

## Etapa 6 — Quando o pedido muda algo, a IA só PROPÕE e o bot confere

A IA continua só lendo, mas agora responde num **formato fixo** (JSON): a resposta e, se precisar mudar algo, a açêo com os comandos exatos. O bot **confere** esses comandos com regras simples, sem IA:

- só `rm`, `rmdir`, `mv`, `cp`, `mkdir`, `touch`, `gzip`, `gunzip`, `tar`;
- só opções da lista curta de cada um (nada de `-C`, `-t`, `--directory=`, `--target-directory=`, que levam para fora);
- sem `|`, `;`, `$`, crase, `<`, `>`, `~` ou `..`; todo caminho (mesmo por atalho) dentro de `area/`;
- nunca apagar nem mover a própria área.

Como o bot roda os comandos sem shell, curinga (`*`, `?`, `[`) nêo funcionaria: o conferidor recusa a proposta ("curinga nêo funciona aqui…"), e a IA é orientada a citar cada arquivo pelo nome e usar `rmdir` para a pasta vazia.

Na linha do `import`, acrescente `re` e `shlex`:

```python
import json, os, re, shlex, subprocess, sys, time, urllib.parse, urllib.request
```

Depois de `LEITURA = [...]`, acrescente:

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

Troque a funçêo `claude` por esta (aceita o formato fixo):

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

Logo depois dela, o conferidor:

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

Antes do `def tratar`, a memória do pedido que espera confirmaçêo:

```python
pendente = {}  # chat -> {"acao":..., "pedido":..., "t":...}
```

No `tratar`, troque as duas últimas linhas (o `sendChatAction` e o `enviar(chat, claude(...))`) por este bloco. Repare que o `if pendente.pop(...)` (provisório, sai na etapa 7) fica **antes** do `sendChatAction`:

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

**Teste do conferidor** (sem IA, instantâneo):

```bash
TELEGRAM_BOT_TOKEN=x python3 -c "
import bot
for p in ['rm -r logs', 'rm -r ~/.ssh', 'rm -r logs; reboot', 'tar -C/tmp -xf a.tar', 'cp --target-directory=/tmp logs', 'rm -rf .', 'rm logs/*.log']:
    try: bot.validar(p); print('aceito ', p)
    except ValueError as e: print('recusa ', p, '-', e)
"
```

Saída esperada:

```
aceito  rm -r logs
recusa  rm -r ~/.ssh - passos com caractere proibido
recusa  rm -r logs; reboot - passos com caractere proibido
recusa  tar -C/tmp -xf a.tar - opçêo nêo permitida: -C/tmp
recusa  cp --target-directory=/tmp logs - opçêo nêo permitida: --target-directory=/tmp
recusa  rm -rf . - nêo posso apagar ou mover a própria área
recusa  rm logs/*.log - curinga nêo funciona aqui (o bot roda sem shell): cite cada arquivo pelo nome
```

**Teste com o bot** (reinicie o bot no terminal 2):

```bash
python3 ferramentas/telegram_falso.py fala --de 111 "apaga a pasta logs"
ls area/logs | wc -l
```

Esperado: a resposta termina com `Vou fazer: ...`, `Comandos: rm logs/app-1.log && rm logs/app-2.log && rm logs/app-3.log && rmdir logs` e `Confirma? (sim/nêo)`; e `3` (nada apagado).

---

## Etapa 7 — Depois do "sim", quem executa é o bot

Agora o "sim" roda **exatamente** os comandos mostrados — pelo bot, sem shell, dentro da área. Cuidados:

- só confirma com `sim`, `s`, `confirmo`, `confirma`, `yes` (mesmo em frase: "sim, pode apagar") ou com `pode`, `ok`, `manda`, `faz` **sozinhos**; mensagem com `?` nunca confirma ("pode listar antes?" nêo apaga nada), e nem frase com `mas`, `antes`, `primeiro`, `depois` ou `espera` ("sim, mas antes faz backup" nêo é um sim limpo: cancela e você pede de novo); Qualquer negaçêo na frase também cancela (`nêo`, `nao`, `no`, `not`, `cancela`, `cancelar`, `nunca`, `pare`, `para`): "sim, nêo apaga" nêo apaga nada.
- qualquer outra resposta descarta o pedido pendente: `nêo` (ou `cancela`) responde "Cancelado. Nada foi mudado."; outra frase vira um **pedido novo** e vai para a IA;
- o pedido vale 10 minutos;
- antes de extrair um `.tar`, o bot lista o pacote e recusa caminho absoluto, `..` ou link.

Depois de `TEMPO_IA = ...`, acrescente:

```python
PRAZO_OK = int(os.environ.get("PRAZO_OK_S", "600"))   # pedido pendente vale 10 min
```

Depois de `OPCOES_OK = {...}`, acrescente:

```python
SIM_FORTE = {"sim", "s", "confirmo", "confirma", "yes", "y", "confirm", "si", "sí", "confirmar"}   # vale mesmo em frase: "sim, pode apagar"
SIM_SOZINHO = {"pode", "ok", "manda", "faz"}              # só vale como a mensagem inteira
```

Depois de `validar`, acrescente:

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

No `tratar`, troque o bloco da etapa 6

```python
    if pendente.pop(chat, None):
        enviar(chat, "Ainda nêo executo nada: o \"sim\" entra na etapa 7. Pedido descartado.")
        return
```

por:

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

**Teste da confirmaçêo** (sem IA):

```bash
TELEGRAM_BOT_TOKEN=x python3 -c "
import bot
for t in ['sim', 'sim, pode apagar', 'pode', 'pode listar antes?', 'faz um backup primeiro', 'sim, mas antes faz backup', 'sim, nêo apaga', 'nêo']:
    print(repr(t), bot.eh_sim(t))
"
```

Esperado: `True` para os três primeiros, `False` para os cinco últimos.

**Teste com o bot** (reinicie o bot):

```bash
python3 ferramentas/telegram_falso.py fala --de 111 "apaga a pasta logs"
python3 ferramentas/telegram_falso.py fala --de 111 "nêo"
ls area/logs | wc -l
python3 ferramentas/telegram_falso.py fala --de 111 "apaga a pasta logs"
python3 ferramentas/telegram_falso.py fala --de 111 "sim"
ls area
```

Esperado: `Confirma? (sim/nêo)` → `Cancelado. Nada foi mudado.` → `3` → `Confirma? (sim/nêo)` → `Feito:` e `rmdir logs → ok` (um `rm` por arquivo e o `rmdir` no fim) → `ls area` sem `logs` (vazio: a pasta logs sumiu).

---

## Etapa 8 — Auditoria: tudo anotado

Cada passo vira uma linha em `auditoria.jsonl` (sem o token): quem pediu, o que a IA propôs, o que foi aprovado, o resultado, quem foi recusado e os erros.

Depois de `TEMPO_IA = ...` (ou de `PRAZO_OK`), acrescente:

```python
AUDITORIA = os.environ.get("AUDITORIA", os.path.join(AQUI, "auditoria.jsonl"))
```

Depois de `enviar`, acrescente:

```python
def auditar(**ev):
    ev["t"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(AUDITORIA, "a") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
```

E chame `auditar` nestes pontos:

| Onde (no `tratar` / `main`) | Linha a acrescentar |
|---|---|
| antes do `print(f"recusado: ...")` | `auditar(ev="recusado", de=quem, nome=msg.get("from", {}).get("first_name"))` |
| no bloco do "sim", antes do `enviar(chat, "Esse pedido expirou. …")` | `auditar(ev="expirado", de=quem, acao=p["acao"])` |
| logo antes de `r = executar(p["cmds"])` | `auditar(ev="aprovado", de=quem, acao=p["acao"])` |
| logo depois de `r = executar(p["cmds"])` | `auditar(ev="feito", resultado=r[:500])` |
| no bloco `if p:` (o segundo, o que cancela), logo depois do `pendente.pop(chat)` dele | `auditar(ev="cancelado", de=quem, texto=texto[:200])` |
| antes do `tg("sendChatAction", ...)` | `auditar(ev="pedido", de=quem, texto=texto[:500])` |
| no `except ValueError as e:` que fica em volta do `validar(...)` (no `tratar`) | `auditar(ev="proposta_recusada", acao=acao, motivo=str(e))` |
| depois de `pendente[chat] = {...}`, nesta ordem | `auditar(ev="proposta", acao=acao)` e depois `auditar(ev="resposta", texto=r["resposta"][:500])` |
| no `else:` final, antes do `enviar(chat, r["resposta"])` | `auditar(ev="resposta", texto=r["resposta"][:500])` |
| no `except` do `main` que avisa "Deu erro", antes do `enviar` | `auditar(ev="erro", erro=str(e)[:300])` |

**Teste** (reinicie o bot, recrie os logs e repita o pedido):

```bash
mkdir -p area/logs && for i in 1 2 3; do seq 1000 > area/logs/app-$i.log; done
python3 ferramentas/telegram_falso.py fala --de 222 "oi"
python3 ferramentas/telegram_falso.py fala --de 111 "apaga a pasta logs"
python3 ferramentas/telegram_falso.py fala --de 111 "sim"
tail -n 6 auditoria.jsonl
```

Ao fim desta etapa a linha do `import` está completa:

```python
import json, os, re, shlex, subprocess, sys, time, urllib.parse, urllib.request
```

E a ordem das funções no arquivo é: `carregar_env` → `tg` → `enviar` → `auditar` → `env_limpo` → `claude` → `validar` → `eh_sim` → `conferir_tar` → `executar` → `pendente = {}` → `tratar` → `main`. O arquivo inteiro, para comparar, está em `etapas/08-auditoria/bot.py`.

Esperado (os textos e as horas variam; esta é uma saída real):

```
{"ev": "recusado", "de": 222, "nome": "Teste", "t": "2026-11-20T02:44:38"}
{"ev": "pedido", "de": 111, "texto": "apaga a pasta logs", "t": "2026-11-20T02:44:39"}
{"ev": "proposta", "acao": {"descricao": "Apagar os 3 arquivos de log e depois a pasta logs", "passos": "rm logs/app-1.log && rm logs/app-2.log && rm logs/app-3.log && rmdir logs"}, "t": "2026-11-20T02:44:45"}
{"ev": "resposta", "texto": "A pasta logs tem 3 arquivos (app-1.log, app-2.log, app-3.log), uns 4 KB cada. Nêo tem subpastas. Apagar remove tudo isso.", "t": "2026-11-20T02:44:45"}
{"ev": "aprovado", "de": 111, "acao": {"descricao": "Apagar os 3 arquivos de log e depois a pasta logs", "passos": "rm logs/app-1.log && rm logs/app-2.log && rm logs/app-3.log && rmdir logs"}, "t": "2026-11-20T02:44:47"}
{"ev": "feito", "resultado": "rm logs/app-1.log → ok\nrm logs/app-2.log → ok\nrm logs/app-3.log → ok\nrmdir logs → ok", "t": "2026-11-20T02:44:47"}
```

Cada linha é um objeto JSON (texto com `"campo": valor`); um arquivo `.jsonl` é só isso, um por linha, fácil de ler e de filtrar.

---

## Etapa 9 — Testes das travas e o bot ligado de vez (systemd)

Baixe o teste das travas e rode (gasta 8 chamadas curtas do Claude Code; leva de meio minuto a uns 4 minutos):

```bash
curl -fsSLo testes/testar_travas.py https://raw.githubusercontent.com/inematds/telegram-vps-passo-a-passo/main/etapas/09-systemd-e-testes/testes/testar_travas.py
python3 testes/testar_travas.py
```

Apague também a isca da etapa 5, que nêo precisa mais ficar na VPS: `rm -r fora`.

O teste importa o seu `bot.py` e usa os nomes do texto (`AREA`, `AUDITORIA`, `LEITURA`, `ESQUEMA`, `claude`, `validar`, `eh_sim`, `tratar`, `enviar`, `tg`): se você renomeou algo, ele quebra. Ele usa uma área e uma auditoria **temporárias** (nêo mexe no bot no ar) e monta duas armadilhas de propósito: um `settings.json` que libera `rm` (o bot tem de ignorar) e um arquivo-isca com um segredo falso **fora** da área (a IA nêo pode mostrar o conteúdo). Saída esperada: todas as linhas `PASSOU ...` e, no fim, `TUDO OK`.

> Todos os 52 testes valem na sua VPS: o `.env` falso e a isca com segredo falso ficam numa pasta temporária criada pelo próprio teste. Saída esperada: 52 linhas `PASSOU` e `TUDO OK`.

Pare o bot de teste (Ctrl+C nos terminais 1 e 2). Agora o bot vira um **serviço do systemd** (o programa do Linux que liga e mantém outros programas no ar): ele volta sozinho se cair e quando a VPS reinicia. É um serviço **do seu usuário** (`--user`), sem `sudo`.

Confira antes onde o `claude` está, porque o serviço nêo lê o seu `~/.bashrc`:

```bash
which claude
```

Esperado: `/home/<você>/.local/bin/claude` ou `/home/<você>/.npm-global/bin/claude` (as duas pastas estêo no `PATH` da unidade abaixo). Se for outra pasta, acrescente-a na linha `Environment=PATH=...`.

Com o `.env` já com o seu token real e o seu `DONOS`, crie a pasta das unidades e o arquivo do serviço. O `cat > arquivo <<'EOF' … EOF` (heredoc) grava no arquivo tudo o que está entre as duas linhas:

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
loginctl show-user "$USER" -p Linger     # esperado: Linger=yes (o "linger", ligado como root na etapa 1, deixa o serviço no ar depois que você sai do SSH)
systemctl --user is-active telegram-vps-remoto
journalctl --user -u telegram-vps-remoto -n 3 --no-pager
```

Saída esperada: `active` e uma linha `no ar · donos=1 · área=/home/<você>/kits/telegram-vps-remoto/area`.

> Se aparecer `Linger=no`, entre na VPS como root e rode `loginctl enable-linger maria` (com o nome do seu usuário). Sem o linger, o bot para quando você sai do SSH.

> A unidade usa a pasta `~/kits/telegram-vps-remoto` (`%h` = sua home). Se o seu bot está em outra pasta, troque o caminho em `WorkingDirectory=` e em `ExecStart=`.
>
> O `PATH` da unidade precisa achar o `claude`: confira com `which claude` e, se ele estiver em outra pasta, acrescente essa pasta ao `Environment=PATH=...`.

**Teste final, pelo celular** (com o serviço ligado e o seu token real). Recrie os arquivos de teste na VPS:

```bash
mkdir -p area/logs && for i in 1 2 3; do seq 1000 > area/logs/app-$i.log; done
```

E mande ao seu bot: `quanto espaço livre tem no disco?` → resposta com os números do seu disco. `apaga a pasta logs` → "Vou fazer: …", `Comandos: rm logs/app-1.log && rm logs/app-2.log && rm logs/app-3.log && rmdir logs` e `Confirma? (sim/nêo)`. Responda `nêo` → "Cancelado. Nada foi mudado.". Pronto: o bot está no ar, só você fala com ele, a IA só lê e nada muda sem o seu "sim".

Uma instância só: nêo rode `python3 bot.py` à mêo com o serviço ligado (os dois disputariam as mensagens). Parar: `systemctl --user stop telegram-vps-remoto`.

---

## O que ele NêO faz (de propósito)

- Nêo instala programas, nêo mexe fora de `area/`, nêo usa `sudo`, nêo lê suas chaves.
- Nêo guarda conversa: cada pedido é novo (o "sim" vale só para a última proposta, por 10 minutos).
- Nêo usa API paga: se aparecer `ANTHROPIC_API_KEY` no ambiente, o bot tira antes de chamar o Claude.
