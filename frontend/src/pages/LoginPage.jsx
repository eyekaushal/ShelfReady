import { AlertCircle } from 'lucide-react'
import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { Button } from '../components/ui/Button'
import { FormField } from '../components/ui/FormField'
import { Input } from '../components/ui/Input'
import { PasswordInput } from '../components/ui/PasswordInput'
import { toApiError } from '../lib/apiError'

// The public demo account created by `manage.py seed_catalog` (see README).
const DEMO = { username: 'demo', password: 'ShelfReady@2026' }

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const destination = location.state?.from?.pathname || '/'

  const signIn = async (credentials) => {
    setBusy(true)
    setError(null)
    try {
      await login(credentials.username, credentials.password)
      navigate(destination, { replace: true })
    } catch (caught) {
      const apiError = toApiError(caught)
      setError(apiError.code === 'no_active_account' ? 'Wrong username or password.' : apiError.message)
      setBusy(false)
    }
  }

  const set = (field) => (event) => setForm((current) => ({ ...current, [field]: event.target.value }))

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault()
        signIn(form)
      }}
      className="space-y-4"
    >
      <div>
        <h1 className="text-lg font-semibold text-gray-900">Welcome back</h1>
        <p className="mt-1 text-sm text-gray-500">Sign in to manage the catalog.</p>
      </div>

      {error ? (
        <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          {error}
        </div>
      ) : null}

      <FormField label="Username" htmlFor="username">
        <Input id="username" value={form.username} onChange={set('username')} autoComplete="username" autoFocus required />
      </FormField>
      <FormField label="Password" htmlFor="password">
        <PasswordInput id="password" value={form.password} onChange={set('password')} autoComplete="current-password" required />
      </FormField>

      <Button type="submit" variant="primary" className="w-full" loading={busy}>
        Sign in
      </Button>
      <Button type="button" variant="ghost" className="w-full" onClick={() => signIn(DEMO)} disabled={busy}>
        Use the demo account
      </Button>

      <p className="pt-2 text-center text-sm text-gray-500">
        No account?{' '}
        <Link to="/register" className="font-medium text-gray-900 hover:text-accent">
          Create one
        </Link>
      </p>
    </form>
  )
}
