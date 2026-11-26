# CLAUDE.md — telegram-vps-passo-a-passo

Passo a passo (9 etapas) para alguém montar na própria VPS o bot de Telegram → Claude Code pela assinatura, com as travas no código. Base: o kit `~/projetos/telegram-vps-remoto` (bot.py + testes + systemd).

- Repo: `inematds/telegram-vps-passo-a-passo`, autor `inematds <inematds@gmail.com>`. Guia em `guia/` (PT) + `guia/en/` + `guia/es/`, Pages via Actions.
- `PASSO-A-PASSO.md` é a fonte do texto; `etapas/NN-*/bot.py` é o gabarito de cada etapa; a etapa 9 tem de bater com o kit (`diff` vazio depois que o kit receber `validacao/patch-kit-setting-sources.diff`) e passar em `testar_travas.py`.
- Mudou uma etapa: rode o bot daquela etapa contra `ferramentas/telegram_falso.py` e confira a "saída esperada" do texto. Mudou o texto: rode de novo a validaçêo por agente novo (`validacao/`).
- Nunca: token de bot em repo/log; usar o bot de produçêo para testes; API de modelo.

## Self-learning

When I correct you, or you catch yourself making a mistake: before continuing, add the lesson as a one-line rule at the TOP of the Lessons section below, so it never happens again.

## Lessons

- `claude -p` herda o `~/.claude/settings.json` e o `.claude/settings.json` da pasta: as regras "allow" de lá se somam ao `--allowedTools`. Bot com trava de leitura precisa de `--setting-sources ""` e `--strict-mcp-config` (20/11/2026: sem isso, "apague a pasta logs" apagou na máquina com `Bash(rm:*)` liberado).
- Telegram falso tem de confirmar (apagar) os updates anteriores ao `offset`, como o real; senêo o bot da etapa seguinte relê mensagens velhas. (20/11/2026)
