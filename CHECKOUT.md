# Nebula Checkout

Esta é uma área de pagamento própria e independente. A página de referência em `/` não processa pagamentos; ela apenas transfere `playerId`, `productId` e o método PIX para `/checkout` por `sessionStorage` da mesma origem.

## Executar localmente

```bash
python3 checkout_server.py
```

Rotas locais:

- `GET /checkout` — checkout da Nebula, sem marca de terceiros.
- `POST /api/orders` — cria pedido a partir de `playerId`, `productId` e `paymentMethod`.
- `POST /api/orders/:id/pix` — emite a cobrança PIX para o pedido.
- `GET /api/orders/:id` — consulta estado do pedido com `X-Checkout-Token`.
- `POST /api/webhooks/turbofy` — recebe eventos do gateway.
- `GET /api/bot/fulfillment/next` — contratos de pedidos prontos para o bot.
- `POST /api/bot/orders/:id/status` — o bot informa `processing`, `fulfilled` ou `failed`.

## Produção e secrets

Copie `checkout_app/.env.example` para um arquivo `checkout_app/.env` fora do Git e exporte as variáveis no processo do servidor. O checkout usa apenas variáveis de ambiente; não há segredo em HTML, CSS ou JavaScript.

Em produção defina `APP_ENV=production`, `CHECKOUT_APP_SECRET`, `BOT_API_TOKEN`, `TURBOFY_CLIENT_ID`, `TURBOFY_CLIENT_SECRET`, `TURBOFY_WEBHOOK_SECRET` e `TURBOFY_WEBHOOK_URL`. A URL de webhook precisa ser HTTPS pública e sob seu controle.

O servidor local incluído é para desenvolvimento. Use um servidor HTTPS reverso e armazenamento protegido em produção.

## TurbofyPay

O backend usa `POST https://api.turbofypay.com/sellers/pix` com `x-client-id`, `x-client-secret` e a chave estável `x-idempotency-key` do pedido. O valor e os bônus vêm de `checkout_app/catalog.py`; o navegador não envia preço confiável.

O endpoint de webhook espera o header `turbofy-signature` e verifica o corpo bruto com o `TURBOFY_WEBHOOK_SECRET`. Antes de ativar produção, confirme no painel da TurbofyPay o formato de assinatura configurado para o seu webhook e rode uma cobrança de teste/sandbox.

## Estados

`payment_status`: `PENDING`, `PAID`, `EXPIRED` ou `FAILED`.

`fulfillment_status`: `PENDING`, `FULFILLMENT_PENDING`, `PROCESSING`, `FULFILLED` ou `FAILED`.

Quando o webhook validado `charge.paid` chega, o pedido vira `PAID` no pagamento e `FULFILLMENT_PENDING` no fulfillment. A tabela `fulfillment_events` tem restrição única por `order_id`, logo vários webhooks não geram mais de um evento.

## Contrato do bot

O bot autentica com:

```http
Authorization: Bearer $BOT_API_TOKEN
```

e consulta:

```http
GET /api/bot/fulfillment/next
```

Resposta:

```json
{
  "events": [{
    "event": "order.ready_for_fulfillment",
    "orderId": "ord_xxx",
    "playerId": "123456789",
    "productId": "diamonds_520",
    "baseDiamonds": 520,
    "bonusDiamonds": 104,
    "totalDiamonds": 624,
    "paymentStatus": "PAID"
  }]
}
```

Depois, o bot informa o andamento sem enviar dados pessoais:

```http
POST /api/bot/orders/ord_xxx/status
Authorization: Bearer $BOT_API_TOKEN
Content-Type: application/json

{"status":"processing"}
```

Os valores aceitos são `processing`, `fulfilled` e `failed`. O pedido só pode ser marcado como fulfillment depois de confirmado `PAID`; este projeto não implementa entrega no jogo.

## Testes

```bash
python3 -m unittest checkout_app.tests.test_checkout_service -v
python3 -m py_compile checkout_server.py checkout_app/*.py
node --check js/checkout.js
```
