// The backend stores timestamps as naive UTC datetimes (no timezone suffix
// in the serialized string, e.g. "2026-08-31T09:43:00.123"). Without a
// suffix, JavaScript's Date parser assumes local time instead of UTC,
// which shows every timestamp offset by the browser's timezone. These
// helpers force UTC interpretation before converting to the viewer's
// local time for display.

function toUtcDate(value) {
  if (!value) return null
  const hasTimezone = /Z$|[+-]\d{2}:?\d{2}$/.test(value)
  return new Date(hasTimezone ? value : `${value}Z`)
}

export function formatDateTime(value) {
  const d = toUtcDate(value)
  return d ? d.toLocaleString() : ''
}

export function formatTime(value) {
  const d = toUtcDate(value)
  return d ? d.toLocaleTimeString() : ''
}
