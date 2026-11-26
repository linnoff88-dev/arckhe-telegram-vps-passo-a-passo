# RELATO — rodada 1 (seguindo só o passo a passo)

Resultado geral: as 9 etapas ficaram OK. O `testes/testar_travas.py` terminou em `TUDO OK`, com 36 linhas `PASSOU`. Rodei esse teste duas vezes e as duas deram `TUDO OK`.

## 1. Etapa por etapa

| Etapa | Estado | O que obtive | Bateu com o esperado? |
|---|---|---|---|
| 1 | OK | Python 3.12.3. `env \| grep -c ANTHROPIC_API_KEY` deu `0`. `claude -p "responda só: ok" --model haiku` deu `ok`. `telegram_falso.py --help` começa com `usage: telegram_falso.py` (arquivo copiado de `_baixados/`). | Sim |
| 2 | OK | `conectado como @bot_falso_bot` | Sim |
| 3 | OK | `você (111) → oi` e `bot → Você disse: oi` | Sim |
| 4 | OK | Com `DONOS=` vazio: `bot → Este bot é privado.` e `recusado: from.id=111` no log. Com `DONOS=111`: `/start` voltou "Pronto. Peça o que quiser na VPS…". | Sim |
| 5 | OK | A pergunta do disco veio com números (1,3 TB livres na raiz etc.). "apaga a pasta logs" voltou "Nêo consegui apagar… O Bash foi negado". `ls area/logs \| wc -l` deu `3`. | Sim |
| 6 | OK | O conferidor deu exatamente as 6 linhas esperadas (1 aceita, 5 recusas com os motivos certos). Com o bot, a resposta trouxe `Vou fazer…`, `Comandos: rm -r logs` e `Confirma? (sim/nêo)`, e `3` arquivos continuaram lá. | Sim, depois de corrigir a ordem das definições (ver 2.1) |
| 7 | OK | `eh_sim` deu True, True, True, False, False, False. "nêo" respondeu `Cancelado. Nada foi mudado.` e `3`. "sim" respondeu `Feito:` e `rm -r logs → ok`. `ls area` ficou sem `logs`. | Sim |
| 8 | OK | `auditoria.jsonl` ficou com `recusado` (222), `pedido`, `proposta`, `resposta`, `aprovado` e `feito` (`rm -r logs → ok`). | Sim |
| 9 | OK | Escrevi `./telegram-vps-remoto.service`. Nêo rodei `systemctl`, `loginctl` nem `journalctl`. `python3 testes/testar_travas.py` terminou em `TUDO OK`. | Sim |

## 2. Pontos ambíguos, faltas e correções

1. **Ordem das definições na etapa 5 (defeito real).**
   - Frases do texto: "Depois de `DONOS = ...`, acrescente as configurações" (`AREA`, `MODELO`, `CLAUDE`, `TEMPO_IA`) e "Depois da linha `API = ...`:" (`H`, `NEGADO`, `LEITURA`).
   - Seguindo literalmente, o bloco `NEGADO`/`LEITURA` fica antes de `AREA`, porque `DONOS` foi posto logo depois de `API` na etapa 4. Na etapa 6 o texto põe `REGRAS_LEITURA`, um f-string que usa `{AREA}`, logo depois de `LEITURA`. Resultado: `NameError: name 'AREA' is not defined` ao importar o `bot.py`.
   - Corrigi movendo as 4 linhas de configuraçêo (`AREA`…`TEMPO_IA`) para antes de `H = ...`. O texto deveria dizer "antes de `NEGADO`" ou mostrar a ordem final.
2. **"Terminal 1/2/3" versus processos em segundo plano.** O texto fala em "dois terminais" e depois em três, mas nêo diz que o servidor falso precisa continuar vivo. Adaptei como o enunciado mandou.
3. **Sem aviso de que `export`/variável de ambiente nêo persiste entre chamadas.**
   - Na etapa 4 esqueci o `TELEGRAM_API` (erro meu, mas fácil de repetir). O bot entêo bateu no Telegram real e devolveu `rede: HTTP Error 401` em loop, e o `fala` esperou 120 s sem resposta.
   - Sugestêo: dizer que, sem `TELEGRAM_API`, o bot fala com o Telegram de verdade, e que `rede: HTTP Error 401` significa token ou `TELEGRAM_API` errado.
4. **Etapa 3 e `__main__`.** "Troque o `main` por este" nêo diz se o `if __name__ == "__main__": main()` do fim fica. Mantive. É óbvio, mas dá para melhorar.
5. **Substituições na etapa 5 ("troque a última linha").** O texto diz "No `tratar`, troque a última linha (`enviar(chat, f"Você disse: {texto}")`)", mas no `tratar` da etapa 4 essa linha é a última do corpo, depois de vários `return`. Funciona, mas a indentaçêo nêo está explícita.
6. **`f"Read(/{AQUI}/.env)"` na lista `NEGADO`.** `AQUI` já começa com `/`, entêo vira `Read(//home/…/.env)`. Funciona (a sintaxe `//` é a de caminho absoluto), mas o texto nêo explica que a barra extra é proposital. Pode parecer erro de digitaçêo.
7. **Etapa 6: `"|;`$<>\n~"`.** Dentro do bloco de código o `\n` é o escape do Python. Quem copiar por um editor que reinterprete o `\n` pode quebrar a string. Nêo aconteceu comigo.
8. **Etapa 6: a mensagem provisória ("o 'sim' entra na etapa 7").** Ela é trocada na etapa 7. O texto da etapa 6 nêo diz que essa mensagem é temporária. Está claro pelo contexto.
9. **Etapa 8: "dentro do `except ValueError` do `validar`".** O `except` está no `tratar`, nêo dentro do `validar`. Entendi pelo contexto. Também nêo ficou explícito onde exatamente ficam as duas linhas de `auditar` em "proposta" (coloquei `proposta` e depois `resposta`, o que deu a ordem esperada).
10. **Etapa 9: o `systemd` mora na sua pasta.** O texto manda gravar em `~/.config/systemd/user/…` e usa `%h/kits/telegram-vps-remoto`. No meu teste a pasta era outra, entêo a unidade só serviria depois de ajustar o caminho. Para o teste o enunciado já cobria isso.
11. **Etapa 9: tempo.** O texto diz "uns 3 minutos" para os testes de travas. Foi coerente com o que vi (cada rodada ficou perto disso).
12. **Etapa 1: o `curl` de instalaçêo e o `/login`.** Pulei por instruçêo do enunciado, entêo nêo validei esses comandos.
13. **Etapa 5: a saída do disco varia muito.** O exemplo do texto é "Sobram 1,3 TB livres de 3,7 TB". Na minha máquina deu algo parecido, mas em lista. A etapa 7 do texto diz "Esperado" só para o fluxo, o que é suficiente.
14. **Log do bot depois do teste da etapa 4.** Apareceram três linhas `recusado: from.id=111` para um único `fala`. O servidor falso reentrega mensagens antigas quando o bot reinicia com `offset=0`. Nêo é defeito do texto, mas confunde quem comparar com a "saída esperada" (uma linha).

## 3. Última linha de `python3 testes/testar_travas.py`

```
TUDO OK
```
