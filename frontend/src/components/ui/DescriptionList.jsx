/**
 * Key/value rows like Attio's "Details" panel. items: [{label, value}].
 * A missing value shows a quiet dash instead of an empty cell.
 */
export function DescriptionList({ items }) {
  return (
    <dl className="divide-y divide-gray-100">
      {items.map((item) => (
        <div key={item.label} className="grid grid-cols-[120px_1fr] gap-3 py-2.5 text-[13px]">
          <dt className="text-gray-500">{item.label}</dt>
          <dd className="min-w-0 break-words text-gray-900">
            {item.value === null || item.value === undefined || item.value === '' ? (
              <span className="text-gray-400">—</span>
            ) : (
              item.value
            )}
          </dd>
        </div>
      ))}
    </dl>
  )
}
