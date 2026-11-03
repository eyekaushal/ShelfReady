import { Menu as MenuIcon } from 'lucide-react'
import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'

import { Button } from '../ui/Button'
import { Sidebar } from './Sidebar'
import { Wordmark } from './Wordmark'

/**
 * App frame: fixed sidebar on desktop, a top bar with a drawer on mobile,
 * and a scrolling main column where pages render.
 */
export function AppShell() {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const location = useLocation()
  const [lastPath, setLastPath] = useState(location.pathname)

  // Close the mobile drawer whenever the route changes.
  if (location.pathname !== lastPath) {
    setLastPath(location.pathname)
    setDrawerOpen(false)
  }

  return (
    <div className="flex min-h-screen bg-white">
      <Sidebar className="hidden md:flex" />

      {drawerOpen ? (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-gray-900/40 animate-fade-in" onClick={() => setDrawerOpen(false)} />
          <Sidebar className="relative h-full w-64 animate-slide-up" onNavigate={() => setDrawerOpen(false)} />
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center gap-2 border-b border-gray-200 px-4 md:hidden">
          <Button variant="ghost" size="icon" onClick={() => setDrawerOpen(true)} aria-label="Open menu">
            <MenuIcon className="size-5" />
          </Button>
          <Wordmark />
        </header>

        <main className="flex-1">
          <div className="mx-auto w-full max-w-[1200px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
