/* Ponte mínima entre a página visual de referência e o checkout independente. */
(function () {
  'use strict';

  const storageKey = 'referencePurchaseStateV2';
  const orderKey = 'nebulaCheckoutOrder';
  const stateApi = window.ReferenceState;
  const formatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
  let catalog = new Map();
  let state = restore();
  let busy = false;

  function restore() {
    try { return JSON.parse(sessionStorage.getItem(storageKey)) || {}; } catch (_) { return {}; }
  }
  function persist() { sessionStorage.setItem(storageKey, JSON.stringify(state)); }
  function product() { return catalog.get(state.selectedProductId); }
  function safeId() { return String(state.playerId || '').replace(/\D/g, ''); }
  function idempotencyKey(prefix) {
    const random = crypto && crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
    return `${prefix}-${random}`;
  }

  const chip = document.createElement('div');
  chip.className = 'reference-player-chip';
  chip.innerHTML = '<img src="/img/006.ico" alt="Avatar local"><span></span>';
  document.body.append(chip);
  const chipText = chip.querySelector('span');

  const modal = document.createElement('div');
  modal.className = 'reference-promo-modal';
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');
  modal.setAttribute('aria-label', 'Promoção');
  modal.innerHTML = '<div class="reference-promo-dialog"><button class="reference-promo-close" type="button" aria-label="Fechar promoção">×</button><img src="/img/evento_bonus_tentativas.png" alt="Bônus nas tentativas"></div>';
  document.body.append(modal);

  const buyBar = document.createElement('section');
  buyBar.className = 'reference-buy-bar';
  buyBar.innerHTML = '<div class="reference-buy-summary"><strong></strong><span></span></div><button type="button" disabled>Comprar</button><p class="reference-buy-error" hidden role="alert"></p>';
  document.body.append(buyBar);
  const buyTitle = buyBar.querySelector('strong');
  const buyPrice = buyBar.querySelector('span');
  const buyButton = buyBar.querySelector('button');
  const buyError = buyBar.querySelector('p');

  function renderHeader() {
    const logged = stateApi.playerIdValid(safeId());
    chip.classList.toggle('is-visible', logged);
    chipText.textContent = logged ? safeId() : '';
  }
  function showModal() {
    if (!state.promoOpen) return;
    modal.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  }
  function closeModal() {
    if (!modal.classList.contains('is-open')) return;
    state = stateApi.dismissPromo(state);
    persist();
    modal.classList.remove('is-open');
    document.body.style.overflow = '';
  }
  function renderBuyBar() {
    const chosen = product();
    buyBar.classList.toggle('is-visible', Boolean(chosen));
    if (!chosen) return;
    buyTitle.textContent = `💎 ${new Intl.NumberFormat('pt-BR').format(chosen.baseDiamonds)}`;
    buyPrice.textContent = formatter.format(chosen.amountCents / 100);
    buyButton.disabled = busy || !stateApi.canPurchase(state);
    buyButton.textContent = busy ? 'Preparando…' : 'Comprar';
  }
  function render() { renderHeader(); renderBuyBar(); showModal(); }

  async function buy() {
    if (!stateApi.canPurchase(state) || busy) return;
    busy = true;
    buyError.hidden = true;
    renderBuyBar();
    try {
      const response = await fetch('/api/orders', {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'Idempotency-Key': idempotencyKey('order') },
        body: JSON.stringify({ playerId: safeId(), productId: state.selectedProductId, paymentMethod: 'PIX' })
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload?.error?.message || 'Não foi possível iniciar o pedido.');
      sessionStorage.setItem(orderKey, JSON.stringify({ id: payload.order.id, checkoutToken: payload.checkoutToken }));
      location.assign('/checkout');
    } catch (error) {
      buyError.textContent = error.message || 'Não foi possível iniciar o pedido.';
      buyError.hidden = false;
      busy = false;
      renderBuyBar();
    }
  }

  modal.querySelector('button').addEventListener('click', closeModal);
  modal.addEventListener('click', (event) => { if (event.target === modal) closeModal(); });
  addEventListener('keydown', (event) => { if (event.key === 'Escape') closeModal(); });
  buyButton.addEventListener('click', buy);

  addEventListener('message', (event) => {
    if (event.origin !== location.origin || !event.data || event.data.type !== 'reference-state-change') return;
    if (event.data.kind === 'playerId' && stateApi.playerIdValid(event.data.value)) {
      state = stateApi.transitionPlayer(state, event.data.value);
    } else if (event.data.kind === 'selectedProductId' && catalog.has(event.data.value)) {
      state.selectedProductId = event.data.value;
    } else if (event.data.kind === 'paymentMethod' && event.data.value === 'PIX') {
      state.paymentMethod = 'PIX';
    } else {
      return;
    }
    persist();
    render();
  });

  fetch('/api/catalog', { credentials: 'same-origin' })
    .then((response) => response.ok ? response.json() : Promise.reject(new Error('catalog')))
    .then((payload) => {
      catalog = new Map((payload.products || []).map((entry) => [entry.id, entry]));
      if (state.selectedProductId && !catalog.has(state.selectedProductId)) {
        delete state.selectedProductId;
        persist();
      }
      render();
    })
    .catch(() => render());
}());
