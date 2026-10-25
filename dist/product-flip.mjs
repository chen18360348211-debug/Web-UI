// Figma 594:1618 supplies the entire back face, including all five assets.
const template = document.getElementById('product-hover-template');
const supportsFlip = CSS.supports('rotate', 'y 180deg') && CSS.supports('backface-visibility', 'hidden');

if (template && supportsFlip) {
  for (const card of document.querySelectorAll('[data-product-flip]')) {
    if (card.hasAttribute('data-flip-ready')) continue;
    const front = document.createElement('div');
    front.className = 'product-card-face product-card-front';
    front.append(...card.childNodes);
    const back = document.createElement('div');
    back.className = 'product-card-face product-card-back';
    back.append(template.content.cloneNode(true));
    back.setAttribute('aria-hidden', 'true');
    back.inert = true;
    const turn = document.createElement('div');
    turn.className = 'product-card-turn';
    turn.append(front, back);
    card.append(turn);
    card.tabIndex = 0;
    card.setAttribute('role', 'group');
    card.setAttribute('aria-label', front.querySelector('p')?.textContent.trim() || 'Product card');
    card.dataset.flipReady = '';
    card.dataset.flipped = 'false';

    let hovered = false;
    let keyboardFocused = false;
    function updateFace() {
      const flipped = hovered || keyboardFocused;
      card.dataset.flipped = String(flipped);
      front.inert = flipped;
      front.setAttribute('aria-hidden', String(flipped));
      back.inert = !flipped;
      back.setAttribute('aria-hidden', String(!flipped));
    }
    function resetFace() {
      hovered = keyboardFocused = false;
      updateFace();
    }
    card.addEventListener('pointerenter', event => {
      if (event.pointerType === 'touch') return;
      hovered = true;
      updateFace();
    }, { passive: true });
    card.addEventListener('pointerleave', () => {
      hovered = false;
      updateFace();
    }, { passive: true });
    card.addEventListener('pointercancel', resetFace, { passive: true });
    card.addEventListener('focusin', () => {
      // Mouse clicks do not latch the back face after the pointer leaves.
      keyboardFocused = card.matches(':focus-visible') || Boolean(card.querySelector(':focus-visible'));
      updateFace();
    });
    card.addEventListener('focusout', () => {
      queueMicrotask(() => {
        keyboardFocused = card.contains(document.activeElement)
          && (card.matches(':focus-visible') || Boolean(card.querySelector(':focus-visible')));
        updateFace();
      });
    });
    window.addEventListener('blur', resetFace);
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) resetFace();
    });
  }
}
