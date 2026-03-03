# Monitor de Vagas - ERU 365 (UFV 2026/1)

Sistema automatizado de monitoramento de vagas livres na disciplina ERU 365 (Relações Internacionais) no site da DTI/UFV. Verifica a cada 30 minutos (configurável) e envia notificações via Telegram.

## ⚙️ Requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)

## 🚀 Instalação

### 1. Clone o repositório (se não estiver dentro dele)

```bash
cd seu-diretorio
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

#### Opção A: Sem Telegram (apenas exibição no terminal)

Você pode rodar o script sem configurar Telegram. Ele apenas exibirá as vagas no terminal.

```bash
python3 monitor_eru365.py
```

#### Opção B: Com Telegram

1. No Telegram, procure o bot **@BotFather**
2. Envie `/newbot` e siga as instruções para criar seu bot
3. Copie o **TOKEN** que ele fornecerá (ex: `7123456789:AAHxyz...`)
4. Abra o seu bot no Telegram e envie qualquer mensagem (ex: "oi")
5. Acesse: `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
6. Procure por `"chat":{"id": XXXXXXX}` — esse é seu **CHAT_ID**
7. Crie um arquivo `.env` na raiz do projeto:

```bash
cp .env.example .env
```

8. Edite o arquivo `.env` e preencha com seus dados:

```ini
TELEGRAM_TOKEN=7123456789:AAHxyz...
TELEGRAM_CHAT_ID=123456789
DISCIPLINA_ALVO=ERU 365
CHECK_INTERVAL_MINUTES=30
LOG_FILE=monitor.log
```

## 🏃 Como Rodar

### Execução simples (no primeiro plano)

```bash
python3 monitor_eru365.py
```

### Execução em background (Linux/macOS)

```bash
nohup python3 monitor_eru365.py > monitor.log 2>&1 &
```

### Execução em background (Windows - PowerShell)

```powershell
Start-Process python3 "monitor_eru365.py" -WindowStyle Hidden
```

## 🛑 Como Parar

### Linux/macOS

```bash
kill $(pgrep -f monitor_eru365.py)
```

### Windows - PowerShell

```powershell
Stop-Process -Name python -Force
```

## ⚙️ Configuração Avançada

Você pode customizar a execução editando o arquivo `.env`:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `TELEGRAM_TOKEN` | (vazio) | Token do seu bot Telegram |
| `TELEGRAM_CHAT_ID` | (vazio) | ID do seu chat Telegram |
| `DISCIPLINA_ALVO` | `ERU 365` | Código da disciplina a monitorar |
| `CHECK_INTERVAL_MINUTES` | `30` | Intervalo entre verificações (em minutos) |
| `LOG_FILE` | (vazio) | Arquivo para salvar logs (deixe vazio para desabilitar) |

## 📊 Exemplo de Saída

```
============================================================
  Monitor de Vagas — ERU 365
  UFV 2026/1 — Departamento ERU
  Verificação a cada 30 minutos
  Telegram: Configurado ✅
============================================================

2026-03-03 14:30:15 | INFO | Verificando vagas para ERU 365...
2026-03-03 14:30:17 | INFO | 🟢 VAGAS DISPONÍVEIS!

============================================================
🚨🚨🚨  VAGAS ABERTAS!  🚨🚨🚨
============================================================
📚 Monitor ERU 365 — 03/03/2026 14:30

🟢 ERU 365 - Relações Internacionais
   Tipo: Teórica | Turma: 01
   Horário: 13:30 - 15:20
   Vagas Total: 40 | Vagas Livres: 5

============================================================
```

## 🐛 Melhorias Implementadas

✅ **Segurança**: Variáveis sensíveis armazenadas em `.env` (não versionado)
✅ **Robustez**: Retry automático com backoff exponencial para falhas de rede
✅ **Parsing Melhorado**: Uso de BeautifulSoup em vez de regex frágil
✅ **Logging**: Suporte a logs em arquivo e console
✅ **State Management**: Classe dedicada para rastrear estado de vagas
✅ **Error Handling**: Tratamento abrangente de erros
✅ **Configuração Flexível**: Suporte a arquivo `.env`
✅ **Type Hints**: Hints de tipo para melhor qualidade de código
✅ **Tratamento de Interrupção**: Graceful shutdown com Ctrl+C

## 📝 Estrutura do Projeto

```
.
├── monitor_eru365.py       # Script principal
├── requirements.txt         # Dependências Python
├── .env.example            # Exemplo de configuração
├── .env                    # Configuração (não versionado)
├── .gitignore             # Arquivos ignorados pelo git
├── README.md              # Este arquivo
└── monitor.log            # Logs (gerado durante execução)
```

## 🔧 Troubleshooting

### "ModuleNotFoundError: No module named 'bs4'"

Execute: `pip install -r requirements.txt`

### Telegram não está recebendo mensagens

1. Verifique se `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID` estão corretos no `.env`
2. Teste a conexão acessando: `https://api.telegram.org/bot<SEU_TOKEN>/getMe`
3. Certifique-se que o bot recebeu sua primeira mensagem

### Script para a verificação de repente

Verifique o arquivo de log (`monitor.log` se configurado) para erros. A DTI/UFV pode ter mudado a estrutura da página.

## 📄 Licença

Este projeto é fornecido como-é para fins educacionais e de uso pessoal.

## 🤝 Contribuições

Sinta-se à vontade para sugerir melhorias ou reportar bugs!
