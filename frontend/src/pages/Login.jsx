import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../api'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)
  const { login } = useAuth()
  const navigate  = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await api.login(username, password)
      login(data.access_token, username)
      navigate('/')
    } catch (err) {
      setError(err.message || 'Ошибка авторизации')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-bg">
      <div className="login-card">
        <div className="login-logo">📈</div>
        <h1 className="login-title">Trader News Bot</h1>
        <p className="login-subtitle">Admin Panel</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Логин</label>
            <input
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="admin"
              required
            />
          </div>

          <div className="form-group" style={{ marginTop: '14px' }}>
            <label>Пароль</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          {error && <div className="error-msg">{error}</div>}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
            style={{ width: '100%', justifyContent: 'center', marginTop: '20px', padding: '10px' }}
          >
            {loading ? 'Вход...' : '→ Войти'}
          </button>
        </form>

        <p className="login-hint">
          Нет аккаунта? Зарегистрируйтесь через <code>POST /auth/register</code>
        </p>
      </div>
    </div>
  )
}
