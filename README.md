# MariaBicoBot 🤖

Bot de Telegram para curadoria automática de produtos Shopee Afiliados com geração de links
rastreáveis.

## 📋 Funcionalidades

- **Curadoria Automática**: Busca e ranqueia produtos da Shopee automaticamente a cada 12h
- **Links Rastreáveis**: Gera short links com subIds padronizados para rastreamento
- **Conversão Manual**: Converta qualquer link Shopee em link rastreável
- **Deduplicação**: Não reenvia produtos já divulgados nos últimos 7 dias
- **Score Inteligente**: Ranqueia produtos baseado em comissão, desconto e preço

## 🚀 Quick Start

### 1. Clone o repositório

```bash
git clone https://github.com/gabrielramos/mariabico-bot.git
cd mariabico-bot
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:

```bash
# Telegram (obter via @BotFather)
TELEGRAM_BOT_TOKEN=seu_token_aqui
ADMIN_TELEGRAM_USER_ID=seu_user_id
TARGET_GROUP_ID=-1001234567890

# Shopee Affiliate API
SHOPEE_APP_ID=seu_app_id
SHOPEE_SECRET=sua_secret_key
```

### 3. Execute localmente (opcional)

```bash
python -m pip install -r requirements.txt
python -m src.main
```

### 4. Deploy via Docker

```bash
# Build
docker build -t gabrielramos/mariabicobot:latest .

# Run
docker run -d \
  --name mariabicobot \
  --env-file .env \
  -v mariabicobot_data:/data \
  gabrielramos/mariabicobot:latest
```

### 5. Deploy via Portainer

1. Faça upload da stack via `docker-compose.yml`
2. Adicione as variáveis de ambiente
3. Deploy

## 📖 Uso

### Menu Principal

```text
/start ou /menu - Abre o menu interativo
```

**Opções disponíveis:**

| Botão              | Descrição                        |
| ------------------ | -------------------------------- |
| 🤖 Curadoria Agora | Executa curadoria imediata       |
| 🔗 Converter Link  | Converte link Shopee manualmente |
| 📊 Status          | Mostra estatísticas do sistema   |
| ⚙️ Ajuda           | Exibe mensagem de ajuda          |

### Exemplo de Fluxo

1. **Curadoria Automática**

   - Bot executa automaticamente a cada 12h
   - Busca produtos, filtra, ranqueia e envia Top 10 no grupo
   - Produtos são marcados para evitar duplicatas

2. **Conversão Manual**
   - Clique em "Converter Link"
   - Envie qualquer link Shopee
   - Receba o short link rastreável instantaneamente

## 🏗️ Arquitetura

```text
mariabico-bot/
├── src/
│   ├── main.py              # Entry point
│   ├── config.py            # Configurações
│   ├── database/            # SQLite
│   ├── shopee/              # Cliente API
│   ├── bot/                 # Handlers, formatters
│   ├── core/                # Curadoria, scoring
│   └── utils/               # Logger, validators
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## ⚙️ Configuração

### Thresholds de Curadoria

Configure em `src/core/scoring.py` ou via banco (fase 2):

```python
FilterThresholds(
    commission_rate_min=0.08,    # 8% mínimo
    commission_min_brl=8.00,      # R$ 8 mínimo
    discount_min_pct=15,          # 15% desconto mínimo
    price_max_brl=250,            # Preço máximo (opcional)
    sales_min=50,                 # 50 vendas mínimo
    rating_min=4.7,               # 4.7 estrelas mínimo
)
```

### Pesos de Score

```python
ScoreWeights(
    commission=1.0,   # Peso da comissão
    discount=0.5,     # Peso do desconto
    price=0.02,       # Penalidade por preço (negativo)
)
```

### Scheduler

Ajuste no `docker-compose.yml`:

```yaml
SCHEDULE_CRON=0 */12 * * * # A cada 12h
```

## 📊 Métricas

O bot coleta as seguintes métricas:

- Total de produtos buscados
- Taxa de aprovação (filtros)
- Produtos enviados ao grupo
- Taxa de sucesso da API
- Uso de rate limit

Acesse via **📊 Status** no menu.

## 🔧 Manutenção

### Logs

```bash
docker logs -f mariabicobot --tail 100
```

### Backup do Banco

```bash
docker cp mariabicobot:/data/mariabico.db ./backup_$(date +%Y%m%d).db
```

### Restore

```bash
docker cp backup_20260113.db mariabicobot:/data/mariabico.db
docker restart mariabicobot
```

## 🐛 Troubleshooting

### Bot não responde

1. Verifique logs: `docker logs mariabicobot`
2. Confirme variáveis de ambiente
3. Valide token do Telegram

### Erro na API Shopee

1. Verifique credenciais (APP_ID e SECRET)
2. Confirme limite de rate (2000 req/h)
3. Consulte logs para detalhes

### Produtos duplicados

Aumente `dedup_days` em `src/core/curator.py` ou limpe a tabela `sent_messages`.

## 🔐 Segurança

- **Allowlist**: Apenas admin configurado pode usar
- **Secrets**: Use variáveis de ambiente, nunca hardcode
- **Input Sanitization**: URLs são validadas antes de processamento
- **Logs**: Sem expor credenciais

## 📈 Roadmap

### Fase 1 (MVP) ✅

- [x] Curadoria automática
- [x] Geração de links rastreáveis
- [x] Conversão manual
- [x] Menu interativo
- [x] Status dashboard

### Fase 2 (Configuração Dinâmica)

- [ ] Configuração via comandos `/config`
- [ ] Integração com `conversionReport`
- [ ] Webhook mode (Traefik)
- [ ] Multi-grupos

### Fase 3 (Analytics)

- [ ] Feed público JSON/HTML
- [ ] Relatórios automáticos
- [ ] Painel web administrativo

## 📝 Licença

MIT License - uso pessoal

## 👤 Autor

Gabriel Ramos

---

**Versão**: 1.0.0 **Status**: MVP
