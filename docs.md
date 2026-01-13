# Shopee Affiliate API - Documentação

## Visão Geral

- **Endpoint**: `https://open-api.affiliate.shopee.com.br/graphql`
- **Método**: `POST`
- **Content-Type**: `application/json`
- **Diferença máxima de timestamp**: 10 minutos
- **Base URL**: `https://open-api.affiliate.shopee.com.br`

### Funcionalidades Disponíveis

- **Lista de ofertas** (offers)
  - `shopeeOfferV2` - Ofertas da Shopee
  - `shopOfferV2` - Ofertas de lojas
  - `productOfferV2` - Ofertas de produtos
- **Links curtos** (short links) - `generateShortLink`
- **Relatórios** (reports)
  - `conversionReport` - Relatório de conversão
  - `validatedReport` - Relatório validado

### Sobre GraphQL

A API Shopee Affiliate utiliza a especificação GraphQL para processar requisições. GraphQL é baseado
no protocolo HTTP, facilitando a integração com diversas bibliotecas HTTP como cURL e Requests.

- [Clientes GraphQL disponíveis](https://graphql.org/code/#graphql-clients)
- [Documentação oficial GraphQL](https://graphql.org/)

### Rate Limit

O sistema limita o número de chamadas da API dentro de um período especificado.

| Limite    | Descrição                             |
| :-------- | :------------------------------------ |
| 2000/hora | Número máximo de requisições por hora |

Se o limite for excedido, o sistema recusará processar a requisição. O cliente precisa aguardar a
próxima janela de tempo para reenviar a requisição.

---

## Estrutura da Requisição

```json
{
  "query": "...",
  "operationName": "...",
  "variables": {
    "myVariable": "someValue"
  }
}
```

> **Nota**: `operationName` e `variables` são opcionais. `operationName` é obrigatório apenas quando
> há múltiplas operações na query.

---

## Estrutura da Resposta

**Status HTTP**: 200 (se a requisição for recebida)

```json
{
  "data": { ... },
  "errors": [ ... ]
}
```

> Sem erros, o campo `errors` não será retornado.

### Estrutura de Erro

| Campo                | Tipo     | Descrição                          |
| :------------------- | :------- | :--------------------------------- |
| `message`            | `String` | Visão geral do erro                |
| `path`               | `String` | Localização da requisição com erro |
| `extensions.code`    | `Int`    | Código do erro                     |
| `extensions.message` | `String` | Descrição do erro                  |

---

## Códigos de Erro

| Código | Significado          | Descrição                                          |
| :----- | :------------------- | :------------------------------------------------- |
| 10000  | Erro de sistema      | Erro do sistema                                    |
| 10010  | Erro de parsing      | Sintaxe incorreta, tipo incorreto, API inexistente |
| 10020  | Erro de autenticação | Assinatura incorreta ou expirada                   |
| 10030  | Limite de taxa       | Número de requisições excede o limite              |
| 11000  | Erro de negócio      | Erro de processamento de negócio                   |

### Códigos de Erro Específicos

| Código | Descrição                                                                                                                                                                                                                 |
| :----- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 11000  | Business Error                                                                                                                                                                                                            |
| 11001  | Params Error : {reason}                                                                                                                                                                                                   |
| 11002  | Bind Account Error : {reason}                                                                                                                                                                                             |
| 10020  | Invalid Signature                                                                                                                                                                                                         |
| 10020  | Your App has been disabled                                                                                                                                                                                                |
| 10020  | Request Expired                                                                                                                                                                                                           |
| 10020  | Invalid Timestamp                                                                                                                                                                                                         |
| 10020  | Invalid Credential                                                                                                                                                                                                        |
| 10020  | Invalid Authorization Header                                                                                                                                                                                              |
| 10020  | Unsupported Auth Type                                                                                                                                                                                                     |
| 10030  | Rate limit exceeded                                                                                                                                                                                                       |
| 10031  | Access deny                                                                                                                                                                                                               |
| 10032  | Invalid affiliate id                                                                                                                                                                                                      |
| 10033  | Account is frozen                                                                                                                                                                                                         |
| 10034  | Affiliate id in black list                                                                                                                                                                                                |
| 10035  | You currently do not have access to the Shopee Affiliate Open API Platform. Please contact us to request access or learn more. [contact link](https://help.shopee.com.br/portal/webform/bbce78695c364ba18c9cbceb74ec9091) |

---

## Autenticação

Todas as requisições devem fornecer informações de autenticação através do Header `Authorization`.

### Formato do Header

```text
Authorization: SHA256 Credential={Appid}, Timestamp={Timestamp}, Signature={Signature}
```

### Componentes

| Componente   | Descrição                                                            |
| :----------- | :------------------------------------------------------------------- |
| `SHA256`     | Algoritmo usado para calcular a assinatura (apenas SHA256 suportado) |
| `Credential` | AppId da Open API obtido na plataforma de afiliados                  |
| `Timestamp`  | Diferença máxima de 10 minutos em relação ao horário do servidor     |
| `Signature`  | Assinatura de 256 bits (64 caracteres hexadecimais minúsculos)       |

### Cálculo da Assinatura

```text
Signature = SHA256(Credential + Timestamp + Payload + Secret)
```

#### Passos para Calcular

1.  Obter o payload da requisição (corpo da requisição)
2.  Obter o timestamp atual
3.  Construir o fator de assinatura: `AppId + Timestamp + Payload + Secret`
4.  Aplicar SHA256 no fator de assinatura
5.  Gerar o header Authorization

### Exemplo de Cálculo

**Dados:**

- AppId: `123456`
- Secret: `demo`
- Timestamp: `1577836800` (2020-01-01 00:00:00 UTC)
- Payload:

```json
{ "query": "{\nbrandOffer{\n    nodes{\n        commissionRate\n        offerName\n    }\n}\n}" }
```

**Fator de assinatura:**

```text
1234561577836800{"query":"{\nbrandOffer{\n    nodes{\n        commissionRate\n        offerName\n    }\n}\n}"}demo
```

**Resultado:**

```text
dc88d72feea70c80c52c3399751a7d34966763f51a7f056aa070a5e9df645412
```

**Header final:**

```text
Authorization: SHA256 Credential=123456, Timestamp=1577836800, Signature=dc88d72feea70c80c52c3399751a7d34966763f51a7f056aa070a5e9df645412
```

### Obter Timestamp

Para obter o timestamp atual (Unix timestamp), acesse:
[https://www.unixtimestamp.com/](https://www.unixtimestamp.com/)

---

## Timestamp e Timezone

A Shopee utiliza o horário local no formato UTC+ de cada região para armazenar os dados.
Independentemente do seu fuso horário, um timestamp representa um momento que é o mesmo em todos os
lugares.

### Formato

- **Formato**: Unix timestamp (UTC)
- **Referência**: [https://www.unixtimestamp.com/](https://www.unixtimestamp.com/)

---

## Notas Importantes (Leitura Obrigatória)

### ScrollId (Paginação)

Para consultar múltiplas páginas de dados, é necessário realizar **duas ou mais queries**!

- **Primeira query**: Retorna o conteúdo da primeira página e o `scrollId`
- **Máximo por página**: 500 dados
- **scrollId**: Usado para consultar o conteúdo da segunda página e subsequentes

> **Importante**: Para obter o conteúdo da segunda página e posteriores, você **deve** consultar com
> o `scrollId`.

#### Regras do ScrollId

| Regra                  | Descrição                                                                                            |
| ---------------------- | ---------------------------------------------------------------------------------------------------- |
| Validade               | O scrollId é válido apenas por **30 segundos**                                                       |
| Uso                    | Após obter o scrollId na primeira requisição, consulte as páginas subsequentes dentro de 30 segundos |
| Intervalo sem scrollId | A query sem scrollId requer um intervalo maior que 30 segundos                                       |

### Intervalo de Consulta do Relatório de Conversão

O intervalo de tempo disponível para consulta de dados é dos **últimos 3 meses**.

O intervalo de tempo que pode ser consultado na Open API é consistente com o intervalo de tempo do
portal do sistema de afiliados. Se você consultar além desse intervalo, o sistema enviará um erro.

---

## Ferramentas

### API Explorer

Ferramenta útil para fazer requisições e testar queries:
[https://open-api.affiliate.shopee.com.br/explorer](https://open-api.affiliate.shopee.com.br/explorer)

### Recursos Adicionais

| Recurso                  | Link                                                |
| :----------------------- | :-------------------------------------------------- |
| GraphQL Clients          | <https://graphql.org/code/#graphql-clients>         |
| GraphQL Documentation    | <https://graphql.org/>                              |
| Unix Timestamp Generator | <https://www.unixtimestamp.com/>                    |
| API Explorer             | <https://open-api.affiliate.shopee.com.br/explorer> |

### Configuração

Recomendamos o uso de um arquivo `.env` para gerenciar suas credenciais de forma segura. O projeto
carrega automaticamente as variáveis `SHOPEE_APP_ID` e `SHOPEE_APP_SECRET` deste arquivo.

---

## Queries Disponíveis

### 1. shopeeOfferV2 - Lista de Ofertas Shopee

**Tipo de retorno**: `ShopeeOfferConnectionV2!`

#### Parâmetros (shopeeOfferV2)

| Campo      | Tipo     | Descrição                      | Exemplo     |
| ---------- | -------- | ------------------------------ | ----------- |
| `keyword`  | `String` | Buscar por nome da oferta      | `"clothes"` |
| `sortType` | `Int`    | Tipo de ordenação              | `1` ou `2`  |
| `page`     | `Int`    | Número da página               | `2`         |
| `limit`    | `Int`    | Quantidade de dados por página | `10`        |

#### Tipos de Ordenação (sortType)

| Valor | Constante                 | Descrição                                       |
| ----- | ------------------------- | ----------------------------------------------- |
| 1     | `LATEST_DESC`             | Ordenar por hora de atualização mais recente    |
| 2     | `HIGHEST_COMMISSION_DESC` | Ordenar por taxa de comissão (maior para menor) |

#### Estrutura de Retorno - ShopeeOfferV2

| Campo             | Tipo     | Descrição                                 |
| ----------------- | -------- | ----------------------------------------- |
| `commissionRate`  | `String` | Taxa de comissão (ex: `"0.0123"` = 1.23%) |
| `imageUrl`        | `String` | URL da imagem                             |
| `offerLink`       | `String` | Link da oferta                            |
| `originalLink`    | `String` | Link original                             |
| `offerName`       | `String` | Nome da oferta                            |
| `offerType`       | `Int`    | Tipo de oferta                            |
| `categoryId`      | `Int64`  | CategoryId (quando offerType = 2)         |
| `collectionId`    | `Int64`  | CollectionId (quando offerType = 1)       |
| `periodStartTime` | `Int`    | Data de início da oferta                  |
| `periodEndTime`   | `Int`    | Data de fim da oferta                     |

#### Tipos de Oferta (offerType)

| Valor | Constante                  |
| ----- | -------------------------- |
| 1     | `CAMPAIGN_TYPE_COLLECTION` |
| 2     | `CAMPAIGN_TYPE_CATEGORY`   |

---

### 2. shopOfferV2 - Lista de Ofertas de Lojas

**Tipo de retorno**: `ShopOfferConnectionV2`

#### Parâmetros (shopOfferV2)

| Campo                 | Tipo     | Descrição                      | Exemplo         |
| --------------------- | -------- | ------------------------------ | --------------- |
| `shopId`              | `Int64`  | Buscar por ID da loja          | `84499012`      |
| `keyword`             | `String` | Buscar por nome da loja        | `"demo"`        |
| `shopType`            | `[Int]`  | Filtrar por tipo de loja       | `[1, 4]`        |
| `isKeySeller`         | `Bool`   | Filtrar ofertas de key sellers | `true`          |
| `sortType`            | `Int`    | Tipo de ordenação              | `1`, `2` ou `3` |
| `sellerCommCoveRatio` | `String` | Razão de produtos com comissão | `"0.123"`       |
| `page`                | `Int`    | Número da página               | `2`             |
| `limit`               | `Int`    | Quantidade de dados por página | `10`            |

#### Tipos de Loja (shopType)

| Valor | Constante             | Descrição                        |
| ----- | --------------------- | -------------------------------- |
| 1     | `OFFICIAL_SHOP`       | Lojas oficiais / Shopee Mall     |
| 2     | `PREFERRED_SHOP`      | Lojas preferenciais (Star)       |
| 4     | `PREFERRED_PLUS_SHOP` | Lojas preferenciais plus (Star+) |

#### Tipos de Ordenação (sortType)

| Valor | Constante                                     | Descrição                               |
| ----- | --------------------------------------------- | --------------------------------------- |
| 1     | `SHOP_LIST_SORT_TYPE_LATEST_DESC`             | Ordenar por última atualização          |
| 2     | `SHOP_LIST_SORT_TYPE_HIGHEST_COMMISSION_DESC` | Ordenar por comissão (maior para menor) |
| 3     | `SHOP_LIST_SORT_TYPE_POPULAR_SHOP_DESC`       | Ordenar por popularidade                |

#### Estrutura de Retorno - ShopOfferV2

| Campo                 | Tipo         | Descrição                      | Exemplo                              |
| --------------------- | ------------ | ------------------------------ | ------------------------------------ |
| `commissionRate`      | `String`     | Taxa de comissão               | `"0.25"`                             |
| `imageUrl`            | `String`     | URL da imagem                  | `https://cf.shopee.co.id/file/...`   |
| `offerLink`           | `String`     | Link da oferta                 | `https://shope.ee/xxxxxxxx`          |
| `originalLink`        | `String`     | Link original                  | `https://shopee.co.id/shop/19162748` |
| `shopId`              | `Int64`      | ID da loja                     | `84499012`                           |
| `shopName`            | `String`     | Nome da loja                   | `"Ikea"`                             |
| `ratingStar`          | `String`     | Avaliação da loja              | `"3.7"`                              |
| `shopType`            | `[Int]`      | Tipo da loja                   | `[]`, `[1, 4]`                       |
| `remainingBudget`     | `Int`        | Orçamento restante             | `0-3`                                |
| `periodStartTime`     | `Int`        | Data de início da oferta       | `1687712400`                         |
| `periodEndTime`       | `Int`        | Data de fim da oferta          | `1690822799`                         |
| `sellerCommCoveRatio` | `String`     | Razão de produtos com comissão | `"0.123"`                            |
| `bannerInfo`          | `BannerInfo` | Informações do banner          |                                      |

#### Níveis de Orçamento Restante (remainingBudget)

| Valor | Descrição                                   |
| ----- | ------------------------------------------- |
| 0     | Ilimitado (oferta sem limite de orçamento)  |
| 3     | Normal (acima de 50% do orçamento restante) |
| 2     | Baixo (abaixo de 50% - risco médio)         |
| 1     | Muito baixo (abaixo de 30% - alto risco)    |

---

### Estruturas Compartilhadas

#### PageInfo

| Campo         | Tipo   | Descrição                      |
| ------------- | ------ | ------------------------------ |
| `page`        | `Int`  | Número da página atual         |
| `limit`       | `Int`  | Quantidade de dados por página |
| `hasNextPage` | `Bool` | Se existe próxima página       |

#### BannerInfo

| Campo     | Tipo         | Descrição             |
| --------- | ------------ | --------------------- |
| `count`   | `Int`        | Quantidade de banners |
| `banners` | `[Banner!]!` | Lista de banners      |

#### Banner

| Campo         | Tipo     | Descrição                  | Exemplo                            |
| ------------- | -------- | -------------------------- | ---------------------------------- |
| `fileName`    | `String` | Nome do arquivo            | `"454.jpg"`                        |
| `imageUrl`    | `String` | URL da imagem              | `https://cf.shopee.co.id/file/...` |
| `imageSize`   | `Int`    | Tamanho da imagem em bytes | `1747107`                          |
| `imageWidth`  | `Int`    | Largura da imagem          | `5998`                             |
| `imageHeight` | `Int`    | Altura da imagem           | `3000`                             |

---

### 3. conversionReport - Relatório de Conversão

**Tipo de retorno**: `ConversionReportConnection`

#### Parâmetros (conversionReport)

| Campo               | Tipo     | Descrição                                      | Exemplo             |
| ------------------- | -------- | ---------------------------------------------- | ------------------- |
| `purchaseTimeStart` | `Int`    | Timestamp de início da compra                  | `1600621200`        |
| `purchaseTimeEnd`   | `Int`    | Timestamp de fim da compra                     | `1601225999`        |
| `scrollId`          | `String` | ID para paginação (opcional na primeira query) | `"some characters"` |
| `page`              | `Int`    | Número da página                               | `1`                 |
| `limit`             | `Int`    | Quantidade de dados por página (máx: 500)      | `10`                |

> **Importante**: Ao usar `scrollId`, aspas duplas no valor devem ser escapadas conforme o padrão
> GraphQL.

#### Intervalo de Consulta

- **Máximo**: Últimos 3 meses
- **Máximo por página**: 500 dados
- **scrollId**: Válido por 30 segundos

---

### 4. productOfferV2 - Lista de Ofertas de Produtos

**Tipo de retorno**: `ProductOfferConnectionV2`

#### Parâmetros (productOfferV2)

| Campo          | Tipo     | Descrição                                          | Exemplo       |
| -------------- | -------- | -------------------------------------------------- | ------------- |
| `shopId`       | `Int64`  | Buscar por ID da loja                              | `84499012`    |
| `itemId`       | `Int64`  | Buscar por ID do produto                           | `17979995178` |
| `productCatId` | `Int32`  | Filtrar por categoria de produto (nível 1, 2 ou 3) | `10001`       |
| `listType`     | `Int`    | Tipo de lista de produtos                          | `1`           |
| `matchId`      | `Int64`  | ID correspondente para listType específico         | `10012`       |
| `keyword`      | `String` | Buscar por nome do produto                         | `"shopee"`    |
| `sortType`     | `Int`    | Tipo de ordenação                                  | `2`           |
| `page`         | `Int`    | Número da página                                   | `2`           |
| `isAMSOffer`   | `Bool`   | Filtrar ofertas com comissão de vendedor           | `true`        |
| `isKeySeller`  | `Bool`   | Filtrar ofertas de key sellers                     | `true`        |
| `limit`        | `Int`    | Quantidade de dados por página                     | `10`          |

#### Tipos de Lista (listType)

| Valor | Constante            | Descrição                 |
| ----- | -------------------- | ------------------------- |
| 0     | `ALL`                | Todos os produtos         |
| 1     | `HIGHEST_COMMISSION` | Maior comissão            |
| 2     | `TOP_PERFORMING`     | Top desempenho            |
| 3     | `LANDING_CATEGORY`   | Categoria de landing page |
| 4     | `DETAIL_CATEGORY`    | Detalhes de categoria     |
| 5     | `DETAIL_SHOP`        | Detalhes de loja          |
| 6     | `DETAIL_COLLECTION`  | Detalhes de coleção       |

#### Tipos de Ordenação (sortType - productOfferV2)

| Valor | Constante         | Descrição      |
| :---- | :---------------- | :------------- |
| 1     | `RELEVANCE_DESC`  | Relevância     |
| 2     | `ITEM_SOLD_DESC`  | Mais vendidos  |
| 3     | `PRICE_DESC`      | Maior preço    |
| 4     | `PRICE_ASC`       | Menor preço    |
| 5     | `COMMISSION_DESC` | Maior comissão |

#### Estrutura de Retorno - ProductOfferV2

| Campo                  | Tipo     | Descrição                                      | Exemplo                             |
| ---------------------- | -------- | ---------------------------------------------- | ----------------------------------- |
| `itemId`               | `Int64`  | ID do produto                                  | `47550807236`                       |
| `productName`          | `String` | Nome do produto                                | `"Jogo De Panelas Induçao..."`      |
| `commissionRate`       | `String` | Taxa máxima de comissão (ex: `"0.11"` = 11%)   | `"0.11"`                            |
| `commission`           | `String` | Valor da comissão = preço × taxa               | `"43.12"`                           |
| `price`                | `String` | Preço atual do produto                         | `"392"`                             |
| `priceMin`             | `String` | Preço mínimo do produto                        | `"392"`                             |
| `priceMax`             | `String` | Preço máximo do produto                        | `"392"`                             |
| `sales`                | `Int32`  | Quantidade de vendas                           | `401`                               |
| `productCatIds`        | `[Int]`  | IDs de categoria (níveis 1, 2, 3)              | `[100636, 100717, 101218]`          |
| `ratingStar`           | `String` | Avaliação do produto                           | `"4.9"`                             |
| `priceDiscountRate`    | `Int`    | Desconto percentual (43 = 43%)                 | `43`                                |
| `imageUrl`             | `String` | URL da imagem                                  | `https://cf.shopee.com.br/file/...` |
| `shopId`               | `Int64`  | ID da loja                                     | `1404215442`                        |
| `shopName`             | `String` | Nome da loja                                   | `"ATOZ DISTRIBUIDORA"`              |
| `shopType`             | `[Int]`  | Tipo da loja (vazio ou `[1]`, `[2]`, `[4]`)    | `[]`, `[1]`, `[2]`, `[4]`           |
| `sellerCommissionRate` | `String` | Taxa de comissão do vendedor (Commission Xtra) | `"0.08"`                            |
| `shopeeCommissionRate` | `String` | Taxa de comissão da Shopee                     | `"0.03"`                            |
| `productLink`          | `String` | Link do produto                                | `https://shopee.com.br/product/...` |
| `offerLink`            | `String` | Link da oferta (link curto)                    | `https://s.shopee.com.br/...`       |
| `periodStartTime`      | `Int`    | Data de início da oferta (timestamp)           | `1764558000`                        |
| `periodEndTime`        | `Int`    | Data de fim da oferta (timestamp)              | `32503651199`                       |

> **Nota sobre shopType**: Quando vazio `[]`, indica loja comum. `[1]` = Official Shop (Mall), `[2]`
> = Preferred Shop (Star), `[4]` = Preferred Plus Shop (Star+).

---

## Mutations Disponíveis

### 1. generateShortLink - Gerar Link Curto

**Tipo de retorno**: `ShortLinkResult!`

Esta mutation é usada para gerar links curtos de rastreamento para produtos Shopee.

#### Parâmetros (generateShortLink)

| Campo       | Tipo       | Descrição                     | Obrigatório | Exemplo                          |
| ----------- | ---------- | ----------------------------- | ----------- | -------------------------------- |
| `originUrl` | `String`   | URL original do produto       | Sim         | `https://shopee.com.br/...`      |
| `subIds`    | `[String]` | Sub IDs para tracking (até 5) | Não         | `["s1", "s2", "s3", "s4", "s5"]` |

#### Estrutura de Retorno

| Campo       | Tipo      | Descrição         |
| ----------- | --------- | ----------------- |
| `shortLink` | `String!` | Link curto gerado |

#### Exemplo de Requisição cURL

```bash
curl -X POST 'https://open-api.affiliate.shopee.com.br/graphql' \
  -H 'Authorization: SHA256 Credential=123456, Signature=x9bc0bd3ba6c41d98a591976bf95db97a58720a9e6d778845408765c3fafad69d, Timestamp=1577836800' \
  -H 'Content-Type: application/json' \
  --data-raw '{
    "query": "mutation {\n generateShortLink(input: {\n originUrl: \"https://shopee.com.br/Apple-Iphone-11-128GB-Local-Set-i.52377417.6309028319\",\n subIds: [\"s1\", \"s2\", \"s3\", \"s4\", \"s5\"]\n }) {\n shortLink\n }\n}"
  }'
```

#### Exemplo de Query GraphQL

```graphql
mutation {
  generateShortLink(
    input: {
      originUrl: "https://shopee.com.br/Apple-Iphone-11-128GB-Local-Set-i.52377417.6309028319"
      subIds: ["s1", "s2", "s3", "s4", "s5"]
    }
  ) {
    shortLink
  }
}
```

---

## Exemplos de Query

### Buscar Ofertas Shopee

```graphql
query {
  shopeeOfferV2(keyword: "clothes", sortType: 2, page: 1, limit: 10) {
    nodes {
      commissionRate
      imageUrl
      offerLink
      offerName
      offerType
    }
    pageInfo {
      page
      limit
      hasNextPage
    }
  }
}
```

### Buscar Ofertas de Lojas

```graphql
query {
  shopOfferV2(keyword: "demo", shopType: [1, 4], sortType: 2, page: 1, limit: 10) {
    nodes {
      commissionRate
      shopId
      shopName
      ratingStar
      remainingBudget
      offerLink
      bannerInfo {
        count
        banners {
          imageUrl
          imageWidth
          imageHeight
        }
      }
    }
    pageInfo {
      page
      limit
      hasNextPage
    }
  }
}
```

### Buscar Relatório de Conversão (Primeira Página)

```graphql
query {
  conversionReport(
    purchaseTimeStart: 1600621200
    purchaseTimeEnd: 1601225999
    page: 1
    limit: 500
  ) {
    nodes {
      orderId
      purchaseTime
      commissionRate
      commissionAmount
      orderStatus
    }
    pageInfo {
      page
      limit
      hasNextPage
      scrollId
    }
  }
}
```

### Buscar Relatório de Conversão (Páginas Seguintes com ScrollId)

```graphql
query {
  conversionReport(
    purchaseTimeStart: 1600621200
    purchaseTimeEnd: 1601225999
    scrollId: "scroll_id_da_primeira_query"
    page: 2
    limit: 500
  ) {
    nodes {
      orderId
      purchaseTime
      commissionRate
      commissionAmount
      orderStatus
    }
    pageInfo {
      page
      limit
      hasNextPage
      scrollId
    }
  }
}
```

> **Atenção**: O `scrollId` expira em 30 segundos. Após a primeira query, faça as consultas
> subsequentes dentro desse prazo.

### Buscar Ofertas de Produtos

```graphql
query {
  productOfferV2(keyword: "shopee", sortType: 2, page: 1, limit: 10) {
    nodes {
      itemId
      productName
      commissionRate
      priceMin
      priceMax
      sales
      ratingStar
      imageUrl
      offerLink
      shopId
      shopName
      shopType
    }
    pageInfo {
      page
      limit
      hasNextPage
    }
  }
}
```

### Buscar Ofertas de Produtos por Categoria

```graphql
query {
  productOfferV2(productCatId: 10001, listType: 1, sortType: 5, page: 1, limit: 10) {
    nodes {
      itemId
      productName
      commissionRate
      priceMin
      priceMax
      sales
      productCatIds
      offerLink
    }
    pageInfo {
      page
      limit
      hasNextPage
    }
  }
}
```

### Buscar Ofertas de Produtos por Loja

```graphql
query {
  productOfferV2(
    shopId: 84499012
    listType: 5
    matchId: 84499012
    sortType: 5
    page: 1
    limit: 10
  ) {
    nodes {
      itemId
      productName
      commissionRate
      sellerCommissionRate
      shopeeCommissionRate
      commission
      priceMin
      priceMax
      offerLink
    }
    pageInfo {
      page
      limit
      hasNextPage
    }
  }
}
```

### Gerar Link Curto

```graphql
mutation {
  generateShortLink(
    input: {
      originUrl: "https://shopee.com.br/Apple-Iphone-11-128GB-Local-Set-i.52377417.6309028319"
      subIds: ["s1", "s2", "s3", "s4", "s5"]
    }
  ) {
    shortLink
  }
}
```
