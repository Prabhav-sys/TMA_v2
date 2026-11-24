export async function api(path, { method = 'GET', body, raw = false } = {}) {
  const token = localStorage.getItem('token')
  const headers = {}
  if (body) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  let res
  try {
    res = await fetch('/api' + path, { method, headers, body: body ? JSON.stringify(body) : undefined })
  } catch {
    throw new Error('Cannot reach the server. Is the Flask backend running?')
  }
  if (raw && res.ok) return res
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    if (res.status === 401 && token) window.dispatchEvent(new Event('auth-expired'))
    throw new Error(data.error || 'Request failed')
  }
  return data
}

export const get = (p) => api(p)
export const post = (p, body = {}) => api(p, { method: 'POST', body })
export const put = (p, body = {}) => api(p, { method: 'PUT', body })
export const del = (p) => api(p, { method: 'DELETE' })

export function qs(params) {
  const s = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => v !== '' && v != null && s.append(k, v))
  const out = s.toString()
  return out ? '?' + out : ''
}
