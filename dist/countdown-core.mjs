export const CAMPAIGN_END = Object.freeze({
  date: '2026-11-30',
  time: '23:59:59',
  timeZone: 'America/New_York',
});

export function campaignDeadline(Temporal, config = CAMPAIGN_END) {
  return Temporal.PlainDate.from(config.date)
    .toPlainDateTime(config.time)
    .toZonedDateTime(config.timeZone)
    .toInstant();
}

// Count complete 24-hour periods, as expected by a DAYS/HRS/MINS/SEC display.
// Work with instants after resolving the campaign's time zone, so a viewer's
// local time zone and November's DST change cannot change the deadline.
export function remainingTime(Temporal, end, now = Temporal.Now.instant()) {
  const expired = Temporal.Instant.compare(now, end) >= 0;
  const total = expired ? 0 : now.until(end, {
    largestUnit: 'second',
    smallestUnit: 'second',
    roundingMode: 'ceil',
  }).seconds;
  return {
    days: Math.floor(total / 86400),
    hours: Math.floor(total / 3600) % 24,
    minutes: Math.floor(total / 60) % 60,
    seconds: total % 60,
    expired,
  };
}
