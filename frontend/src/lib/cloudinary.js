import { ApiError } from './apiError'

/**
 * Optional photo hosting on Cloudinary (free tier), using an *unsigned* upload preset:
 * the browser uploads straight to Cloudinary and gets back a permanent https URL, so our
 * server never stores files. Without these two env vars, uploads still work for
 * photo → form, but the photo is only used once.
 *
 * Unsigned presets are public by design: restrict the preset in Cloudinary to image formats,
 * 5 MB and a "shelfready" folder (see the README).
 */
const CLOUD_NAME = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME
const UPLOAD_PRESET = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET

export const isCloudinaryEnabled = Boolean(CLOUD_NAME && UPLOAD_PRESET)

/** Upload an image file. Resolves to its permanent https URL. */
export async function uploadToCloudinary(file) {
  const form = new FormData()
  form.append('file', file)
  form.append('upload_preset', UPLOAD_PRESET)

  let response
  try {
    response = await fetch(`https://api.cloudinary.com/v1_1/${CLOUD_NAME}/image/upload`, {
      method: 'POST',
      body: form,
    })
  } catch {
    throw new ApiError({ code: 'upload_failed', message: "Couldn't upload the photo. Check your connection." })
  }

  const body = await response.json().catch(() => ({}))
  if (!response.ok || !body.secure_url) {
    throw new ApiError({
      code: 'upload_failed',
      message: body.error?.message || "Couldn't upload the photo. Please try again.",
    })
  }
  return body.secure_url
}
