(function () {
  'use strict';
  const toast = document.getElementById('category-toast');
  let timer;
  const sendHeight = () => parent.postMessage({ type: 'category-height', frame: location.pathname, height: document.documentElement.scrollHeight }, location.origin);
  const message = (text) => {
    if (!toast) return;
    toast.textContent = text;
    toast.classList.add('is-visible');
    clearTimeout(timer);
    timer = setTimeout(() => toast.classList.remove('is-visible'), 2400);
  };
  document.addEventListener('click', (event) => {
    const choice = event.target.closest('.diamond-option,.offer-card,.payment-card,.redeem-row');
    if (choice) {
      choice.parentElement.querySelectorAll('.is-selected').forEach((item) => item.classList.remove('is-selected'));
      choice.classList.add('is-selected');
      message('Selecionado no modo demonstração.');
      return;
    }
    if (event.target.closest('.category-login,.category-action')) {
      const state = document.getElementById('login-state');
      if (state) state.textContent = 'Modo demonstração — nenhuma informação foi enviada.';
      message('Modo demonstração — nenhuma informação foi enviada.');
    }
  });
  const tabs = document.querySelectorAll('.tab');
  tabs.forEach((tab) => tab.addEventListener('click', () => {
    tabs.forEach((item) => item.classList.toggle('is-active', item === tab));
    document.getElementById('buy-panel').classList.toggle('is-hidden', tab.dataset.tab !== 'buy');
    document.getElementById('redeem-panel').classList.toggle('is-hidden', tab.dataset.tab !== 'redeem');
    sendHeight();
  }));
  const toggle = document.getElementById('toggle-offers');
  if (toggle) toggle.addEventListener('click', () => {
    const card = document.getElementById('weekly-lite');
    const open = card.classList.contains('is-hidden');
    card.classList.toggle('is-hidden', !open);
    toggle.innerHTML = open ? 'Ver menos <span>⌃</span>' : 'Ver mais <span>⌄</span>';
    sendHeight();
  });
  new ResizeObserver(sendHeight).observe(document.body);
  addEventListener('load', sendHeight);
  setTimeout(sendHeight, 100);
}());
