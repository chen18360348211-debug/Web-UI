import './product-flip.mjs';

const entryMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const entryCards = new Map();
const pendingTargets = new Map();
let entryObserver;

function stopObserving(target) {
  if (!target) return;
  pendingTargets.delete(target);
  entryObserver?.unobserve(target);
}

function updateCardState(record) {
  record.card.dataset.productEntry = record.sceneState === 'complete'
    && [...record.stages.values()].every(stage => stage.state === 'complete')
    ? 'complete' : 'running';
}

function finishStage(record, stage) {
  if (!stage || stage.state === 'complete') return;
  stopObserving(stage.gate);
  stage.state = 'complete';
  for (const node of stage.nodes) node.dataset.productPartState = 'complete';
  updateCardState(record);
}

function completeEntry(record) {
  stopObserving(record.scene);
  record.sceneState = 'complete';
  record.scene.dataset.productSceneState = 'complete';
  for (const stage of record.stages.values()) finishStage(record, stage);
  updateCardState(record);
}

function startStage(record, stage) {
  if (!stage || stage.state !== 'pending') return;
  stopObserving(stage.gate);
  stage.state = 'running';
  for (const node of stage.nodes) node.dataset.productPartState = 'running';
  updateCardState(record);
}

function startScene(record) {
  if (record.sceneState !== 'pending') return;
  // Stop observing the fixed pending pose before its first upward movement.
  stopObserving(record.scene);
  record.sceneState = 'running';
  record.scene.dataset.productSceneState = 'running';
  startStage(record, record.stages.get('image'));
  updateCardState(record);
}

function positionGate(record, stage) {
  let left = 0;
  let top = 0;
  let node = stage.reference;
  while (node && node !== record.scene) {
    left += node.offsetLeft;
    top += node.offsetTop;
    node = node.offsetParent;
  }
  const rise = parseFloat(getComputedStyle(stage.reference).getPropertyValue('--product-part-rise')) || 0;
  Object.assign(stage.gate.style, {
    left: `${left}px`,
    top: `${top + rise}px`,
    width: `${stage.reference.offsetWidth}px`,
    height: `${stage.reference.offsetHeight}px`,
  });
}

function observePendingEntries() {
  entryObserver?.disconnect();
  entryObserver = undefined;
  if (entryMotion.matches || typeof IntersectionObserver === 'undefined') {
    for (const record of entryCards.values()) completeEntry(record);
    return;
  }
  if (!pendingTargets.size) return;

  for (const descriptor of pendingTargets.values()) {
    if (descriptor.stage) positionGate(descriptor.record, descriptor.stage);
  }
  const observer = new IntersectionObserver(entries => {
    if (entryObserver !== observer) return;
    const visible = entries.filter(entry => entry.isIntersecting)
      .map(entry => pendingTargets.get(entry.target)).filter(Boolean);
    // A large scroll can expose a scene and its text gates in the same batch.
    for (const descriptor of visible) {
      if (!descriptor.stage) startScene(descriptor.record);
    }
    for (const descriptor of visible) {
      if (!descriptor.stage) continue;
      startScene(descriptor.record);
      startStage(descriptor.record, descriptor.stage);
      if (descriptor.stage.kind === 'price') {
        startStage(descriptor.record, descriptor.record.stages.get('button'));
      }
    }
  }, { rootMargin: '0px', threshold: 0 });
  entryObserver = observer;
  for (const target of pendingTargets.keys()) observer.observe(target);
}

const cards = document.querySelectorAll('[data-product-flip]');
for (const [index, card] of [...cards].entries()) {
  const turn = card.querySelector(':scope > .product-card-turn');
  // Unsupported flip enhancement leaves the original static card visible.
  if (!turn || card.hasAttribute('data-product-entry')) continue;

  const scene = document.createElement('div');
  scene.className = 'product-card-entry-scene';
  scene.style.setProperty('--product-entry-delay', `${index % 4 * 65}ms`);
  turn.before(scene);
  scene.append(turn);
  scene.dataset.productSceneState = 'pending';
  card.dataset.productEntry = 'pending';

  const record = { card, scene, sceneState: 'pending', stages: new Map() };
  entryCards.set(card, record);
  pendingTargets.set(scene, { record });

  for (const kind of ['image', 'title', 'price', 'button']) {
    const nodes = [...turn.querySelectorAll(`[data-product-entry-part="${kind}"]`)];
    const stage = { kind, nodes, state: nodes.length ? 'pending' : 'complete' };
    record.stages.set(kind, stage);
    for (const node of nodes) node.dataset.productPartState = 'pending';
    // The CTA shares the price trigger, including while below the viewport.
    if (kind === 'image' || kind === 'button' || !nodes.length) continue;

    stage.reference = turn.querySelector(`.product-card-front [data-product-entry-part="${kind}"]`) || nodes[0];
    const gate = document.createElement('span');
    gate.className = 'product-entry-gate';
    gate.dataset.productEntryGate = kind;
    gate.setAttribute('aria-hidden', 'true');
    stage.gate = gate;
    // This plane follows scene entry but is outside the rotating turn.
    scene.append(gate);
    pendingTargets.set(gate, { record, stage });
  }

  scene.addEventListener('animationend', event => {
    if (event.target === scene && event.animationName === 'product-card-enter') {
      record.sceneState = 'complete';
      scene.dataset.productSceneState = 'complete';
      updateCardState(record);
    } else if (event.animationName === 'product-part-enter') {
      const kind = event.target.dataset.productEntryPart;
      finishStage(record, record.stages.get(kind));
    }
  });
  // Keyboard navigation and reduced motion reveal every stage immediately.
  card.addEventListener('focusin', () => completeEntry(record));
  if (entryMotion.matches || typeof IntersectionObserver === 'undefined'
      || card.contains(document.activeElement)) completeEntry(record);
}

observePendingEntries();
window.addEventListener('resize', observePendingEntries, { passive: true });

entryMotion.addEventListener('change', event => {
  if (!event.matches) return;
  for (const record of entryCards.values()) completeEntry(record);
  entryObserver?.disconnect();
  entryObserver = undefined;
});
