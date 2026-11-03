import { BookOpen, LogOut, Package, Plus } from 'lucide-react'
import { NavLink } from 'react-router-dom'

import { API_BASE_URL } from '../../api/apiClient'
import { useAuth } from '../../auth/useAuth'
import { cn } from '../../lib/cn'
import { Avatar } from '../ui/Avatar'
import { Button } from '../ui/Button'
import { Wordmark } from './Wordmark'

const itemClasses =
  'flex h-8 items-center gap-2.5 rounded-md px-2 text-[13px] font-medium transition-colors duration-150'

function NavItem({ to, icon: Icon, children, end = false, onNavigate }) {
  return (
    <NavLink
      to={to}
      end={end}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(itemClasses, isActive ? 'bg-gray-100 text-gray-900' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900')
      }
    >
      <Icon className="size-4 shrink-0 text-gray-500" aria-hidden="true" />
      {children}
    </NavLink>
  )
}

function SectionLabel({ children }) {
  return <p className="mb-1 mt-5 px-2 text-[11px] font-medium uppercase tracking-wider text-gray-400">{children}</p>
}

export function Sidebar({ className, onNavigate }) {
  const { user, logout } = useAuth()

  return (
    <aside className={cn('w-60 shrink-0 flex-col border-r border-gray-200 bg-white', className)}>
      <div className="flex h-14 items-center px-4">
        <Wordmark />
      </div>

      <nav className="flex-1 px-3">
        <SectionLabel>Workspace</SectionLabel>
        <NavItem to="/" icon={Package} end onNavigate={onNavigate}>
          Catalog
        </NavItem>
        <NavItem to="/products/new" icon={Plus} onNavigate={onNavigate}>
          Add product
        </NavItem>

        <SectionLabel>Resources</SectionLabel>
        <a
          href={`${API_BASE_URL}/docs/`}
          target="_blank"
          rel="noreferrer"
          className={cn(itemClasses, 'text-gray-600 hover:bg-gray-50 hover:text-gray-900')}
        >
          <BookOpen className="size-4 shrink-0 text-gray-500" aria-hidden="true" />
          API docs
        </a>
      </nav>

      <div className="border-t border-gray-200 p-3">
        {user ? (
          <div className="flex items-center gap-2.5 px-1">
            <Avatar name={user.username} className="size-7 text-xs" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-medium text-gray-900">{user.username}</p>
              <p className="truncate text-xs text-gray-500">{user.is_staff ? 'Staff' : 'Catalog manager'}</p>
            </div>
            <Button variant="ghost" size="icon" onClick={logout} aria-label="Log out" title="Log out">
              <LogOut className="size-4" />
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            <Button variant="primary" to="/login" className="w-full" onClick={onNavigate}>
              Sign in
            </Button>
            <p className="text-center text-xs text-gray-500">
              New here?{' '}
              <NavLink to="/register" className="font-medium text-gray-700 hover:text-gray-900" onClick={onNavigate}>
                Create an account
              </NavLink>
            </p>
          </div>
        )}
      </div>
    </aside>
  )
}
