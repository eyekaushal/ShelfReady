/** Shared classes for Input, Select, Textarea and PasswordInput, so every field looks the same. */
export const fieldClasses =
  'w-full rounded-md border bg-white text-sm text-gray-900 placeholder:text-gray-400 ' +
  'transition-[border-color,box-shadow] duration-150 ' +
  'hover:border-gray-300 focus:border-accent focus:ring-2 focus:ring-accent-ring focus:outline-none ' +
  'disabled:bg-gray-50 disabled:text-gray-500'

export function fieldBorder(invalid) {
  return invalid ? 'border-red-300 focus:border-red-400 focus:ring-red-100' : 'border-gray-200'
}
