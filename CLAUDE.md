# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

MariaBicoBot é um bot de Telegram que faz curadoria automática de produtos da Shopee Afiliados. O bot busca produtos, filtra por comissão/desconto/preço, ranqueia e envia os melhores para um grupo alvo com links rastreáveis.

## Development Commands

### Local Development

```bash
# Instalar dependências
python -m pip install -r requirements.txt

# Executar o bot localmente
python -m src.main
```

### Docker Development

```bash
# Build da imagem
docker build -t gabrielramos/mariabicobot:latest .

# Executar container
docker run -d \
  --name mariabicobot \
  --env-file .env \
  -v mariabicobot_data:/data \
  gabrielramos/mariabicobot:latest
```

### Testes

```bash
# Testar bot Telegram (requer sessão Telethon válida)
python scripts/test_telegram.py
```

### Deploy/Production

```bash
# Via docker-compose
docker-compose up -d

# Ver logs
docker logs -f mariabicobot --tail 100

# Backup do banco
docker cp mariabicobot:/data/mariabico.db ./backup_$(date +%Y%m%d).db
```

## Architecture

### Entry Point & Initialization

**`src/main.py`** - Entry point do bot. Fluxo de inicialização:
1. Carrega settings via `get_settings()` (singleton em `src/config.py`)
2. Inicializa SQLite database em `init_db()`
3. Cria `ShopeeClient` para API GraphQL
4. Cria `Curator` com dependências (ShopeeClient, Database, parâmetros de curadoria)
5. Configura `Application` do python-telegram-bot
6. Registra handlers e inicia scheduler APScheduler
7. Inicia polling do Telegram

### Configuration

**`src/config.py`** - Configurações via variáveis de ambiente (`.env`):
- `TELEGRAM_BOT_TOKEN` - Token do bot (formato: `{bot_id}:{secret}`)
- `ADMIN_TELEGRAM_USER_ID` - ID do admin autorizado (int)
- `TARGET_GROUP_ID` - ID do grupo alvo (negativo, ex: `-1001234567890`)
- `SHOPEE_APP_ID` / `SHOPEE_SECRET` - Credenciais Shopee Affiliate API
- `SCHEDULE_CRON` - Cron para curadoria automática (default: `0 */12 * * *`)
- `TZ` / `LOG_LEVEL` / `DB_PATH` - Configurações gerais

### Core Components

#### `src/core/curator.py` - Curator
Orquestra o fluxo de curadoria:
1. `fetch_products()` - Busca produtos via ShopeeClient (paginado)
2. `filter_products()` - Aplica filtros de thresholds
3. `rank_products()` (via scoring) - Ranqueia por score
4. `deduplicate_products()` - Remove produtos já enviados
5. `generate_links()` - Gera short links rastreáveis
6. Salva produtos vistos no banco

O método `_normalize_offer()` converte campos da API `productOfferV2` para o formato interno. Importante: campos como `commissionRate` e `priceMin` vêm como strings e precisam ser convertidos para float.

#### `src/core/scoring.py` - Filtros e Scoring
- `FilterThresholds` - Define limites mínimos (comissão, desconto, preço, vendas, avaliação)
- `ScoreWeights` - Pesos para cálculo de score
- `passes_filters()` - Verifica se produto atende thresholds
- `calculate_score()` - Calcula score ponderado
- `rank_products()` - Ordena por score decrescente

#### `src/core/deduplicator.py` - Deduplicator
Marca produtos já enviados e filtra duplicatas por período (default 7 dias). Usa tabela `sent_messages`.

#### `src/core/link_gen.py` - LinkGenerator
Gera short links rastreáveis via mutation `generateShortLink`. Usa cache no banco para evitar re-geração.

### Shopee API Integration

**`src/shopee/client.py`** - ShopeeClient
Cliente HTTP assíncrono para Shopee Affiliate GraphQL API:
- Endpoint: `https://open-api.affiliate.shopee.com.br/graphql`
- Autenticação SHA256: `Credential={AppId}, Timestamp={ts}, Signature={SHA256(AppId+Timestamp+Payload+Secret)}`
- Retry automático para erros 10020 (auth)
- Rate limit: 2000 req/hora

**`src/shopee/queries.py`** - Queries GraphQL
- `PRODUCT_OFFER_V2_QUERY` - Query principal para buscar produtos
- `get_short_link_query()` - Mutation para gerar short link
- Importante: Usa `productOfferV2` (não `shopeeOfferV2`)

**`src/shopee/auth.py`** - Autenticação
Calcula signature SHA256 conforme docs da Shopee. Payload deve ser JSON minificado com chaves ordenadas.

### Telegram Bot

**`src/bot/handlers.py`** - Handlers
- `menu_command` / `menu_callback` - Menu principal
- `curate_now_callback` - Executa curadoria manual
- `status_callback` - Mostra estatísticas
- `convert_link_start/message` - Conversão de links (ConversationHandler)
- `help_callback` - Mensagem de ajuda

**`src/bot/keyboards.py`** - CallbackData
Enum com callbacks dos botões inline: MENU, STATUS, CURATE_NOW, CONVERT_LINK, HELP

**`src/bot/formatters.py`** - Formatação de Mensagens
`format_consolidated_message()` - Formata lista de produtos para HTML

**`src/bot/validators.py`** - Validação
`is_valid_shopee_url()` - Valida URLs Shopee (regex)

### Database

**`src/database/`** - SQLite
- `schema.sql` - Schema das tabelas
- `models.py` - Database class com CRUD
- Tabelas: `products`, `sent_messages`, `runs`

### Scheduler

Usa `APScheduler` com `CronTrigger`. Job `scheduled_curation()` em `src/main.py:42` executa curadoria e envia mensagem consolidada para o grupo alvo.

## Important Implementation Details

### Campo CommissionRate
Na API `productOfferV2`, `commissionRate` vem como string (ex: `"0.11"` = 11%). Sempre converter para float antes de cálculos.

### Deduplicação
Produtos são marcados como enviados após curadoria bem-sucedida. O período de deduplicação (`dedup_days`) é configurável no Curator.

### SubIds para Tracking
Short links são gerados com subIds padronizados: `campaign_type`, `group_hash`, `keyword`, `item_id`.

### Error Handling Shopee API
- Erro 10020: Erro de autenticação - retry automático
- Erro 10030: Rate limit excedido - aguardar próxima janela
- Erro "Unknown type": Verificar se query/mutation está usando tipos corretos

### Allowlist
Apenas o `ADMIN_TELEGRAM_USER_ID` configurado pode interagir com o bot (verificado em handlers).

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required variables:
- `TELEGRAM_BOT_TOKEN` - Token do @BotFather
- `ADMIN_TELEGRAM_USER_ID` - Seu Telegram user ID
- `TARGET_GROUP_ID` - ID do grupo alvo (deve ser negativo)
- `SHOPEE_APP_ID` - App ID da plataforma Shopee Afiliados
- `SHOPEE_SECRET` - Secret key da plataforma Shopee Afiliados

## Troubleshooting

### Bot não responde
1. Verifique logs: `docker logs mariabicobot`
2. Confirme token válido via @BotFather
3. Verifique se admin ID está correto

### Erro 10020 (Invalid Signature)
1. Confirme `SHOPEE_APP_ID` e `SHOPEE_SECRET`
2. Verifique se o timestamp está dentro da janela de 10 minutos
3. Payload deve ser JSON minificado com chaves ordenadas

### Produtos duplicados
Aumente `dedup_days` no Curator ou limpe tabela `sent_messages`.

### Rate Limit (10030)
A API limita a 2000 requisições por hora. Aguarde a próxima janela.
