import { AlertCircle, Sparkles, X } from 'lucide-react'

/**
 * One line above the filter chips after an AI search:
 * - "AI understood “…” as:" (the chips below show exactly how), or
 * - a fallback note when AI was unavailable and we searched for the words instead.
 */
export function AiSearchNotice({ notice, onDismiss }) {
  if (!notice) return null
  const fallback = notice.kind === 'fallback'

  return (
    <div className="flex items-start gap-2 text-[13px] text-gray-600 animate-fade-in" role="status">
      {fallback ? (
        <AlertCircle className="mt-0.5 size-4 shrink-0 text-amber-500" aria-hidden="true" />
      ) : (
        <Sparkles className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden="true" />
      )}
      <p className="min-w-0 flex-1">
        {fallback ? (
          <>
            {notice.message} Showing keyword results for <span className="font-medium text-gray-900">“{notice.query}”</span>.
          </>
        ) : (
          <>
            AI understood <span className="font-medium text-gray-900">“{notice.query}”</span> as the filters below.
            Remove any that look wrong.
          </>
        )}
      </p>
      <button
        type="button"
        onClick={onDismiss}
        className="rounded p-0.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
        aria-label="Dismiss"
      >
        <X className="size-3.5" />
      </button>
    </div>
  )
}
