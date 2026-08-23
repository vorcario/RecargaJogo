const test = require('node:test');
const assert = require('node:assert/strict');
const state = require('../js/reference-state.js');

test('login por ID atualiza estado e abre a promoção uma vez', () => {
  const logged = state.transitionPlayer({ promoDismissed: false }, '123456789');
  assert.equal(logged.playerId, '123456789');
  assert.equal(logged.promoOpen, true);
  const closed = state.dismissPromo(logged);
  assert.equal(closed.promoOpen, false);
  assert.equal(closed.promoDismissed, true);
});

test('botão Comprar exige ID, produto e Pix', () => {
  assert.equal(state.canPurchase({ playerId: '123456789' }), false);
  assert.equal(state.canPurchase({ playerId: '123456789', selectedProductId: 'diamonds_65' }), false);
  assert.equal(state.canPurchase({ playerId: '123456789', selectedProductId: 'diamonds_65', paymentMethod: 'PIX' }), true);
});
