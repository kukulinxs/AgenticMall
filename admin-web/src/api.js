const API_PREFIX = import.meta.env.VITE_API_PREFIX || '/api/shop/goods'

async function request(path, options = {}) {
  const response = await fetch(`${API_PREFIX}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options
  })
  const payload = await response.json()
  if (!response.ok) throw new Error(payload.detail || '请求失败')
  if (payload.code !== 0) throw new Error(payload.msg || '操作失败')
  return payload.data
}

export function listGoods(filters) {
  const query = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== '' && value != null) query.set(key, value)
  })
  const suffix = query.size ? `?${query}` : ''
  return request(`/list${suffix}`)
}

export function createGoods(payload) {
  return request('/add', { method: 'POST', body: JSON.stringify(payload) })
}

export function updateGoods(payload) {
  return request('/update', { method: 'PUT', body: JSON.stringify(payload) })
}

export function setGoodsStatus(goods_id, target_status) {
  return request('/status', { method: 'PUT', body: JSON.stringify({ goods_id, target_status }) })
}

export function removeGoods(goods_id) {
  return request('/delete', { method: 'DELETE', body: JSON.stringify({ goods_id }) })
}
