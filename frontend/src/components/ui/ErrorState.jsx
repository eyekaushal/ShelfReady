import { AlertTriangle, RotateCw } from 'lucide-react'

import { Button } from './Button'

/** Something failed to load: message + retry. `error` is an ApiError. */
export function ErrorState({ error, onRetry, title = "Couldn't load this" }) {
  return (
    <div className="flex flex-col items-center px-6 py-16 text-center">
      <div className="mb-4 flex size-11 items-center justify-center rounded-full bg-red-50 text-red-600">
        <AlertTriangle className="size-5" aria-hidden="true" />
      </div>
      <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
      <p className="mt-1 max-w-sm text-sm text-gray-500">{error?.message || 'Something went wrong.'}</p>
      {onRetry ? (
        <Button className="mt-5" onClick={onRetry}>
          <RotateCw className="size-4" />
          Try again
        </Button>
      ) : null}
    </div>
  )
}
