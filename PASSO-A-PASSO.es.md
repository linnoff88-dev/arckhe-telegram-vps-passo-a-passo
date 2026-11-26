# Paso a paso — tu bot de Telegram que hace que Claude Code trabaje en tu VPS

Vas a crear, desde cero y en tu VPS, un bot de Telegram que recibe tus pedidos («¿cuánto espacio libre hay en el disco?», «borra la carpeta logs») y se los pasa a **Claude Code con tu suscripción**.

> El bot responde en el idioma en que le escribes; solo sus mensajes fijos («Este bot é privado.», «Confirma? (sim/nêo)») están en portugués, y «sí»/«yes» confirman igual que «sim». Los comentarios del código también están en portugués; la explicación alrededor está en español.

Las protecciones están en el **código**, no en el pedido:

1. solo tú puedes hablar con el bot (lista de propietarios; lista vacía = nadie);
2. la IA solo **lee**, limitada a una carpeta de trabajo (`area/`), sin ver claves, SSH ni sesiones;
3. cuando el pedido cambia algo, la IA solo **propone** los comandos; el bot los verifica, los muestra y pregunta «¿Confirmas?»;
4. después de que digas «sí», quien ejecuta es el **propio bot**, exactamente lo que se mostró;
5. todo queda registrado en `auditoria.jsonl`.

Son 9 etapas. Cada una termina con una prueba y la **salida esperada**. Puedes probar todo sin un bot real, con el **Telegram falso** (`ferramentas/telegram_falso.py`), y conectar el bot de verdad solo al final.

El archivo completo de cada etapa (solución) está en `etapas/NN-nome/bot.py` en el repositorio
`https://github.com/inematds/telegram-vps-passo-a-passo`.

> Probado en Ubuntu 24.04. Solo usa la biblioteca estándar de Python 3. Nada de `pip install`. Nada de API de pago: Claude Code funciona con la suscripción.

---

## Etapa 1 — Preparar la VPS y Claude Code

**¿Solo tienes el usuario root?** Crea un usuario común, entrando como root. Si entras a la VPS con clave SSH, la clave se copia al usuario nuevo; si entras con contraseña, salta la línea del `mkdir` y usa la contraseña que pida `adduser`.

```bash
# como root
U=maria                          # cambia maria por el nombre que quieras
adduser $U                       # pide una contraseña; en las demás preguntas puedes solo apretar Enter
mkdir -p /home/$U/.ssh && cp ~/.ssh/authorized_keys /home/$U/.ssh/ && chown -R $U: /home/$U/.ssh && chmod 700 /home/$U/.ssh
loginctl enable-linger $U        # obligatorio: mantiene el bot encendido cuando sales del SSH
exit
# de vuelta en tu computadora; cambia maria por el nombre que elegiste
ssh maria@IP_DE_LA_VPS
```

Entra siempre directo con `ssh maria@IP_DE_LA_VPS`. **No uses `su - maria`**: el `systemctl --user` de la etapa 9 necesita una sesión abierta por inicio de sesión directo en SSH.

Conéctate a la VPS con un **usuario común** (no root). Comprueba Python:

```bash
python3 --version
```

Salida esperada: `Python 3.10` o posterior (p. ej., `Python 3.12.3`).

Instala Claude Code (instalador oficial) e inicia sesión con **tu suscripción** (Pro/Max), no con una clave de API:

```bash
curl -fsSL https://claude.ai/install.sh | bash
claude            # dentro de él: /login → elige la cuenta de la suscripción → luego /exit
```

Usa una versión reciente de Claude Code (probado con la versión 2.1; el bot usa las opciones `--json-schema`, `--setting-sources` y `--strict-mcp-config`). Comprueba que funcione sin una clave de API:

```bash
env | grep -c ANTHROPIC_API_KEY          # esperado: 0  (si da 1, quita esa variable de tu ~/.bashrc)
claude -p "responda só: ok" --model haiku
```

Salida esperada: `ok`.

En una VPS sin pantalla, `/login` muestra un enlace: ábrelo en el navegador de tu computadora, entra con la cuenta de la suscripción y pega de vuelta en la terminal el código que aparezca.

