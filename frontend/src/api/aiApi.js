import { apiClient } from './apiClient'

// Reading a pack photo takes Claude a few seconds (more on a cold server), so allow longer
// than the client's default 20 s.
const AI_TIMEOUT = 60000

export const aiApi = {
  /** {enabled: bool}: false when the server has no API key, so AI buttons show "unavailable". */
  status: () => apiClient.get('/ai/status/'),

  /** Read a pack shot from a URL. Returns {fields, confidence, notes}. */
  extractFromUrl: (imageUrl) =>
    apiClient.post('/ai/extract-product/', { image_url: imageUrl }, { timeout: AI_TIMEOUT }),

  /** Read a pack shot from a file (one-off; the server doesn't store it). */
  extractFromFile: (file) => {
    const form = new FormData()
    form.append('image', file)
    return apiClient.post('/ai/extract-product/', form, { timeout: AI_TIMEOUT })
  },

  /** "Britannia biscuits under ₹50" → {filters: {search, brand, category, min_price, max_price, ordering}, cached} */
  parseSearch: (query) => apiClient.post('/ai/parse-search/', { query }, { timeout: AI_TIMEOUT }),

  /** {name, brand, category?, pack_size?, variant?} → {description, tags} */
  generateDescription: (details) =>
    apiClient.post('/ai/generate-description/', details, { timeout: AI_TIMEOUT }),
}
