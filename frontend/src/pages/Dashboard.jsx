import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

export default function Dashboard() {
  const [counts, setCounts] = useState({ sources: '—', news: '—', rules: '—' })

  useEffect(() => {
    //загружаем статистику из реального API
    Promise.all([api.getSources(), api.getNews(), api.getRules()])
      .then(([sources, news, rules]) => {
        setCounts({
          sources: sources.length,
          news:    news.length,
          rules:   rules.length,
        })
      })
      .catch(() => {}) //ошибки на дашборде просто игнорируем
  }, [])

  const stats = [
    { icon: 'S', label: 'RSS-источников',    value: counts.sources, bg: 'rgba(99,179,237,0.12)'  },
    { icon: 'N', label: 'Новостей',          value: counts.news,    bg: 'rgba(72,187,120,0.12)'  },
    { icon: 'R', label: 'Правил фильтрации', value: counts.rules,   bg: 'rgba(159,122,234,0.12)' },
  ]

  const quickLinks = [
    { to: '/sources', icon: 'S', title: 'Управление источниками', desc: 'Добавить и настроить RSS-ленты' },
    { to: '/news',    icon: 'N', title: 'Просмотр новостей',     desc: 'Последние статьи из RSS'        },
    { to: '/rules',   icon: 'R', title: 'Правила антиспама',     desc: 'Настроить фильтрацию сообщений' },
  ]

  return (
    <div>
      <div className="page-header">
        <h2>Дашборд</h2>
        <p>Данные из базы данных в реальном времени</p>
      </div>

      <div className="stats-grid">
        {stats.map(({ icon, label, value, bg }) => (
          <div className="stat-card" key={label}>
            <div className="stat-icon" style={{ background: bg }}>{icon}</div>
            <div className="stat-info">
              <h3>{value}</h3>
              <p>{label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Быстрые переходы</h3>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
          Управление ключевыми разделами системы
        </p>
        <div className="quick-links">
          {quickLinks.map(({ to, icon, title, desc }) => (
            <Link className="quick-link-card" to={to} key={to}>
              <span className="ql-icon">{icon}</span>
              <span className="ql-title">{title}</span>
              <span className="ql-desc">{desc}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
