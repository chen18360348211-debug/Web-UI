// Scale the desktop artboard uniformly to the browser width, without animation.
// Campaign interactions live in their own files and do not change this layout.
const artboard = document.getElementById('design-canvas');
function fitDesktop() {
  const scale = document.documentElement.clientWidth / 1920;
  artboard.style.zoom = String(scale);
  artboard.style.setProperty('--desktop-viewport-height', `${window.innerHeight / scale}px`);
}
fitDesktop();
window.addEventListener('resize', fitDesktop);
