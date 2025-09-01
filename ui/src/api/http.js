import { API_BASE_URL, DEFAULT_TIMEOUT_MS } from './config'

// Simple timeout wrapper for fetch
function fetchWithTimeout(resource, options = {}, timeout = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), timeout)
  return fetch(resource, { ...options, signal: options.signal || controller.signal })
    .finally(() => clearTimeout(id))
}

// Build URL with base
function buildUrl(path) {
  if (!path) return API_BASE_URL
  if (path.startsWith('http')) return path
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}

function buildQuery(params) {
  if (!params || typeof params !== 'object') return ''
  const usp = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null) return
    if (Array.isArray(v)) v.forEach((val) => usp.append(k, String(val)))
    else usp.append(k, String(v))
  })
  const qs = usp.toString()
  return qs ? `?${qs}` : ''
}

// Fetch adapter
async function fetchAdapter({ url, method = 'GET', headers, data, params, timeout, signal }) {
  const fullUrl = buildUrl(url) + buildQuery(params)
  const res = await fetchWithTimeout(fullUrl, {
    method,
    headers: { 'Content-Type': 'application/json', ...(headers || {}) },
    body: data != null ? JSON.stringify(data) : undefined,
    signal,
  }, timeout)
  const contentType = res.headers.get('content-type') || ''
  const body = contentType.includes('application/json') ? await res.json() : await res.text()
  if (!res.ok) {
    const err = new Error(typeof body === 'string' ? body : body?.message || 'Request failed')
    err.status = res.status
    err.data = body
    throw err
  }
  return { status: res.status, data: body }
}

// We standardize on fetch only
const adapter = fetchAdapter

export const http = {
  // Stable signatures across adapters
  // - get(url, { headers, params, timeout, signal })
  // - delete(url, { headers, params, timeout, signal })
  // - post/put/patch(url, data, { headers, params, timeout, signal })
  get: (url, config = {}) => adapter({ url, method: 'GET', ...config }),
  delete: (url, config = {}) => adapter({ url, method: 'DELETE', ...config }),
  post: (url, data, config = {}) => adapter({ url, method: 'POST', data, ...config }),
  put: (url, data, config = {}) => adapter({ url, method: 'PUT', data, ...config }),
  patch: (url, data, config = {}) => adapter({ url, method: 'PATCH', data, ...config }),
  buildUrl,
}
