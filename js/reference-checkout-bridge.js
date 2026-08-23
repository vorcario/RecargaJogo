/* A referência só encaminha seleção local; cobrança acontece em /checkout. */
(function () {
  'use strict';
  const key = 'nebulaCheckoutSelection';
  const read = () => { try { return JSON.parse(sessionStorage.getItem(key) || '{}'); } catch { return {}; } };
  const save = (value) => sessionStorage.setItem(key, JSON.stringify(value));
  const slot = document.createElement('aside');
  slot.className = 'nebula-handoff';
  slot.innerHTML = '<div><strong>Nebula Checkout</strong><span>Pagamento pela nossa plataforma independente</span></div><button type="button" disabled>Continuar para checkout</button>';
  const button = slot.querySelector('button');
  const render = () => {
    const state = read();
    const ready = state.playerId && state.productId && state.paymentMethod === 'PIX';
    button.disabled = !ready;
    button.textContent = ready ? 'Continuar para checkout próprio' : 'Selecione ID, pacote e PIX';
  };
  button.addEventListener('click', () => location.assign('/checkout'));
  addEventListener('message', (event) => {
    if (event.origin !== location.origin || !event.data || event.data.type !== 'nebula-selection') return;
    const state = read(); state[event.data.kind] = event.data.value; save(state); render();
  });
  document.addEventListener('DOMContentLoaded', () => { document.body.append(slot); render(); });
  if (document.readyState !== 'loading') { document.body.append(slot); render(); }
}());
