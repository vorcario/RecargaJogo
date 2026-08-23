/* Dentro das etapas de referência: envia somente as escolhas locais ao pai. */
(function () {
  'use strict';
  const send = (kind, value) => parent.postMessage({ type: 'nebula-selection', kind, value }, location.origin);
  const amounts = { '65': 'diamonds_65', '100': 'diamonds_100', '310': 'diamonds_310', '520': 'diamonds_520', '1.060': 'diamonds_1060', '2.180': 'diamonds_2180', '5.600': 'diamonds_5600', '22.400': 'diamonds_22400' };
  document.addEventListener('click', (event) => {
    if (event.target.closest('.category-login')) {
      const id = (document.getElementById('player-id') || {}).value || '';
      if (/^[0-9]{4,32}$/.test(id.trim())) send('playerId', id.trim());
    }
    const diamond = event.target.closest('.diamond-option');
    if (diamond) {
      const amount = diamond.textContent.trim();
      if (amounts[amount]) send('productId', amounts[amount]);
    }
    const payment = event.target.closest('.payment-card');
    if (payment && /^pix$/i.test(payment.textContent.trim())) send('paymentMethod', 'PIX');
  });
}());
