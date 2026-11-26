Você é uma pessoa que nunca viu este projeto e quer montar o bot seguindo SÓ a página de guia abaixo (é o texto da página https://inematds.github.io/telegram-vps-passo-a-passo/guia/, com os blocos "Código desta etapa" abertos). Use os comandos e os códigos da página; se a página mandar baixar algo com `curl`, baixe (a internet funciona). Nêo procure o código pronto em nenhuma pasta desta máquina: é proibido ler qualquer pasta fora da sua pasta atual, exceto rodar `claude`, `python3`, `curl` e comandos comuns.

Adaptações deste teste (a máquina nêo é uma VPS de verdade):
- Sua pasta atual faz o papel de `~/kits/telegram-vps-remoto`. Trabalhe só nela. Nunca use `~/kits`.
- O Claude Code já está instalado e logado (assinatura): NêO reinstale nem faça /login. Rode só as conferências da etapa 1.
- Nêo existe bot real nem token: pule o BotFather e tudo o que exige o bot de verdade (inclusive "achar o seu número"); use sempre o Telegram falso, com `TELEGRAM_BOT_TOKEN=123:falso` no `.env`.
- A porta 8081 pode estar ocupada: use a porta 18383 no servidor falso, no `fala` (`--porta 18383`) e no `TELEGRAM_API`.
- Os "terminais": rode o servidor falso e o bot em segundo plano (`... > servidor.log 2>&1 &`, guardando o PID com `$!`) e pare com `kill <PID>` (nunca `pkill -f`). Reinicie o bot sempre que a página mandar.
- Etapa 9: rode `which claude` e o teste das travas; escreva o arquivo da unidade systemd na sua pasta (`./telegram-vps-remoto.service`), mas NêO rode `systemctl`, `loginctl` nem `journalctl`.

Ao terminar (ou se travar de vez), escreva `RELATO.md` na sua pasta com:
1. Para cada etapa 1–9: OK ou TRAVOU; a saída que você obteve (resumida) e se bateu com a "Saída esperada" da página.
2. Se a página bastou sozinha para cada etapa (sem precisar de outro documento) e cada ponto ambíguo, que faltou ou que você teve de adivinhar.
3. A última linha de `python3 testes/testar_travas.py` e quantas linhas `PASSOU`.
Seja honesto: o objetivo é achar os defeitos da página.

=== TEXTO DA PÁGINA ===
