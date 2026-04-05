import { useState, useEffect } from 'react'
import { fetchTransactions } from '../api/client'
import './TransactionsPage.css'

const TYPE_META = {
  deposit:      { label: 'Пополнение',      icon: '⬇️', positive: true  },
  withdrawal:   { label: 'Вывод',           icon: '⬆️', positive: false },
  purchase:     { label: 'Покупка',         icon: '🛒', positive: false },
  renewal:      { label: 'Продление',       icon: '🔄', positive: false },
  cashback:     { label: 'Кэшбэк',         icon: '🎁', positive: true  },
  refund:       { label: 'Возврат',         icon: '↩️', positive: true  },
  admin_credit: { label: 'Зачисление',      icon: '✅', positive: true  },
  admin_debit:  { label: 'Списание',        icon: '❌', positive: false },
  traffic_reset:{ label: 'Сброс трафика',   icon: '📶', positive: false },
}

function formatDate(iso) {
  const d = new Date(iso)
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
    + ' · '
    + d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

export default function TransactionsPage() {
  const [items, setItems]     = useState([])
  const [total, setTotal]     = useState(0)
  const [page, setPage]       = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  useEffect(() => {
    setLoading(true)
    fetchTransactions(page)
      .then(data => {
        setItems(prev => page === 1 ? data.items : [...prev, ...data.items])
        setTotal(data.total)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [page])

  const hasMore = items.length < total

  return (
    <div className="tx-page">

      {/* Header card */}
      <div className="tx-header-card">
        <div className="tx-header-icon">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
            <line x1="8" y1="6" x2="21" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <line x1="8" y1="12" x2="21" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <line x1="8" y1="18" x2="21" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <line x1="3" y1="6" x2="3.01" y2="6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <line x1="3" y1="12" x2="3.01" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            <line x1="3" y1="18" x2="3.01" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
        <h1 className="tx-header-title">История операций</h1>
        <p className="tx-header-sub">
          Отслеживайте ваши траты с помощью общего списка транзакций
        </p>
      </div>

      {/* Content */}
      {loading && page === 1 ? (
        <div className="tx-empty-card">
          <p className="tx-empty-text">Загрузка…</p>
        </div>
      ) : error ? (
        <div className="tx-empty-card">
          <p className="tx-empty-text" style={{ color: '#ff6b6b' }}>{error}</p>
        </div>
      ) : items.length === 0 ? (
        <div className="tx-empty-card">
          <svg className="tx-empty-icon" width="40" height="40" viewBox="0 0 24 24" fill="none">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"
              stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
          </svg>
          <p className="tx-empty-text">Еще нет транзакций</p>
        </div>
      ) : (
        <div className="tx-list">
          {items.map(tx => {
            const meta = TYPE_META[tx.type] ?? { label: tx.type, icon: '💱', positive: true }
            const sign = meta.positive ? '+' : '−'
            return (
              <div key={tx.id} className="tx-item">
                <div className="tx-item-icon">{meta.icon}</div>
                <div className="tx-item-info">
                  <span className="tx-item-label">{tx.description || meta.label}</span>
                  <span className="tx-item-date">{formatDate(tx.created_at)}</span>
                </div>
                <span className={`tx-item-amount ${meta.positive ? 'pos' : 'neg'}`}>
                  {sign}{parseFloat(tx.amount).toFixed(2)} ₽
                </span>
              </div>
            )
          })}

          {hasMore && (
            <button className="tx-load-more" onClick={() => setPage(p => p + 1)} disabled={loading}>
              {loading ? 'Загрузка…' : 'Загрузить ещё'}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