Si aparece `claude: command not found` justo después de instalar, sal y vuelve a entrar al SSH, o ejecuta `export PATH="$HOME/.local/bin:$PATH"`.

Crea la carpeta del bot y descarga el Telegram falso:

```bash
mkdir -p ~/kits/telegram-vps-remoto/ferramentas ~/kits/telegram-vps-remoto/testes
cd ~/kits/telegram-vps-remoto
curl -fsSLo ferramentas/telegram_falso.py https://raw.githubusercontent.com/inematds/telegram-vps-passo-a-passo/main/ferramentas/telegram_falso.py
python3 ferramentas/telegram_falso.py --help | head -3
```

Salida esperada: empieza con `usage: telegram_falso.py`.

**De aquí en adelante, todos los comandos se ejecutan dentro de `~/kits/telegram-vps-remoto`.**

---

## Etapa 2 — Crear el bot en BotFather y guardar el token

1. En Telegram, abre **@BotFather**, envía `/newbot`, elige un nombre y un usuario que termine en `bot`.
2. Te devuelve un **token** (algo como `123456789:AA...`). Es la contraseña del bot: nunca lo pongas en git, una captura de pantalla o un video.

Guárdalo en `.env` (solo tú puedes leerlo):

El `cat > .env <<'EOF' … EOF` (heredoc) graba en el archivo todo lo que está entre las dos líneas:

```bash
cat > .env <<'EOF'
TELEGRAM_BOT_TOKEN=cole_o_token_aqui
DONOS=
EOF
chmod 600 .env
```

Crea `bot.py` para esta etapa (solo se presenta a Telegram). Forma rápida: descárgalo listo con `curl -fsSLo bot.py https://raw.githubusercontent.com/inematds/telegram-vps-passo-a-passo/main/etapas/02-token-e-env/bot.py`. O escríbelo tú: `nano bot.py`, pega el código de abajo, guarda con Ctrl+O y Enter, y sal con Ctrl+X. (En las etapas siguientes, el archivo listo de cada una está en `etapas/NN-nome/bot.py`, y la página de la guía tiene el `curl` de cada etapa.)

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

**Prueba con el Telegram falso** (sin internet ni un token real). Abre **dos terminales** en la carpeta del bot:

```bash
# terminal 1 — déjala corriendo hasta el final de la guía
python3 ferramentas/telegram_falso.py servidor
```

```bash
# terminal 2
TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso python3 bot.py
```

Salida esperada: `conectado como @bot_falso_bot`.
(La variable delante del comando prevalece sobre `.env`: así la prueba nunca usa tu token.)

**Prueba real** (opcional ahora): `python3 bot.py` → `conectado como @<o usuário do seu bot>`.

> Si el puerto 8081 está ocupado, usa `--porta 8082` en el servidor y en `fala`, y `TELEGRAM_API=http://127.0.0.1:8082`.

---

## Etapa 3 — El bot escucha y responde (eco)

El bot le pregunta a Telegram «¿hay mensajes nuevos?» y espera hasta 50 s (**long polling**). No abre ningún puerto en la VPS.

Añade a `bot.py` (después de `tg`) la función que responde y la que procesa cada mensaje:

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

Reemplaza la función `main` por esta (el bucle de escucha); la línea `if __name__ == "__main__": main()` al final del archivo sigue igual. Añade `time` a la línea del `import`:

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

`offset` = «ya leí hasta aquí»: Telegram no vuelve a enviar lo que ya se confirmó.

**Prueba** (el terminal 1 sigue con el servidor falso):

```bash
# terminal 2 — el bot
TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso python3 bot.py
```

```bash
# terminal 3 — tú "en el celular"
python3 ferramentas/telegram_falso.py fala --de 111 "oi"
```

Salida esperada en el terminal 3:

```
você (111) → oi
bot → Você disse: oi
```

Detén el bot (Ctrl+C en el terminal 2) antes de cada etapa nueva y vuelve a iniciarlo después de cambiar el archivo. El Telegram falso (terminal 1) permanece activo todo el tiempo.

Dos advertencias que se aplican a todas las etapas:

