# Checkout independente — versão local ativa

Execute a versão corrigida com:

```bash
python3 checkout_server_v2.py
```

A página de referência fica em `/`. Ela não exibe a barra antiga e não processa credenciais ou pagamentos. Depois de selecionar um ID numérico, um produto e Pix, ela envia exclusivamente estes identificadores para `POST /api/orders`:

```json
{
  "playerId": "123456789",
  "productId": "diamonds_65",
  "paymentMethod": "PIX"
}
```

O catálogo usado para API e interface é [`checkout_app/catalog_store.py`](checkout_app/catalog_store.py). Os três preços configurados são 65 por R$ 4,99, 100 por R$ 5,99 e 310 por R$ 17,00; `amountCents` do navegador é ignorado.

## Produção e PIX

Exporte no processo do servidor, nunca no browser:

```text
APP_ENV=production
CHECKOUT_APP_SECRET=...
BOT_API_TOKEN=...
TURBOFY_CLIENT_ID=...
TURBOFY_CLIENT_SECRET=...
TURBOFY_WEBHOOK_SECRET=...
TURBOFY_WEBHOOK_URL=https://sua-loja.example/api/webhooks/turbofy
```

O backend usa `POST /sellers/pix` da TurbofyPay, `x-idempotency-key` estável por pedido e retorna para o checkout somente os dados PIX da resposta do gateway (QR Code e Copia e Cola). Sem essas credenciais, criar um PIX responde com indisponibilidade e nenhuma cobrança é feita.

## Bot de fulfillment

O bot deve se autenticar com `Authorization: Bearer $BOT_API_TOKEN` e buscar:

```http
GET /api/bot/fulfillment/next
```

Cada evento possui somente o necessário para a entrega:

```json
{
  "event": "order.ready_for_fulfillment",
  "orderId": "ord_xxx",
  "playerId": "123456789",
  "productId": "diamonds_520",
  "baseDiamonds": 520,
  "bonusDiamonds": 104,
  "totalDiamonds": 624,
  "paymentStatus": "PAID"
}
```

Depois o bot sinaliza o progresso:

```http
POST /api/bot/orders/ord_xxx/status
Authorization: Bearer $BOT_API_TOKEN
Content-Type: application/json

{"status":"processing"}
```

Estados aceitos: `processing`, `fulfilled` e `failed`. O backend só cria esse evento depois de webhook validado `charge.paid`; repetição de webhook não duplica o evento devido à chave única por pedido. A entrega específica não está implementada nesta aplicação.
