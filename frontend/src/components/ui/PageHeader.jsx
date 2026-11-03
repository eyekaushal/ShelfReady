import { ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'

/**
 * Page title block: optional breadcrumb, big title, grey subtitle, actions on the right.
 * breadcrumb: [{label, to}] — the last item is the current page and has no `to`.
 */
export function PageHeader({ breadcrumb, title, subtitle, actions }) {
  return (
    <div className="mb-6">
      {breadcrumb?.length ? (
        <nav className="mb-2 flex items-center gap-1 text-[13px] text-gray-500" aria-label="Breadcrumb">
          {breadcrumb.map((item, index) => (
            <span key={item.label} className="flex items-center gap-1">
              {index > 0 ? <ChevronRight className="size-3.5 text-gray-300" aria-hidden="true" /> : null}
              {item.to ? (
                <Link to={item.to} className="hover:text-gray-900">
                  {item.label}
                </Link>
              ) : (
                <span className="text-gray-700">{item.label}</span>
              )}
            </span>
          ))}
        </nav>
      ) : null}
      <div className="flex flex-wrap items-start justify-between gap-x-6 gap-y-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold tracking-[-0.01em] text-gray-900">{title}</h1>
          {subtitle ? <p className="mt-1 text-sm text-gray-500">{subtitle}</p> : null}
        </div>
        {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
      </div>
    </div>
  )
}