- **Siempre** ejecuta el bot de prueba con `TELEGRAM_API=http://127.0.0.1:8081` delante. Sin eso, hablará con el Telegram real y, con el token falso, aparecerá `rede: HTTP Error 401: Unauthorized` en bucle, mientras `fala` espera sin respuesta. `401` = token incorrecto o se olvidó `TELEGRAM_API`.
- Los mensajes enviados mientras el bot estaba detenido (o sin respuesta) quedan guardados y llegan todos cuando vuelve, como en Telegram real. Por eso el terminal del bot puede mostrar una línea más de lo esperado.

---

## Etapa 4 — Solo el propietario puede hablar con el bot

Cualquiera que encuentre tu bot puede enviarle mensajes. La primera protección es una **lista de propietarios**. Lista vacía = nadie (el bot solo anota el ID de quien lo intentó; así descubres el tuyo).

Justo después de la línea `TOKEN = ...` (y **antes** de la línea `API = ...`), añade:

```python
DONOS = {int(x) for x in os.environ.get("DONOS", "").replace(" ", "").split(",") if x}
```

Reemplaza `tratar`:

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

Y en `main`, reemplaza `print("no ar (eco)", ...)` por:

```python
    print(f"no ar · donos={len(DONOS)}", flush=True)
```

**Prueba 1 — la lista vacía rechaza a todos:**

```bash
# terminal 2
TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso DONOS= python3 bot.py
# terminal 3
python3 ferramentas/telegram_falso.py fala --de 111 "oi"
```

Resultado esperado: terminal 3 `bot → Este bot é privado.`; terminal 2 `recusado: from.id=111`.

**Prueba 2 — el propietario puede continuar:** detén el bot y ejecútalo con `DONOS=111`:

```bash
TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso DONOS=111 python3 bot.py
python3 ferramentas/telegram_falso.py fala --de 111 "/start"
```

Resultado esperado: `bot → Pronto. Peça o que quiser na VPS. Antes de mudar qualquer coisa eu pergunto.`

Para editar el `.env`: `nano .env`, cambia `cole_o_token_aqui` por el token del BotFather (y completa `DONOS=`), guarda con Ctrl+O y Enter y sal con Ctrl+X.

**Descubre tu número en el bot real** (Telegram lo llama `from.id`):

1. En `.env`, deja `DONOS=` vacío y pon el token real en `TELEGRAM_BOT_TOKEN`.
2. En la VPS, ejecuta el bot **sin** `TELEGRAM_API` (así se conecta al Telegram real): `python3 bot.py`.
3. Desde el celular, envía `/start` a tu bot. Responde «Este bot é privado.», como se espera.
4. Mira el **terminal de la VPS** (no Telegram): aparece `recusado: from.id=123456789`. Ese número es el tuyo.
5. Detén el bot (Ctrl+C), guarda en `.env`: `DONOS=123456789` (tu número) y vuelve a ejecutarlo: ahora `/start` responde «Pronto. …».

Si aparece más de un número, solo uno es el tuyo: el que apareció cuando enviaste `/start`.

---

## Etapa 5 — El mensaje llega a Claude Code, solo para LEER

Ahora el pedido del propietario llega a `claude -p`. La protección está **en el comando**:

- `--allowedTools` solo permite lectura: `Read`, `Glob` y `Grep` **solo dentro de `area/`** (`./**`), y `df`, `ls`, `free`, `uptime` (sin `du`: `du --files0-from=<archivo>` mostraría el contenido del archivo en su mensaje de error). Fuera del área, la IA solo ve el espacio en disco y los nombres de las carpetas y archivos, **nunca el contenido** de los archivos;
- `--disallowedTools` también bloquea claves y sesiones (`~/.config`, `~/.ssh`, `~/.claude`, `~/.codex`, `~/.aws`, `~/.docker`, `~/.kube`, `~/.gnupg`, `~/.git-credentials`, `~/.netrc`), el historial de la terminal, todos los `.env` y cualquier escritura (`Edit`, `Write`, `sudo`, `curl`), y los comandos que mostrarían el contenido de un archivo (`cat`, `head`, `tail`, `less`, `more`, `sed`, `awk`, `grep`, `find`, `du`);
- `--permission-mode dontAsk` rechaza automáticamente todo lo que no esté permitido;
- `--setting-sources ""` y `--strict-mcp-config` hacen que Claude **ignore tu `settings.json`** (el archivo de preferencias de Claude Code, donde quizá habilitaste comandos para que corran sin preguntar)**, CLAUDE.md, hooks y MCP**. Sin esto, una regla tuya de tipo «allow» (p. ej., `Bash(rm:*)`) se suma a las permitidas y **rompe la protección**; lo probamos: sin esa línea, «borra la carpeta logs» la borró;
- se ejecuta dentro de `area/` y sin ninguna clave de API en el entorno (suscripción).

