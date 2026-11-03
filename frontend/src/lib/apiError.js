/**
 * One error shape for the whole frontend, mirroring the backend's
 * {"error": {"code", "message", "details"}} format.
 */
export class ApiError extends Error {
  constructor({ code = 'error', message = 'Something went wrong.', details = {}, status = 0 }) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.details = details
    this.status = status
  }

  /** Field errors as {field: "first message"}, ready to show under form inputs. */
  fieldErrors() {
    const out = {}
    for (const [field, messages] of Object.entries(this.details)) {
      out[field] = Array.isArray(messages) ? messages[0] : String(messages)
    }
    return out
  }

  /** Messages that don't belong to a specific field (shown at the top of a form). */
  formMessage() {
    const general = this.details.non_field_errors
    if (general) return Array.isArray(general) ? general.join(' ') : String(general)
    return this.code === 'validation_error' && Object.keys(this.details).length ? null : this.message
  }
}

export function toApiError(error) {
  return error instanceof ApiError ? error : new ApiError({ message: error?.message })
}
