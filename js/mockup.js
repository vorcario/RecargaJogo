/* Mockup local: estados visuais somente. Não há API, autenticação ou pagamento. */
(function () {
  'use strict';

  const diamondOptions = [65, 100, 310, 520, 1060, 2180, 5600, 22400];
  const specialOffers = [
    { id: 'weekly', name: 'Assinatura Semanal', image: 'img/assinatura_semanal.png' },
    { id: 'monthly', name: 'Assinatura Mensal', image: 'img/assinatura_mensal.png' },
    { id: 'booyah', name: 'Passe Booyah', image: 'img/passe_booyah.png' },
    { id: 'booyah-premium', name: 'Passe Booyah Premium Plus', image: 'img/passe_booyah_premium_plus.png' },
    { id: 'weekly-lite', name: 'Semanal Econômica', image: 'img/semanal_economica.png' }
  ];
  const socialProviders = [
    { id: 'facebook', label: 'Facebook', image: 'img/social_facebook.png' },
    { id: 'google', label: 'Google', image: 'img/social_google.png' },
    { id: 'x', label: 'X', image: 'img/social_x.png' },
    { id: 'vk', label: 'VK', image: 'img/social_vk.png' },
    { id: 'apple', label: 'Apple', image: 'img/social_apple.png' }
  ];
  const redeemOptions = [
    { amount: '100 Diamante', bonus: '+ Bônus Geral 10', price: 'R$ 4,49' },
    { amount: '310 Diamante', bonus: '+ Bônus Geral 31', price: 'R$ 13,99' },
    { amount: '520 Diamante', bonus: '+ Bônus Geral 52', price: 'R$ 20,99' },
    { amount: '1.060 Diamante', bonus: '+ Bônus Geral 106', price: 'R$ 44,99' },
    { amount: '2.180 Diamante', bonus: '+ Bônus Geral 218', price: 'R$ 87,99' },
    { amount: '5.600 Diamante', bonus: '+ Bônus Geral 560', price: 'R$ 209,99' }
  ];
  const paymentMethods = [
    { id: 'pix', name: 'Pix', image: 'img/pagamento_pix.png', promo: true },
    { id: 'nupay', name: 'NuPay', image: 'img/pagamento_nupay.png', promo: true },
    { id: 'picpay', name: 'PicPay', image: 'img/pagamento_picpay.png', promo: true },
    { id: 'credit', name: 'Cartão de Crédito', image: 'img/pagamento_cartao_credito.png', promo: true },
    { id: 'mercado', name: 'Mercado Pago', image: 'img/pagamento_mercado_pago.png', promo: true, isNew: true },
    { id: 'google-pay', name: 'Google Pay', image: 'img/pagamento_google_pay.png', promo: true },
    { id: 'wallet', name: 'Carteira Virtual', image: 'img/pagamento_pagseguro.png', promo: true },
    { id: 'boleto', name: 'Boleto', image: 'img/pagamento_boleto.png' },
    { id: 'razer', name: 'Razer Gold', image: 'img/pagamento_razer_gold.png', promo: true }
  ];

  const byId = (id) => document.getElementById(id);
  const formatAmount = (amount) => amount.toLocaleString('pt-BR');
  const diamond = () => '<i class="diamond-shape" aria-hidden="true"></i>';
  let toastTimer;

  function showToast(message) {
    const toast = byId('demo-toast');
    toast.textContent = message || 'Modo demonstração — nenhuma informação foi enviada.';
    toast.classList.add('is-visible');
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => toast.classList.remove('is-visible'), 3000);
  }

  function buildDiamondOptions() {
    const grid = byId('diamond-grid');
    grid.innerHTML = diamondOptions.map((amount) => `
      <button class="diamond-option" type="button" data-amount="${amount}" aria-label="Selecionar ${formatAmount(amount)} diamantes">
        ${diamond()}<span>${formatAmount(amount)}</span>
      </button>`).join('');
    grid.addEventListener('click', (event) => {
      const option = event.target.closest('.diamond-option');
      if (!option) return;
      grid.querySelectorAll('.diamond-option').forEach((card) => card.classList.remove('is-selected'));
      option.classList.add('is-selected');
      showToast(`${option.dataset.amount} diamantes selecionados no modo demonstração.`);
    });
  }

  function buildOffers() {
    const grid = byId('offer-grid');
    const createCard = (offer, hidden) => `
      <button class="offer-card${hidden ? ' is-hidden' : ''}" type="button" data-offer="${offer.id}">
        <img src="${offer.image}" alt="${offer.name}" />
        <span class="offer-name">${offer.name}<i class="offer-info" aria-hidden="true">i</i></span>
      </button>`;
    grid.innerHTML = specialOffers.map((offer, index) => createCard(offer, index > 3)).join('');
    grid.addEventListener('click', (event) => {
      const card = event.target.closest('.offer-card');
      if (!card) return;
      grid.querySelectorAll('.offer-card').forEach((item) => item.classList.remove('is-selected'));
      card.classList.add('is-selected');
      showToast('Oferta selecionada apenas para visualização.');
    });
  }

  function buildSocialProviders() {
    const list = byId('social-list');
    list.innerHTML = socialProviders.map((provider) => `
      <button class="social-button" type="button" data-provider="${provider.id}" aria-label="Selecionar ${provider.label}">
        <img src="${provider.image}" alt="" />
      </button>`).join('');
    list.addEventListener('click', (event) => {
      const button = event.target.closest('.social-button');
      if (!button) return;
      list.querySelectorAll('.social-button').forEach((item) => item.classList.remove('is-selected'));
      button.classList.add('is-selected');
      showToast('Login social indisponível: este é um mockup local.');
    });
  }

  function buildRedeemList() {
    const list = byId('redeem-list');
    list.innerHTML = redeemOptions.map((option, index) => `
      <button class="redeem-row" type="button" data-redeem="${index}">
        ${diamond()}
        <span><strong class="redeem-amount">${option.amount}</strong><small class="redeem-bonus">${option.bonus}</small></span>
        <strong class="redeem-price">${option.price}</strong>
      </button>`).join('');
    list.addEventListener('click', (event) => {
      const row = event.target.closest('.redeem-row');
      if (!row) return;
      list.querySelectorAll('.redeem-row').forEach((item) => item.classList.remove('is-selected'));
      row.classList.add('is-selected');
      showToast('Pacote selecionado no modo demonstração.');
    });
  }

  function buildPayments() {
    const grid = byId('payment-grid');
    grid.innerHTML = paymentMethods.map((method) => `
      <button class="payment-card${method.isNew ? ' has-new' : ''}" type="button" data-payment="${method.id}" aria-label="Selecionar ${method.name}">
        <img src="${method.image}" alt="" /><span class="payment-name">${method.name}</span>
        ${method.promo ? '<span class="promo-badge"><i></i> PROMO</span>' : ''}
        ${method.isNew ? '<span class="new-badge">NOVO</span>' : ''}
      </button>`).join('');
    grid.addEventListener('click', (event) => {
      const card = event.target.closest('.payment-card');
      if (!card) return;
      grid.querySelectorAll('.payment-card').forEach((item) => item.classList.remove('is-selected'));
      card.classList.add('is-selected');
      showToast('Método selecionado apenas visualmente — nenhum pagamento será processado.');
    });
  }

  function wireTabs() {
    const panels = { buy: byId('buy-panel'), redeem: byId('redeem-panel') };
    document.querySelector('.tabs').addEventListener('click', (event) => {
      const tab = event.target.closest('.tab');
      if (!tab) return;
      const selected = tab.dataset.tab;
      document.querySelectorAll('.tab').forEach((item) => {
        const active = item === tab;
        item.classList.toggle('is-active', active);
        item.setAttribute('aria-selected', String(active));
      });
      panels.buy.classList.toggle('is-hidden', selected !== 'buy');
      panels.redeem.classList.toggle('is-hidden', selected !== 'redeem');
    });
  }

  function wireLogin() {
    byId('login-button').addEventListener('click', () => {
      byId('login-card').classList.add('is-selected');
      byId('login-state').textContent = 'Modo demonstração ativo — o ID permanece somente neste navegador.';
      showToast('Login simulado. Nenhuma informação foi enviada.');
    });
  }

  function wireOfferToggle() {
    const toggle = byId('toggle-offers');
    toggle.addEventListener('click', () => {
      const hiddenCard = byId('offer-grid').querySelector('.offer-card:nth-child(5)');
      const isClosed = hiddenCard.classList.contains('is-hidden');
      hiddenCard.classList.toggle('is-hidden', !isClosed);
      toggle.innerHTML = isClosed ? 'Ver menos <span aria-hidden="true">⌃</span>' : 'Ver mais <span aria-hidden="true">⌄</span>';
    });
  }

  function wireDemoActions() {
    document.querySelectorAll('.demo-action').forEach((button) => {
      button.addEventListener('click', () => showToast());
    });
  }

  buildDiamondOptions();
  buildOffers();
  buildSocialProviders();
  buildRedeemList();
  buildPayments();
  wireTabs();
  wireLogin();
  wireOfferToggle();
  wireDemoActions();
}());
