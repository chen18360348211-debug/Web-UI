import { campaignDeadline, remainingTime } from './countdown-core.mjs';

let TemporalAPI = globalThis.Temporal;
if (!TemporalAPI) {
  // The local, pinned polyfill keeps the timer available in browsers that do
  // not ship Temporal yet. Native implementations need no additional download.
  await import('./vendor/temporal-polyfill-0.5.1.js');
  TemporalAPI = globalThis.temporal.Temporal;
}

const timer = document.querySelector('[data-countdown]');
if (timer) {
  const deadline = campaignDeadline(TemporalAPI);
  const fields = Object.fromEntries(
    [...timer.querySelectorAll('[data-countdown-unit]')]
      .map(node => [node.dataset.countdownUnit, node]),
  );
  let timeout;
  timer.dataset.deadline = deadline.toString();
  timer.setAttribute('role', 'timer');
  timer.setAttribute('aria-live', 'off');

  function update() {
    clearTimeout(timeout);
    const remaining = remainingTime(TemporalAPI, deadline);
    for (const unit of ['days', 'hours', 'minutes', 'seconds']) {
      const value = String(remaining[unit]).padStart(2, '0');
      if (fields[unit].textContent !== value) fields[unit].textContent = value;
    }
    timer.dataset.state = remaining.expired ? 'expired' : 'running';
    timer.setAttribute('aria-label', remaining.expired
      ? 'Black Friday has ended.'
      : `Black Friday ends November 30, 2026, at 11:59:59 PM Eastern Time. ${remaining.days} days, ${remaining.hours} hours, ${remaining.minutes} minutes, ${remaining.seconds} seconds remaining.`);
    if (!remaining.expired && document.visibilityState !== 'hidden') {
      timeout = setTimeout(update, 1000);
    }
  }

  update();
  // Recompute from the clock, rather than decrementing a stored number. This
  // also catches browser suspension, back/forward cache, and clock corrections.
  document.addEventListener('visibilitychange', update);
  window.addEventListener('pageshow', update);
  window.addEventListener('pagehide', () => clearTimeout(timeout));
}
