import { Loader2 } from 'lucide-react'
import { Link } from 'react-router-dom'

import { cn } from '../../lib/cn'

const variants = {
  primary: 'bg-accent text-white hover:bg-accent-hover shadow-[inset_0_1px_0_rgb(255_255_255/0.15)]',
  secondary: 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50 hover:border-gray-300',
  ghost: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
  danger: 'bg-red-600 text-white hover:bg-red-700',
}

const sizes = {
  sm: 'h-8 px-2.5 text-[13px] gap-1.5 rounded-md',
  md: 'h-9 px-3.5 text-sm gap-2 rounded-md',
  icon: 'h-8 w-8 rounded-md',
}

/**
 * <Button variant="primary|secondary|ghost|danger" size="sm|md|icon" to="/route" loading>
 * Passing `to` renders a React Router <Link> with the same look.
 */
export function Button({
  variant = 'secondary',
  size = 'md',
  to,
  loading = false,
  disabled = false,
  className,
  children,
  type = 'button',
  ...props
}) {
  const classes = cn(
    'inline-flex items-center justify-center font-medium whitespace-nowrap select-none',
    'transition-colors duration-150 disabled:opacity-50 disabled:pointer-events-none',
    variants[variant],
    sizes[size],
    className,
  )

  if (to) {
    return (
      <Link to={to} className={classes} {...props}>
        {children}
      </Link>
    )
  }

  return (
    <button type={type} className={classes} disabled={disabled || loading} {...props}>
      {loading ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : null}
      {children}
    </button>
  )
}
