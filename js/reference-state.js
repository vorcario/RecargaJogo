(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ReferenceState = api;
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const playerIdValid = (value) => /^[0-9]{4,32}$/.test(String(value || '').trim());
  const canPurchase = (state) => Boolean(state && playerIdValid(state.playerId) && state.selectedProductId && state.paymentMethod === 'PIX');
  const transitionPlayer = (previous, playerId) => ({
    ...previous,
    playerId: String(playerId || '').trim(),
    promoOpen: !previous.playerId && playerIdValid(playerId) && !previous.promoDismissed,
  });
  const dismissPromo = (state) => ({ ...state, promoOpen: false, promoDismissed: true });
  return { playerIdValid, canPurchase, transitionPlayer, dismissPromo };
}));
