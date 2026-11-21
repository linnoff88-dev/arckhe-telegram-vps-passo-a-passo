# Telegram VPS remoto â€” passo a passo

<div align="center">
  <img src="capa/logo.svg" alt="Arckhé AI" height="48" />
  <p><strong>Arckhé AI</strong></p>
</div>


[![Bot na sua VPS â€” passo a passo](guia/assets/banner.jpg)](https://inematds.github.io/telegram-vps-passo-a-passo/guia/)

**ðŸ‡§ðŸ‡· [PortuguÃªs](README.md) Â· ðŸ‡ºðŸ‡¸ [English](README.en.md) Â· ðŸ‡ªðŸ‡¸ [EspaÃ±ol](README.es.md)**

## O que Ã©

Um passo a passo para vocÃª montar, com as prÃ³prias mÃ£os e na sua VPS, um bot de Telegram que passa os seus pedidos para o Claude Code pela sua assinatura. Serve para quem tem uma VPS e quer cuidar dela pelo celular sem dar Ã  IA a chave da casa: sÃ³ vocÃª fala com o bot, a IA sÃ³ lÃª, e qualquer mudanÃ§a espera o seu "sim". SÃ£o 9 etapas, cada uma com o comando, a saÃ­da esperada e um Telegram falso para testar sem bot real. Precisa de uma VPS Linux com Python 3, o Claude Code logado na sua assinatura e uma conta no Telegram.

## ðŸ“– Guia

Guia completo (landing + passo a passo): **https://inematds.github.io/telegram-vps-passo-a-passo/guia/**

- O texto inteiro, com todo o cÃ³digo de cada etapa: [`PASSO-A-PASSO.md`](PASSO-A-PASSO.md) (tambÃ©m em [inglÃªs](PASSO-A-PASSO.en.md) e [espanhol](PASSO-A-PASSO.es.md))
- O `bot.py` pronto de cada etapa (gabarito): [`etapas/`](etapas/)
- O Telegram falso para testar sem bot real: [`ferramentas/telegram_falso.py`](ferramentas/telegram_falso.py)

## Quer que a IA monte com vocÃª?

Abra o Claude Code (ou o Codex) na sua VPS e cole:

```
Leia https://github.com/inematds/telegram-vps-passo-a-passo (o PASSO-A-PASSO.md). Vamos montar o bot
juntos, etapa por etapa, na pasta ~/kits/telegram-vps-remoto. Em cada etapa: me explique em linguagem
simples o que muda, rode o teste com o Telegram falso e me mostre a saÃ­da comparada com a esperada.
NÃ£o ligue nada no systemd nem use meu token real antes de eu dizer sim.
```

---

## O processo, do inÃ­cio ao fim

Quem faz: ðŸ§  vocÃª (na VPS) Â· âš™ï¸ script/serviÃ§o Â· ðŸ¤– Claude Code (`claude -p`, chamado pelo bot)

| # | Passo | Comando | Quem |
|---|---|---|---|
| 1 | Conferir Python e Claude Code logado na assinatura | `python3 --version` Â· `claude -p "responda sÃ³: ok" --model haiku` | ðŸ§  |
| 2 | Criar o bot no @BotFather e guardar o token no `.env` (600) | `chmod 600 .env` | ðŸ§  |
| 3 | Subir o Telegram falso para testar | `python3 ferramentas/telegram_falso.py servidor` | âš™ï¸ |
| 4 | Montar o `bot.py` etapa por etapa e testar cada uma | `TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso DONOS=111 python3 bot.py` Â· `python3 ferramentas/telegram_falso.py fala --de 111 "oi"` | ðŸ§  |
| 5 | A cada pedido, a IA sÃ³ lÃª e propÃµe | (o bot chama `claude -p` com `--allowedTools` de leitura, `--disallowedTools`, `--permission-mode dontAsk`, `--setting-sources ""`) | ðŸ¤– |
| 6 | O bot confere a proposta e pergunta "Confirma?" | `validar()` no `bot.py` | âš™ï¸ |
| 7 | VocÃª diz "sim"; o bot executa o que mostrou e anota | `auditoria.jsonl` | ðŸ§  + âš™ï¸ |
| 8 | Rodar os testes das travas | `python3 testes/testar_travas.py` â†’ `TUDO OK` | ðŸ§  |
| 9 | Ligar o bot de vez | `systemctl --user enable --now telegram-vps-remoto` Â· `loginctl enable-linger "$USER"` | ðŸ§  + âš™ï¸ |

## InstalaÃ§Ã£o tÃ©cnica

**PrÃ©-requisitos:** VPS Linux (testado em Ubuntu 24.04), usuÃ¡rio comum (nÃ£o root), Python 3.10+, Claude Code logado pela assinatura (Pro/Max, sem `ANTHROPIC_API_KEY`), uma conta no Telegram. SÃ³ biblioteca padrÃ£o do Python.

**Arquivos**

| Arquivo | O que Ã© |
|---|---|
| `PASSO-A-PASSO.md` | o texto das 9 etapas, com o cÃ³digo que entra em cada uma |
| `etapas/NN-*/bot.py` | o `bot.py` completo no fim de cada etapa |
| `etapas/09-systemd-e-testes/testes/testar_travas.py` | testes das travas (8 chamadas curtas do Claude Code) |
| `etapas/09-systemd-e-testes/systemd/telegram-vps-remoto.service` | unidade systemd de usuÃ¡rio |
| `ferramentas/telegram_falso.py` | imita `getMe`, `getUpdates`, `sendMessage`, `sendChatAction`; `fala` manda mensagem como alguÃ©m |
| `validacao/` | relatos do agente novo que seguiu o texto do zero |

**As travas (no cÃ³digo):**

1. `DONOS` vazio recusa todos; o bot anota o `from.id` de quem tentou.
2. A IA roda com `--allowedTools Read(./**) Glob(./**) Grep(./**) Bash(df/ls/free/uptime)`: conteÃºdo de arquivo sÃ³ dentro de `area/`; fora dela sÃ³ espaÃ§o em disco e nomes de pastas. `--disallowedTools` nega chaves e logins (`~/.config`, `~/.ssh`, `~/.claude`, `~/.codex`, `~/.aws`, `~/.docker`, `~/.kube`, `~/.gnupg`, `~/.git-credentials`, `~/.netrc`), `~/.bash_history`, todo `.env`, escrita, `sudo`, `curl`, `cat`â€¦; `--permission-mode dontAsk`.
3. `--setting-sources ""` e `--strict-mcp-config`: sem isso, regras "allow" do seu `~/.claude/settings.json` se somam e furam a trava (medido: "apague a pasta logs" apagou).
4. A aÃ§Ã£o vem num JSON fixo (`--json-schema`); `validar()` aceita sÃ³ `rm rmdir mv cp mkdir touch gzip gunzip tar`, sÃ³ opÃ§Ãµes da lista curta, sem `| ; $ \` < > ~ ..`, todo caminho (com `realpath`) dentro de `area/`.
5. SÃ³ `sim`/`s`/`confirmo`/`confirma`/`yes` (ou `pode`/`ok`/`manda`/`faz` sozinhos) confirmam; com `?` nunca, nem com `mas`/`antes`/`primeiro`/`depois`/`espera` ("sim, mas antes faz backup" cancela), nem com negaÃ§Ã£o (`nÃ£o`/`no`/`not`/`cancela`/`nunca`/`pare`/`para`: "sim, nÃ£o apaga" cancela). Vale 10 min. Quem executa Ã© o bot, sem shell. `tar -x` Ã© listado antes (recusa `/`, `..`, link).
6. `auditoria.jsonl` guarda cada evento, sem o token. Nenhuma chave `ANTHROPIC_*`/`OPENAI_*`/`OPENROUTER_*`/`TELEGRAM_*` vai para o processo do Claude.

**Testes:** `python3 etapas/09-systemd-e-testes/testes/testar_travas.py` (8 chamadas curtas do Claude Code) usa Ã¡rea e auditoria temporÃ¡rias, coloca um `settings.json` armadilha que libera `rm` e uma isca com segredo falso fora da Ã¡rea; 52 testes, saÃ­da `TUDO OK`. Todos valem na sua VPS: o teste das chaves usa um `.env` falso dentro da Ã¡rea temporÃ¡ria.

**Prova:** a validaÃ§Ã£o estÃ¡ em [`validacao/`](validacao/): um agente novo (Claude Code, modelo Sonnet) recebeu sÃ³ o texto, montou o bot do zero com o Telegram falso e rodou os testes.

## Lessons

Ver [CLAUDE.md](CLAUDE.md).

---

Feito no [INEMA.CLUB](https://inema.club) â€” conteÃºdo aberto e gratuito.

---

<div align="center">
  <img src="capa/logo.svg" alt="Arckhé AI" height="32" />
  <p><strong>Arckhé AI</strong></p>
</div>