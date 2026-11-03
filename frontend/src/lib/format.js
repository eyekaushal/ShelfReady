const inr = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

/** "123.5" → "₹123.50" (Indian digit grouping: ₹1,23,456.00). */
export function formatPrice(value) {
  const number = Number(value)
  return Number.isFinite(number) ? inr.format(number) : '—'
}

const dateFormat = new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })

export function formatDate(iso) {
  return iso ? dateFormat.format(new Date(iso)) : '—'
}

/** "2 hours ago", "3 days ago", or the date once it's older than a month. */
export function timeAgo(iso) {
  if (!iso) return '—'
  const seconds = Math.round((Date.now() - new Date(iso).getTime()) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes} min ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`
  const days = Math.round(hours / 24)
  if (days < 31) return `${days} day${days === 1 ? '' : 's'} ago`
  return formatDate(iso)
}

/** "Food › Biscuits › Glucose Biscuits" → "Glucose Biscuits" */
export function leafName(fullPath) {
  return fullPath ? fullPath.split(' › ').at(-1) : ''
}

export function initials(name) {
  return (name || '?').trim().charAt(0).toUpperCase()
}
