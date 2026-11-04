import { Sparkles } from 'lucide-react'

import { cn } from '../../lib/cn'

/**
 * Marks a form field that AI filled in. Blue like the rest of the accent; amber when the AI
 * said it wasn't sure, so the user knows which fields to look at first.
 * The form removes the badge as soon as the user edits that field.
 */
export function AiBadge({ confidence = 'high' }) {
  const unsure = confidence === 'low'
  return (
    <span
      title={unsure ? 'AI was not sure about this one. Please check it.' : 'Suggested by AI. Please review.'}
      className={cn(
        'inline-flex h-5 items-center gap-1 rounded px-1.5 text-[11px] font-medium whitespace-nowrap',
        unsure ? 'bg-amber-50 text-amber-700' : 'bg-accent-soft text-accent-hover',
      )}
    >
      <Sparkles className="size-3" aria-hidden="true" />
      {unsure ? 'AI · check this' : 'AI-filled · review'}
    </span>
  )
}
