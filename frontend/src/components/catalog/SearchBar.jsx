import { Search, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { useDebounce } from '../../hooks/useDebounce'
import { Input } from '../ui/Input'

/**
 * Keyword search box. Typing updates the URL after a 300 ms pause, so we don't hit the API
 * on every keystroke. Pressing "/" anywhere on the page focuses it (like Linear).
 * It's type="text", not "search": browsers add their own second clear button to search inputs.
 */
export function SearchBar({ value, onChange }) {
  const [text, setText] = useState(value)
  const [lastValue, setLastValue] = useState(value)
  const debounced = useDebounce(text, 300)
  const inputRef = useRef(null)

  // When the URL changes from elsewhere (chip removed, "Clear filters", AI search), follow it.
  if (value !== lastValue) {
    setLastValue(value)
    setText(value)
  }

  // Push the debounced text to the URL (only when it actually differs).
  useEffect(() => {
    if (debounced !== value) onChange(debounced)
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

  return (
    <Input
      ref={inputRef}
      type="text"
      value={text}
      onChange={(event) => setText(event.target.value)}
      placeholder="Search name, brand or description"
      aria-label="Search products"
      leading={<Search className="size-4" />}
      trailing={
        text ? (
          <button
            type="button"
            onClick={() => setText('')}
            className="pointer-events-auto rounded p-0.5 text-gray-400 hover:text-gray-700"
            aria-label="Clear search"
          >
            <X className="size-3.5" />
          </button>
        ) : (
          <kbd className="rounded border border-gray-200 bg-gray-50 px-1.5 font-sans text-[11px] text-gray-400">/</kbd>
        )
      }
      className="min-w-0 flex-1"
    />
  )
}
