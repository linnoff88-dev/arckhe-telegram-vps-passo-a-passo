# RELATO — validação do passo a passo (rodada 2)

Escrevi o `bot.py` do zero, etapa por etapa, seguindo só o texto. Usei o Telegram falso na porta 18282, em segundo plano, e matei cada processo pelo PID. Não rodei `systemctl`, `loginctl` nem `journalctl`.

## 1. Resultado por etapa

| Etapa | Resultado | Saída obtida | Bateu com o esperado? |
|---|---|---|---|
| 1 | OK | `Python 3.12.3`; `env \| grep -c ANTHROPIC_API_KEY` = `0`; `claude -p ... --model haiku` = `ok`. Copiei o `telegram_falso.py` de `_baixados/`; o `--help` começa com `usage: telegram_falso.py`. | Sim |
| 2 | OK | `conectado como @bot_falso_bot` | Sim |
| 3 | OK | `você (111) → oi` / `bot → Você disse: oi` | Sim |
| 4 | OK | Com `DONOS=` vazio: `bot → Este bot é privado.` e `recusado: from.id=111`. Com `DONOS=111`: `/start` devolveu "Pronto. Peça o que quiser na VPS. ...". | Sim. Apareceram 3 linhas `recusado` a mais no log por causa da fila (veja 2.7). |
| 5 | OK | O disco respondeu com números ("`/` NVMe 3,7 TB: 1,3 TB livres..."). "apaga a pasta logs" respondeu que não conseguiu apagar (Bash negado). `ls area/logs \| wc -l` = `3`. | Sim |
| 6 | OK | O conferidor deu exatamente as 6 linhas esperadas (`aceito rm -r logs`, e as outras 5 recusas com os motivos do texto). Com o bot: "Vou fazer: ... / Comandos: rm -r logs / Confirma? (sim/não)", e `3` arquivos mantidos. | Sim |
| 7 | OK | `eh_sim` deu True, True, True, False, False, False. Fluxo: Confirma? → "Cancelado. Nada foi mudado." → `3` → Confirma? → "Feito:\nrm -r logs → ok" → `ls area` vazio. | Sim |
| 8 | OK | `auditoria.jsonl` ficou com `recusado` (de 222), `pedido`, `proposta`, `resposta`, `aprovado` e `feito` (`rm -r logs → ok`). | Sim |
| 9 | OK | Escrevi `./telegram-vps-remoto.service` (não ativei). `testar_travas.py` terminou com todas as linhas `PASSOU` e `TUDO OK`. | Sim |

## 2. Ambiguidades, lacunas e adivinhações

1. **Etapa 2: o `bot.py` já nasce com `import ... urllib.parse, urllib.request` sem `time`.** A etapa 3 manda acrescentar `time`, e as etapas 5, 6 e 8 também mexem no `import`. Funciona, mas sou eu quem tem de manter a linha em dia a cada etapa. Seria mais simples dar a linha final do `import` de uma vez.
2. **Etapas 3 a 8 dizem "troque X" e "acrescente depois de Y" sem dar o arquivo final.** O gabarito só está no repositório, que ainda não está publicado. Tive de reconstruir a ordem das definições a partir de frases soltas:
   - "Depois da linha `API = ...`, as listas..."
   - "Antes da linha `API = ...`" (etapas 4 e 5)
   - "Depois de `enviar`" (etapas 5 e 8)
   - Pus `env_limpo`, `claude`, `validar`, `eh_sim`, `conferir_tar`, `executar` e `pendente` entre `enviar` e `tratar`, e `auditar` logo antes de `env_limpo`. Funciona, mas é uma escolha minha.
3. **Etapa 5, "Troque a última linha (`enviar(chat, f"Você disse: {texto}")`) por: [duas linhas]".** Entendi que `sendChatAction` e `enviar(claude(...))` substituem a linha do eco. A etapa 6 depois diz "troque as duas últimas linhas (o `sendChatAction` e o `enviar(chat, claude(...))`)", e eu a li como referência a essas duas linhas.
4. **Etapa 6: o bloco provisório entra no meio do `tratar` ("Troque as duas últimas linhas por:").** O bloco novo começa com `if pendente.pop(chat, None):` e termina com o `if acao: ... else: ...`. Isso só fica claro lendo o código. Faltou dizer "o bloco `if pendente.pop...` vai ANTES do `sendChatAction`".
5. **Etapa 7: o texto para localizar o bloco da etapa 6 não bate letra por letra.** O bloco mostrado na etapa 7 não tem o comentário `# provisório: some na etapa 7` que existe na linha da etapa 6. Quem usa busca e troca literal não acha o trecho.
6. **Etapa 7: "qualquer outra resposta cancela" não corresponde ao código dado.**
   - Se a resposta não é sim nem "não", o código descarta o pedido pendente e deixa a mensagem seguir adiante, que é tratada como um pedido novo e vai ao Claude. Não existe aviso de cancelamento nesse caso.
   - O texto sugere um cancelamento simples. O comportamento real é "cancela e trata como pedido novo".
7. **Etapa 8: a tabela diz "logo depois do `pendente.pop(chat)` do bloco `if p:`", mas há dois `pendente.pop(chat)` no `tratar`.**
   - Um fica dentro de `if p and eh_sim(texto):` e o outro dentro de `if p:`.
   - Entendi pelo nome do bloco (`if p:`, o segundo) e coloquei `auditar(ev="cancelado")` lá. Isso só funciona porque o texto da etapa 7 deixa os dois blocos claros.
   - A linha `auditar(ev="erro")` no `except` do `main` não diz se vai antes ou depois do `enviar`. Coloquei antes.
8. **O `fala` espera só 120 s por padrão e não é avisado.** As etapas 5 a 8 chamam o Claude de verdade (10 a 60 s, às vezes mais). Usei `--espera 150` para não correr risco. O texto cita `--espera` em nenhum lugar. Sugiro uma nota nas etapas 5 a 8.
9. **O aviso sobre a fila do Telegram falso aparece só no fim da etapa 3, e funcionou como descrito.** Na etapa 4 vi `recusado: from.id=111` 3 vezes no log, mesmo mandando uma mensagem só. Eram as mensagens da tentativa anterior com o bot sem o token falso.
10. **Comando em segundo plano:**
    - Variável exportada em uma chamada do shell não vale na seguinte. O `export TELEGRAM_API=...` que usei no começo se perdeu e o bot falou com o Telegram real (`rede: HTTP Error 401: Unauthorized`).
    - O texto já avisa o 401 ("`401` = token errado ou `TELEGRAM_API` esquecido"), então a mensagem ajudou.
    - Criei um `rodar.sh` auxiliar fora do passo a passo, só para repetir a mesma linha de comando.
11. **Etapa 9: o teste exige que o `bot.py` tenha exatamente `AREA`, `AUDITORIA`, `validar`, `eh_sim` e as demais funções, com esses nomes e formatos.** O texto não diz isso. Passou porque segui os nomes dados, mas quem renomear algo quebra o teste sem aviso.
12. **A etapa 5 depende de o `claude` aceitar `--setting-sources ""`, `--json-schema` e `--strict-mcp-config`.** O texto não pede uma versão mínima do Claude Code. Funcionou com o `claude` instalado aqui.
13. **O `tar` não tem teste no passo a passo.** `conferir_tar` só é exercitado indiretamente pelo caso "recusa link para fora" do `testar_travas.py`. Não testei `tar` fora disso.

## 3. Última linha de `python3 testes/testar_travas.py`

```
TUDO OK
```
