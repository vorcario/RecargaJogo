/* Checkout independente. Todo PIX exibido vem da API interna, nunca do HTML. */
(function () {
  'use strict';
  const key = 'nebulaCheckoutOrder';
  const saved = (() => { try { return JSON.parse(sessionStorage.getItem(key)); } catch (_) { return null; } })();
  const $ = (selector) => document.querySelector(selector);
  const formatBRL = (cents) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100);
  const formatNumber = (value) => new Intl.NumberFormat('pt-BR').format(value);
  let order = null;
  let creating = false;
  let poll = null;

  function idem(prefix) {
    const suffix = crypto && crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
    return `${prefix}-${suffix}`;
  }
  function headers() { return { 'X-Checkout-Token': saved.checkoutToken }; }
  function show(selector) { $(selector).classList.remove('is-hidden'); }
  function hide(selector) { $(selector).classList.add('is-hidden'); }
  function summary(target) {
    const product = order.product;
    target.innerHTML = [
      ['Total', `💎 ${formatNumber(product.totalDiamonds)}`],
      ['Preço original', `💎 ${formatNumber(product.baseDiamonds)}`],
      ['Bônus geral', `💎 ${formatNumber(product.bonusDiamonds)}`],
      ['Preço', formatBRL(order.amountCents)],
      ['Método de pagamento', 'Pix'],
      ['ID', order.playerIdMasked]
    ].map(([label, value]) => `<div><span>${label}</span><strong>${value}</strong></div>`).join('');
  }
  function qrSource(qr) { return qr ? (qr.startsWith('data:') ? qr : `data:image/png;base64,${qr}`) : ''; }
  function paintPix() {
    hide('#loading'); hide('#checkout-content'); show('#pix-content');
    summary($('#pix-summary'));
    const pix = order.pix || {};
    const qr = $('#qr-code');
    if (pix.qrCode) { qr.src = qrSource(pix.qrCode); qr.classList.remove('is-hidden'); hide('#qr-unavailable'); }
    $('#copy-paste').value = pix.copyPaste || '';
    $('#beneficiary').textContent = pix.beneficiaryName ? `Beneficiário: ${pix.beneficiaryName}` : '';
    setStatus(order.paymentStatus);
  }
  function setStatus(status) {
    const text = status === 'PAID' ? 'Pagamento confirmado.' : status === 'EXPIRED' ? 'Cobrança expirada.' : status === 'FAILED' ? 'Não foi possível concluir a cobrança.' : 'Aguardando pagamento…';
    $('#pix-status').textContent = text;
    if (status !== 'PENDING' && poll) { clearInterval(poll); poll = null; }
  }
  function paintOrder() { hide('#loading'); show('#checkout-content'); summary($('#summary')); if (order.pix && order.pix.copyPaste) paintPix(); }
  async function readOrder() {
    const response = await fetch(`/api/orders/${encodeURIComponent(saved.id)}`, { headers: headers(), credentials: 'same-origin' });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload?.error?.message || 'Pedido indisponível.');
    order = payload;
  }
  async function createPix() {
    if (creating || order.pix) return;
    creating = true;
    $('#pay-button').disabled = true;
    $('#pay-button').textContent = 'Gerando PIX…';
    $('#checkout-error').textContent = '';
    try {
      const response = await fetch(`/api/orders/${encodeURIComponent(order.id)}/pix`, { method: 'POST', credentials: 'same-origin', headers: { ...headers(), 'Idempotency-Key': idem('pix') } });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload?.error?.message || 'Não foi possível gerar o PIX.');
      order = payload;
      paintPix();
      startPolling();
    } catch (error) {
      $('#checkout-error').textContent = error.message || 'Não foi possível gerar o PIX.';
      $('#pay-button').disabled = false;
      $('#pay-button').textContent = 'Tentar gerar PIX';
    } finally { creating = false; }
  }
  async function refresh() { try { await readOrder(); if (order.pix) paintPix(); } catch (_) { /* conserva dados exibidos */ } }
  function startPolling() { if (!poll && order.paymentStatus === 'PENDING') poll = setInterval(refresh, 5000); }

  $('#pay-button').addEventListener('click', createPix);
  $('#copy-button').addEventListener('click', async () => {
    const code = $('#copy-paste').value;
    if (!code) return;
    try { await navigator.clipboard.writeText(code); $('#copy-feedback').textContent = 'Código copiado'; }
    catch (_) { $('#copy-feedback').textContent = 'Não foi possível copiar automaticamente.'; }
  });

  if (!saved || !saved.id || !saved.checkoutToken) { hide('#loading'); show('#missing-selection'); return; }
  readOrder().then(() => { paintOrder(); if (order.pix) startPolling(); else createPix(); }).catch((error) => {
    hide('#loading'); show('#missing-selection'); $('#missing-selection p').textContent = error.message || 'Pedido indisponível.';
  });
}());
