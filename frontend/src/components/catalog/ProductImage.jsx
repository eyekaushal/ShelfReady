import { ImageOff } from 'lucide-react'
import { useState } from 'react'

import { cn } from '../../lib/cn'

/**
 * Pack shot on a light tile. Falls back to an icon when there's no URL or the image
 * fails to load (external URLs break; the catalog shouldn't look broken with them).
 */
export function ProductImage({ src, alt, className, iconClassName = 'size-5' }) {
  const [failed, setFailed] = useState(false)
  const showImage = src && !failed

  return (
    <div
      className={cn(
        'flex shrink-0 items-center justify-center overflow-hidden rounded-md border border-gray-200/80 bg-gray-50',
        className,
      )}
    >
      {showImage ? (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          onError={() => setFailed(true)}
          className="size-full object-contain p-1 mix-blend-multiply"
        />
      ) : (
        <ImageOff className={cn('text-gray-300', iconClassName)} aria-label="No image" />
      )}
    </div>
  )
}
