ï»¿# Telegram VPS remoto ê¢â¬â passo a passo

<div align="center">
  <img src="capa/logo.svg" alt="Arckhé AI" height="48" />
  <p><strong>Arckhé AI</strong></p>
</div>


[![Bot na sua VPS ê¢â¬â passo a passo](guia/assets/banner.jpg)](https://inematds.github.io/telegram-vps-passo-a-passo/guia/)

**ê°Å¸â¡Â§ê°Å¸â¡Â· [PortuguêÂªs](README.md) êÂ· ê°Å¸â¡Âºê°Å¸â¡Â¸ [English](README.en.md) êÂ· ê°Å¸â¡Âªê°Å¸â¡Â¸ [EspaêÂ±ol](README.es.md)**

## O que êÂ©

Um passo a passo para vocêÂª montar, com as prêÂ³prias mêÂ£os e na sua VPS, um bot de Telegram que passa os seus pedidos para o Claude Code pela sua assinatura. Serve para quem tem uma VPS e quer cuidar dela pelo celular sem dar êÂ  IA a chave da casa: sêÂ³ vocêÂª fala com o bot, a IA sêÂ³ lêÂª, e qualquer mudanêÂ§a espera o seu "sim". SêÂ£o 9 etapas, cada uma com o comando, a saêÂ­da esperada e um Telegram falso para testar sem bot real. Precisa de uma VPS Linux com Python 3, o Claude Code logado na sua assinatura e uma conta no Telegram.

## ê°Å¸ââ Guia

Guia completo (landing + passo a passo): **https://inematds.github.io/telegram-vps-passo-a-passo/guia/**

- O texto inteiro, com todo o cêÂ³digo de cada etapa: [`PASSO-A-PASSO.md`](PASSO-A-PASSO.md) (tambêÂ©m em [inglêÂªs](PASSO-A-PASSO.en.md) e [espanhol](PASSO-A-PASSO.es.md))
- O `bot.py` pronto de cada etapa (gabarito): [`etapas/`](etapas/)
- O Telegram falso para testar sem bot real: [`ferramentas/telegram_falso.py`](ferramentas/telegram_falso.py)

## Quer que a IA monte com vocêÂª?

Abra o Claude Code (ou o Codex) na sua VPS e cole:

```
Leia https://github.com/inematds/telegram-vps-passo-a-passo (o PASSO-A-PASSO.md). Vamos montar o bot
juntos, etapa por etapa, na pasta ~/kits/telegram-vps-remoto. Em cada etapa: me explique em linguagem
simples o que muda, rode o teste com o Telegram falso e me mostre a saêÂ­da comparada com a esperada.
NêÂ£o ligue nada no systemd nem use meu token real antes de eu dizer sim.
```

---

## O processo, do inêÂ­cio ao fim

Quem faz: ê°Å¸Â§Â  vocêÂª (na VPS) êÂ· ê¢Å¡â¢ê¯Â¸Â script/serviêÂ§o êÂ· ê°Å¸Â¤â Claude Code (`claude -p`, chamado pelo bot)

| # | Passo | Comando | Quem |
|---|---|---|---|
| 1 | Conferir Python e Claude Code logado na assinatura | `python3 --version` êÂ· `claude -p "responda sêÂ³: ok" --model haiku` | ê°Å¸Â§Â  |
| 2 | Criar o bot no @BotFather e guardar o token no `.env` (600) | `chmod 600 .env` | ê°Å¸Â§Â  |
| 3 | Subir o Telegram falso para testar | `python3 ferramentas/telegram_falso.py servidor` | ê¢Å¡â¢ê¯Â¸Â |
| 4 | Montar o `bot.py` etapa por etapa e testar cada uma | `TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso DONOS=111 python3 bot.py` êÂ· `python3 ferramentas/telegram_falso.py fala --de 111 "oi"` | ê°Å¸Â§Â  |
| 5 | A cada pedido, a IA sêÂ³ lêÂª e propêÂµe | (o bot chama `claude -p` com `--allowedTools` de leitura, `--disallowedTools`, `--permission-mode dontAsk`, `--setting-sources ""`) | ê°Å¸Â¤â |
| 6 | O bot confere a proposta e pergunta "Confirma?" | `validar()` no `bot.py` | ê¢Å¡â¢ê¯Â¸Â |
| 7 | VocêÂª diz "sim"; o bot executa o que mostrou e anota | `auditoria.jsonl` | ê°Å¸Â§Â  + ê¢Å¡â¢ê¯Â¸Â |
| 8 | Rodar os testes das travas | `python3 testes/testar_travas.py` ê¢â â `TUDO OK` | ê°Å¸Â§Â  |
| 9 | Ligar o bot de vez | `systemctl --user enable --now telegram-vps-remoto` êÂ· `loginctl enable-linger "$USER"` | ê°Å¸Â§Â  + ê¢Å¡â¢ê¯Â¸Â |

## InstalaêÂ§êÂ£o têÂ©cnica

**PrêÂ©-requisitos:** VPS Linux (testado em Ubuntu 24.04), usuêÂ¡rio comum (nêÂ£o root), Python 3.10+, Claude Code logado pela assinatura (Pro/Max, sem `ANTHROPIC_API_KEY`), uma conta no Telegram. SêÂ³ biblioteca padrêÂ£o do Python.

**Arquivos**

| Arquivo | O que êÂ© |
|---|---|
| `PASSO-A-PASSO.md` | o texto das 9 etapas, com o cêÂ³digo que entra em cada uma |
| `etapas/NN-*/bot.py` | o `bot.py` completo no fim de cada etapa |
| `etapas/09-systemd-e-testes/testes/testar_travas.py` | testes das travas (8 chamadas curtas do Claude Code) |
| `etapas/09-systemd-e-testes/systemd/telegram-vps-remoto.service` | unidade systemd de usuêÂ¡rio |
| `ferramentas/telegram_falso.py` | imita `getMe`, `getUpdates`, `sendMessage`, `sendChatAction`; `fala` manda mensagem como alguêÂ©m |
| `validacao/` | relatos do agente novo que seguiu o texto do zero |

**As travas (no cêÂ³digo):**

1. `DONOS` vazio recusa todos; o bot anota o `from.id` de quem tentou.
2. A IA roda com `--allowedTools Read(./**) Glob(./**) Grep(./**) Bash(df/ls/free/uptime)`: conteêÂºdo de arquivo sêÂ³ dentro de `area/`; fora dela sêÂ³ espaêÂ§o em disco e nomes de pastas. `--disallowedTools` nega chaves e logins (`~/.config`, `~/.ssh`, `~/.claude`, `~/.codex`, `~/.aws`, `~/.docker`, `~/.kube`, `~/.gnupg`, `~/.git-credentials`, `~/.netrc`), `~/.bash_history`, todo `.env`, escrita, `sudo`, `curl`, `cat`ê¢â¬Â¦; `--permission-mode dontAsk`.
3. `--setting-sources ""` e `--strict-mcp-config`: sem isso, regras "allow" do seu `~/.claude/settings.json` se somam e furam a trava (medido: "apague a pasta logs" apagou).
4. A aêÂ§êÂ£o vem num JSON fixo (`--json-schema`); `validar()` aceita sêÂ³ `rm rmdir mv cp mkdir touch gzip gunzip tar`, sêÂ³ opêÂ§êÂµes da lista curta, sem `| ; $ \` < > ~ ..`, todo caminho (com `realpath`) dentro de `area/`.
5. SêÂ³ `sim`/`s`/`confirmo`/`confirma`/`yes` (ou `pode`/`ok`/`manda`/`faz` sozinhos) confirmam; com `?` nunca, nem com `mas`/`antes`/`primeiro`/`depois`/`espera` ("sim, mas antes faz backup" cancela), nem com negaêÂ§êÂ£o (`nêÂ£o`/`no`/`not`/`cancela`/`nunca`/`pare`/`para`: "sim, nêÂ£o apaga" cancela). Vale 10 min. Quem executa êÂ© o bot, sem shell. `tar -x` êÂ© listado antes (recusa `/`, `..`, link).
6. `auditoria.jsonl` guarda cada evento, sem o token. Nenhuma chave `ANTHROPIC_*`/`OPENAI_*`/`OPENROUTER_*`/`TELEGRAM_*` vai para o processo do Claude.

**Testes:** `python3 etapas/09-systemd-e-testes/testes/testar_travas.py` (8 chamadas curtas do Claude Code) usa êÂ¡rea e auditoria temporêÂ¡rias, coloca um `settings.json` armadilha que libera `rm` e uma isca com segredo falso fora da êÂ¡rea; 52 testes, saêÂ­da `TUDO OK`. Todos valem na sua VPS: o teste das chaves usa um `.env` falso dentro da êÂ¡rea temporêÂ¡ria.

**Prova:** a validaêÂ§êÂ£o estêÂ¡ em [`validacao/`](validacao/): um agente novo (Claude Code, modelo Sonnet) recebeu sêÂ³ o texto, montou o bot do zero com o Telegram falso e rodou os testes.

## Lessons

Ver [CLAUDE.md](CLAUDE.md).

---

Feito no [INEMA.CLUB](https://inema.club) ê¢â¬â conteêÂºdo aberto e gratuito.

---

<div align="center">
  <img src="capa/logo.svg" alt="Arckhé AI" height="32" />
  <p><strong>Arckhé AI</strong></p>
</div>