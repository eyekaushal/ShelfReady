import { Compass } from 'lucide-react'

import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'

export function NotFoundPage() {
  return (
    <EmptyState
      icon={Compass}
      title="Page not found"
      description="There's nothing on this shelf. Check the link, or head back to the catalog."
      action={<Button to="/">Back to catalog</Button>}
      className="min-h-[50vh] justify-center"
    />
  )
}