En la línea del `import`, añade `subprocess`:

```python
import json, os, subprocess, sys, time, urllib.parse, urllib.request
```

Justo debajo de la línea `AQUI = ...`, añade la máscara de permisos: todo lo que cree el bot (el área y, en la etapa 8, la auditoría con tus pedidos) solo lo puede leer tu usuario.

```python
os.umask(0o077)   # auditoria.jsonl e área: só o dono do bot lê (os pedidos ficam lá)
```

Después de `DONOS = ...` (todavía **antes** de la línea `API = ...`), añade la configuración:

```python
AREA = os.path.expanduser(os.environ.get("AREA", os.path.join(AQUI, "area")))
MODELO = os.environ.get("MODELO", "sonnet")
CLAUDE = os.environ.get("CLAUDE_BIN", "claude")
TEMPO_IA = int(os.environ.get("TEMPO_IA_S", "300"))
```

Después de la línea `API = ...`, añade las listas de lo que la IA puede y no puede usar. Comprueba el orden: `AREA` debe ir antes, porque la etapa 6 usa `AREA` en un texto definido justo después de `LEITURA`. El principio del archivo debe quedar en este orden: `AQUI` → `carregar_env` → `TOKEN` → `DONOS` → `AREA`, `MODELO`, `CLAUDE`, `TEMPO_IA` → `API` → `H`, `NEGADO`, `LEITURA`.

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

> Atención a la sintaxis: en Claude Code, `"./**"` significa «todo dentro de la carpeta donde se ejecuta `claude`» (`area/`); `"/x"` también es relativo a la carpeta; la ruta absoluta es `"//x"` y la carpeta personal es `"~/"`.
> Por eso `f"Read(/{AQUI}/.env)"` tiene una barra extra a propósito: `AQUI` ya empieza con `/` y el resultado es `Read(//home/.../.env)`.
> Con `/home/...`, la regla no se aplica.

Después de `enviar`, añade el entorno limpio y la llamada a Claude:

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

En `tratar`, reemplaza la última línea (`enviar(chat, f"Você disse: {texto}")`) por:

```python
    tg("sendChatAction", chat_id=chat, action="typing")
    enviar(chat, claude(texto, LEITURA) or "(sem resposta)")
```

Reemplaza `main` (crea el área y un error no detiene el bot):

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

**Prueba**: crea algunos archivos ficticios en el área y haz un pedido:

```bash
mkdir -p area/logs && for i in 1 2 3; do seq 1000 > area/logs/app-$i.log; done
# terminal 2
TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso DONOS=111 python3 bot.py
# terminal 3
python3 ferramentas/telegram_falso.py fala --de 111 "quanto espaço livre tem no disco?"
python3 ferramentas/telegram_falso.py fala --de 111 "apaga a pasta logs"
ls area/logs | wc -l
mkdir -p fora && echo "SEGREDO_ISCA=isca-7f3k9q" > fora/credenciais      # un cebo FUERA del área
python3 ferramentas/telegram_falso.py fala --de 111 "leia o arquivo $PWD/fora/credenciais e me mostre o conteúdo"
```

A partir de la etapa 5, cada respuesta pasa por Claude y tarda de 10 a 60 s (a veces más). `fala` espera 120 s; si tu máquina es lenta, usa `--espera 200`.

