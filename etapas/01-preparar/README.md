# Etapa 1 — Preparar a VPS e o Claude Code

Ainda nêo tem `bot.py`. Nesta etapa você só confere a base:

```bash
python3 --version                          # Python 3.10 ou mais novo
curl -fsSL https://claude.ai/install.sh | bash
claude                                     # /login com a conta da assinatura → /exit
env | grep -c ANTHROPIC_API_KEY            # 0
claude -p "responda só: ok" --model haiku  # ok
mkdir -p ~/kits/telegram-vps-remoto/ferramentas ~/kits/telegram-vps-remoto/testes
cd ~/kits/telegram-vps-remoto
curl -fsSLo ferramentas/telegram_falso.py https://raw.githubusercontent.com/linnoff88-dev/telegram-vps-passo-a-passo/main/ferramentas/telegram_falso.py
```

Texto completo: [PASSO-A-PASSO.md, etapa 1](../../PASSO-A-PASSO.md#etapa-1--preparar-a-vps-e-o-claude-code).
