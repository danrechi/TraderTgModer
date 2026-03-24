import { useState, useEffect } from 'react'
import { api } from '../api'

export default function News() {
  const [news,    setNews]    = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState('')

  useEffect(() => {
    api.getNews()
      .then(setNews)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <div className="page-header">
        <h2>Новости</h2>
        <p>Статьи, собранные из RSS-источников</p>
      </div>

      {error   && <div className="error-banner">{error}</div>}
      {loading && <div className="loading-state">Загрузка новостей...</div>}

      {!loading && !error && news.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">N</div>
          <p>Новостей пока нет. Добавьте RSS-источники и запустите парсер.</p>
        </div>
      )}

      {!loading && news.length > 0 && (
        <div className="news-grid">
          {news.map(item => (
            <div className="news-card" key={item.id}>
              <a className="news-card-title" href={item.url} target="_blank" rel="noreferrer">
                {item.title}
              </a>
              <div className="news-card-meta">
                {item.source_name && <span>Источник: {item.source_name}</span>}
                {item.published_at && <span>{item.published_at}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
