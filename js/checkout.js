(function () {
  'use strict';
  const selectionKey = 'nebulaCheckoutSelection';
  const orderKey = 'nebulaCheckoutOrder';
  const byId = (id) => document.getElementById(id);
  const read = (key) => { try { return JSON.parse(sessionStorage.getItem(key) || '{}'); } catch { return {}; } };
  const save = (key, value) => sessionStorage.setItem(key, JSON.stringify(value));
  const idempotency = (name) => {
    const current = read(orderKey); if (current[name]) return current[name];
    current[name] = crypto.randomUUID(); save(orderKey, current); return current[name];
  };
  const money = (cents) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100);
  const api = async (url, options = {}) => {
    const response = await fetch(url, options); const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.error?.message || 'Não foi possível processar seu pedido.'); return body;
  };
  const headerToken = (order) => ({ 'X-Checkout-Token': order.checkoutToken || '', 'Content-Type': 'application/json' });
  const rows = (order) => `
    <div class="summary-row total"><span>Total</span><strong>💎 ${order.product.totalDiamonds.toLocaleString('pt-BR')}</strong></div>
    <div class="summary-row"><span>Preço original</span><strong>💎 ${order.product.baseDiamonds.toLocaleString('pt-BR')}</strong></div>
    <div class="summary-row"><span>+ Bônus</span><strong>💎 ${order.product.bonusDiamonds.toLocaleString('pt-BR')}</strong></div>
    <div class="summary-row"><span>Preço</span><strong>${money(order.amountCents)}</strong></div>
    <div class="summary-row"><span>Método</span><strong>Pix</strong></div>
    <div class="summary-row"><span>ID do jogador</span><strong>${order.playerIdMasked}</strong></div>`;
  const show = (id) => byId(id).classList.remove('is-hidden'); const hide = (id) => byId(id).classList.add('is-hidden');
  let order = read(orderKey); let pollTimer;
  function renderOrder(value) { byId('summary').innerHTML = rows(value); byId('pix-summary').innerHTML = rows(value); }
  function showPix(value) {
    order = { ...order, ...value }; save(orderKey, order); renderOrder(value); hide('loading'); hide('checkout-content'); show('pix-content');
    byId('pix-status').textContent = value.paymentStatus === 'PAID' ? 'Pagamento confirmado. Preparando fulfillment.' : 'Aguardando pagamento…';
    const pix = value.pix || {}; byId('copy-paste').value = pix.copyPaste || '';
    byId('beneficiary').textContent = pix.beneficiaryName ? `Beneficiário: ${pix.beneficiaryName}` : '';
    const code = pix.qrCode || ''; const image = byId('qr-code'); const fallback = byId('qr-unavailable');
    const source = code.startsWith('data:') || code.startsWith('http') ? code : (/^[A-Za-z0-9+/=]+$/.test(code) && code.length > 80 ? `data:image/png;base64,${code}` : '');
    if (source) { image.src = source; image.classList.remove('is-hidden'); fallback.classList.add('is-hidden'); }
    if (value.paymentStatus === 'PENDING') startPolling(); else stopPolling();
  }
  function startPolling() { stopPolling(); pollTimer = setInterval(async () => { try { const current = await api(`/api/orders/${order.id}`, { headers: headerToken(order) }); showPix(current); } catch (_) {} }, 8000); }
  function stopPolling() { if (pollTimer) clearInterval(pollTimer); }
  async function createPix() {
    const button = byId('pay-button'); button.disabled = true; byId('checkout-error').textContent = '';
    try { const value = await api(`/api/orders/${order.id}/pix`, { method: 'POST', headers: { ...headerToken(order), 'Idempotency-Key': idempotency('pixKey') } }); history.replaceState({}, '', `/checkout/pix/${order.id}`); showPix(value); }
    catch (error) { byId('checkout-error').textContent = error.message; button.disabled = false; }
  }
  async function bootstrap() {
    const selection = read(selectionKey); const existingId = location.pathname.match(/^\/checkout\/pix\/(ord_[A-Za-z0-9_-]+)$/)?.[1] || order.id;
    try {
      if (existingId && order.checkoutToken) { const value = await api(`/api/orders/${existingId}`, { headers: headerToken(order) }); showPix(value); return; }
      if (!selection.playerId || !selection.productId || selection.paymentMethod !== 'PIX') { hide('loading'); show('missing-selection'); return; }
      const created = await api('/api/orders', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Idempotency-Key': idempotency('orderKey') }, body: JSON.stringify(selection) });
      order = { ...created.order, checkoutToken: created.checkoutToken, orderKey: idempotency('orderKey') }; save(orderKey, order); renderOrder(order); hide('loading'); show('checkout-content');
    } catch (error) { hide('loading'); show('checkout-content'); byId('checkout-error').textContent = error.message; }
  }
  byId('pay-button').addEventListener('click', createPix);
  byId('copy-button').addEventListener('click', async () => { try { await navigator.clipboard.writeText(byId('copy-paste').value); byId('copy-feedback').textContent = 'Código copiado!'; } catch (_) { byId('copy-feedback').textContent = 'Copie o código manualmente.'; } });
  addEventListener('beforeunload', stopPolling); bootstrap();
}());
