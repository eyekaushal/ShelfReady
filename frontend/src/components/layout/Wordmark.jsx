import { Link } from 'react-router-dom'

/** The ShelfReady logo: accent tile with a shelf glyph + the name. */
export function Wordmark() {
  return (
    <Link to="/" className="flex items-center gap-2 rounded-md text-gray-900">
      <span className="flex size-6 items-center justify-center rounded-md bg-accent" aria-hidden="true">
        <svg viewBox="0 0 32 32" className="size-5" fill="#fff">
          <rect x="7" y="9" width="18" height="2.5" rx="1.25" />
          <rect x="7" y="20.5" width="18" height="2.5" rx="1.25" />
          <rect x="9" y="12.5" width="4" height="7" rx="1" opacity=".9" />
          <rect x="14.5" y="14" width="4" height="5.5" rx="1" opacity=".7" />
          <rect x="20" y="12.5" width="3" height="7" rx="1" opacity=".9" />
        </svg>
      </span>
      <span className="text-[15px] font-semibold tracking-[-0.01em]">ShelfReady</span>
    </Link>
  )
}
