import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { to: '/',        label: 'Дашборд',   icon: '📊' },
  { to: '/sources', label: 'Источники', icon: '📡' },
  { to: '/news',    label: 'Новости',   icon: '📰' },
  { to: '/rules',   label: 'Правила',   icon: '🛡️' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">📈</div>
        <div>
          <h1>Trader News</h1>
          <span>Admin Panel</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => 'nav-item' + (isActive ? ' active' : '')}
          >
            <span className="nav-icon">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Блок пользователя с кнопкой выхода */}
      <div>
        <div className="sidebar-user">
          <div className="sidebar-user-icon">👤</div>
          <span className="sidebar-user-name">{user || 'admin'}</span>
          <button className="btn-logout" onClick={handleLogout} title="Выйти">⏻</button>
        </div>
        <div className="sidebar-footer">Trader News Bot v0.3</div>
      </div>
    </aside>
  )
}
