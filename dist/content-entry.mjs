// Coupon enhancement retains ownership of its original direct children.
import './coupon-marquee.mjs';

const preference = matchMedia('(prefers-reduced-motion: reduce)');
const records = [];
const pending = new Map();
let observer;

function releaseGate(record) {
  if (!record.gate) return;
  observer?.unobserve(record.gate);
  pending.delete(record.gate);
  record.gate.remove();
  record.gate = undefined;
}

function finish(record) {
  releaseGate(record);
  record.node.dataset.contentEntryState = 'complete';
}

function start(record) {
  if (record.node.dataset.contentEntryState !== 'pending') return;
  releaseGate(record);
  record.node.dataset.contentEntryState = 'running';
}

function placeGate(record) {
  const { node, gate } = record;
  if (!gate) return;
  const parent = node.offsetParent;
  if (!parent) return finish(record);
  // offset geometry excludes both the new entry translate and existing
  // scroll transforms. CSS zoom scales the source and marker together.
  const style = getComputedStyle(node);
  Object.assign(gate.style, {
    left: `${node.offsetLeft}px`, top: `${node.offsetTop}px`,
    width: style.width, height: style.height,
  });
  if (gate.parentElement !== parent) parent.append(gate);
}

for (const node of document.querySelectorAll('[data-content-entry]')) {
  if (node.hasAttribute('data-content-entry-state')) continue;
  if (preference.matches || typeof IntersectionObserver === 'undefined') {
    node.dataset.contentEntryState = 'complete';
    continue;
  }

  let visual = node;
  if (node.hasAttribute('data-content-entry-inner')) {
    visual = document.createElement('span');
    visual.className = 'content-entry-visual';
    const style = getComputedStyle(node);
    // Paint gradient lettering only on the animated inner text, otherwise
    // the transparent text on its parent would still show through at entry.
    if (style.backgroundImage !== 'none') {
      visual.style.backgroundImage = style.backgroundImage;
      visual.style.backgroundClip = style.backgroundClip;
      visual.style.webkitBackgroundClip = style.webkitBackgroundClip;
      node.style.backgroundImage = 'none';
    }
    visual.append(...node.childNodes);
    node.append(visual);
  }

  const gate = document.createElement('span');
  gate.className = 'content-entry-gate';
  gate.dataset.contentEntryFor = node.dataset.nodeId;
  gate.setAttribute('aria-hidden', 'true');
  node.style.setProperty('--content-entry-delay', `${Number(node.dataset.contentEntry) || 0}ms`);
  node.dataset.contentEntryState = 'pending';
  const record = { node, visual, gate };
  records.push(record);
  pending.set(gate, record);
  placeGate(record);
  visual.addEventListener('animationend', event => {
    if (event.target === visual && event.animationName === 'content-enter') finish(record);
  });
  // Keyboard navigation must never land on an invisible button or tab.
  node.addEventListener('focusin', () => finish(record));
  if (node.contains(document.activeElement)) finish(record);
}

if (pending.size) {
  observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      const record = pending.get(entry.target);
      if (entry.isIntersecting && record) start(record);
    }
  }, { rootMargin: '0px', threshold: 0 });
  for (const gate of pending.keys()) observer.observe(gate);
}

function refreshGates() {
  for (const record of pending.values()) placeGate(record);
}
window.addEventListener('resize', refreshGates, { passive: true });
document.fonts?.ready.then(refreshGates);
preference.addEventListener('change', event => {
  if (!event.matches) return;
  for (const record of records) finish(record);
  observer?.disconnect();
});
