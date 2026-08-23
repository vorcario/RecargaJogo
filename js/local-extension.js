/* Anexa conteúdo visual local sem alterar a árvore do aplicativo já carregado. */
(function () {
  'use strict';
  const frameId = 'local-content-frame';

  function updateHeight(height) {
    const frame = document.getElementById(frameId);
    if (frame && Number.isFinite(height)) frame.style.height = `${Math.max(2000, Math.ceil(height))}px`;
  }

  function addLocalContent() {
    if (document.getElementById(frameId)) return;
    const section = document.createElement('section');
    section.id = 'local-content-extension';
    section.setAttribute('aria-label', 'Conteúdo local de demonstração');

    const frame = document.createElement('iframe');
    frame.id = frameId;
    frame.title = 'Conteúdo local de demonstração';
    frame.src = '/conteudo_local.html';
    frame.setAttribute('scrolling', 'no');
    section.append(frame);
    document.body.append(section);
  }

  addEventListener('message', (event) => {
    if (event.origin !== location.origin || !event.data || event.data.type !== 'local-content-height') return;
    updateHeight(Number(event.data.height));
  });

  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', () => setTimeout(addLocalContent, 300));
  else setTimeout(addLocalContent, 300);
}());
