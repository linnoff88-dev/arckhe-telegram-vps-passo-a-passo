# Etapas — o bot.py como ele fica no fim de cada etapa

Cada pasta tem o `bot.py` **completo e rodável** daquela etapa (o gabarito). O texto que ensina a montar, com o que muda, o comando e a saída esperada, está em [`../PASSO-A-PASSO.md`](../PASSO-A-PASSO.md).

| Etapa | Pasta | O que o bot passa a fazer | Teste (com o Telegram falso) | Saída esperada |
|---|---|---|---|---|
| 1 | `01-preparar/` | (nada ainda) VPS com Python 3 e Claude Code logado pela assinatura | `claude -p "responda só: ok" --model haiku` | `ok` |
| 2 | `02-token-e-env/` | lê o token do `.env` e se apresenta | `TELEGRAM_API=http://127.0.0.1:8081 TELEGRAM_BOT_TOKEN=123:falso python3 bot.py` | `conectado como @bot_falso_bot` |
| 3 | `03-eco/` | ouve por long polling e responde | `python3 ferramentas/telegram_falso.py fala --de 111 "oi"` | `bot → Você disse: oi` |
| 4 | `04-donos/` | só os DONOS falam; lista vazia recusa todos | `fala --de 111 "oi"` com `DONOS=` vazio | `bot → Este bot é privado.` |
| 5 | `05-leitura/` | pedido vai ao `claude -p` só de leitura, preso em `area/` | `fala --de 111 "apaga a pasta logs"` | não apaga; `ls area/logs \| wc -l` → `3` |
| 6 | `06-proposta-e-validador/` | a IA propõe comandos; o bot confere e pergunta | `fala --de 111 "apaga a pasta logs"` | `Confirma? (sim/não)` e nada apagado |
| 7 | `07-sim-e-execucao/` | depois do "sim", o bot executa o que mostrou | `fala ... "apaga a pasta logs"` e `fala ... "sim"` | `Feito:` / `rm -r logs → ok` |
| 8 | `08-auditoria/` | tudo anotado em `auditoria.jsonl` | `cut -c1-90 auditoria.jsonl` | eventos `pedido`, `proposta`, `aprovado`, `feito` |
| 9 | `09-systemd-e-testes/` | testes das travas + serviço systemd | `python3 testes/testar_travas.py` | `TUDO OK` |

A etapa 9 é o bot final (igual à 8), com `testes/testar_travas.py` e `systemd/telegram-vps-remoto.service`.
