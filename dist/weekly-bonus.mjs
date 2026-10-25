const video = document.querySelector('[data-weekly-bonus-video]');

if (video) {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let nearViewport = false;
  video.muted = true;

  function syncPlayback() {
    if (!nearViewport || document.hidden || reducedMotion.matches) {
      video.pause();
      return;
    }
    // Avoid fetching a below-fold 18 MB loop until it approaches the viewport,
    // including on browsers without native loading="lazy" media support.
    if (!video.getAttribute('src')) {
      video.src = video.dataset.src;
      video.load();
    }
    video.play().catch(() => {}); // The original Figma poster remains on failure.
  }

  if (reducedMotion.matches) video.removeAttribute('autoplay');
  const observer = new IntersectionObserver((entries) => {
    nearViewport = entries[0].isIntersecting;
    syncPlayback();
  }, { rootMargin: '200px 0px' });
  observer.observe(video);
  reducedMotion.addEventListener('change', () => {
    video.autoplay = !reducedMotion.matches;
    syncPlayback();
  });
  document.addEventListener('visibilitychange', syncPlayback);
  window.addEventListener('pageshow', syncPlayback);
}
