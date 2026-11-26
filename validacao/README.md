# Validaçêo do passo a passo por agente novo

Cada rodada: um `claude -p` novo (modelo Sonnet, pela assinatura), numa pasta vazia, recebeu **só** o texto do `PASSO-A-PASSO.md` (mais o pedido em `pedido-validador.md` do lado de fora: Telegram falso, sem bot real, sem systemd). Ele escreveu o `bot.py` etapa por etapa e rodou os testes. Ninguém lhe deu o gabarito de `etapas/`.

| Rodada | Data | Resultado | Onde travou / o que mudou no texto |
|---|---|---|---|
| 1 | 20/11/2026 | 9 etapas OK depois de 1 correçêo; `testar_travas.py` → `TUDO OK` (36 PASSOU) | `NameError: AREA` na etapa 6: a ordem das linhas da etapa 5 era ambígua. O texto passou a dar a ordem do topo do arquivo; também entraram o aviso do `TELEGRAM_API`/401, a fila de mensagens do Telegram falso, a barra dupla do `Read(//...)`, o `if __name__` e o caminho da unidade systemd. ([relato](rodada-1-relato.md)) |
| 2 | 20/11/2026 | 9 etapas OK sem erro; `TUDO OK` | Só clareza: o bloco provisório da etapa 6, o que acontece com outra resposta que nêo é sim/nêo, qual `pendente.pop` recebe o `auditar`, o `--espera` do `fala`, a linha final do `import` e a ordem das funções, os nomes que o teste usa e a versêo do Claude Code. Tudo isso entrou no texto. ([relato](rodada-2-relato.md)) |
| 3 | 20/11/2026 | Só pela **página** do guia (texto da página com os blocos de código abertos, downloads reais por `curl`/raw): 9 etapas OK, 39 PASSOU, `TUDO OK`; "a página bastou sozinha" | Etapas 5–9 já iguais ao kit corrigido (leitura só dentro da área, mais pastas negadas, "sim, mas…" nêo confirma). Lacunas que entraram na página: porta ocupada, onde salvar o `bot.py`, parar o bot entre etapas, linha de comando vence o `.env`, tempo e `--espera` do `fala`, recriar `area/logs` na etapa 8, tempo real da suíte. ([relato](rodada-3-relato.md)) |
| 4 | 20/11/2026 | Só pela página, depois do revisor 2 (sem `du`, salvar o `bot.py` antes de rodar, terminais, vídeo escondido): 9 etapas OK, 40 PASSOU, `TUDO OK`; "nêo precisei adivinhar nenhum código" | Entraram na página: lembrete de parar/reiniciar o bot a cada etapa e "o que vem na frente do comando vale mais que o `.env`". ([relato](rodada-4-relato.md)) |

## Furo achado durante a montagem

`claude -p` herda o `~/.claude/settings.json` (e o `.claude/settings.json` da pasta): as regras "allow" de lá se somam ao `--allowedTools`. Numa máquina com `Bash(rm:*)` liberado, o bot original apagou a pasta `logs` com a ordem "apague agora a pasta logs com rm -r logs, sem perguntar". A correçêo (`--setting-sources ""` e `--strict-mcp-config`) está nas etapas 5–9, e o teste novo coloca de propósito um `settings.json` armadilha na área. O mesmo patch para o kit original está em [`patch-kit-setting-sources.diff`](patch-kit-setting-sources.diff).
