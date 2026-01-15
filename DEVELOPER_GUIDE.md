# Guia do Desenvolvedor - MariaBicoBot

Este guia fornece instruções essenciais para configurar, desenvolver e manter o bot MariaBico.

## 1. Configuração do Ambiente

O projeto utiliza **`uv`** como gerenciador de pacotes e ambientes Python, garantindo instalações
rápidas e reprodutíveis.

### Pré-requisitos

- **Python 3.12+**
- **uv**: [Instalação](https://docs.astral.sh/uv/getting-started/installation/)

```bash
# Instalar uv (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Instalação das Dependências

Na raiz do projeto, execute:

```bash
uv sync
```

Isso criará o ambiente virtual (`.venv`) e instalará todas as dependências listadas em
`pyproject.toml`.

### Ativação do Ambiente Virtual

Embora o `uv run` utilize o ambiente automaticamente, recomenda-se ativá-lo para garantir que seu
terminal e IDE (como VS Code) reconheçam as dependências instaladas.

**macOS / Linux:**

```bash
source .venv/bin/activate
```

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**

```cmd
.venv\Scripts\activate.bat
```

**Verificação:**

Para confirmar que o ambiente está ativo, execute:

```bash
which python
# Deve retornar algo como: .../mariabico-bot/.venv/bin/python
```

## 2. Configuração (.env)

O bot requer variáveis de ambiente para funcionar. Crie um arquivo `.env` na raiz do projeto com as
seguintes chaves:

```ini
# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz # Token do BotFather
ADMIN_TELEGRAM_USER_ID=123456789 # Seu ID de usuário (userinfobot)
TARGET_GROUP_ID=-1001234567890 # ID do grupo/canal para envio de ofertas

# Shopee Affiliate API
SHOPEE_APP_ID=1234567890
SHOPEE_SECRET=seu_segredo_aqui

# Geral
TZ=America/Sao_Paulo
LOG_LEVEL=INFO # DEBUG, INFO, WARNING, ERROR
DB_PATH=mariabico.db # Caminho para o banco SQLite
SCHEDULE_CRON="0 */12 * * *" # Cron para curadoria automática
```

## 3. Estrutura do Projeto

```text
mariabico-bot/
├── src/
│   ├── bot/          # Handlers, keyboards e lógica do Telegram
│   ├── core/         # Lógica de negócio (Curator, Scoring)
│   ├── shopee/       # Cliente da API Shopee (Auth, Queries)
│   ├── utils/        # Loggers e utilitários
│   ├── config.py     # Carregamento e validação de configurações
│   └── main.py       # Ponto de entrada da aplicação
├── scripts/          # Scripts auxiliares (testes manuais, updates)
├── tests/            # Testes automatizados (pytest)
└── pyproject.toml    # Definição de dependências e configuração de ferramentas
```

## 4. Fluxo de Trabalho de Desenvolvimento

### Executar o Bot Localmente

Para rodar o bot em modo de desenvolvimento:

```bash
uv run python src/main.py
```

### Executar Testes

Utilizamos `pytest` para testes automatizados.

```bash
# Rodar todos os testes
uv run pytest

# Rodar testes com cobertura
uv run pytest --cov=src
```

### Linting e Formatação

Utilizamos `ruff` para manter a qualidade do código.

```bash
# Verificar problemas de linting
uv run ruff check

# Corrigir problemas automaticamente (quando possível)
uv run ruff check --fix

# Formatar o código
uv run ruff format
```

## 5. Solução de Problemas Comuns

### Erro: `ShopeeAPIError: Invalid Signature`

- **Causa:** `SHOPEE_SECRET` incorreto ou relógio do sistema dessincronizado.
- **Solução:** Verifique o segredo no `.env` e assegure-se de que o horário do sistema está correto.

### Erro: `ValueError: TELEGRAM_BOT_TOKEN é obrigatório`

- **Causa:** Arquivo `.env` não encontrado ou variável não definida.
- **Solução:** Confirme se o arquivo `.env` está na raiz e se o nome da variável está correto.

### Testes falhando com `ModuleNotFoundError`

- **Causa:** Execução direta do python sem o ambiente virtual.
- **Solução:** Sempre use `uv run ...` para garantir que o `PYTHONPATH` e dependências estejam
  carregados corretamente.
