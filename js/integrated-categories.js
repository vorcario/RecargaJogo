/* Preenche as etapas já existentes sem alterar o aplicativo original. */
(function () {
  'use strict';
  const root = document.getElementById('root');
  const steps = [
    { id: 'local-category-login', label: 'login', number: '1', src: '/categoria_1_local.html', minHeight: 130 },
    { id: 'local-category-recharge', label: 'valor de recarga', number: '2', src: '/categoria_2_local.html', minHeight: 920 },
    { id: 'local-category-payment', label: 'metodo de pagamento', number: '3', src: '/categoria_3_local.html', minHeight: 500 }
  ];

  const clean = (value) => String(value || '')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().replace(/\s+/g, ' ').trim();
  const visible = (element) => Boolean(element && element.getClientRects().length);

  function textOf(element) { return clean(element.innerText || element.textContent); }
  function matchesStep(element, step) {
    const text = textOf(element);
    return text === step.label || text === `${step.number} ${step.label}` || text === `[${step.number}] ${step.label}`;
  }

  function findHeading(step) {
    if (!root) return null;
    const nodes = [...root.querySelectorAll('h1,h2,h3,h4,h5,h6,div,span,p,strong')]
      .filter(visible).filter((element) => matchesStep(element, step));
    if (!nodes.length) return null;
    const semantic = nodes.find((element) => /^H[1-6]$/.test(element.tagName));
    return semantic || nodes.sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top)[0];
  }

  function targetFor(heading, step) {
    let node = heading;
    let candidate = heading;
    while (node.parentElement && node.parentElement !== root) {
      const parent = node.parentElement;
      const text = textOf(parent);
      const containsAnotherStep = steps.some((other) => other !== step && text.includes(other.label));
      if (containsAnotherStep) break;
      candidate = parent;
      node = parent;
    }
    return candidate;
  }

  function appendStep(step) {
    if (document.getElementById(step.id)) return true;
    const heading = findHeading(step);
    if (!heading) return false;
    const target = targetFor(heading, step);
    const slot = document.createElement('div');
    slot.id = step.id;
    slot.className = 'local-category-slot';
    const frame = document.createElement('iframe');
    frame.title = `${step.label} — demonstração local`;
    frame.src = step.src;
    frame.style.height = `${step.minHeight}px`;
    frame.setAttribute('scrolling', 'no');
    slot.append(frame);
    target.append(slot);
    return true;
  }

  function removePlatformIcons() {
    if (!root) return;
    root.querySelectorAll('button,a,[role="button"],li').forEach((item) => {
      const label = clean(item.getAttribute('aria-label') || item.getAttribute('title') || item.innerText);
      if (label === 'facebook' || label === 'google') item.style.display = 'none';
    });
    root.querySelectorAll('img').forEach((image) => {
      const source = clean(`${image.src} ${image.alt} ${image.getAttribute('aria-label') || ''}`);
      if (!/(facebook|google)/.test(source)) return;
      const container = image.closest('button,a,[role="button"],li');
      if (container) container.style.display = 'none';
    });
  }

  function sync() {
    removePlatformIcons();
    steps.forEach(appendStep);
  }

  addEventListener('message', (event) => {
    if (event.origin !== location.origin || !event.data || event.data.type !== 'category-height') return;
    const slot = steps.find((step) => step.src === event.data.frame);
    const frame = slot && document.querySelector(`#${slot.id} iframe`);
    const height = Number(event.data.height);
    if (frame && Number.isFinite(height)) frame.style.height = `${Math.max(slot.minHeight, Math.ceil(height))}px`;
  });

  let tries = 0;
  const timer = setInterval(() => {
    sync();
    tries += 1;
    if (tries >= 32 || steps.every((step) => document.getElementById(step.id))) clearInterval(timer);
  }, 250);
  addEventListener('DOMContentLoaded', sync);
  setTimeout(sync, 650);
}());
