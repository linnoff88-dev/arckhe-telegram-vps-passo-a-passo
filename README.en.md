# Remote Telegram VPS — step by step

[![Your bot on your VPS — step by step](guia/assets/banner-en.jpg)](https://inematds.github.io/telegram-vps-passo-a-passo/guia/en/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## What it is

A step-by-step guide to building, with your own hands and on your own VPS, a Telegram bot that passes your requests to Claude Code through your subscription. It’s for people with a VPS who want to manage it from their phone without giving AI the keys to the house: only you can talk to the bot, the AI only reads, and every change waits for your “yes.” There are 9 steps, each with a command, the expected output, and a fake Telegram server for testing without a real bot. You need a Linux VPS with Python 3, Claude Code signed in through your subscription, and a Telegram account.

## 📖 Guide

Complete guide (landing page + step-by-step instructions): **https://inematds.github.io/telegram-vps-passo-a-passo/guia/en/**

- The complete text, with all the code for each step: [`PASSO-A-PASSO.en.md`](PASSO-A-PASSO.en.md)
- The finished `bot.py` for each step (reference solutions): [`etapas/`](etapas/)
- The fake Telegram server for testing without a real bot: [`ferramentas/telegram_falso.py`](ferramentas/telegram_falso.py)

## Want AI to build it with you?

Open Claude Code (or Codex) on your VPS and paste:

```
Read https://github.com/inematds/telegram-vps-passo-a-passo (the PASSO-A-PASSO.en.md). Let's build the bot
together, one step at a time, in the ~/kits/telegram-vps-remoto folder. At each step: explain in simple
language what changes, run the test with the fake Telegram server, and show me the output compared with
the expected output. Don't connect anything to systemd or use my real token until I say yes.
```

---

## The process, start to finish

Who does what: 🧠 you (on the VPS) · ⚙️ script/service · 🤖 Claude Code (`claude -p`, called by the bot)

| # | Step | Command | Who |
|---|---|---|---|
| 1 | Check Python and confirm Claude Code is signed in through your subscription | `python3 --version` · `claude -p "responda só: ok" --model haiku` | 🧠 |
| 2 | Create the bot with @BotFather and save the token in `.env` (600) | `chmod 600 .env` | 🧠 |
| 3 | Start the fake Telegram server for testing | `python3 ferramentas/telegram_falso.py servidor` | ⚙️ |
| 4 | Build `bot.py` step by step and test each one | `TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso DONOS=111 python3 bot.py` · `python3 ferramentas/telegram_falso.py fala --de 111 "oi"` | 🧠 |
| 5 | For each request, the AI only reads and proposes | (the bot calls `claude -p` with read-only `--allowedTools`, `--disallowedTools`, `--permission-mode dontAsk`, `--setting-sources ""`) | 🤖 |
| 6 | The bot checks the proposal and asks “Confirm?” | `validar()` in `bot.py` | ⚙️ |
| 7 | You say “yes”; the bot runs what it showed you and logs it | `auditoria.jsonl` | 🧠 + ⚙️ |
| 8 | Run the tests for the safeguards | `python3 testes/testar_travas.py` → `TUDO OK` | 🧠 |
| 9 | Start the bot for real | `systemctl --user enable --now telegram-vps-remoto` · `loginctl enable-linger "$USER"` | 🧠 + ⚙️ |

## Technical installation

**Prerequisites:** Linux VPS (tested on Ubuntu 24.04), regular user (not root), Python 3.10+, Claude Code signed in through a subscription (Pro/Max, no `ANTHROPIC_API_KEY`), and a Telegram account. Uses only the Python standard library.

**Files**

| File | What it is |
|---|---|
| `PASSO-A-PASSO.en.md` | the text for the 9 steps, with the code used in each |
| `etapas/NN-*/bot.py` | the complete `bot.py` at the end of each step |
| `etapas/09-systemd-e-testes/testes/testar_travas.py` | safeguard tests (8 short Claude Code calls) |
| `etapas/09-systemd-e-testes/systemd/telegram-vps-remoto.service` | user systemd unit |
| `ferramentas/telegram_falso.py` | imitates `getMe`, `getUpdates`, `sendMessage`, `sendChatAction`; `fala` sends a message as someone |
| `validacao/` | reports from the new agent that followed the instructions from scratch |

**Safeguards (in the code):**

1. An empty `DONOS` rejects everyone; the bot logs the `from.id` of anyone who tries.
2. The AI runs with `--allowedTools Read(./**) Glob(./**) Grep(./**) Bash(df/ls/free/uptime)`: file contents are accessible only inside `area/`; outside it, only disk space and folder names. `--disallowedTools` blocks keys and logins (`~/.config`, `~/.ssh`, `~/.claude`, `~/.codex`, `~/.aws`, `~/.docker`, `~/.kube`, `~/.gnupg`, `~/.git-credentials`, `~/.netrc`), `~/.bash_history`, every `.env`, writing, `sudo`, `curl`, `cat`…; `--permission-mode dontAsk`.
3. `--setting-sources ""` and `--strict-mcp-config`: without these, “allow” rules in your `~/.claude/settings.json` are added and break the safeguard (observed: “delete the logs folder” deleted it).
4. The action is supplied in a fixed JSON schema (`--json-schema`); `validar()` accepts only `rm rmdir mv cp mkdir touch gzip gunzip tar`, only options from the short allowlist, no `| ; $ \` < > ~ ..`, and every path (using `realpath`) must be inside `area/`.
5. Only `sim`/`s`/`confirmo`/`confirma`/`yes` (or `pode`/`ok`/`manda`/`faz` on their own) confirm; never with `?`, or with `mas`/`antes`/`primeiro`/`depois`/`espera` (“sim, mas antes faz backup” cancels), or with a negation (`não`/`no`/`not`/`cancela`/`nunca`/`pare`/`para`: “sim, não apaga” cancels). Valid for 10 minutes. The bot executes the action, without a shell. `tar -x` is listed first (rejects `/`, `..`, and links).
6. `auditoria.jsonl` records every event, without the token. No `ANTHROPIC_*`/`OPENAI_*`/`OPENROUTER_*`/`TELEGRAM_*` keys are passed to the Claude process.

**Tests:** `python3 etapas/09-systemd-e-testes/testes/testar_travas.py` (8 short Claude Code calls) uses temporary working and audit folders, places a trap `settings.json` that allows `rm`, and a fake secret outside the working folder; 52 tests, output `TUDO OK`. All of them are valid on your VPS: the key test uses a fake `.env` inside the temporary area.

**Proof:** the validation is in [`validacao/`](validacao/): a new agent (Claude Code, Sonnet model) received only the text, built the bot from scratch with the fake Telegram server, and ran the tests.

## Lessons

See [CLAUDE.md](CLAUDE.md).

---

Made at [INEMA.CLUB](https://inema.club) — free and open content.