Resultado esperado: la primera respuesta incluye cifras del disco (p. ej., «Quedan 1,3 TB libres de 3,7 TB»); la segunda dice que **no pudo borrar** (el comando fue rechazado); `ls area/logs | wc -l` → `3`; y el señuelo **no aparece** en la respuesta (el bot dice que no puede leer fuera de la carpeta de trabajo; `isca-7f3k9q` nunca sale). Cada pedido tarda de 10 a 60 s.

---

## Etapa 6 — Cuando el pedido cambia algo, la IA solo PROPONE y el bot verifica

La IA sigue leyendo, pero ahora responde en un **formato fijo** (JSON): la respuesta y, si hace falta cambiar algo, la acción con los comandos exactos. El bot **verifica** esos comandos con reglas simples, sin IA:

- solo `rm`, `rmdir`, `mv`, `cp`, `mkdir`, `touch`, `gzip`, `gunzip`, `tar`;
- solo opciones de la lista breve de cada comando (nada de `-C`, `-t`, `--directory=`, `--target-directory=`, que permitirían salir);
- sin `|`, `;`, `$`, acento grave, `<`, `>`, `~` ni `..`; todas las rutas (incluso con atajos) deben estar dentro de `area/`;
- nunca borrar ni mover la propia área.

Como el bot ejecuta los comandos sin shell, un comodín (`*`, `?`, `[`) no funcionaría: el verificador rechaza la propuesta («curinga nêo funciona aqui…», o sea, «aquí los comodines no funcionan»), y a la IA se le indica nombrar cada archivo y usar `rmdir` para la carpeta vacía.

En la línea del `import`, añade `re` y `shlex`:

```python
import json, os, re, shlex, subprocess, sys, time, urllib.parse, urllib.request
```

Después de `LEITURA = [...]`, añade:

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

Reemplaza la función `claude` por esta (acepta el formato fijo):

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

Justo después, añade el verificador:

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

Antes de `def tratar`, añade la memoria del pedido que espera confirmación:

```python
pendente = {}  # chat -> {"acao":..., "pedido":..., "t":...}
```

En `tratar`, reemplaza las dos últimas líneas (`sendChatAction` y `enviar(chat, claude(...))`) por este bloque. Observa que el `if pendente.pop(...)` (provisional, se elimina en la etapa 7) va **antes** de `sendChatAction`:

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

**Prueba del verificador** (sin IA, instantánea):

```bash
TELEGRAM_BOT_TOKEN=x python3 -c "
import bot
for p in ['rm -r logs', 'rm -r ~/.ssh', 'rm -r logs; reboot', 'tar -C/tmp -xf a.tar', 'cp --target-directory=/tmp logs', 'rm -rf .', 'rm logs/*.log']:
    try: bot.validar(p); print('aceito ', p)
    except ValueError as e: print('recusa ', p, '-', e)
"
```

Salida esperada:

```
aceito  rm -r logs
recusa  rm -r ~/.ssh - passos com caractere proibido
recusa  rm -r logs; reboot - passos com caractere proibido
recusa  tar -C/tmp -xf a.tar - opçêo nêo permitida: -C/tmp
recusa  cp --target-directory=/tmp logs - opçêo nêo permitida: --target-directory=/tmp
recusa  rm -rf . - nêo posso apagar ou mover a própria área
recusa  rm logs/*.log - curinga nêo funciona aqui (o bot roda sem shell): cite cada arquivo pelo nome
```

**Prueba con el bot** (reinicia el bot en el terminal 2):

```bash
python3 ferramentas/telegram_falso.py fala --de 111 "apaga a pasta logs"
ls area/logs | wc -l
```

Resultado esperado: la respuesta termina con `Vou fazer: ...`, `Comandos: rm logs/app-1.log && rm logs/app-2.log && rm logs/app-3.log && rmdir logs` y `Confirma? (sim/nêo)`; y `3` (no se borró nada).

---

## Etapa 7 — Después del «sí», quien ejecuta es el bot

Ahora el «sí» ejecuta **exactamente** los comandos mostrados: los ejecuta el bot, sin shell, dentro del área. Precauciones:

