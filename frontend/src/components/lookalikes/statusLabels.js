/** How each look-alike status is shown. Keys match LookalikePair.status on the backend. */
export const STATUS_LABELS = {
  unresolved: { label: 'Unresolved', tone: 'amber' },
  resolved_distinct: { label: 'Distinct', tone: 'green' },
  duplicate: { label: 'Duplicate', tone: 'red' },
}
