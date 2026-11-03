import { AlertCircle } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { Button } from '../components/ui/Button'
import { FormField } from '../components/ui/FormField'
import { Input } from '../components/ui/Input'
import { PasswordInput } from '../components/ui/PasswordInput'
import { useToast } from '../components/ui/toastContext'
import { toApiError } from '../lib/apiError'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const toast = useToast()
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState(null)
  const [busy, setBusy] = useState(false)

  const set = (field) => (event) => {
    const value = event.target.value
    setForm((current) => ({ ...current, [field]: value }))
    if (errors[field]) setErrors((current) => ({ ...current, [field]: undefined }))
  }

  const submit = async (event) => {
    event.preventDefault()
    const problems = {}
    if (form.username.trim().length < 3) problems.username = 'Use at least 3 characters.'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) problems.email = 'Enter a valid email address.'
    if (form.password.length < 8) problems.password = 'Use at least 8 characters.'
    setErrors(problems)
    if (Object.keys(problems).length) return

    setBusy(true)
    setFormError(null)
    try {
      const user = await register({ ...form, username: form.username.trim() })
      toast.success(`Welcome, ${user.username}.`)
      navigate('/', { replace: true })
    } catch (caught) {
      const apiError = toApiError(caught)
      setErrors(apiError.fieldErrors())
      setFormError(apiError.formMessage())
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <div>
        <h1 className="text-lg font-semibold text-gray-900">Create your account</h1>
        <p className="mt-1 text-sm text-gray-500">Add and manage products in the catalog.</p>
      </div>

      {formError ? (
        <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          {formError}
        </div>
      ) : null}

      <FormField label="Username" htmlFor="username" error={errors.username}>
        <Input id="username" value={form.username} onChange={set('username')} invalid={Boolean(errors.username)} autoComplete="username" autoFocus />
      </FormField>
      <FormField label="Email" htmlFor="email" error={errors.email}>
        <Input id="email" type="email" value={form.email} onChange={set('email')} invalid={Boolean(errors.email)} autoComplete="email" />
      </FormField>
      <FormField label="Password" htmlFor="password" error={errors.password} hint="At least 8 characters. Not just numbers, not too common.">
        <PasswordInput id="password" value={form.password} onChange={set('password')} invalid={Boolean(errors.password)} autoComplete="new-password" />
      </FormField>

      <Button type="submit" variant="primary" className="w-full" loading={busy}>
        Create account
      </Button>

      <p className="pt-2 text-center text-sm text-gray-500">
        Already have an account?{' '}
        <Link to="/login" className="font-medium text-gray-900 hover:text-accent">
          Sign in
        </Link>
      </p>
    </form>
  )
}
