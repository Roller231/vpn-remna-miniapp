const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
const TOKEN_KEY = 'vpn_jwt'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t)
export const clearToken = () => localStorage.removeItem(TOKEN_KEY)

async function request(method, path, body = null, auth = true) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth) {
    const t = getToken()
    if (t) headers['Authorization'] = `Bearer ${t}`
  }
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (res.status === 204) return null
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw Object.assign(new Error(data?.detail || `HTTP ${res.status}`), { status: res.status })
  return data
}

const get  = (path, auth = true) => request('GET', path, null, auth)
const post = (path, body, auth = true) => request('POST', path, body, auth)

export const authTelegram = (initData) =>
  post('/auth/telegram', { init_data: initData }, false)

export const fetchMe = () => get('/users/me')
export const fetchCatalog = () => get('/subscriptions/catalog', false)

export const purchaseWithYookassa = (planId, returnUrl) => {
  const p = new URLSearchParams({ plan_id: planId })
  if (returnUrl) p.append('return_url', returnUrl)
  return post(`/subscriptions/purchase-with-yookassa?${p}`, null)
}

export const createStarsInvoice = (planId) => {
  const p = new URLSearchParams({ plan_id: planId })
  return post(`/subscriptions/create-stars-invoice?${p}`, null)
}

export const purchaseFromBalance = (planId) =>
  post('/subscriptions/purchase', { plan_id: planId, pay_from_balance: true })

export const activateTrial = (planId) =>
  post('/subscriptions/trial', { plan_id: planId })

export const fetchReferralLink = () => get('/users/me/referral-link')
export const fetchReferralStats = () => get('/referrals/stats')
export const fetchLoginLink   = () => get('/users/me/login-link')
export const fetchMySubscriptions = () => get('/subscriptions/my')
