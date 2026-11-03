/** A titled card that groups related fields (Stripe's form layout). */
export function FormSection({ title, description, children }) {
  return (
    <section className="rounded-lg border border-gray-200 bg-white">
      <header className="border-b border-gray-100 px-5 py-3.5">
        <h2 className="text-sm font-semibold text-gray-900">{title}</h2>
        {description ? <p className="mt-0.5 text-xs text-gray-500">{description}</p> : null}
      </header>
      <div className="space-y-4 px-5 py-4">{children}</div>
    </section>
  )
}
