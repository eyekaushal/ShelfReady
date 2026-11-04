import { CornerDownLeft, Loader2, Search, Sparkles, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { useDebounce } from '../../hooks/useDebounce'
import { cn } from '../../lib/cn'
import { Input } from '../ui/Input'

/**
 * Search box with two modes:
 * - Keyword (default): typing updates the URL after a 300 ms pause. "/" focuses it (like Linear).
 * - Ask AI: type a sentence and press Enter; `onAsk(sentence)` turns it into filters.
 */
export function SearchBar({ value, onChange, aiEnabled = false, onAsk, asking = false }) {
  const [mode, setMode] = useState('keyword')
  const [text, setText] = useState(value)
  const [lastValue, setLastValue] = useState(value)
  const debounced = useDebounce(text, 300)
  const inputRef = useRef(null)
  const isAi = mode === 'ai'

  // In keyword mode, follow URL changes made elsewhere (chip removed, "Clear filters").
  if (value !== lastValue) {
    setLastValue(value)
    if (!isAi) setText(value)
  }

  // Keyword mode only: push the debounced text to the URL when it actually differs.
  useEffect(() => {
    if (!isAi && debounced !== value) onChange(debounced)
  }, [debounced]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const onKey = (event) => {
      const typing = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)
      if (event.key === '/' && !typing) {
        event.preventDefault()
        inputRef.current?.focus()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [])

  const toggleMode = () => {
    const next = isAi ? 'keyword' : 'ai'
    setMode(next)
    setText(next === 'keyword' ? value : '')
    inputRef.current?.focus()
  }

  const submit = (event) => {
    event.preventDefault()
    if (isAi && text.trim().length >= 2 && !asking) onAsk(text.trim())
  }

  let trailing
  if (isAi) {
    trailing = asking ? (
      <Loader2 className="size-4 animate-spin text-accent" aria-label="Asking AI" />
    ) : (
      <kbd className="flex items-center rounded border border-gray-200 bg-gray-50 px-1 text-gray-400" title="Press Enter">
        <CornerDownLeft className="size-3" aria-hidden="true" />
      </kbd>
    )
  } else if (text) {
    trailing = (
      <button
        type="button"
        onClick={() => setText('')}
        className="pointer-events-auto rounded p-0.5 text-gray-400 hover:text-gray-700"
        aria-label="Clear search"
      >
        <X className="size-3.5" />
      </button>
    )
  } else {
    trailing = <kbd className="rounded border border-gray-200 bg-gray-50 px-1.5 font-sans text-[11px] text-gray-400">/</kbd>
  }

  return (
    <form onSubmit={submit} className="flex w-full items-center gap-2 sm:max-w-lg" role="search">
      <Input
        ref={inputRef}
        type="search"
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder={isAi ? 'e.g. Britannia biscuits under ₹50, cheapest first' : 'Search name, brand or description'}
        aria-label={isAi ? 'Describe what you are looking for' : 'Search products'}
        leading={isAi ? <Sparkles className="size-4 text-accent" /> : <Search className="size-4" />}
        trailing={trailing}
        maxLength={200}
        className={cn('min-w-0 flex-1', isAi && '[&_input]:border-accent-ring')}
      />
      {aiEnabled ? (
        <button
          type="button"
          onClick={toggleMode}
          aria-pressed={isAi}
          title={isAi ? 'Back to keyword search' : 'Search with a sentence'}
          className={cn(
            'inline-flex h-9 shrink-0 items-center gap-1.5 rounded-md border px-3 text-sm font-medium transition-colors duration-150',
            isAi
              ? 'border-accent-ring bg-accent-soft text-accent-hover'
              : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50',
          )}
        >
          <Sparkles className={cn('size-4', isAi ? 'text-accent' : 'text-gray-500')} aria-hidden="true" />
          Ask AI
        </button>
      ) : null}
    </form>
  )
}
