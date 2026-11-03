/**
 * Client-side rules that mirror backend/catalog/serializers/product_serializer.py,
 * so the user sees problems before the request is sent. The backend is still the
 * source of truth; its errors are mapped onto the same fields.
 */

const GTIN_LENGTHS = [8, 12, 13, 14]

/** GS1 mod-10 check digit, same algorithm as services/gtin_validator.py. */
export function gtinCheckDigit(digits) {
  let total = 0
  const reversed = digits.split('').reverse()
  reversed.forEach((char, position) => {
    total += Number(char) * (position % 2 === 0 ? 3 : 1)
  })
  return (10 - (total % 10)) % 10
}

export function gtinError(raw) {
  const gtin = (raw || '').replace(/[\s-]/g, '')
  if (!gtin) return null
  if (!/^\d+$/.test(gtin)) return 'GTIN must contain digits only.'
  if (!GTIN_LENGTHS.includes(gtin.length)) return 'GTIN must be 8, 12, 13 or 14 digits long.'
  if (Number(gtin.at(-1)) !== gtinCheckDigit(gtin.slice(0, -1))) {
    return 'GTIN check digit is wrong. Please re-check the barcode number.'
  }
  return null
}

export function isHttpUrl(value) {
  try {
    const url = new URL(value)
    return url.protocol === 'http:' || url.protocol === 'https:'
  } catch {
    return false
  }
}

export function parseTags(text) {
  const cleaned = (text || '')
    .split(',')
    .map((tag) => tag.trim().toLowerCase())
    .filter(Boolean)
  return [...new Set(cleaned)]
}

/** Returns {field: message} for every invalid field. Empty object = valid. */
export function validateProduct(values) {
  const errors = {}
  const name = values.name.trim()
  const brand = values.brand.trim()

  if (name.length < 2) errors.name = 'Name must be at least 2 characters.'
  else if (name.length > 200) errors.name = 'Name must be 200 characters or fewer.'

  if (brand.length < 2) errors.brand = 'Brand must be at least 2 characters.'
  else if (brand.length > 100) errors.brand = 'Brand must be 100 characters or fewer.'

  if (!values.category) errors.category = 'Pick a category.'

  if (!values.description.trim()) errors.description = 'Add a short description.'
  else if (values.description.length > 2000) errors.description = 'Description must be 2000 characters or fewer.'

  const price = values.price.trim()
  if (!price) errors.price = 'Enter a price.'
  else if (!/^\d+(\.\d{1,2})?$/.test(price)) errors.price = 'Use a number with up to 2 decimals, e.g. 45.00.'
  else if (Number(price) <= 0) errors.price = 'Must be greater than 0.'

  if (values.image_url.trim() && !isHttpUrl(values.image_url.trim())) {
    errors.image_url = 'Enter a valid http or https URL.'
  }

  const gtinProblem = gtinError(values.gtin)
  if (gtinProblem) errors.gtin = gtinProblem

  if (values.pack_size.length > 50) errors.pack_size = 'Pack size must be 50 characters or fewer.'
  if (values.variant.length > 100) errors.variant = 'Variant must be 100 characters or fewer.'

  const tags = parseTags(values.tags)
  if (tags.length > 10) errors.tags = 'Use at most 10 tags.'
  else if (tags.some((tag) => tag.length > 40)) errors.tags = 'Each tag must be 40 characters or fewer.'

  return errors
}