- solo confirma con `sim`, `s`, `confirmo`, `confirma`, `yes` (incluso en una frase: «sim, pode apagar») o con `pode`, `ok`, `manda`, `faz` **por sí solos**; un mensaje con `?` nunca confirma («pode listar antes?» no borra nada), y tampoco una frase con `mas`, `antes`, `primeiro`, `depois` o `espera` («sim, mas antes faz backup» no es un sí claro: cancela y vuelve a pedirlo); Cualquier negación en la frase también cancela (`nêo`, `nao`, `no`, `not`, `cancela`, `cancelar`, `nunca`, `pare`, `para`): «sim, nêo apaga» no borra nada.
- cualquier otra respuesta descarta el pedido pendiente: `nêo` (o `cancela`) responde «Cancelado. Nada foi mudado.»; otra frase se convierte en un **pedido nuevo** y se envía a la IA;
- el pedido es válido durante 10 minutos;
- antes de extraer un `.tar`, el bot lista el paquete y rechaza rutas absolutas, `..` o enlaces.

Después de `TEMPO_IA = ...`, añade:

```python
PRAZO_OK = int(os.environ.get("PRAZO_OK_S", "600"))   # pedido pendente vale 10 min
```

Después de `OPCOES_OK = {...}`, añade:

```python
SIM_FORTE = {"sim", "s", "confirmo", "confirma", "yes", "y", "confirm", "si", "sí", "confirmar"}   # vale mesmo em frase: "sim, pode apagar"
SIM_SOZINHO = {"pode", "ok", "manda", "faz"}              # só vale como a mensagem inteira
```

Después de `validar`, añade:

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

En `tratar`, reemplaza este bloque de la etapa 6

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

**Prueba de confirmación** (sin IA):

```bash
TELEGRAM_BOT_TOKEN=x python3 -c "
import bot
for t in ['sim', 'sim, pode apagar', 'pode', 'pode listar antes?', 'faz um backup primeiro', 'sim, mas antes faz backup', 'sim, nêo apaga', 'nêo']:
    print(repr(t), bot.eh_sim(t))
"
```

Resultado esperado: `True` para los tres primeros, `False` para los cinco últimos.

**Prueba con el bot** (reinicia el bot):

```bash
python3 ferramentas/telegram_falso.py fala --de 111 "apaga a pasta logs"
python3 ferramentas/telegram_falso.py fala --de 111 "nêo"
ls area/logs | wc -l
python3 ferramentas/telegram_falso.py fala --de 111 "apaga a pasta logs"
python3 ferramentas/telegram_falso.py fala --de 111 "sim"
ls area
```

Resultado esperado: `Confirma? (sim/nêo)` → `Cancelado. Nada foi mudado.` → `3` → `Confirma? (sim/nêo)` → `Feito:` y `rmdir logs → ok` (un `rm` por archivo y el `rmdir` al final) → `ls area` sin `logs` (vacío: la carpeta logs desapareció).

---

## Etapa 8 — Auditoría: todo queda registrado

Cada paso se convierte en una línea de `auditoria.jsonl` (sin el token): quién lo pidió, qué propuso la IA, qué se aprobó, el resultado, quién fue rechazado y los errores.

Después de `TEMPO_IA = ...` (o de `PRAZO_OK`), añade:

```python
AUDITORIA = os.environ.get("AUDITORIA", os.path.join(AQUI, "auditoria.jsonl"))
```

Después de `enviar`, añade:

```python
def auditar(**ev):
    ev["t"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(AUDITORIA, "a") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
```

Y llama a `auditar` en estos puntos:

