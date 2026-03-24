const API_BASE = 'http://127.0.0.1:8000'

//формируем заголовки — добавляем JWT если есть
function getHeaders(isJson = true) {
  const token = localStorage.getItem('token')
  return {
    ...(isJson ? { 'Content-Type': 'application/json' } : {}),
    ...(token   ? { Authorization: `Bearer ${token}` } : {}),
  }
}

//базовая функция запроса с обработкой ошибок
async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...getHeaders(), ...options.headers },
  })

  //401 — токен истёк или невалиден
  if (response.status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.href = '/login'
    return
  }

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Ошибка сервера: HTTP ${response.status}`)
  }

  if (response.status === 204) return null
  return response.json()
}

//API-методы для всех сущностей
export const api = {
  //Sources
  getSources:   ()     => apiFetch('/sources/'),
  createSource: (data) => apiFetch('/sources/', { method: 'POST', body: JSON.stringify(data) }),
  deleteSource: (id)   => apiFetch(`/sources/${id}`, { method: 'DELETE' }),

  //News
  getNews: () => apiFetch('/news/'),

  //Rules
  getRules:   ()     => apiFetch('/rules/'),
  createRule: (data) => apiFetch('/rules/', { method: 'POST', body: JSON.stringify(data) }),
  deleteRule: (id)   => apiFetch(`/rules/${id}`, { method: 'DELETE' }),

  //Auth — логин использует JSON
  login: (username, password) =>
    apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  register: (username, password) =>
    apiFetch('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
}
