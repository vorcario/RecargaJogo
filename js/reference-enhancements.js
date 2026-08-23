/* Acrescenta estados locais à página de referência, sem autenticação ou pagamentos nela. */
(function () {
  'use strict';

  const productByAmount = {
    '65': 'diamonds_65', '100': 'diamonds_100', '310': 'diamonds_310', '520': 'diamonds_520',
    '1.060': 'diamonds_1060', '2.180': 'diamonds_2180', '5.600': 'diamonds_5600', '22.400': 'diamonds_22400'
  };
  const formatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
  const send = (kind, value) => parent.postMessage({ type: 'reference-state-change', kind, value }, location.origin);

  function normalizeAmount(button) {
    return (button.dataset.amount || button.textContent || '').replace(/\s+/g, ' ').trim().split(' ')[0];
  }

  function applyCatalog(catalog) {
    const products = new Map(catalog.map((product) => [product.id, product]));
    document.querySelectorAll('.diamond-option').forEach((button) => {
      const productId = productByAmount[normalizeAmount(button)];
      const product = products.get(productId);
      if (!product || button.dataset.enhanced === 'true') return;
      button.dataset.enhanced = 'true';
      button.dataset.productId = productId;
      const diamond = button.querySelector('.diamond-shape');
      const amount = normalizeAmount(button);
      const line = document.createElement('span');
      line.className = 'diamond-topline';
      if (diamond) line.append(diamond.cloneNode(true));
      line.append(document.createTextNode(amount));
      const price = document.createElement('small');
      price.className = 'diamond-price';
      price.textContent = formatter.format(product.amountCents / 100);
      button.replaceChildren(line, price);
    });
    parent.postMessage({ type: 'reference-catalog-ready' }, location.origin);
  }

  fetch('/api/catalog', { credentials: 'same-origin' })
    .then((response) => response.ok ? response.json() : Promise.reject(new Error('catalog')))
    .then((payload) => applyCatalog(payload.products || []))
    .catch(() => {});

  document.addEventListener('click', (event) => {
    const login = event.target.closest('.category-login');
    if (login) {
      const input = document.getElementById('player-id');
      const playerId = String(input ? input.value : '').trim();
      if (/^[0-9]{4,32}$/.test(playerId)) send('playerId', playerId);
      return;
    }
    const diamond = event.target.closest('.diamond-option');
    if (diamond) {
      const productId = diamond.dataset.productId || productByAmount[normalizeAmount(diamond)];
      if (productId) send('selectedProductId', productId);
      return;
    }
    const payment = event.target.closest('.payment-card');
    if (payment && /^pix$/i.test(payment.textContent.trim())) send('paymentMethod', 'PIX');
  });
}());
