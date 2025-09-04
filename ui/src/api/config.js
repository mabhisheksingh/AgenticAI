// Central API config (fetch-only)
const SERVER_URL = (import.meta.env.VITE_SERVER_URL || '').replace(/\/$/, '')
const API_PATH = (import.meta.env.VITE_API_PATH || '/v1')
const DIRECT_API_BASE = import.meta.env.VITE_API_BASE_URL

// If VITE_API_BASE_URL is explicitly set, use it.
// Else, if VITE_SERVER_URL is provided, combine it with VITE_API_PATH.
// Else, fall back to just the API path (works with Vite proxy in dev).
export const API_BASE_URL = DIRECT_API_BASE
  ? DIRECT_API_BASE
  : SERVER_URL
  ? `${SERVER_URL}${API_PATH.startsWith('/') ? API_PATH : `/${API_PATH}`}`
  : (API_PATH || '/v1')

export const DEFAULT_TIMEOUT_MS = Number(import.meta.env.VITE_REQUEST_TIMEOUT_MS || 30000)

// Common header keys used by backend
// Note: FastAPI converts snake_case parameter names to kebab-case headers
export const HEADER_USER_ID = 'user-id'
export const HEADER_THREAD_ID = 'thread-id'
