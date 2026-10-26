// CSS artwork is not covered by native image lazy loading. Warm the shared
// thumbnail just before its intro, including when the scene is transformed.
const scene = document.getElementById('featured-packages');
const intro = document.getElementById('customize');
if (scene && intro) {
  const showArtwork = () => {
    scene.style.setProperty('--package-thumbnail-art', `url("${scene.dataset.thumbnailArt}")`);
  };
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      if (!entries.some(entry => entry.isIntersecting)) return;
      showArtwork();
      observer.disconnect();
    }, { rootMargin: '700px 0px' });
    observer.observe(intro);
  } else {
    showArtwork();
  }
}
