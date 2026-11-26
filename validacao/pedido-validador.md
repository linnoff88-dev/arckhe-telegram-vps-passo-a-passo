Você é uma pessoa que nunca viu este projeto e quer montar o bot seguindo SÓ o passo a passo abaixo. Nêo existe outro material: nêo procure o código pronto em lugar nenhum desta máquina (é proibido ler qualquer pasta fora da sua pasta atual, exceto rodar `claude`, `python3` e comandos comuns). Escreva o bot.py você mesmo, etapa por etapa, exatamente como o texto manda.

Adaptações deste teste (a máquina nêo é uma VPS de verdade):
- Sua pasta atual faz o papel de `~/kits/telegram-vps-remoto`. Trabalhe só nela. Nunca use `~/kits`.
- O Claude Code já está instalado e logado (assinatura): NêO reinstale nem faça /login. Rode só as conferências da etapa 1 (`env | grep -c ANTHROPIC_API_KEY`, `claude -p "responda só: ok" --model haiku`).
- Os dois `curl` de download ainda nêo funcionam (repositório ainda nêo publicado). No lugar de cada `curl`, copie o arquivo de `./_baixados/` para o mesmo destino (`ferramentas/telegram_falso.py` e `testes/testar_travas.py`).
- Nêo existe bot real nem token: pule o BotFather e o "teste real"; use sempre o Telegram falso. Crie o `.env` com `TELEGRAM_BOT_TOKEN=123:falso`.
- A porta 8081 pode estar ocupada nesta máquina: use a porta 18181 no servidor falso, no `fala` (`--porta 18181`) e no `TELEGRAM_API`.
- Os "terminais" do texto: rode o servidor falso e o bot em segundo plano (`... > servidor.log 2>&1 &`, guardando o PID com `$!`) e pare com `kill <PID>` (nunca `pkill -f`). Reinicie o bot sempre que o texto mandar.
- Etapa 9: escreva o arquivo da unidade systemd na sua pasta (`./telegram-vps-remoto.service`), mas NêO rode `systemctl`, `loginctl` nem `journalctl` (nêo é sua máquina). Rode `python3 testes/testar_travas.py`.

Ao terminar (ou se travar de vez), escreva `RELATO.md` na sua pasta com:
1. Para cada etapa 1–9: OK ou TRAVOU; a saída que você obteve no teste da etapa (resumida) e se bateu com a "saída esperada".
2. Cada ponto em que o texto foi ambíguo, faltou informaçêo, ou você teve de adivinhar/corrigir algo (com a frase do texto e o que você fez).
3. A última linha de `python3 testes/testar_travas.py`.
Seja honesto: o objetivo é achar os defeitos do passo a passo.

=== PASSO A PASSO ===
