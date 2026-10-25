// Each strip keeps its own original Figma coupons, geometry, and play state.
for (const viewport of document.querySelectorAll('[data-coupon-marquee]')) {
  if (viewport.hasAttribute('data-ready')) continue;
  const coupons = [...viewport.children];
  if (coupons.length > 1) enhanceCoupons(viewport, coupons);
}

function enhanceCoupons(viewport, coupons) {
  const preference = matchMedia('(prefers-reduced-motion: reduce)');
  const sequence = document.createElement('div');
  sequence.className = 'coupon-sequence';
  for (const coupon of coupons) {
    sequence.append(coupon);
  }

  const repeated = sequence.cloneNode(true);
  repeated.setAttribute('aria-hidden', 'true');
  repeated.inert = true;
  const track = document.createElement('div');
  track.className = 'coupon-track coupon-content-track';
  track.append(sequence, repeated);

  // A second paint layer contains only the original border artwork. Both
  // tracks start together and share the exact same geometry and play state.
  const outlines = track.cloneNode(true);
  outlines.className = 'coupon-track coupon-outline-track';
  outlines.setAttribute('aria-hidden', 'true');
  outlines.inert = true;

  const canvas = document.createElement('canvas');
  canvas.className = 'coupon-pixels';
  canvas.setAttribute('aria-hidden', 'true');
  const pause = document.createElement('button');
  pause.type = 'button';
  pause.className = 'coupon-pause';
  pause.setAttribute('aria-pressed', 'false');
  pause.textContent = 'PAUSE COUPON SCROLLING';
  viewport.append(track, canvas, outlines, pause);
  viewport.dataset.ready = '';

  let inView = false;
  let paused = false;
  function updatePlayback() {
    viewport.dataset.playing = String(inView && !document.hidden && !preference.matches && !paused);
  }
  pause.addEventListener('click', () => {
    paused = !paused;
    pause.setAttribute('aria-pressed', String(paused));
    pause.textContent = paused ? 'RESUME COUPON SCROLLING' : 'PAUSE COUPON SCROLLING';
    updatePlayback();
  });

  const context = canvas.getContext('2d');
  const cells = new Map();
  const cellSize = 24;
  let frame = 0;
  let pendingPointer = null;
  let previousCell = null;
  let width = 1601;
  let height = 172;

  function clearPixels() {
    cancelAnimationFrame(frame);
    frame = 0;
    pendingPointer = previousCell = null;
    cells.clear();
    context?.clearRect(0, 0, width, height);
    viewport.dataset.pixelCount = '0';
  }

  function resizePixels() {
    clearPixels();
    const bounds = viewport.getBoundingClientRect();
    const style = getComputedStyle(viewport);
    width = parseFloat(style.width);
    height = parseFloat(style.height);
    canvas.width = Math.max(1, Math.round(bounds.width * devicePixelRatio));
    canvas.height = Math.max(1, Math.round(bounds.height * devicePixelRatio));
    context?.setTransform(canvas.width / width, 0, 0, canvas.height / height, 0, 0);
  }

  function stamp(column, row, now) {
    for (let y = -3; y <= 3; y++) {
      for (let x = -4; x <= 4; x++) {
        const c = column + x;
        const r = row + y;
        if (c < 0 || r < 0 || c * cellSize >= width || r * cellSize >= height) continue;
        const seed = (c * 37 + r * 53 + c * r * 11) % 19;
        if ((x / 4.1) ** 2 + (y / 3.1) ** 2 > .9 + seed / 60) continue;
        const lifetime = 390 + seed * 14;
        cells.set(`${c},${r}`, { x: c * cellSize, y: r * cellSize, expires: now + lifetime });
      }
    }
  }

  function drawPixels(now) {
    frame = 0;
    if (pendingPointer) {
      // One layout read per frame, including after scrolling or CSS zoom.
      const bounds = viewport.getBoundingClientRect();
      const x = (pendingPointer.x - bounds.left) * width / bounds.width;
      const y = (pendingPointer.y - bounds.top) * height / bounds.height;
      pendingPointer = null;
      if (x >= 0 && y >= 0 && x < width && y < height) {
        const current = { column: Math.floor(x / cellSize), row: Math.floor(y / cellSize) };
        const start = previousCell ?? current;
        const steps = Math.max(1, Math.abs(current.column - start.column), Math.abs(current.row - start.row));
        for (let step = 1; step <= steps; step++) {
          stamp(Math.round(start.column + (current.column - start.column) * step / steps),
            Math.round(start.row + (current.row - start.row) * step / steps), now);
        }
        previousCell = current;
      }
    }
    // Keep the local brush visible while the cursor rests inside the strip;
    // only positions left behind form the short, hard-edged retiring trail.
    if (previousCell) stamp(previousCell.column, previousCell.row, now);
    context.clearRect(0, 0, width, height);
    context.fillStyle = '#fff';
    for (const [key, cell] of cells) {
      if (cell.expires <= now) cells.delete(key);
      else context.fillRect(cell.x, cell.y, cellSize, cellSize);
    }
    viewport.dataset.pixelCount = String(cells.size);
    if (cells.size || pendingPointer) frame = requestAnimationFrame(drawPixels);
  }

  function movePointer(event) {
    if (!context || preference.matches || document.hidden || event.pointerType === 'touch') return;
    pendingPointer = { x: event.clientX, y: event.clientY };
    if (!frame) frame = requestAnimationFrame(drawPixels);
  }
  viewport.addEventListener('pointerenter', movePointer, { passive: true });
  viewport.addEventListener('pointermove', movePointer, { passive: true });
  viewport.addEventListener('pointerleave', () => {
    pendingPointer = previousCell = null;
  }, { passive: true });
  viewport.addEventListener('pointercancel', clearPixels, { passive: true });
  window.addEventListener('resize', resizePixels, { passive: true });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) clearPixels();
    updatePlayback();
  });
  preference.addEventListener('change', () => {
    clearPixels();
    updatePlayback();
  });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(([entry]) => {
      inView = entry.isIntersecting;
      if (!inView) clearPixels();
      updatePlayback();
    }).observe(viewport);
  } else {
    inView = true;
    updatePlayback();
  }
  resizePixels();
}
