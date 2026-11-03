import { Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'

import { cn } from '../../lib/cn'
import { fieldBorder, fieldClasses } from './fieldStyles'

/** Password field with a show/hide toggle. */
export function PasswordInput({ invalid = false, className, ...props }) {
  const [visible, setVisible] = useState(false)

  return (
    <div className={cn('relative', className)}>
      <input
        type={visible ? 'text' : 'password'}
        className={cn(fieldClasses, fieldBorder(invalid), 'h-9 pl-3 pr-10')}
        aria-invalid={invalid || undefined}
        {...props}
      />
      <button
        type="button"
        onClick={() => setVisible((value) => !value)}
        className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-gray-400 hover:text-gray-700"
        aria-label={visible ? 'Hide password' : 'Show password'}
      >
        {visible ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
      </button>
    </div>
  )
}
