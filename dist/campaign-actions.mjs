// The scene is transformed by its scroll animation. Its untransformed layout
// position is the reliable destination where the main product image is open.
const enterButton = document.querySelector('[data-bonus-enter-hover]');
const target = document.getElementById('featured-packages');
const canvas = document.getElementById('design-canvas');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

// Observe an untransformed layout marker spanning the intro and main scene.
// Visibility is functional navigation state, so reduced-motion users receive
// the same uncluttered product view without adding a scroll animation.
const navigationTrack = document.querySelector('.campaign-sticky-track');
const navigation = document.getElementById('campaign-navigation');
const featuredRegion = document.querySelector('.featured-navigation-region');
const stickySentinel = document.querySelector('.campaign-sticky-sentinel');

if (navigationTrack && navigation) {
  const artwork = navigation.querySelector('[data-node-id="541:1215"]');
  let stuck = false;
  let entranceFrame = 0;
  let revealFrame = 0;

  const cancelEntrance = () => {
    cancelAnimationFrame(entranceFrame);
    cancelAnimationFrame(revealFrame);
    entranceFrame = revealFrame = 0;
    navigationTrack.classList.remove('campaign-entering');
  };
  const setNavigationHidden = hidden => {
    navigationTrack.classList.toggle('campaign-hidden', hidden);
    navigation.inert = hidden;
    if (hidden) cancelEntrance();
  };
  const setStuck = next => {
    if (next === stuck) return;
    stuck = next;
    navigationTrack.classList.toggle('campaign-stuck', stuck);
    if (!stuck) {
      cancelEntrance();
      return;
    }
    if (!artwork || reducedMotion.matches || navigationTrack.classList.contains('campaign-hidden')) return;

    // A quick direction change continues the current CSS transition instead
    // of snapping back to its start. This read never determines stickiness.
    const translation = getComputedStyle(artwork).translate;
    if (translation.split(/\s+/).some(value => Math.abs(parseFloat(value)) > .01)) return;
    navigationTrack.classList.add('campaign-entering');
    entranceFrame = requestAnimationFrame(() => {
      entranceFrame = 0;
      revealFrame = requestAnimationFrame(() => {
        revealFrame = 0;
        navigationTrack.classList.remove('campaign-entering');
      });
    });
  };

  if (featuredRegion) {
    const regionBounds = featuredRegion.getBoundingClientRect();
    setNavigationHidden(regionBounds.top < window.innerHeight && regionBounds.bottom > 0);
  }
  if (stickySentinel) setStuck(stickySentinel.getBoundingClientRect().bottom < 0);

  const regionObserver = new IntersectionObserver(entries => {
    // Resolve the product region first when a large scroll crosses both.
    for (const entry of entries) {
      if (entry.target === featuredRegion) setNavigationHidden(entry.isIntersecting);
    }
    for (const entry of entries) {
      if (entry.target === stickySentinel) {
        // An edge-adjacent sentinel is still intersecting. Clear at re-entry,
        // rather than waiting for another threshold callback inside the view.
        setStuck(!entry.isIntersecting && entry.boundingClientRect.bottom <= 0);
      }
    }
  }, { threshold: 0 });
  if (featuredRegion) regionObserver.observe(featuredRegion);
  if (stickySentinel) regionObserver.observe(stickySentinel);
}

if (enterButton && target && canvas) {
  let latestRequest = 0;

  enterButton.addEventListener('click', async () => {
    const request = ++latestRequest;
    const canvasBounds = canvas.getBoundingClientRect();
    const scale = canvasBounds.width / canvas.offsetWidth;
    const canvasDocumentTop = canvasBounds.top + window.scrollY;
    const top = canvasDocumentTop + target.offsetTop * scale;

    // Native scroll promises wait for completion where supported. Awaiting
    // undefined remains safe in older browsers; preventScroll below ensures
    // their immediate focus change cannot start a competing scroll.
    await window.scrollTo({
      top,
      behavior: reducedMotion.matches ? 'instant' : 'smooth',
    });

    if (request !== latestRequest) return;
    target.focus({ preventScroll: true });
  });
}
