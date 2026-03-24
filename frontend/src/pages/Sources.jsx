import { useState, useEffect } from 'react'
import { api } from '../api'

export default function Sources() {
  const [sources,  setSources]  = useState([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState('')
  const [name,     setName]     = useState('')
  const [url,      setUrl]      = useState('')
  const [adding,   setAdding]   = useState(false)
  const [addError, setAddError] = useState('')

  //загружаем источники из API при монтировании
  useEffect(() => {
    api.getSources()
      .then(setSources)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  async function handleAdd(e) {
    e.preventDefault()
    if (!name.trim() || !url.trim()) return
    setAdding(true)
    setAddError('')
    try {
      const created = await api.createSource({ name, url })
      setSources(prev => [...prev, created])
      setName(''); setUrl('')
    } catch (err) {
      setAddError(err.message)
    } finally {
      setAdding(false)
    }
  }

  async function handleDelete(id) {
    try {
      await api.deleteSource(id)
      setSources(prev => prev.filter(s => s.id !== id))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>RSS-источники</h2>
        <p>Управление лентами финансовых новостей</p>
      </div>

      <div className="add-form">
        <h4>➕ Добавить источник</h4>
        <form onSubmit={handleAdd}>
          <div className="form-row">
            <div className="form-group">
              <label>Название</label>
              <input value={name} onChange={e => setName(e.target.value)} placeholder="Например: РБК Финансы" />
            </div>
            <div className="form-group">
              <label>URL RSS-ленты</label>
              <input value={url} onChange={e => setUrl(e.target.value)} placeholder="https://..." />
            </div>
            <button type="submit" className="btn btn-primary" disabled={adding}>
              {adding ? 'Сохранение...' : 'Добавить'}
            </button>
          </div>
          {addError && <div className="error-msg">{addError}</div>}
        </form>
      </div>

      <div className="card">
        <div className="section-header">
          <h3>Все источники ({sources.length})</h3>
        </div>

        {error   && <div className="error-banner">⚠️ {error}</div>}
        {loading && <div className="loading-state">⏳ Загрузка...</div>}

        {!loading && !error && sources.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">📡</div>
            <p>Источников пока нет. Добавьте первый RSS-источник.</p>
          </div>
        )}

        {!loading && sources.length > 0 && (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr><th>#</th><th>Название</th><th>URL</th><th>Статус</th><th>Действие</th></tr>
              </thead>
              <tbody>
                {sources.map(s => (
                  <tr key={s.id}>
                    <td style={{ color: 'var(--text-muted)' }}>{s.id}</td>
                    <td style={{ fontWeight: 500 }}>{s.name}</td>
                    <td><a className="url-link" href={s.url} target="_blank" rel="noreferrer">{s.url}</a></td>
                    <td>
                      <span className={`badge ${s.is_active ? 'badge-green' : 'badge-red'}`}>
                        {s.is_active ? 'Активен' : 'Отключён'}
                      </span>
                    </td>
                    <td>
                      <button className="btn btn-danger" onClick={() => handleDelete(s.id)}>🗑 Удалить</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
