import { useState, useEffect } from 'react'
import { api } from '../api'

const ACTION = {
  delete: { label: 'Удалить',        cls: 'badge-red'    },
  warn:   { label: 'Предупреждение', cls: 'badge-yellow' },
  ban:    { label: 'Бан',            cls: 'badge-red'    },
}

const TYPE = {
  keyword: { label: 'Ключевое слово', cls: 'badge-blue'   },
  regex:   { label: 'Регулярка',      cls: 'badge-yellow' },
  link:    { label: 'Ссылка',         cls: 'badge-blue'   },
}

export default function Rules() {
  const [rules,    setRules]   = useState([])
  const [loading,  setLoading] = useState(true)
  const [error,    setError]   = useState('')
  const [type,     setType]    = useState('keyword')
  const [pattern,  setPattern] = useState('')
  const [action,   setAction]  = useState('delete')
  const [adding,   setAdding]  = useState(false)
  const [addError, setAddError]= useState('')

  useEffect(() => {
    api.getRules()
      .then(setRules)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  async function handleAdd(e) {
    e.preventDefault()
    if (!pattern.trim()) return
    setAdding(true)
    setAddError('')
    try {
      const created = await api.createRule({ type, pattern, action })
      setRules(prev => [...prev, created])
      setPattern('')
    } catch (err) {
      setAddError(err.message)
    } finally {
      setAdding(false)
    }
  }

  async function handleDelete(id) {
    try {
      await api.deleteRule(id)
      setRules(prev => prev.filter(r => r.id !== id))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>Правила фильтрации</h2>
        <p>Антиспам-правила для автоматической модерации чатов</p>
      </div>

      <div className="add-form">
        <h4>Добавить правило</h4>
        <form onSubmit={handleAdd}>
          <div className="form-row">
            <div className="form-group">
              <label>Тип</label>
              <select value={type} onChange={e => setType(e.target.value)}>
                <option value="keyword">Ключевое слово</option>
                <option value="regex">Регулярное выражение</option>
                <option value="link">По ссылке</option>
              </select>
            </div>
            <div className="form-group" style={{ flex: 2 }}>
              <label>Паттерн</label>
              <input value={pattern} onChange={e => setPattern(e.target.value)} placeholder="Слово, паттерн или URL..." />
            </div>
            <div className="form-group">
              <label>Действие</label>
              <select value={action} onChange={e => setAction(e.target.value)}>
                <option value="delete">Удалить</option>
                <option value="warn">Предупреждение</option>
                <option value="ban">Бан</option>
              </select>
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
          <h3>Все правила ({rules.length})</h3>
        </div>

        {error   && <div className="error-banner">{error}</div>}
        {loading && <div className="loading-state">Загрузка...</div>}

        {!loading && !error && rules.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">R</div>
            <p>Правил пока нет. Добавьте первое правило фильтрации.</p>
          </div>
        )}

        {!loading && rules.length > 0 && (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr><th>#</th><th>Тип</th><th>Паттерн</th><th>Действие</th><th>Удалить</th></tr>
              </thead>
              <tbody>
                {rules.map(r => (
                  <tr key={r.id}>
                    <td style={{ color: 'var(--text-muted)' }}>{r.id}</td>
                    <td><span className={`badge ${TYPE[r.type]?.cls ?? 'badge-blue'}`}>{TYPE[r.type]?.label ?? r.type}</span></td>
                    <td style={{ fontFamily: 'monospace', fontSize: '13px' }}>{r.pattern}</td>
                    <td><span className={`badge ${ACTION[r.action]?.cls ?? 'badge-red'}`}>{ACTION[r.action]?.label ?? r.action}</span></td>
                    <td><button className="btn btn-danger" onClick={() => handleDelete(r.id)}>Удалить</button></td>
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