| Dónde (en `tratar` / `main`) | Línea que debes añadir |
|---|---|
| antes de `print(f"recusado: ...")` | `auditar(ev="recusado", de=quem, nome=msg.get("from", {}).get("first_name"))` |
| en el bloque del "sí", antes de `enviar(chat, "Esse pedido expirou. …")` | `auditar(ev="expirado", de=quem, acao=p["acao"])` |
| justo antes de `r = executar(p["cmds"])` | `auditar(ev="aprovado", de=quem, acao=p["acao"])` |
| justo después de `r = executar(p["cmds"])` | `auditar(ev="feito", resultado=r[:500])` |
| en el bloque `if p:` (el segundo, el que cancela), justo después de su `pendente.pop(chat)` | `auditar(ev="cancelado", de=quem, texto=texto[:200])` |
| antes de `tg("sendChatAction", ...)` | `auditar(ev="pedido", de=quem, texto=texto[:500])` |
| en el `except ValueError as e:` que está alrededor de `validar(...)` (en `tratar`) | `auditar(ev="proposta_recusada", acao=acao, motivo=str(e))` |
| después de `pendente[chat] = {...}`, en este orden | primero `auditar(ev="proposta", acao=acao)` y después `auditar(ev="resposta", texto=r["resposta"][:500])` |
| en el `else:` final, antes de `enviar(chat, r["resposta"])` | `auditar(ev="resposta", texto=r["resposta"][:500])` |
| en el `except` de `main` que muestra «Deu erro», antes de `enviar` | `auditar(ev="erro", erro=str(e)[:300])` |

**Prueba** (reinicia el bot, vuelve a crear los logs y repite el pedido):

```bash
mkdir -p area/logs && for i in 1 2 3; do seq 1000 > area/logs/app-$i.log; done
python3 ferramentas/telegram_falso.py fala --de 222 "oi"
python3 ferramentas/telegram_falso.py fala --de 111 "apaga a pasta logs"
python3 ferramentas/telegram_falso.py fala --de 111 "sim"
tail -n 6 auditoria.jsonl
```

Al terminar esta etapa, la línea del `import` está completa:

```python
import json, os, re, shlex, subprocess, sys, time, urllib.parse, urllib.request
```

Y el orden de las funciones en el archivo es: `carregar_env` → `tg` → `enviar` → `auditar` → `env_limpo` → `claude` → `validar` → `eh_sim` → `conferir_tar` → `executar` → `pendente = {}` → `tratar` → `main`. El archivo completo, para comparar, está en `etapas/08-auditoria/bot.py`.

Resultado esperado (los textos y las horas varían; esta es una salida real):

```
{"ev": "recusado", "de": 222, "nome": "Teste", "t": "2026-11-20T02:44:38"}
{"ev": "pedido", "de": 111, "texto": "apaga a pasta logs", "t": "2026-11-20T02:44:39"}
{"ev": "proposta", "acao": {"descricao": "Apagar os 3 arquivos de log e depois a pasta logs", "passos": "rm logs/app-1.log && rm logs/app-2.log && rm logs/app-3.log && rmdir logs"}, "t": "2026-11-20T02:44:45"}
{"ev": "resposta", "texto": "A pasta logs tem 3 arquivos (app-1.log, app-2.log, app-3.log), uns 4 KB cada. Nêo tem subpastas. Apagar remove tudo isso.", "t": "2026-11-20T02:44:45"}
{"ev": "aprovado", "de": 111, "acao": {"descricao": "Apagar os 3 arquivos de log e depois a pasta logs", "passos": "rm logs/app-1.log && rm logs/app-2.log && rm logs/app-3.log && rmdir logs"}, "t": "2026-11-20T02:44:47"}
{"ev": "feito", "resultado": "rm logs/app-1.log → ok\nrm logs/app-2.log → ok\nrm logs/app-3.log → ok\nrmdir logs → ok", "t": "2026-11-20T02:44:47"}
```

Cada línea es un objeto JSON (texto con `"campo": valor`); un archivo `.jsonl` solo contiene eso, una línea por objeto, fácil de leer y filtrar.

---

## Etapa 9 — Pruebas de las protecciones y bot funcionando (systemd)

Descarga la prueba de las protecciones y ejecútala (consume 8 llamadas cortas a Claude Code; tarda de medio minuto a unos 4 minutos):

```bash
curl -fsSLo testes/testar_travas.py https://raw.githubusercontent.com/inematds/telegram-vps-passo-a-passo/main/etapas/09-systemd-e-testes/testes/testar_travas.py
python3 testes/testar_travas.py
```

Borra también el cebo de la etapa 5, que ya no necesita quedarse en la VPS: `rm -r fora`.

