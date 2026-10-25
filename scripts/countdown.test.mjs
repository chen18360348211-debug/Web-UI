import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { CAMPAIGN_END, campaignDeadline, remainingTime } from '../dist/countdown-core.mjs';

const require = createRequire(import.meta.url);
const { Temporal } = require('../dist/vendor/temporal-polyfill-0.5.1.js');
const end = campaignDeadline(Temporal);
assert.equal(end.toString(), '2026-12-01T04:59:59Z', 'Deadline must use Eastern Standard Time on November 30.');
assert.deepEqual(CAMPAIGN_END, { date: '2026-11-30', time: '23:59:59', timeZone: 'America/New_York' });

const cases = [
  [86400, [1, 0, 0, 0, false]],
  [90061, [1, 1, 1, 1, false]],
  [3600, [0, 1, 0, 0, false]],
  [60, [0, 0, 1, 0, false]],
  [1, [0, 0, 0, 1, false]],
  [0, [0, 0, 0, 0, true]],
  [-1, [0, 0, 0, 0, true]],
];
for (const [seconds, expected] of cases) {
  const result = remainingTime(Temporal, end, end.subtract({ seconds }));
  assert.deepEqual(Object.values(result), expected, `Boundary: ${seconds} seconds remaining`);
}
assert.equal(remainingTime(Temporal, end, end.subtract({ milliseconds: 1 })).seconds, 1, 'Do not end before the final fraction of a second.');

// The US DST change is in the interval: elapsed days must still be 24 hours.
const beforeDST = Temporal.Instant.from('2026-10-31T16:00:00Z');
assert.deepEqual(Object.values(remainingTime(Temporal, end, beforeDST)), [30, 12, 59, 59, false]);
for (const zone of ['Asia/Shanghai', 'America/New_York', 'UTC']) {
  const sameInstant = beforeDST.toZonedDateTimeISO(zone).toInstant();
  assert.deepEqual(remainingTime(Temporal, end, sameInstant), remainingTime(Temporal, end, beforeDST));
}
const initial = end.subtract({ seconds: 125 });
assert.equal(remainingTime(Temporal, end, initial).minutes, 2);
assert.equal(remainingTime(Temporal, end, initial.add({ seconds: 90 })).seconds, 35, 'Recalculate after a suspended interval.');
console.log('Countdown deadline, rollovers, expiry, subsecond rounding, DST, viewer time zones, and suspended-clock recovery passed.');
