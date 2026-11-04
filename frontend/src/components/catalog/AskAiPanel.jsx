import { Sparkles, X } from 'lucide-react'
import { useState } from 'react'

import { Button } from '../ui/Button'
import { Input } from '../ui/Input'

// Each one finds products in the demo catalog, so a first-time visitor gets a real result.
const EXAMPLES = ['Cheapest noodles', 'Parle biscuits under ₹20', 'Masala chips under ₹30', 'Most expensive coffee']

/**
 * The separate box for AI search, opened by the "Ask AI" button. The keyword search box above
 * never changes its meaning. Clicking an example asks it straight away.
 */
export function AskAiPanel({ onAsk, asking, onClose }) {
  const [query, setQuery] = useState('')
  const canAsk = query.trim().length >= 2 && !asking

  const submit = (event) => {
    event.preventDefault()
    if (canAsk) onAsk(query.trim())
  }

  const askExample = (example) => {
    setQuery(example)
    onAsk(example)
  }

  return (
    <section className="rounded-lg border border-accent-ring bg-accent-soft/40 p-4 animate-fade-in" aria-label="Ask AI">
      <div className="mb-2.5 flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-gray-900">
          <Sparkles className="size-4 text-accent" aria-hidden="true" />
          Describe what you need
        </h2>
        <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close Ask AI" className="-my-1 -mr-1">
          <X className="size-4" />
        </Button>
      </div>

      <form onSubmit={submit} className="flex items-center gap-2">
        <Input
          type="text"
          autoFocus
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => event.key === 'Escape' && onClose()}
          placeholder="e.g. Britannia biscuits under ₹50, cheapest first"
          aria-label="Describe what you are looking for"
          maxLength={200}
          className="min-w-0 flex-1"
        />
        <Button type="submit" variant="primary" disabled={!canAsk} loading={asking}>
          {asking ? 'Asking…' : 'Ask'}
        </Button>
      </form>

      <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
        <span className="text-xs text-gray-500">Try:</span>
        {EXAMPLES.map((example) => (
          <button
            key={example}
            type="button"
            onClick={() => askExample(example)}
            disabled={asking}
            className="rounded-full border border-gray-200 bg-white px-2.5 py-1 text-xs text-gray-700 transition-colors hover:border-accent-ring hover:text-accent-hover disabled:opacity-50"
          >
            {example}
          </button>
        ))}
      </div>
    </section>
  )
}