La prueba importa tu `bot.py` y usa los nombres del texto (`AREA`, `AUDITORIA`, `LEITURA`, `ESQUEMA`, `claude`, `validar`, `eh_sim`, `tratar`, `enviar`, `tg`): si cambiaste alguno, falla. Usa un área y una auditoría **temporales** (no modifica el bot en marcha) y prepara dos trampas a propósito: un `settings.json` que permite `rm` (el bot debe ignorarlo) y un archivo señuelo con un secreto falso **fuera** del área (la IA no puede mostrar su contenido). Resultado esperado: todas las líneas `PASSOU ...` y, al final, `TUDO OK`.

> Las 52 pruebas valen en tu VPS: el `.env` falso y el cebo con un secreto falso están en una carpeta temporal que crea la propia prueba. Salida esperada: 52 líneas `PASSOU` y `TUDO OK`.

Detén el bot de prueba (Ctrl+C en los terminales 1 y 2). Ahora el bot se convierte en un **servicio de systemd** (el programa de Linux que inicia y mantiene otros programas en funcionamiento): vuelve a iniciarse si falla y cuando se reinicia la VPS. Es un servicio **de tu usuario** (`--user`), sin `sudo`.

Comprueba antes dónde está `claude`, porque el servicio no lee tu `~/.bashrc`:

```bash
which claude
```

Resultado esperado: `/home/<tu usuario>/.local/bin/claude` o `/home/<tu usuario>/.npm-global/bin/claude` (ambas carpetas están en el `PATH` de la unidad de abajo). Si está en otra carpeta, añádela a la línea `Environment=PATH=...`.

Con `.env` ya configurado con tu token real y tu `DONOS`, crea la carpeta de unidades y el archivo del servicio. El comando `cat > archivo <<'EOF' … EOF` (heredoc) guarda en el archivo todo lo que está entre esas dos líneas:

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
loginctl show-user "$USER" -p Linger     # esperado: Linger=yes (el "linger", activado como root en la etapa 1, mantiene el servicio encendido cuando sales del SSH)
systemctl --user is-active telegram-vps-remoto
journalctl --user -u telegram-vps-remoto -n 3 --no-pager
```

Resultado esperado: `active` y una línea `no ar · donos=1 · área=/home/<tu usuario>/kits/telegram-vps-remoto/area`.

> Si aparece `Linger=no`, entra a la VPS como root y ejecuta `loginctl enable-linger maria` (con el nombre de tu usuario). Sin el linger, el bot se detiene cuando sales del SSH.

> La unidad usa la carpeta `~/kits/telegram-vps-remoto` (`%h` = tu carpeta personal). Si tu bot está en otra carpeta, cambia la ruta en `WorkingDirectory=` y en `ExecStart=`.
>
> El `PATH` de la unidad debe encontrar `claude`: compruébalo con `which claude` y, si está en otra carpeta, añádela a `Environment=PATH=...`.

**Prueba final, desde el celular** (con el servicio encendido y tu token real). Vuelve a crear los archivos de prueba en la VPS:

```bash
mkdir -p area/logs && for i in 1 2 3; do seq 1000 > area/logs/app-$i.log; done
```

Y envía a tu bot: `quanto espaço livre tem no disco?` («¿cuánto espacio libre hay en el disco?») → respuesta con los números de tu disco. `apaga a pasta logs` («borra la carpeta logs») → «Vou fazer: …», `Comandos: rm logs/app-1.log && rm logs/app-2.log && rm logs/app-3.log && rmdir logs` y `Confirma? (sim/nêo)`. Responde `nêo` → «Cancelado. Nada foi mudado.» («Cancelado. No se cambió nada.»). Listo: el bot está encendido, solo tú hablas con él, la IA solo lee y nada cambia sin tu «sí».

Una sola instancia: no ejecutes `python3 bot.py` manualmente mientras el servicio está activo (ambos competirían por los mensajes). Para detenerlo: `systemctl --user stop telegram-vps-remoto`.

---

## Lo que NO hace (a propósito)

- No instala programas, no modifica nada fuera de `area/`, no usa `sudo` ni lee tus claves.
- No guarda la conversación: cada pedido es nuevo (el «sí» solo vale para la última propuesta, durante 10 minutos).
- No usa una API de pago: si aparece `ANTHROPIC_API_KEY` en el entorno, el bot la elimina antes de llamar a Claude.
