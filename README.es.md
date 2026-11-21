# Telegram VPS remoto — guía paso a paso

[![Bot en tu VPS — guía paso a paso](guia/assets/banner-es.jpg)](https://inematds.github.io/telegram-vps-passo-a-passo/guia/es/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## Qué es

Una guía paso a paso para que montes con tus propias manos, en tu VPS, un bot de Telegram que envía tus solicitudes a Claude Code mediante tu suscripción. Está pensada para quienes tienen una VPS y quieren administrarla desde el celular sin darle a la IA las llaves de la casa: solo tú hablas con el bot, la IA solo lee y cualquier cambio espera tu «sí». Son 9 etapas, cada una con el comando, la salida esperada y un Telegram falso para probar sin un bot real. Necesitas una VPS Linux con Python 3, Claude Code conectado a tu suscripción y una cuenta de Telegram.

## 📖 Guía

Guía completa (landing + paso a paso): **https://inematds.github.io/telegram-vps-passo-a-passo/guia/**

- El texto completo, con todo el código de cada etapa: [`PASSO-A-PASSO.es.md`](PASSO-A-PASSO.es.md)
- El `bot.py` listo para cada etapa (solución): [`etapas/`](etapas/)
- El Telegram falso para probar sin un bot real: [`ferramentas/telegram_falso.py`](ferramentas/telegram_falso.py)

## ¿Quieres que la IA lo monte contigo?

Abre Claude Code (o Codex) en tu VPS y pega:

```
Lee https://github.com/inematds/telegram-vps-passo-a-passo (el PASSO-A-PASSO.es.md). Vamos a montar el bot
juntos, etapa por etapa, en la carpeta ~/kits/telegram-vps-remoto. En cada etapa: explícame con palabras
sencillas qué cambia, ejecuta la prueba con el Telegram falso y muéstrame la salida comparada con la esperada.
No conectes nada a systemd ni uses mi token real antes de que te diga que sí.
```

---

## El proceso, de principio a fin

Quién lo hace: 🧠 tú (en la VPS) · ⚙️ script/servicio · 🤖 Claude Code (`claude -p`, llamado por el bot)

| # | Paso | Comando | Quién |
|---|---|---|---|
| 1 | Comprobar Python y que Claude Code esté conectado a la suscripción | `python3 --version` · `claude -p "responda só: ok" --model haiku` | 🧠 |
| 2 | Crear el bot en @BotFather y guardar el token en `.env` (600) | `chmod 600 .env` | 🧠 |
| 3 | Iniciar el Telegram falso para probar | `python3 ferramentas/telegram_falso.py servidor` | ⚙️ |
| 4 | Crear `bot.py` etapa por etapa y probar cada una | `TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso DONOS=111 python3 bot.py` · `python3 ferramentas/telegram_falso.py fala --de 111 "oi"` | 🧠 |
| 5 | En cada solicitud, la IA solo lee y propone | (el bot llama a `claude -p` con `--allowedTools` de lectura, `--disallowedTools`, `--permission-mode dontAsk`, `--setting-sources ""`) | 🤖 |
| 6 | El bot revisa la propuesta y pregunta «¿Confirmas?» | `validar()` en `bot.py` | ⚙️ |
| 7 | Dices «sí»; el bot ejecuta lo que mostró y lo registra | `auditoria.jsonl` | 🧠 + ⚙️ |
| 8 | Ejecutar las pruebas de las barreras | `python3 testes/testar_travas.py` → `TUDO OK` | 🧠 |
| 9 | Dejar el bot funcionando | `systemctl --user enable --now telegram-vps-remoto` · `loginctl enable-linger "$USER"` | 🧠 + ⚙️ |

## Instalación técnica

**Requisitos previos:** VPS Linux (probado en Ubuntu 24.04), usuario común (no root), Python 3.10+, Claude Code conectado mediante la suscripción (Pro/Max, sin `ANTHROPIC_API_KEY`) y una cuenta de Telegram. Solo usa la biblioteca estándar de Python.

**Archivos**

| Archivo | Qué es |
|---|---|
| `PASSO-A-PASSO.es.md` | el texto de las 9 etapas, con el código que se agrega en cada una |
| `etapas/NN-*/bot.py` | el `bot.py` completo al final de cada etapa |
| `etapas/09-systemd-e-testes/testes/testar_travas.py` | pruebas de las barreras (8 llamadas breves de Claude Code) |
| `etapas/09-systemd-e-testes/systemd/telegram-vps-remoto.service` | unidad systemd de usuario |
| `ferramentas/telegram_falso.py` | imita `getMe`, `getUpdates`, `sendMessage`, `sendChatAction`; `fala` envía un mensaje como alguien |
| `validacao/` | informes del agente nuevo que siguió el texto desde cero |

**Las barreras (en el código):**

1. Si `DONOS` está vacío, el bot rechaza a todos y registra el `from.id` de quien lo intentó.
2. La IA se ejecuta con `--allowedTools Read(./**) Glob(./**) Grep(./**) Bash(df/ls/free/uptime)`: el contenido de los archivos solo se lee dentro de `area/`; fuera de esa carpeta solo se consultan el espacio en disco y los nombres de las carpetas. `--disallowedTools` bloquea claves e inicios de sesión (`~/.config`, `~/.ssh`, `~/.claude`, `~/.codex`, `~/.aws`, `~/.docker`, `~/.kube`, `~/.gnupg`, `~/.git-credentials`, `~/.netrc`), `~/.bash_history`, todos los `.env`, la escritura, `sudo`, `curl`, `cat`…; `--permission-mode dontAsk`.
3. `--setting-sources ""` y `--strict-mcp-config`: sin esto, las reglas «allow» de tu `~/.claude/settings.json` se suman y rompen la barrera (comprobado: se borró la carpeta `logs` al pedir «borra la carpeta logs»).
4. La acción llega en un JSON fijo (`--json-schema`); `validar()` solo acepta `rm rmdir mv cp mkdir touch gzip gunzip tar`, solo opciones de la lista corta, sin `| ; $ \` < > ~ ..` y con todas las rutas (mediante `realpath`) dentro de `area/`.
5. Solo confirman `sim`/`s`/`confirmo`/`confirma`/`yes` (o `pode`/`ok`/`manda`/`faz` por sí solas); si hay un `?`, nunca, ni tampoco con `mas`/`antes`/`primeiro`/`depois`/`espera` («sim, mas antes faz backup» cancela), ni con negación (`não`/`no`/`not`/`cancela`/`nunca`/`pare`/`para`: «sim, não apaga» cancela). Tiene una validez de 10 min. Quien ejecuta es el bot, sin shell. `tar -x` se muestra antes (rechaza `/`, `..`, enlaces).
6. `auditoria.jsonl` guarda cada evento, sin el token. Ninguna clave `ANTHROPIC_*`/`OPENAI_*`/`OPENROUTER_*`/`TELEGRAM_*` se envía al proceso de Claude.

**Pruebas:** `python3 etapas/09-systemd-e-testes/testes/testar_travas.py` (8 llamadas breves de Claude Code) usa un área y una auditoría temporales, coloca un `settings.json` trampa que permite `rm` y un señuelo con un secreto falso fuera del área; son 52 pruebas y la salida es `TUDO OK`. Todas valen en tu VPS: la prueba de las claves usa un `.env` falso dentro del área temporal.

**Prueba:** la validación está en [`validacao/`](validacao/): un agente nuevo (Claude Code, modelo Sonnet) recibió solo el texto, montó el bot desde cero con el Telegram falso y ejecutó las pruebas.

## Lessons

Consulta [CLAUDE.md](CLAUDE.md).

---

Hecho en [INEMA.CLUB](https://inema.club): contenido abierto y gratuito.
